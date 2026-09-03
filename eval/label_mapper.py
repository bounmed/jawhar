"""
label_mapper.py — Convert Jawhar analyzer output to PADT coarse-grained tags.

Loads the mapping defined in tagset_mapping.json and exposes:
  - tag_for_candidate(candidate) -> Optional[str]
  - best_tag(candidates, use_rule_priority=True) -> str

Matching is diacritic-insensitive: the analyzer outputs voweled Arabic
(e.g. ضَمِير) while mapping keys may be unvoweled (ضَمير); both are
normalised before lookup.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import List, Optional

_DIR = os.path.dirname(os.path.abspath(__file__))
_MAPPING_PATH = os.path.join(_DIR, "tagset_mapping.json")
_FALLBACK_TAG = "FALLBACK"

logger = logging.getLogger(__name__)

_DIACRITICS_RE = re.compile(r"[ًٌٍَُِّْٰ]")


def _normalize(s: str) -> str:
    """Strip Arabic diacritics and normalise alef/ta-marbuta for matching."""
    s = _DIACRITICS_RE.sub("", s)
    s = s.replace("إ", "ا").replace("أ", "ا").replace("آ", "ا").replace("ئ", "ي").replace("ؤ", "و")
    s = s.replace("ة", "ه").replace("ى", "ي")
    return s


class LabelMapper:
    def __init__(self, mapping_path: str = _MAPPING_PATH, fallback_tag: str = _FALLBACK_TAG):
        with open(mapping_path, encoding="utf-8") as f:
            raw = json.load(f)
        # build a normalised-key -> tag dict; skip documentation keys
        self.mapping: dict[str, str] = {}
        for k, v in raw.get("mapping", raw).items():
            if k.startswith("_"):
                continue
            self.mapping[_normalize(k)] = v
        self.fallback_tag = fallback_tag
        self._unmapped: set = set()

    def tag_for_candidate(self, candidate) -> Optional[str]:
        """Return the PADT tag for a single Jawhar Result, or None if unmapped."""
        wt = getattr(candidate, "word_type", "") or ""
        tag = self.mapping.get(_normalize(wt))
        if tag is None and wt and wt not in self._unmapped:
            self._unmapped.add(wt)
            logger.warning("Unmapped word_type: %r", wt)
        return tag

    def best_tag(self, candidates: list, use_rule_priority: bool = True) -> str:
        """Pick the best tag from a list of candidates.

        If use_rule_priority: take the first (lowest-priority) candidate whose
        word_type maps to a PADT tag (Jawhar already sorts by priority ascending).
        """
        if not candidates:
            return self.fallback_tag
        for c in candidates:
            tag = self.tag_for_candidate(c)
            if tag is not None:
                return tag
        return self.fallback_tag

    @property
    def unmapped_types(self) -> set:
        return set(self._unmapped)
