"""
BERTReranker — Context-aware reranker for Arabic morphological analysis.

Strategy (zero-shot, no labelled training data required):
  1. Encode the full sentence with Arabic BERT to get contextual word embeddings.
  2. For every candidate analysis, build a linguistic "signature" string that
     combines its morphological type, POS description, root, pattern, and voweled
     form, and embed it with Arabic BERT (cached).
  3. For each token, score each candidate by the cosine similarity between the
     token's contextual embedding and its candidate-signature embedding, then
     blend that score with the existing rule-based priority.

Two embedding modes are supported:
  - "signature" (default): score via the full candidate-signature embedding. This
    also covers verbs and function words whose long descriptions do not reduce to
    a small shared label set.
  - "label": score via a fixed vocabulary of 25 coarse type labels (e.g. "اسم فاعل").

The reranker is optional: if torch/transformers are not installed, or the model
cannot be loaded, the Analyzer falls back to its built-in priority ranking.
"""

from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Availability guard — keep the rest of the app import-safe without torch
# ---------------------------------------------------------------------------
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    logger.warning(
        "torch / transformers not installed. "
        "BERTReranker is disabled; falling back to rule-based priority ranking."
    )


# ---------------------------------------------------------------------------
# Morphological type labels (Arabic) used for label-embedding scoring
# These map the word_type values produced by interpret_vnp / interpret_vvp
# to the Arabic phrases the BERT model was trained on.
# ---------------------------------------------------------------------------
_TYPE_LABELS: List[str] = [
    "اسم فاعل",
    "اسم مفعول",
    "مبالغة اسم الفاعل",
    "اسم آلة",
    "اسم زمان أو مكان",
    "اسم تفضيل",
    "صفة مشبهة",
    "مصدر أصلي",
    "مصدر ميمي",
    "مصدر هيئة",
    "مصدر مرة",
    "مصدر صناعي",
    "اسم جامد",
    "نسبة",
    "فعل ماضٍ",
    "فعل مضارع مرفوع",
    "فعل مضارع منصوب",
    "فعل مضارع مجزوم",
    "فعل أمر",
    "أداة",
    "حرف جر",
    "حرف عطف",
    "حرف نفي",
    "اسم علم",
    "ضمير",
]

# Default BERT model — MSA-tuned Arabic BERT from CAMeL Lab
_DEFAULT_MODEL = "CAMeL-Lab/bert-base-arabic-camelbert-msa"


