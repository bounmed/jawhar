# Jawhar — Morphological Analysis and Contextual Reranking for Arabic POS Tagging

Jawhar is a hybrid Arabic part-of-speech (POS) tagging framework that couples a
rule-based morphological analyzer — an autonomous Python/JSON reconstruction inspired
by Al-Khalil MorphoSys — with contextual reranking and scoring by a pretrained Arabic
BERT (CAMeL-BERT). For each token the analyzer enumerates the morphologically valid
candidate analyses (voweled form, morphological type, root, pattern, grammatical
description); a neural stage then scores candidates or predicts the tag directly.

This repository contains the analyzer, the evaluation harness, and the scripts needed
to reproduce the results reported in the paper *"Jawhar: Optimized Morphological
Analysis and Contextual Reranking for Arabic Part-of-Speech Tagging."*

## What is here

```
src/                      Jawhar morphological analyzer
  services/               analyzer, tokenizer, reranker
  models/                 morphological data structures
  data/                   Al-Khalil-derived pattern/root databases (JSON)
eval/                     evaluation harness
  metrics.py              token accuracy, macro-F1, OOV accuracy, MVR, per-tag report
  label_mapper.py         Jawhar type-string -> 17-tag UPOS mapping
  tagset_mapping_upos.json  the mapping table used throughout
  build_candidate_cache.py  precompute candidate UPOS sets per token
  run_evaluation.py       rule / zero-shot reranker / fine-tuned scorer / hybrid
  train_tag_scorer.py     fine-tune CAMeL-BERT as a UPOS token scorer
  run_external_baseline.py  same-harness CAMeL Tools baseline (MLE or BERT)
  convert_ud_padt.py      convert UD Arabic-PADT (CoNLL-U) to the 2-column format
  report_*.txt            per-tag reports for each system
  cameltools_*_per_token.csv  per-token CAMeL Tools predictions
  data/
    candidates_test.json  cached candidate UPOS sets for the test split
    ar_padt_train.vocab   training-vocabulary list (for OOV accuracy)
```

## Data

The evaluation uses the **Universal Dependencies distribution of the Prague Arabic
Dependency Treebank (UD_Arabic-PADT)**, mapped to the 17-tag UPOS scheme. That corpus
is distributed under its own license (CC BY-NC-SA) and is **not redistributed here**.
To obtain it, download UD_Arabic-PADT and run the converter:

```bash
# place ar_padt-ud-{train,dev,test}.conllu in eval/data/, then:
python eval/convert_ud_padt.py --in_dir eval/data --out_dir eval/data --upos --write_vocab
```

This regenerates `eval/data/ar_padt_test.conll` (and the train vocab). The derived
candidate cache (`candidates_test.json`) and vocab are included so the evaluation
scripts can run immediately once the test `.conll` is present.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# rule-based + zero-shot reranker
python eval/run_evaluation.py --gold eval/data/ar_padt_test.conll \
    --train-vocab eval/data/ar_padt_train.vocab

# fine-tuned CAMeL-BERT UPOS scorer (needs torch + transformers + a GPU is recommended)
python eval/train_tag_scorer.py
python eval/run_evaluation.py --pred-ft --ft-model <model_dir> \
    --gold eval/data/ar_padt_test.conll --train-vocab eval/data/ar_padt_train.vocab
```

See `REPRODUCE.md` for the full step-by-step reproduction, including the same-harness
CAMeL Tools baseline.

## License

The Jawhar analyzer is derived from Al-Khalil MorphoSys, which is released under the
**GNU General Public License v3**. This repository is therefore distributed under the
**GPLv3** — see `LICENSE`. The UD_Arabic-PADT corpus is not included and remains under
its own license.

## Citation

If you use this code, please cite the Jawhar paper (see the article for the full
reference).
