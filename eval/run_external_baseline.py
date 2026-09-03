#!/usr/bin/env python3
"""
run_external_baseline.py — Same-harness CAMeL Tools baseline for the Jawhar paper.

Answers Reviewer 2, Comment 5: evaluate an independent, established Arabic tagger
(CAMeL Tools) under *exactly* the paper's own conditions, so the accuracy is
directly comparable to the fine-tuned scorer (96.42%) rather than a raw figure
from a different setup.

Every factor is held constant with run_evaluation.py:
  * same gold file (eval/data/ar_padt_test.conll), same PADT test split;
  * same PADT tokenization — CAMeL Tools is run on the gold token sequence,
    word by word, with NO re-tokenization / clitic re-splitting;
  * same NUM/SYM deterministic pre-filter (identical regexes) applied first;
  * same diacritic-insensitive target: the 17-tag UPOS scheme;
  * same scoring functions from eval/metrics.py;
  * same OOV reference vocabulary (eval/data/ar_padt_train.vocab).

CAMeL's own POS feature is mapped to UPOS by a fixed table (below), applied to
every token identically — the analogue of the LabelMapper used for Jawhar.

Usage
-----
    # from the repo root, after: pip install camel-tools
    #                       and: camel_data -i disambig-mle-calima-msa-r13
    python eval/run_external_baseline.py \
        --gold eval/data/ar_padt_test.conll \
        --train-vocab eval/data/ar_padt_train.vocab \
        --backend mle \
        --out eval/report_cameltools.txt \
        --per-token eval/cameltools_per_token.csv

    # stronger CAMeL model (needs: camel_data -i disambig-bert-unfactored-msa)
    python eval/run_external_baseline.py --backend bert ... (same other args)

Then send Mohamed the printed "Token accuracy" line; it fills the
[CAMELTOOLS: XX.X%] placeholder and the added row in Table (main results).
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.metrics import (
    load_conll,
    token_accuracy,
    macro_f1,
    oov_accuracy,
    classification_report,
)

# --- identical NUM/SYM pre-filter (copied verbatim from run_evaluation.py) ---
_NUM_RE = re.compile(r"^[\d٠-٩٪-٬.,]+$")
_SYM_RE = re.compile(
    r"^[^\s\w؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]+$"
)


def classify_trivial(tok: str):
    if not tok:
        return None
    if _NUM_RE.match(tok):
        return "NUM"
    if _SYM_RE.match(tok):
        return "SYM"
    return None


# --- CAMeL Tools POS -> UPOS (17-tag scheme; punctuation/foreign -> X, as in gold) ---
CAMEL_POS_TO_UPOS = {
    "noun": "NOUN",
    "noun_quant": "NOUN",
    "noun_num": "NUM",
    "noun_prop": "PROPN",
    "adj": "ADJ",
    "adj_comp": "ADJ",
    "adj_num": "ADJ",       # ordinals -> ADJ (UD convention)
    "adv": "ADV",
    "adv_interrog": "ADV",
    "adv_rel": "ADV",
    "pron": "PRON",
    "pron_dem": "PRON",
    "pron_exclam": "PRON",
    "pron_interrog": "PRON",
    "pron_rel": "PRON",
    "verb": "VERB",
    "verb_pseudo": "AUX",   # pseudo-verbs (e.g. laysa) -> AUX
    "part": "PART",
    "part_dem": "PART",
    "part_det": "DET",
    "part_focus": "PART",
    "part_fut": "PART",
    "part_interrog": "PART",
    "part_neg": "PART",
    "part_restrict": "PART",
    "part_verb": "PART",
    "part_voc": "PART",
    "prep": "ADP",
    "abbrev": "X",
    "punc": "X",            # gold maps punctuation to X (no PUNCT in this scheme)
    "conj": "CCONJ",
    "conj_sub": "SCONJ",
    "interj": "INTJ",
    "digit": "NUM",
    "latin": "X",
    "foreign": "X",
}
_FALLBACK = "X"


def load_disambiguator(backend: str):
    """Return a callable: tokens(list[str]) -> list[pos_string]."""
    if backend == "bert":
        from camel_tools.disambig.bert import BERTUnfactoredDisambiguator
        d = BERTUnfactoredDisambiguator.pretrained("msa")
        print("Using BERTUnfactoredDisambiguator (msa)")
    else:
        from camel_tools.disambig.mle import MLEDisambiguator
        d = MLEDisambiguator.pretrained()  # calima-msa-r13
        print("Using MLEDisambiguator (calima-msa-r13)")

    def tag(tokens):
        out = []
        disambig = d.disambiguate(tokens)
        for dw in disambig:
            pos = None
            if dw.analyses:
                pos = dw.analyses[0].analysis.get("pos")
            out.append(pos)
        return out

    return tag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="eval/data/ar_padt_test.conll")
    ap.add_argument("--train-vocab", default="eval/data/ar_padt_train.vocab")
    ap.add_argument("--backend", choices=["mle", "bert"], default="mle")
    ap.add_argument("--out", default=None, help="write metrics report here")
    ap.add_argument("--per-token", default=None, help="write per-token CSV here")
    args = ap.parse_args()

    gold = load_conll(args.gold)
    n_tokens = sum(len(s) for s in gold)
    print(f"Loaded {n_tokens} gold tokens from {args.gold}")

    tagger = load_disambiguator(args.backend)

    pred = []
    rows = []
    unmapped = {}
    for sent in gold:
        tokens = [tok for tok, _ in sent]
        # NUM/SYM pre-filter FIRST (identical to Jawhar harness); only the
        # remaining tokens are POS-tagged by CAMeL, but CAMeL is still run on
        # the full sentence so its context window is unchanged.
        camel_pos = tagger(tokens)
        sent_pred = []
        for (tok, g), cpos in zip(sent, camel_pos):
            triv = classify_trivial(tok)
            if triv is not None:
                upos = triv
            else:
                upos = CAMEL_POS_TO_UPOS.get(cpos, _FALLBACK)
                if cpos is not None and cpos not in CAMEL_POS_TO_UPOS:
                    unmapped[cpos] = unmapped.get(cpos, 0) + 1
            sent_pred.append((tok, upos))
            rows.append((tok, g, cpos or "", upos, "yes" if upos == g else "no"))
        pred.append(sent_pred)

    # --- same scoring functions as the paper ---
    acc = token_accuracy(pred, gold)
    mf1 = macro_f1(pred, gold)
    vocab = None
    if args.train_vocab and os.path.exists(args.train_vocab):
        with open(args.train_vocab, encoding="utf-8") as f:
            vocab = {ln.strip() for ln in f if ln.strip()}
    oov = oov_accuracy(pred, gold, vocab) if vocab else float("nan")

    lines = []
    lines.append("== CAMeL Tools baseline (same harness, 17-tag UPOS) ==")
    lines.append(f"Backend        : {args.backend}")
    lines.append(f"Token accuracy : {acc:.2f}%")
    lines.append(f"Macro-F1       : {mf1:.4f}")
    lines.append(f"OOV accuracy   : {oov:.2f}%")
    lines.append("")
    lines.append(classification_report(pred, gold))
    if unmapped:
        lines.append("")
        lines.append("Unmapped CAMeL POS (mapped to X): " +
                     ", ".join(f"{k}({v})" for k, v in sorted(unmapped.items(), key=lambda x: -x[1])))
    # --- diagnostic: gold UPOS x top CAMeL POS (helps fix scheme/tokenization mismatch) ---
    from collections import Counter, defaultdict
    xtab = defaultdict(Counter)
    for tok, g, cpos, up, ok in rows:
        xtab[g][cpos or "(none)"] += 1
    dlines = ["", "== Diagnostic: gold UPOS -> most common CAMeL pos ==="]
    for g in sorted(xtab, key=lambda k: -sum(xtab[k].values())):
        top = ", ".join(f"{cp}:{n}" for cp, n in xtab[g].most_common(4))
        dlines.append(f"{g:6s} (N={sum(xtab[g].values()):5d}) -> {top}")
    diag_txt = "\n".join(dlines)
    lines.append(diag_txt)

    report = "\n".join(lines)
    print("\n" + report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nReport written to {args.out}")
    if args.per_token:
        with open(args.per_token, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["token", "gold_upos", "camel_pos", "pred_upos", "correct"])
            w.writerows(rows)
        print(f"Per-token predictions written to {args.per_token}")


if __name__ == "__main__":
    main()
