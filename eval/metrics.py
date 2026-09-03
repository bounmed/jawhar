"""
metrics.py — Evaluation metrics for Arabic POS tagging.

Computes the metrics reported in the paper:
  - Token accuracy
  - Macro-averaged F1
  - OOV (out-of-vocabulary) accuracy
  - Morphological validity rate (MVR)

Expected data format
--------------------
Gold files are CoNLL-style: one token per line as "token<TAB>tag",
sentences separated by a blank line. Example:

	كتب	VERB
	الطالب	NOUN
	الدرس	NOUN

	SENT	ROOT
	...
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple


def load_conll(path: str) -> List[List[Tuple[str, str]]]:
    """Read a CoNLL file into a list of sentences of (token, tag) pairs."""
    sentences: List[List[Tuple[str, str]]] = []
    current: List[Tuple[str, str]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if current:
                    sentences.append(current)
                    current = []
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                current.append((parts[0], parts[1]))
            else:
                # fallback: token only
                current.append((parts[0], ""))
    if current:
        sentences.append(current)
    return sentences


def _flatten(
    sentences: List[List[Tuple[str, str]]],
) -> List[str]:
    return [tag for sent in sentences for _, tag in sent]


def token_accuracy(pred: List[List[Tuple[str, str]]], gold: List[List[Tuple[str, str]]]) -> float:
    """Percentage of tokens where predicted tag equals gold tag."""
    correct = total = 0
    for psent, gsent in zip(pred, gold):
        for (_, pt), (_, gt) in zip(psent, gsent):
            total += 1
            if pt == gt:
                correct += 1
    return (correct / total * 100.0) if total else 0.0


def macro_f1(pred: List[List[Tuple[str, str]]], gold: List[List[Tuple[str, str]]]) -> float:
    """Unweighted mean of per-class F1 scores."""
    # collect per-class tp/fp/fn
    stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    classes = set()
    for psent, gsent in zip(pred, gold):
        for (_, pt), (_, gt) in zip(psent, gsent):
            classes.add(gt)
            classes.add(pt)
            if pt == gt:
                stats[gt]["tp"] += 1
            else:
                stats[pt]["fp"] += 1
                stats[gt]["fn"] += 1

    f1_sum = 0.0
    for cls in classes:
        s = stats[cls]
        prec = s["tp"] / (s["tp"] + s["fp"]) if (s["tp"] + s["fp"]) else 0.0
        rec = s["tp"] / (s["tp"] + s["fn"]) if (s["tp"] + s["fn"]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1_sum += f1
    return (f1_sum / len(classes)) if classes else 0.0


def oov_accuracy(
    pred: List[List[Tuple[str, str]]],
    gold: List[List[Tuple[str, str]]],
    training_vocab: set,
) -> float:
    """Token accuracy restricted to tokens unseen in the training vocabulary."""
    correct = total = 0
    for psent, gsent in zip(pred, gold):
        for (tok, pt), (_, gt) in zip(psent, gsent):
            if tok not in training_vocab:
                total += 1
                if pt == gt:
                    correct += 1
    return (correct / total * 100.0) if total else 0.0


def mvr(pred: List[List[Tuple[str, str]]]) -> float:
    """Morphological validity rate: % of predictions that have a Jawhar analysis.

    A prediction is considered valid iff its tag is not the fallback default
    (i.e. the analyzer produced at least one candidate). The caller is expected
    to mark fallback predictions with a sentinel tag (e.g. "FALLBACK") so they
    can be excluded. If no sentinel is used, returns 100.0.
    """
    valid = total = 0
    FALLBACK = "FALLBACK"
    for sent in pred:
        for _, tag in sent:
            total += 1
            if tag != FALLBACK:
                valid += 1
    return (valid / total * 100.0) if total else 0.0


def classification_report(
    pred: List[List[Tuple[str, str]]], gold: List[List[Tuple[str, str]]]
) -> str:
    """Return a readable precision/recall/F1 table sorted by frequency."""
    stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    freq: Dict[str, int] = defaultdict(int)
    for psent, gsent in zip(pred, gold):
        for (_, pt), (_, gt) in zip(psent, gsent):
            freq[gt] += 1
            if pt == gt:
                stats[gt]["tp"] += 1
            else:
                stats[pt]["fp"] += 1
                stats[gt]["fn"] += 1

    lines = [f"{'TAG':<18}{'P':>8}{'R':>8}{'F1':>8}{'N':>8}"]
    for cls in sorted(stats, key=lambda c: -freq.get(c, 0)):
        s = stats[cls]
        prec = s["tp"] / (s["tp"] + s["fp"]) if (s["tp"] + s["fp"]) else 0.0
        rec = s["tp"] / (s["tp"] + s["fn"]) if (s["tp"] + s["fn"]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        lines.append(f"{cls:<18}{prec:>8.3f}{rec:>8.3f}{f1:>8.3f}{freq.get(cls, 0):>8}")
    return "\n".join(lines)
