"""
tests/test_name_matching.py — Unit tests for fuzzy name matching
==================================================================
"""

import pytest

from kpvs.persons import Person, Alias
from kpvs.name_matching import (
    normalize, strip_diacritics, transliteration_variants,
    match_score, find_person, find_persons_above,
)


# ─────────────────────────────────────────────────────────────────────────
# Normalization
# ─────────────────────────────────────────────────────────────────────────
class TestNormalize:
    def test_diacritics_stripped(self):
        assert normalize("Cǎi Qí") == "cai qi"
        assert normalize("Khāmenei") == "khamenei"
        assert normalize("José") == "jose"

    def test_lowercase(self):
        assert normalize("XI JINPING") == "xi jinping"

    def test_whitespace_collapsed(self):
        assert normalize("  Xi   Jinping  ") == "xi jinping"

    def test_hyphens_become_spaces(self):
        assert normalize("Kim Jong-un") == "kim jong un"

    def test_apostrophes_stripped(self):
        # Wade-Giles uses apostrophes for aspiration: t'ai → tai
        assert normalize("Hsi Chin-p'ing") == "hsi chin ping"

    def test_punctuation_handled(self):
        assert normalize("Putin, V.V.") == "putin v v"

    def test_empty_returns_empty(self):
        assert normalize("") == ""


# ─────────────────────────────────────────────────────────────────────────
# Transliteration variants
# ─────────────────────────────────────────────────────────────────────────
class TestTransliterationVariants:
    def test_includes_original(self):
        variants = transliteration_variants("xi jinping")
        assert "xi jinping" in variants

    def test_pinyin_to_wade_giles(self):
        variants = transliteration_variants("xi jinping")
        # Should contain Wade-Giles surname variant
        assert any("hsi" in v for v in variants)

    def test_handles_reversed_order(self):
        variants = transliteration_variants("xi jinping")
        # Should include reversed token form
        assert any(v.startswith("jinping") for v in variants)


# ─────────────────────────────────────────────────────────────────────────
# Match scoring
# ─────────────────────────────────────────────────────────────────────────
class TestMatchScore:
    def test_exact_normalized_match(self):
        assert match_score("Xi Jinping", "xi jinping") == 1.0
        assert match_score("XI JINPING", "Xi Jinping") == 1.0

    def test_diacritics_dont_block_exact(self):
        assert match_score("Cǎi Qí", "Cai Qi") == 1.0

    def test_token_set_match(self):
        # Reversed order
        score = match_score("Jinping Xi", "Xi Jinping")
        assert score >= 0.95

    def test_wade_giles_to_pinyin(self):
        # Hsi Chin-p'ing should match Xi Jinping
        score = match_score("Hsi Chinping", "Xi Jinping")
        assert score >= 0.85, f"got {score}"

    def test_partial_match_below_one(self):
        # "Xi" alone should partially match "Xi Jinping" but not perfectly
        score = match_score("Xi", "Xi Jinping")
        assert 0 < score < 1.0

    def test_unrelated_low_score(self):
        score = match_score("Vladimir Putin", "Xi Jinping")
        assert score < 0.5

    def test_empty_returns_zero(self):
        assert match_score("", "Xi Jinping") == 0.0
        assert match_score("Xi Jinping", "") == 0.0


# ─────────────────────────────────────────────────────────────────────────
# Person.match() integration
# ─────────────────────────────────────────────────────────────────────────
class TestPersonMatch:
    def test_match_against_primary_name(self):
        p = Person(id="P-XI", name="Xi Jinping", country="CN")
        result = p.match("Xi Jinping")
        assert result is not None
        score, text = result
        assert score == 1.0

    def test_match_against_alias(self):
        p = Person(
            id="P-XI", name="Xi Jinping", country="CN",
            aliases=[Alias(text="Hsi Chin-p'ing",
                           romanization="wade-giles")],
        )
        result = p.match("Hsi Chin-p'ing")
        assert result is not None
        score, _ = result
        assert score >= 0.95

    def test_match_native_script(self):
        p = Person(
            id="P-XI", name="Xi Jinping", country="CN",
            name_native="习近平",
        )
        result = p.match("习近平")
        assert result is not None
        score, text = result
        assert score == 1.0
        assert text == "习近平"

    def test_no_match_returns_none(self):
        p = Person(id="P-XI", name="Xi Jinping", country="CN")
        assert p.match("Vladimir Putin") is None

    def test_threshold_respected(self):
        p = Person(id="P-XI", name="Xi Jinping", country="CN")
        # Low-confidence partial query
        result = p.match("Xi", threshold=0.99)  # too strict
        assert result is None

    def test_wade_giles_via_aliases(self):
        """The intended use case — aliases populated with transliterations
        let cross-script queries resolve."""
        p = Person(
            id="P-XI", name="Xi Jinping", country="CN",
            name_native="习近平",
            aliases=[
                Alias(text="Hsi Chin-p'ing", language="zh",
                      romanization="wade-giles"),
                Alias(text="Си Цзиньпин", script="cyrl", language="ru"),
            ],
        )
        # Russian-source spelling
        r1 = p.match("Си Цзиньпин")
        assert r1 is not None and r1[0] >= 0.95
        # Wade-Giles spelling
        r2 = p.match("Hsi Chinping")
        assert r2 is not None and r2[0] >= 0.85


