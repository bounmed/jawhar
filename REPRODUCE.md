# Reproducing the Jawhar results

All numbers are on the UD_Arabic-PADT **test** split, mapped to the 17-tag UPOS scheme.

## 0. Environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.11 was used. `torch` and `transformers` are needed only for the neural
experiments; the rule-based path and the candidate analysis run without them.

## 1. Data

Download **UD_Arabic-PADT** and place the three CoNLL-U files in `eval/data/`:
`ar_padt-ud-train.conllu`, `ar_padt-ud-dev.conllu`, `ar_padt-ud-test.conllu`. Then:

```bash
python eval/convert_ud_padt.py --in_dir eval/data --out_dir eval/data --upos --write_vocab
```

This writes `ar_padt_{train,dev,test}.conll` and `ar_padt_train.vocab`. (The repo already
ships `ar_padt_train.vocab` and `candidates_test.json`; the test `.conll` is regenerated
here because the corpus itself is not redistributed.)

Optional — rebuild the candidate cache from the analyzer:

```bash
python eval/build_candidate_cache.py --data eval/data/ar_padt_test.conll \
    --mapping eval/tagset_mapping_upos.json --out eval/data/candidates_test.json
```

## 2. Rule-based and zero-shot reranker

```bash
python eval/run_evaluation.py --gold eval/data/ar_padt_test.conll \
    --train-vocab eval/data/ar_padt_train.vocab
```

Expected: Jawhar-Rule 54.46% token accuracy; zero-shot CAMeL-BERT reranker 54.32%
(`report_rule.txt`, `report_bert.txt`).

## 3. Fine-tuned CAMeL-BERT UPOS scorer

```bash
python eval/train_tag_scorer.py            # trains from CAMeL-Lab/bert-base-arabic-camelbert-msa
python eval/run_evaluation.py --pred-ft --ft-model <model_dir> \
    --gold eval/data/ar_padt_test.conll --train-vocab eval/data/ar_padt_train.vocab
```

Expected: 96.42% token accuracy, macro-F1 0.9209, OOV 83.97% (`report_tag_scorer.txt`);
candidate-constrained oracle ceiling 97.39%; realistic hybrid 96.42% with morphological
backing on 65.9% of tokens.

## 4. Same-harness CAMeL Tools baseline

```bash
pip install camel-tools
camel_data -i disambig-mle-calima-msa-r13          # MLE model
camel_data -i disambig-bert-unfactored-msa         # BERT model (stronger)

python eval/run_external_baseline.py --backend mle  \
    --per-token eval/cameltools_per_token.csv      --out eval/report_cameltools.txt
python eval/run_external_baseline.py --backend bert \
    --per-token eval/cameltools_bert_per_token.csv --out eval/report_cameltools_bert.txt
```

CAMeL Tools is evaluated through the identical harness (same split, tokenization,
NUM/SYM pre-filter, UPOS mapping). See the paper for the aligned-category comparison and
the discussion of the tokenization/scheme confounds that make a single overall accuracy
not directly comparable.

## Notes

- The NUM/SYM deterministic pre-filter and the diacritic-insensitive type-to-UPOS
  mapping are applied identically to every system.
- Reported figures are on the freely available UD distribution of PADT (17-tag UPOS),
  not the licensed 24-tag LDC release, and are therefore not comparable to accuracies
  reported on the LDC scheme.
