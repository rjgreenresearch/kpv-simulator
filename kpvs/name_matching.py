"""
kpvs/name_matching.py — Name normalization and fuzzy matching utilities
========================================================================

Foundation utilities for fuzzy name matching across multi-script OSINT
sources. Used by Person.match() and by the future entity resolver (PR #5).

Scope
-----
This module provides the *building blocks* — it is not a full entity
resolver. It handles:

  • Diacritic stripping & whitespace normalization
  • Cross-script transliteration confusions (Pinyin ↔ Wade-Giles,
    common Cyrillic-Latin pairs, hyphen variations)
  • Token-set matching (handles "Last, First" vs "First Last")
  • SequenceMatcher-based fuzzy scoring
  • Person lookup by query string with confidence threshold

The full resolver in PR #5 will add:
  • Cross-source merge candidate generation
  • Role-context disambiguation against curated taxonomies
  • Confidence calibration against ground-truth pairs
  • Bulk graph deduplication
"""

from __future__ import annotations

import logging
import unicodedata
from difflib import SequenceMatcher
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Common cross-romanization confusion pairs
# ─────────────────────────────────────────────────────────────────────────
# These are the single highest-leverage entries for Chinese names. The
# pairs are bidirectional (we try both directions during matching).
#
# Pinyin → Wade-Giles for the top surnames and most common syllables
# encountered in CCP elite names. Not exhaustive; intended to catch the
# 80%-case for CCP/PLA leadership where Anglosphere sources still
# occasionally use Wade-Giles or older transliterations.
PINYIN_WADE_GILES = {
    # Surnames
    "xi": "hsi",
    "zhao": "chao",
    "zhang": "chang",
    "zhou": "chou",
    "zhu": "chu",
    "chen": "chen",
    "cao": "tsao",
    "cheng": "cheng",
    "ji": "chi",
    "jiang": "chiang",
    "qing": "ching",
    "qiao": "chiao",
    "qin": "chin",
    "qu": "chu",
    "huang": "hwang",
    "wu": "wu",
    "yu": "yu",
    "ye": "yeh",
    "ren": "jen",
    "ruan": "juan",
    "rui": "jui",
    "ze": "tse",
    "zi": "tzu",
    # Syllables common in given names
    "jinping": "chinping",
    "jintao": "chintao",
    "zemin": "tsemin",
    "xiaoping": "hsiaoping",
    "qiang": "chiang",
    "huning": "huning",
    "leji": "lochi",
    "youxia": "yuhsia",
    "weidong": "weitung",
    "qi": "chi",
    "ping": "ping",
    "tao": "tao",
    "min": "min",
    "ji": "chi",
    "qiao": "chiao",
}

# Common Russian Cyrillic ↔ Latin transliteration confusions for names
# encountered in Russian leadership OSINT.
RUSSIAN_LATIN_PAIRS = {
    # Given-name short forms
    "vladimir": "владимир",
    "sergei": "сергей",
    "sergey": "сергей",
    "dmitry": "дмитрий",
    "dmitri": "дмитрий",
    "nikolai": "николай",
    "nikolay": "николай",
    "alexei": "алексей",
    "alexey": "алексей",
    "yevgeny": "евгений",
    "evgeny": "евгений",
    "mikhail": "михаил",
    "boris": "борис",
    # Surnames
    "putin": "путин",
    "lavrov": "лавров",
    "shoigu": "шойгу",
    "patrushev": "патрушев",
    "medvedev": "медведев",
    "naryshkin": "нарышкин",
    "bortnikov": "бортников",
}

# Persian/Farsi common transliteration confusions for IRGC/regime leadership
PERSIAN_LATIN_PAIRS = {
    "khamenei": "خامنه‌ای",
    "khomeini": "خمینی",
    "raisi": "رئیسی",
    "salami": "سلامی",
    "qaani": "قاآنی",
    "ghaani": "قاآنی",
    "soleimani": "سلیمانی",
    "rouhani": "روحانی",
}

# Korean revised ↔ McCune-Reischauer for DPRK leadership
KOREAN_PAIRS = {
    "kim jong un": "kim chong un",
    "kim jong-un": "kim chong un",
    "kim chŏng ŭn": "kim chong un",
    "kim jong il": "kim chong il",
    "kim jong-il": "kim chong il",
    "kim il sung": "kim il-song",
}


def _build_bidirectional(table: dict) -> dict:
    """Build a bidirectional lookup from a one-way table."""
    out = dict(table)
    for k, v in table.items():
        out.setdefault(v, k)
    return out


_ALL_PAIRS = {}
for table in (PINYIN_WADE_GILES, RUSSIAN_LATIN_PAIRS,
              PERSIAN_LATIN_PAIRS, KOREAN_PAIRS):
    _ALL_PAIRS.update(_build_bidirectional(table))


