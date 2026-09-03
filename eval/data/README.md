# Evaluation data

The experiments use the **Universal Dependencies distribution of the Prague Arabic
Dependency Treebank (UD_Arabic-PADT)**, mapped to the 17-tag UPOS scheme.

**The treebank is not redistributed in this repository.** It is available under its own
license (CC BY-NC-SA) from the Universal Dependencies project. To reproduce the
evaluation, download UD_Arabic-PADT, place the CoNLL-U files here
(`ar_padt-ud-train.conllu`, `ar_padt-ud-dev.conllu`, `ar_padt-ud-test.conllu`), and run:

```bash
python ../convert_ud_padt.py --in_dir . --out_dir . --upos --write_vocab
```

## Files shipped here (derived, not the corpus itself)

- `candidates_test.json` — for each unique test token, the set of candidate UPOS labels
  the Jawhar analyzer produces (used to share candidate sets across evaluation runs).
- `ar_padt_train.vocab` — the list of unique training-split surface tokens, used only to
  compute out-of-vocabulary (OOV) accuracy.

These are transformations of the corpus (label sets / a token list), not the annotated
treebank. `ar_padt_test.conll` is produced by the converter above and is git-ignored.