# ─────────────────────────────────────────────────────────────────────────
# find_person across a population
# ─────────────────────────────────────────────────────────────────────────
class TestFindPerson:
    @pytest.fixture
    def population(self):
        return {
            "P-XI": Person(
                id="P-XI", name="Xi Jinping", country="CN",
                name_native="习近平",
                aliases=[Alias(text="Hsi Chin-p'ing", romanization="wade-giles")],
            ),
            "P-LI-Q": Person(
                id="P-LI-Q", name="Li Qiang", country="CN",
                name_native="李强",
            ),
            "P-PUTIN": Person(
                id="P-PUTIN", name="Vladimir Putin", country="RU",
                name_native="Владимир Путин",
                aliases=[Alias(text="V.V. Putin")],
            ),
        }

    def test_finds_by_primary_name(self, population):
        result = find_person("Xi Jinping", population)
        assert result is not None
        person, score, _ = result
        assert person.id == "P-XI"

    def test_finds_by_native_script(self, population):
        result = find_person("习近平", population)
        assert result is not None
        person, _, _ = result
        assert person.id == "P-XI"

    def test_finds_by_alias(self, population):
        result = find_person("Hsi Chin-p'ing", population)
        assert result is not None
        person, _, _ = result
        assert person.id == "P-XI"

    def test_finds_putin_variants(self, population):
        for query in ["Vladimir Putin", "V.V. Putin", "Владимир Путин",
                      "Putin"]:
            result = find_person(query, population, threshold=0.7)
            assert result is not None, f"failed on '{query}'"
            person, _, _ = result
            assert person.id == "P-PUTIN", f"wrong match on '{query}'"

    def test_threshold_filters_out_weak(self, population):
        # Single token "Li" shouldn't confidently resolve at 0.95
        result = find_person("Li", population, threshold=0.95)
        assert result is None

    def test_find_persons_above_returns_sorted(self, population):
        # Add a Wang person to create ambiguity
        population["P-WANG-H"] = Person(
            id="P-WANG-H", name="Wang Huning", country="CN")
        population["P-WANG-Y"] = Person(
            id="P-WANG-Y", name="Wang Yi", country="CN")

        results = find_persons_above("Wang", population, threshold=0.4)
        assert len(results) >= 2
        # Sorted descending by score
        scores = [r[1] for r in results]
        assert scores == sorted(scores, reverse=True)


# ─────────────────────────────────────────────────────────────────────────
# Backward compatibility — old aliases=[str] still works
# ─────────────────────────────────────────────────────────────────────────
class TestBackwardCompat:
    def test_string_aliases_promoted(self):
        p = Person(id="P", name="Xi Jinping", country="CN",
                   aliases=["Hsi Chin-p'ing", "习近平"])
        assert len(p.aliases) == 2
        assert all(isinstance(a, Alias) for a in p.aliases)
        assert p.aliases[0].text == "Hsi Chin-p'ing"
        assert p.aliases[0].confidence == 1.0  # default

    def test_dict_aliases_promoted(self):
        p = Person(id="P", name="Xi Jinping", country="CN",
                   aliases=[
                       {"text": "Hsi Chin-p'ing",
                        "romanization": "wade-giles",
                        "confidence": 0.9},
                   ])
        assert isinstance(p.aliases[0], Alias)
        assert p.aliases[0].confidence == 0.9
        assert p.aliases[0].romanization == "wade-giles"

    def test_mixed_alias_types(self):
        p = Person(
            id="P", name="Xi Jinping", country="CN",
            aliases=[
                "Hsi Chin-p'ing",
                Alias(text="习近平", script="hans", language="zh"),
                {"text": "Си Цзиньпин", "script": "cyrl"},
            ],
        )
        assert len(p.aliases) == 3
        assert all(isinstance(a, Alias) for a in p.aliases)


# ─────────────────────────────────────────────────────────────────────────
# Alias validation
# ─────────────────────────────────────────────────────────────────────────
class TestAliasValidation:
    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="text"):
            Alias(text="")

    def test_confidence_out_of_range(self):
        with pytest.raises(ValueError, match="confidence"):
            Alias(text="X", confidence=1.5)

    def test_to_dict_roundtrip(self):
        a = Alias(text="Hsi Chin-p'ing",
                  script="latn", language="zh",
                  romanization="wade-giles", confidence=0.9)
        d = a.to_dict()
        a2 = Alias(**d)
        assert a == a2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