# ─────────────────────────────────────────────────────────────────────────
# Normalization
# ─────────────────────────────────────────────────────────────────────────
def strip_diacritics(text: str) -> str:
    """Remove combining diacritical marks via Unicode NFKD decomposition.

    'Cǎi Qí' → 'Cai Qi'
    'Khāmenei' → 'Khamenei'
    'José' → 'Jose'
    """
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Canonicalize a name string for comparison.

    Applies (in order):
      1. Strip surrounding whitespace
      2. Lowercase
      3. Strip diacritics
      4. Replace hyphens with spaces
      5. Collapse multiple spaces
      6. Strip apostrophes (Wade-Giles aspiration marks: t'ai → tai)
      7. Strip common punctuation
    """
    if not text:
        return ""
    s = text.strip().lower()
    s = strip_diacritics(s)
    s = s.replace("-", " ").replace("'", "").replace("'", "")
    s = s.replace(".", " ").replace(",", " ")
    s = s.replace("ʿ", "").replace("ʾ", "")  # Arabic ayin/hamza marks
    # Collapse whitespace
    s = " ".join(s.split())
    return s


# ─────────────────────────────────────────────────────────────────────────
# Transliteration variant generation
# ─────────────────────────────────────────────────────────────────────────
def transliteration_variants(text: str) -> list:
    """Generate plausible cross-romanization variants of a normalized name.

    Looks up each token against the bidirectional confusion table and
    yields strings with substitutions applied. Returns a list (order
    preserved, deduplicated) including the original.
    """
    if not text:
        return [""]

    norm = normalize(text)
    tokens = norm.split()
    variants = {norm}

    # Single-token substitutions (one swap at a time)
    for i, tok in enumerate(tokens):
        if tok in _ALL_PAIRS:
            new_tokens = list(tokens)
            new_tokens[i] = _ALL_PAIRS[tok]
            variants.add(" ".join(new_tokens))

    # Joint-token substitution (e.g., "jin ping" ↔ "chin ping")
    if len(tokens) >= 2:
        # Try "jinping" ↔ "chinping" type joint forms
        joined = "".join(tokens[1:]) if len(tokens) > 1 else ""
        if joined in _ALL_PAIRS:
            variants.add(tokens[0] + " " + _ALL_PAIRS[joined])

    # Try with reversed token order (handles "Smith, John" vs "John Smith")
    if len(tokens) >= 2:
        variants.add(" ".join(reversed(tokens)))

    return list(variants)


# ─────────────────────────────────────────────────────────────────────────
# Match scoring
# ─────────────────────────────────────────────────────────────────────────
def match_score(query: str, candidate: str) -> float:
    """Score similarity between query and candidate name in [0, 1].

    Uses normalized exact match (1.0), token-set match (0.95),
    transliteration-variant match (0.92), and SequenceMatcher ratio
    (0.0–1.0) as fallback. Returns the max.
    """
    if not query or not candidate:
        return 0.0

    q_norm = normalize(query)
    c_norm = normalize(candidate)

    if not q_norm or not c_norm:
        return 0.0

    # Exact normalized
    if q_norm == c_norm:
        return 1.0

    # Token-set equality (handles reversed order, comma-separated)
    q_toks = set(q_norm.split())
    c_toks = set(c_norm.split())
    if q_toks and q_toks == c_toks:
        return 0.95

    # Transliteration variants
    best = 0.0
    for variant in transliteration_variants(c_norm):
        if q_norm == variant:
            return 0.92
        ratio = SequenceMatcher(None, q_norm, variant).ratio()
        if ratio > best:
            best = ratio

    # Direct ratio against original (in case transliteration isn't relevant)
    direct = SequenceMatcher(None, q_norm, c_norm).ratio()
    return max(best, direct)


def find_person(query: str, persons, threshold: float = 0.85) -> Optional[tuple]:
    """Find the person whose name/aliases best match a query.

    Parameters
    ----------
    query     : str — the lookup string (any script, any romanization)
    persons   : iterable of Person objects (or dict[id, Person])
    threshold : float in [0, 1] — minimum match score to return a hit

    Returns
    -------
    (person, score, matched_text) tuple, or None if no match exceeds
    threshold.
    """
    if isinstance(persons, dict):
        candidates = persons.values()
    else:
        candidates = persons

    best_person = None
    best_score = 0.0
    best_text = None

    for person in candidates:
        # Build candidate texts: primary name + native + all alias texts
        candidate_texts = [person.name]
        if getattr(person, "name_native", ""):
            candidate_texts.append(person.name_native)
        for alias in getattr(person, "aliases", []):
            # Handle both Alias objects and plain strings
            text = alias.text if hasattr(alias, "text") else str(alias)
            candidate_texts.append(text)

        for text in candidate_texts:
            score = match_score(query, text)
            if score > best_score:
                best_score = score
                best_person = person
                best_text = text

    if best_score >= threshold:
        return (best_person, best_score, best_text)
    return None


def find_persons_above(query: str, persons, threshold: float = 0.7) -> list:
    """Like find_person but returns ALL matches above threshold, sorted
    by score descending. Useful when ambiguity should be surfaced rather
    than auto-resolved (e.g., 'Wang' could match many Politburo members).
    """
    if isinstance(persons, dict):
        candidates = persons.values()
    else:
        candidates = persons

    results = []
    for person in candidates:
        candidate_texts = [person.name]
        if getattr(person, "name_native", ""):
            candidate_texts.append(person.name_native)
        for alias in getattr(person, "aliases", []):
            text = alias.text if hasattr(alias, "text") else str(alias)
            candidate_texts.append(text)

        best_for_this = 0.0
        best_text = None
        for text in candidate_texts:
            score = match_score(query, text)
            if score > best_for_this:
                best_for_this = score
                best_text = text

        if best_for_this >= threshold:
            results.append((person, best_for_this, best_text))

    return sorted(results, key=lambda r: -r[1])
