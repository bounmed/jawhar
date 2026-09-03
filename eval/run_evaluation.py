"""
run_evaluation.py — Evaluate Jawhar (and Jawhar-BERT) against a gold POS corpus.

Usage
-----
    python run_evaluation.py --gold data/padt_test.conll --pred-rule
    python run_evaluation.py --gold data/padt_test.conll --pred-bert [--model CAMeL-Lab/bert-base-arabic-camelbert-msa]

Arguments
--gold        Path to gold CoNLL file (token<TAB>tag per line, blank line = sentence).
--pred-rule   Use rule-based priority ranking (no BERT).
--pred-bert   Use BERT reranking (requires torch + transformers).
--model       HuggingFace model id (default: CAMeL-Lab/bert-base-arabic-camelbert-msa).
--alpha       Blend weight for BERT score (default 0.35).
--mode        Embedding mode: 'signature' (default) or 'label'.
--train-vocab Path to a file with one training token per line (for OOV accuracy).

Outputs token accuracy, macro-F1, OOV accuracy, MVR, and a per-tag P/R/F1 table.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# allow running from the eval/ directory by adding project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.analyzer import Analyzer
from src.services.tokenizer import Tokenizer
from src.services.reranker import load_reranker

from eval.metrics import (
    load_conll,
    token_accuracy,
    macro_f1,
    oov_accuracy,
    mvr,
    classification_report,
)
from eval.label_mapper import LabelMapper
_NUM_RE = re.compile(r"^[\d\u0660-\u0669\u066A-\u066C.,]+$")
_SYM_RE = re.compile(r"^[^\s\w\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+$")


def classify_trivial(tok: str):
    """Return a direct UPOS tag for numbers and symbols, else None.

    The tokenizer strips digits and non-Arabic symbols, so these tokens would
    otherwise produce no analysis. Detect them from the raw token instead.
    """
    if not tok:
        return None
    if _NUM_RE.match(tok):
        return "NUM"
    if _SYM_RE.match(tok):
        return "SYM"
    return None


def predict(analyzer, mapper, sentences, reranker=None):
    """Run analysis (+ optional BERT reranking) over a list of tokenised sentences."""
    predictions = []
    # BERT reranking works at sentence level, so pass full token lists
    if reranker is not None:
        tokens = [tok for sent in sentences for tok, _ in sent]
        # Build unvoweled tokens WITHOUT stop-word removal (Tokenizer strips
        # words when len(words) > 2, which would misalign the token list).
        full_text = " ".join(tokens)
        raw_words = full_text.replace("ـ", "").split()
        unvoweled_tokens = []
        for w in raw_words:
            uv = w
            for d in "ًٌٍَُِّْ":
                uv = uv.replace(d, "")
            unvoweled_tokens.append(uv)
        idx = 0
        all_candidate_lists = []
        for sent in sentences:
            sent_cands = []
            for tok, _ in sent:
                try:
                    cands = analyzer.Analyze(tok, unvoweled_tokens[idx], keep_stop_word=True)
                except Exception:
                    cands = []
                sent_cands.append(cands)
                idx += 1
            all_candidate_lists.append(sent_cands)
        # rerank expects flat list of all tokens + candidate lists in order
        flat_cands = [c for sent_c in all_candidate_lists for c in sent_c]
        reranked_flat = reranker.rerank(unvoweled_tokens, flat_cands)
        # rebuild per-sentence structure
        per_sent = []
        pos = 0
        for sent in sentences:
            n = len(sent)
            per_sent.append(reranked_flat[pos : pos + n])
            pos += n
        for sent, cands in zip(sentences, per_sent):
            pred_sent = []
            for (tok, _), clist in zip(sent, cands):
                tag = classify_trivial(tok) or mapper.best_tag(clist, use_rule_priority=False)
                pred_sent.append((tok, tag))
            predictions.append(pred_sent)
    else:
        for sent in sentences:
            pred_sent = []
            for tok, _ in sent:
                trivial = classify_trivial(tok)
                if trivial:
                    pred_sent.append((tok, trivial))
                    continue
                unvoweled = Tokenizer(tok).get_unvoweled_tokens()
                uv = unvoweled[0] if unvoweled else tok
                try:
                    cands = analyzer.Analyze(tok, uv, keep_stop_word=True)
                except Exception:
                    cands = []
                tag = mapper.best_tag(cands, use_rule_priority=True)
                pred_sent.append((tok, tag))
            predictions.append(pred_sent)
    return predictions


def run_ft_evaluation(gold, ft_model, candidate_cache_path, args):
    """Evaluate the fine-tuned UPOS tag scorer, with and without the Jawhar
    candidate-set constraint.

    Two numbers are reported:
      * fine-tuned accuracy — the honest neural baseline on the UPOS scheme;
      * constrained accuracy — an oracle ceiling for the hybrid system: a token
        is answered from Jawhar's candidate set whenever the gold tag is among
        the candidate tags (always correct then), otherwise the fine-tuned tag
        is used. This is the "+10-15pp" diagnostic from the analysis.
    """
    from eval.tag_scorer import TagScorer

    scorer = TagScorer(ft_model)
    print(f"Fine-tuned tag scorer loaded from {ft_model} on {scorer.device}")

    ft_pred = []
    for sent in gold:
        tokens = [tok for tok, _ in sent]
        tags = scorer.predict_sentence(tokens)
        ft_pred.append(list(zip(tokens, tags)))

    ft_acc = token_accuracy(ft_pred, gold)
    ft_mf1 = macro_f1(ft_pred, gold)
    print(f"\n== Fine-tuned neural baseline (UPOS tag scorer) ==")
    print(f"Token accuracy : {ft_acc:.2f}%")
    print(f"Macro F1       : {ft_mf1:.4f}")
    if args.train_vocab:
        with open(args.train_vocab, encoding="utf-8") as f:
            vocab = {line.strip() for line in f if line.strip()}
        print(f"OOV accuracy   : {oov_accuracy(ft_pred, gold, vocab):.2f}%")
    print("\nPer-tag report:\n" + classification_report(ft_pred, gold))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(classification_report(ft_pred, gold))

    if not candidate_cache_path:
        print("\n(Skipping constrained evaluation: pass --candidate-cache to enable.)")
        return

    with open(candidate_cache_path, encoding="utf-8") as f:
        cand_cache = json.load(f)

    constrained = []
    for gsent, fsent in zip(gold, ft_pred):
        c_sent = []
        for (tok, ft_tag), (_, gt) in zip(fsent, gsent):
            cand_tags = cand_cache.get(tok, {}).get("tags", [])
            if gt in cand_tags:
                c_sent.append((tok, gt))       # answered from Jawhar (correct)
            else:
                c_sent.append((tok, ft_tag))
        constrained.append(c_sent)

    c_acc = token_accuracy(constrained, gold)
    n_with_analysis = sum(
        1 for gsent, fsent in zip(gold, ft_pred)
        for (tok, ft_tag), _ in zip(fsent, gsent)
        if ft_tag in cand_cache.get(tok, {}).get("tags", [])
    )
    n_total = sum(len(s) for s in gold)
    print(f"\n== Candidate-constrained (oracle ceiling) ==")
    print(f"Token accuracy : {c_acc:.2f}%  (+{c_acc - ft_acc:.2f}pp over neural)")
    print(f"Macro F1       : {macro_f1(constrained, gold):.4f}")
    print(f"\n== Realistic hybrid (neural tags with Jawhar analysis when available) ==")
    print(f"Token accuracy : {ft_acc:.2f}%")
    print(f"Jawhar analysis available for {n_with_analysis / n_total * 100:.1f}% of tokens")


def main():
    ap = argparse.ArgumentParser(description="Evaluate Jawhar POS tagging.")
    ap.add_argument("--gold", required=True, help="gold CoNLL file")
    ap.add_argument("--pred-rule", action="store_true", help="use rule-based priority")
    ap.add_argument("--pred-bert", action="store_true", help="use BERT reranking")
    ap.add_argument("--model", default="CAMeL-Lab/bert-base-arabic-camelbert-msa")
    ap.add_argument("--alpha", type=float, default=0.35)
    ap.add_argument("--mode", default="signature", choices=["signature", "label"])
    ap.add_argument("--train-vocab", default=None, help="training tokens file (for OOV)")
    ap.add_argument("--report", default=None, help="write per-tag report to this file")
    ap.add_argument("--mapping", default=None, help="path to tagset mapping JSON")
    ap.add_argument("--pred-ft", action="store_true", help="use fine-tuned tag scorer (--ft-model)")
    ap.add_argument("--ft-model", default=None, help="directory of the fine-tuned tag scorer")
    ap.add_argument("--candidate-cache", default=None,
                    help="JSON of candidate UPOS tags per token (from build_candidate_cache.py)")
    args = ap.parse_args()

    if not args.pred_rule and not args.pred_bert and not args.pred_ft:
        ap.error("choose --pred-rule, --pred-bert, or --pred-ft")

    gold = load_conll(args.gold)
    analyzer = Analyzer()
    mapper = LabelMapper(mapping_path=args.mapping) if args.mapping else LabelMapper()

    if args.pred_ft:
        if not args.ft_model:
            ap.error("--pred-ft requires --ft-model")
        run_ft_evaluation(gold, args.ft_model, args.candidate_cache, args)
        return

    reranker = None
    if args.pred_bert:
        reranker = load_reranker(model_name=args.model, alpha=args.alpha, embedding_mode=args.mode)
        if reranker is None:
            print("ERROR: could not load BERT reranker. Is torch/transformers installed?")
            sys.exit(1)

    pred = predict(analyzer, mapper, gold, reranker=reranker)

    acc = token_accuracy(pred, gold)
    mf1 = macro_f1(pred, gold)
    print(f"Token accuracy : {acc:.2f}%")
    print(f"Macro F1       : {mf1:.4f}")
    if args.train_vocab:
        with open(args.train_vocab, encoding="utf-8") as f:
            vocab = {line.strip() for line in f if line.strip()}
        oov_acc = oov_accuracy(pred, gold, vocab)
        print(f"OOV accuracy   : {oov_acc:.2f}%")
    print(f"MVR            : {mvr(pred):.1f}%")

    report = classification_report(pred, gold)
    print("\nPer-tag report:\n" + report)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)


if __name__ == "__main__":
    main()
