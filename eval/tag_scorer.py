"""
tag_scorer.py — Fine-tuned BERT token-level UPOS tag scorer.

Wraps a BERTForTokenClassification fine-tuned by train_tag_scorer.py and exposes
sentence-level prediction. It is the honest neural baseline on the PADT UPOS
scheme, and the scorer used by the candidate-constrained hybrid evaluation.

Usage
-----
    from eval.tag_scorer import TagScorer
    scorer = TagScorer("./checkpoints/tag-scorer")
    tags = scorer.predict_sentence(["و", "قال", "الرئيس", "."])
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from transformers import AutoTokenizer, BertForTokenClassification


class TagScorer:
    def __init__(self, model_dir: str, device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = BertForTokenClassification.from_pretrained(model_dir).to(self.device)
        self.model.eval()
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}

    def predict_sentence(self, tokens: list[str]) -> list[str]:
        """Predict one UPOS tag per input token (unvoweled raw word)."""
        enc = self.tokenizer(tokens, is_split_into_words=True, truncation=True,
                             max_length=512, return_tensors="pt")
        word_ids = enc.word_ids(batch_index=0)
        enc = {k: v.to(self.device) for k, v in enc.items()}
        with torch.no_grad():
            logits = self.model(**enc).logits  # (1, L, C)
        preds = logits.argmax(-1)[0].tolist()  # per subword
        tags = []
        prev = None
        for word_id, p in zip(word_ids, preds):
            if word_id is None or word_id == prev:
                continue
            tags.append(self.id2label.get(p, "X"))
            prev = word_id
        return tags

    def predict_batch(self, sentences: list[list[str]]) -> list[list[str]]:
        return [self.predict_sentence(s) for s in sentences]
