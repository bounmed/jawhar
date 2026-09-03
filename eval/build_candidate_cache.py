"""
build_candidate_cache.py — Precompute the UPOS tag set produced by Jawhar for
every unique token in a gold CoNLL file, and persist it as JSON.

The analyzer caches per-word results in memory, so re-analyzing repeated tokens
is cheap; this cache exists so that different evaluation runs (rule baseline,
BERT reranker, fine-tuned scorer, oracle-constrained hybrid) share the same
candidate sets without re-running the analyzer.

Output format (one entry per unique token):

    {
      "token": {"has_analysis": true, "tags": ["NOUN", "VERB", ...]},
      ...
    }

`tags` is the ordered list of distinct UPOS tags produced by mapping every
candidate through LabelMapper (priority order preserved, duplicates removed).
Tokens whose analysis crashed or produced nothing map to {"has_analysis": false}.

Usage
-----
    python eval/build_candidate_cache.py \
        --data eval/data/ar_padt_test.conll \
        --mapping eval/tagset_mapping_upos.json \
        --out eval/data/candidates_test.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.analyzer import Analyzer
from src.services.tokenizer import Tokenizer
from eval.metrics import load_conll
from eval.label_mapper import LabelMapper


def analyze_unique_tokens(analyzer, mapper, tokens):
    """Return {token: {"has_analysis": bool, "tags": [upos, ...]}}."""
    cache = {}
    for tok in tokens:
        uv = Tokenizer(tok).get_unvoweled_tokens()
        uv = uv[0] if uv else tok
        try:
            cands = analyzer.Analyze(tok, uv, keep_stop_word=True)
        except Exception:
            cands = []
        tags = []
        for c in cands:
            t = mapper.tag_for_candidate(c)
            if t is not None and t not in tags:
                tags.append(t)
        cache[tok] = {"has_analysis": bool(cands), "tags": tags}
    return cache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="gold CoNLL file")
    ap.add_argument("--mapping", default=None, help="tagset mapping JSON (default: upos)")
    ap.add_argument("--out", required=True, help="output JSON path")
    args = ap.parse_args()

    mapping = args.mapping
    if mapping is None:
        mapping = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tagset_mapping_upos.json")

    sentences = load_conll(args.data)
    tokens = sorted({tok for sent in sentences for tok, _ in sent})
    print(f"Loaded {sum(len(s) for s in sentences)} tokens ({len(tokens)} unique) from {args.data}")

    analyzer = Analyzer()
    mapper = LabelMapper(mapping_path=mapping)
    cache = analyze_unique_tokens(analyzer, mapper, tokens)

    with_analysis = sum(1 for v in cache.values() if v["has_analysis"])
    n_tags = sum(len(v["tags"]) for v in cache.values())
    print(f"Analyzed {len(tokens)} unique tokens: {with_analysis} with analysis, "
          f"{len(tokens) - with_analysis} without; {n_tags} mapped tags")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