class BERTReranker:
    """
    Reranks morphological analysis candidates using contextual Arabic BERT.

    Usage::

        reranker = BERTReranker()                    # loads model once
        reranked = reranker.rerank(tokens, candidates)  # list[list[Result]]
    """

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        alpha: float = 0.35,
        embedding_mode: str = "signature",
    ):
        """
        Args:
            model_name:     HuggingFace model identifier for an Arabic BERT model.
            alpha:          Blend weight for the BERT score.
                            0.0 → pure rule-based priority (reranker is a no-op).
                            1.0 → pure BERT similarity score.
                            0.35 is a conservative default that improves precision
                            without fully overriding the rule-based engine.
            embedding_mode: "signature" (default) scores candidates by the embedding
                            of their full morphological signature (type, POS, root,
                            pattern, voweled form); "label" uses the fixed 25-type
                            label vocabulary. Signature mode also covers verbs and
                            function words whose descriptions do not match the
                            fixed label set.
        """
        if not _TORCH_AVAILABLE:
            raise RuntimeError(
                "torch and transformers must be installed to use BERTReranker. "
                "Run: pip install torch transformers"
            )

        self.alpha = alpha
        self.embedding_mode = embedding_mode
        if embedding_mode not in ("signature", "label"):
            raise ValueError(
                "embedding_mode must be 'signature' or 'label', got %r" % (embedding_mode,)
            )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info("Loading Arabic BERT model: %s (device=%s)", model_name, self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        self.model.to(self.device)
        logger.info("Model loaded successfully.")

        # "signature" mode: lazily embed candidate-signature strings (cached).
        self._signature_cache: dict[str, torch.Tensor] = {}

        # "label" mode: pre-compute type-label embeddings once at startup.
        self._label_embeddings: dict[str, torch.Tensor] = {}
        if embedding_mode == "label":
            self._label_embeddings = self._compute_label_embeddings()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed_texts(self, texts: List[str]) -> torch.Tensor:
        """Return mean-pooled BERT embeddings for a batch of strings."""
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=64,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            hidden = self.model(**encoded).last_hidden_state  # (B, T, H)

        mask = encoded["attention_mask"].unsqueeze(-1).float()  # (B, T, 1)
        pooled = (hidden * mask).sum(1) / mask.sum(1)           # (B, H)
        return pooled

    def _compute_label_embeddings(self) -> dict[str, torch.Tensor]:
        """Pre-compute and cache a BERT embedding for each morphological label."""
        embeddings = self._embed_texts(_TYPE_LABELS)
        return {label: embeddings[i] for i, label in enumerate(_TYPE_LABELS)}

    def _get_word_embeddings(self, tokens: List[str]) -> List[torch.Tensor]:
        """
        Encode the full sentence and return one embedding per input word,
        averaging over sub-word pieces that belong to the same word.

        Args:
            tokens: Pre-split word list (unvoweled Arabic words).

        Returns:
            List of tensors (one per token), shape (hidden_size,).
            Falls back to an empty list on encoding failure.
        """
        encoded = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(self.device)

        word_ids = encoded.word_ids(batch_index=0)  # subtoken → original word index

        with torch.no_grad():
            hidden = self.model(**encoded).last_hidden_state[0]  # (T, H)

        # Accumulate sub-token hidden states per original word
        word_to_subtokens: dict[int, List[torch.Tensor]] = {}
        for tok_idx, word_id in enumerate(word_ids):
            if word_id is None:
                continue
            word_to_subtokens.setdefault(word_id, []).append(hidden[tok_idx])

        # Mean-pool sub-tokens for each word
        result: List[torch.Tensor] = []
        for word_id in sorted(word_to_subtokens):
            stacked = torch.stack(word_to_subtokens[word_id])
            result.append(stacked.mean(0))

        return result

    @staticmethod
    def _cosine_sim(a: torch.Tensor, b: torch.Tensor) -> float:
        a = a / (a.norm() + 1e-8)
        b = b / (b.norm() + 1e-8)
        return float((a * b).sum().item())

    def _bert_score(self, token_emb: torch.Tensor, word_type: str) -> float:
        """
        Cosine similarity between the contextual token embedding and the
        pre-computed embedding of the candidate's morphological type label.
        Returns 0.0 if the word_type is not in the label vocabulary.
        """
        label_emb = self._label_embeddings.get(word_type)
        if label_emb is None:
            return 0.0
        return self._cosine_sim(token_emb, label_emb)

    # ------------------------------------------------------------------
    # Signature-based scoring (default mode)
    # ------------------------------------------------------------------

    @staticmethod
    def _signature(candidate) -> str:
        """
        Build the linguistic signature string of a morphological candidate by
        concatenating its type, POS description, root, pattern, and voweled form.
        Empty fields are dropped. This is the embeddable unit in "signature" mode.
        """
        parts = [
            getattr(candidate, "word_type", ""),
            getattr(candidate, "pos", ""),
            getattr(candidate, "word_root", ""),
            getattr(candidate, "word_pattern", ""),
            getattr(candidate, "voweled_word", ""),
        ]
        return " | ".join(p for p in parts if p and str(p).strip())

    def _ensure_signature_embeddings(self, signatures: List[str]) -> None:
        """
        Embed any unseen candidate signatures in one batched forward pass and add
        them to the cache. Repeated signatures across tokens/sentences reuse the
        cached embeddings at no extra cost.
        """
        missing = [s for s in signatures if s and s not in self._signature_cache]
        if not missing:
            return
        embeddings = self._embed_texts(missing)
        for sig, emb in zip(missing, embeddings):
            self._signature_cache[sig] = emb

    def _signature_bert_score(self, token_emb: torch.Tensor, candidate) -> float:
        """
        Cosine similarity between the contextual token embedding and the embedding
        of the candidate's morphological signature. Returns 0.0 if the signature is
        empty or was not embeddable.
        """
        sig = self._signature(candidate)
        if not sig:
            return 0.0
        emb = self._signature_cache.get(sig)
        if emb is None:
            return 0.0
        return self._cosine_sim(token_emb, emb)

    @staticmethod
    def _priority_score(priority: str) -> float:
        """
        Convert the rule-based priority string to a normalised float score
        where *higher* means *better* (inverse of the raw priority number).
        """
        try:
            raw = float(priority)
            # Priorities are ~8-digit numbers; negate so lower number = higher score
            return -raw / 1e8
        except (ValueError, TypeError):
            return 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rerank(self, tokens: List[str], all_candidates: list) -> list:
        """
        Rerank morphological analysis candidates for every token in the sentence.

        Args:
            tokens:         The sentence as a list of (unvoweled) word strings.
            all_candidates: A list of lists of Result objects — one inner list
                            per token, exactly as returned by Analyzer.Analyze().

        Returns:
            The same structure with inner lists re-sorted so the best candidate
            is first. Falls back to the original order if BERT encoding fails.
        """
        if not tokens or not any(all_candidates):
            return all_candidates

        try:
            word_embeddings = self._get_word_embeddings(tokens)
        except Exception as exc:
            logger.warning("BERTReranker encoding failed (%s); using rule-based order.", exc)
            return all_candidates

        reranked = []
        for i, candidates in enumerate(all_candidates):
            if not candidates:
                reranked.append(candidates)
                continue

            # If BERT produced fewer word embeddings than tokens (e.g. truncation),
            # fall back to the original candidate order for that token.
            if i >= len(word_embeddings):
                reranked.append(candidates)
                continue

            token_emb = word_embeddings[i]
            alpha = self.alpha

            if self.embedding_mode == "signature":
                # Embed every distinct candidate signature of this token once, so a
                # single batched forward pass covers all of them; repeated signatures
                # hit the cache.
                signatures = [self._signature(c) for c in candidates]
                self._ensure_signature_embeddings(signatures)

                def score(candidate) -> float:
                    rule = self._priority_score(candidate.priority)
                    bert = self._signature_bert_score(token_emb, candidate)
                    return (1.0 - alpha) * rule + alpha * bert
            else:
                def score(candidate) -> float:
                    rule = self._priority_score(candidate.priority)
                    bert = self._bert_score(token_emb, candidate.word_type)
                    return (1.0 - alpha) * rule + alpha * bert

            reranked.append(sorted(candidates, key=score, reverse=True))

        return reranked


# ---------------------------------------------------------------------------
# Factory — returns None if dependencies are missing, so callers can
# use `if reranker:` as an availability check.
# ---------------------------------------------------------------------------

def load_reranker(
    model_name: str = _DEFAULT_MODEL,
    alpha: float = 0.35,
    embedding_mode: str = "signature",
):
    """
    Attempt to instantiate BERTReranker. Returns None if torch/transformers
    are unavailable or the model fails to load (e.g. no internet, no disk space).
    """
    if not _TORCH_AVAILABLE:
        return None
    try:
        return BERTReranker(
            model_name=model_name, alpha=alpha, embedding_mode=embedding_mode
        )
    except Exception as exc:
        logger.warning("Could not load BERTReranker: %s. Falling back to rule-based ranking.", exc)
        return None
