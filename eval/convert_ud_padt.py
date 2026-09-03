"""
convert_ud_padt.py — Convert Universal Dependencies Arabic PADT (CoNLL-U)
into the 2-column CoNLL format expected by run_evaluation.py.

Drops multi-word token ranges (ID containing '-' or '.'), optionally drops
punctuation, and writes token<TAB>tag lines separated by blank lines.

Usage
-----
    python convert_ud_padt.py --in_dir eval/data --out_dir eval/data --upos --drop_punct

Also writes a training-vocab file (unique tokens from train split) for OOV accuracy.
"""

from __future__ import annotations

import argparse
import os
from collections import Counter

import conllu


def convert(in_path: str, out_path, upos: bool = True, drop_punct: bool = False):
    """Convert one CoNLL-U file to 2-column CoNLL."""
    kept_tokens = 0
    with open(in_path, encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
        for sent in conllu.parse_incr(f):
            for tok in sent:
                # skip multi-word token ranges (e.g. "1-2") and empty nodes ("1.1")
                tid = str(tok["id"])
                if "-" in tid or "." in tid:
                    continue
                form = tok["form"]
                tag = tok["upos"] if upos else tok["xpos"]
                if drop_punct and tag == "PUNCT":
                    continue
                if form.strip():
                    out.write(f"{form}\t{tag}\n")
                    kept_tokens += 1
            out.write("\n")
    return kept_tokens


def write_vocab(in_dir: str, out_path: str):
    """Collect unique tokens from the train split for OOV computation."""
    vocab: set = set()
    train = os.path.join(in_dir, "ar_padt-ud-train.conllu")
    with open(train, encoding="utf-8") as f:
        for sent in conllu.parse_incr(f):
            for tok in sent:
                tid = str(tok["id"])
                if "-" not in tid and "." not in tid and tok["form"].strip():
                    vocab.add(tok["form"])
    with open(out_path, "w", encoding="utf-8") as out:
        for tok in sorted(vocab):
            out.write(tok + "\n")
    return len(vocab)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir", default="eval/data")
    ap.add_argument("--out_dir", default="eval/data")
    ap.add_argument("--upos", action="store_true", help="use UPOS instead of XPOS")
    ap.add_argument("--drop_punct", action="store_true", help="drop punctuation tokens")
    ap.add_argument("--write_vocab", action="store_true", help="write train vocab file")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    for split in ["train", "dev", "test"]:
        inp = os.path.join(args.in_dir, f"ar_padt-ud-{split}.conllu")
        outp = os.path.join(args.out_dir, f"ar_padt_{split}.conll")
        if os.path.exists(inp):
            n = convert(inp, outp, upos=args.upos, drop_punct=args.drop_punct)
            print(f"{split}: {n} tokens -> {outp}")
        else:
            print(f"{split}: source {inp} not found, skipped")

    if args.write_vocab:
        vpath = os.path.join(args.out_dir, "ar_padt_train.vocab")
        nv = write_vocab(args.in_dir, vpath)
        print(f"vocab: {nv} unique tokens -> {vpath}")


if __name__ == "__main__":
    main()
