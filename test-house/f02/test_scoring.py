"""F02 scorer, glossary and calibration differentials."""

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from math import ceil, fsum, log1p
from random import Random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities.f02.calibration import Calibration, Pair, fit
from capabilities.f02.scoring import Candidate, Entry, Exclusion, TariffIndex, TariffPack, tokenize
from data.synthetic.calibration.classification import SOURCE_ID, commercial_names, generate_pairs
from kernel.decision import FactEntry
from kernel.lib.conformal import calibrate

AT = datetime(2026, 11, 1, tzinfo=UTC)
ENDS = AT + timedelta(days=1)
TEXTS = {
    "1101": "wheat flour finely ground",
    "1201": "soy beans edible seeds",
    "1301": "natural gum extracted resin",
    "1401": "reed strips woven fiber",
}
PACK = TariffPack(
    SOURCE_ID,
    "SYNTHETIC",
    AT,
    ENDS,
    (2, 4, 6),
    4,
    tuple(Entry(code, (text,), AT, ENDS) for code, text in TEXTS.items()),
    frozenset({"the", "a", "as"}),
)
INDEX = TariffIndex.build(PACK)
HELD = (Pair("1101", TEXTS["1101"], "pack_text"),)
SHIFTED = (Pair("1101", "assorted unidentified cargo", "commercial_name"),)


def pairs_for(pack: TariffPack, counts: tuple[int, ...]) -> tuple[Pair, ...]:
    return tuple(
        Pair(row.code, row.path[0], "commercial_name" if number % 2 else "pack_text")
        for row, count in zip(pack.entries, counts, strict=True)
        for number in range(count)
    )


def calibration() -> Calibration:
    rows = generate_pairs(TEXTS, commercial_names("en"), chapter_digits=2, seed=19, count=500)
    pairs = tuple(Pair(row.code, row.text, row.layer) for row in rows)
    return fit(INDEX, pairs, HELD, SHIFTED, language="en", source_id=SOURCE_ID)


def reference_scores(pack: TariffPack, query: tuple[str, ...]) -> dict[str, float]:
    """Score each entry independently by scanning every description."""
    terms = {
        row.code: Counter(tokenize(" ".join(row.path), pack).terms)
        for row in pack.entries
        if len(row.code) == pack.resolution
    }
    average = fsum(counts.total() for counts in terms.values()) / len(terms)
    result = {}
    for code, counts in terms.items():
        weights = {
            term: log1p(
                (len(terms) - sum(term in doc for doc in terms.values()) + 0.5)
                / (0.5 + sum(term in doc for doc in terms.values()))
            )
            * frequency
            * (pack.k1 + 1)
            / (frequency + pack.k1 * (1 - pack.b + pack.b * counts.total() / average))
            for term, frequency in counts.items()
        }
        result[code] = fsum(weights.get(term, 0) for term in set(query)) / fsum(weights.values())
    return result


@pytest.mark.fast
@given(st.lists(st.sampled_from(tuple(" ".join(TEXTS.values()).split())), max_size=80))
def test_T_F02_0201_similarity_matches_reference(words: list[str]) -> None:
    """
    id: T-F02-0201
    title: Similarity matches reference
    purpose: Similarity matches reference
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    actual = INDEX.similarity(words)
    assert all(0 <= score <= 1 for score in actual.values())
    assert actual == pytest.approx(reference_scores(PACK, tuple(words)), abs=1e-14)


@pytest.mark.fast
@pytest.mark.parametrize(
    "description",
    [
        "soy beans edible seeds",
        "natural gum extracted resin",
        "reed strips woven fiber",
        "  WHEAT   flour  FINELY ground ",
        "soy beans a edible seeds 1101",
        "soy beans １１０１ edible seeds",
        "soy beans ١١٠١ edible seeds",
        "wheat wheat wheat wheat",
        "not part of heading",
        "reed strips woven fiber 1401",
    ],
    ids=[f"T-F02-{number:04}" for number in range(202, 212)],
)
def test_scorer_optimized_and_differential(description: str) -> None:
    """
    id: T-F02-0202
    title: Scorer optimized and differential
    purpose: Scorer optimized and differential
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    tokens = tokenize(description, PACK)
    assert INDEX.similarity(tokens.terms) == pytest.approx(reference_scores(PACK, tokens.terms))


@pytest.mark.fast
@pytest.mark.parametrize(
    ("alpha", "smaller"),
    [(0.2, 0.1), (0.1, 0.05), (0.05, 0.01)],
    ids=["T-F02-0212", "T-F02-0213", "T-F02-0214"],
)
def test_smaller_alpha_never_shrinks_candidates(alpha: float, smaller: float) -> None:
    """
    id: T-F02-0212
    title: Smaller alpha never shrinks candidates
    purpose: Smaller alpha never shrinks candidates
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    pairs = pairs_for(PACK, (125,) * 4)
    broad = fit(INDEX, pairs, HELD, SHIFTED, language="en", source_id=SOURCE_ID, alpha=smaller)
    tight = fit(INDEX, pairs, HELD, SHIFTED, language="en", source_id=SOURCE_ID, alpha=alpha)
    terms = tokenize(TEXTS["1101"], PACK).terms
    assert set(INDEX.candidates(terms, AT, tight.threshold)) <= set(
        INDEX.candidates(terms, AT, broad.threshold)
    )


@pytest.mark.fast
def test_T_F02_0215_quantile_matches_definition() -> None:
    """
    id: T-F02-0215
    title: Quantile matches definition
    purpose: Quantile matches definition
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    rows = generate_pairs(TEXTS, commercial_names("en"), chapter_digits=2, seed=19, count=500)
    scores = [
        1 - reference_scores(PACK, tokenize(record.text, PACK).terms)[record.code]
        for record in rows
    ]
    order = ceil(Fraction(9, 10) * (len(scores) + 1))
    expected = next(
        value
        for value in sorted(set(scores))
        if scores.count(value) + sum(score < value for score in scores) >= order
    )
    assert calibration().threshold == pytest.approx(expected)


@pytest.mark.slow
def test_T_F02_0216_seeded_conformal_coverage_implementation_correctness() -> None:
    """
    id: T-F02-0216
    title: Seeded conformal coverage implementation correctness
    purpose: Seeded conformal coverage implementation correctness
    level: slow
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    rng = Random(9817)
    covered = 0
    for _trial in range(1000):
        artifact = calibrate(
            {"tariff": [rng.random() for _ in range(500)]},
            alpha=0.1,
            version=INDEX.pack_hash,
            source_id=SOURCE_ID,
        )
        quantile = artifact.thresholds[0].threshold
        assert quantile is not None
        covered += rng.random() <= quantile
    assert abs(covered / 1000 - 0.9) <= 3 * (0.9 * 0.1 / 1000) ** 0.5


@pytest.mark.fast
def test_T_F02_0217_english_only_without_glossary() -> None:
    """
    id: T-F02-0217
    title: English only without glossary
    purpose: English only without glossary
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert not tokenize("خبز كعك دقيق", replace(PACK, languages=("ar", "en"))).supported


@pytest.mark.fast
def test_T_F02_0218_glossary_expansion_is_stable_and_recorded() -> None:
    """
    id: T-F02-0218
    title: Glossary expansion is stable and recorded
    purpose: Glossary expansion is stable and recorded
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    bilingual = replace(
        PACK,
        languages=("ar", "en"),
        glossary=(("خبز", ("wheat",)), ("دقيق", ("flour",)), ("كعك", ("ground",))),
    )
    original = tokenize("خبز كعك دقيق", bilingual)
    assert original == tokenize("خبز كعك دقيق", bilingual)
    assert original.supported and original.language == "ar"
    assert original.terms == ("wheat", "ground", "flour")
    assert dict(original.expansion)["دقيق"] == ("flour",)


@pytest.mark.fast
def test_T_F02_0219_refuse_a_mismatched_calibration_language() -> None:
    """
    id: T-F02-0219
    title: Refuse a mismatched calibration language
    purpose: Refuse a mismatched calibration language
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    pack = replace(PACK, languages=("en", "ar"))
    with pytest.raises(ValueError, match="CALIBRATION_STALE"):
        fit(
            TariffIndex.build(pack),
            pairs_for(pack, (125,) * 4),
            HELD,
            SHIFTED,
            language="ar",
            source_id=SOURCE_ID,
        )


def many_chapters(count: int) -> TariffPack:
    entries = tuple(
        Entry(f"{i:02}01", ("manufactured synthetic sample",), AT, ENDS)
        for i in range(1, count + 1)
    )
    return replace(PACK, entries=entries)


@pytest.mark.fast
@pytest.mark.parametrize(
    ("chapters", "counts", "valid"),
    [
        (96, (6,) * 20 + (5,) * 76, False),
        (96, (10,) * 96, True),
        (96, (9, 11) + (10,) * 94, False),
        (50, (10,) * 50, True),
        (51, (10,) * 50 + (0,), False),
        (51, (10,) * 51, True),
        (49, (10,) * 49, False),
    ],
    ids=[f"T-F02-{number:04}" for number in range(220, 227)],
)
def test_pack_derived_minimum(chapters: int, counts: tuple[int, ...], valid: bool) -> None:
    """
    id: T-F02-0220
    title: Pack derived minimum
    purpose: Pack derived minimum
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    tariff = many_chapters(chapters)
    index = TariffIndex.build(tariff)
    pairs = pairs_for(tariff, counts)
    sample = (Pair(tariff.entries[0].code, tariff.entries[0].path[0], "pack_text"),)
    if not valid:
        with pytest.raises(ValueError, match="CALIBRATION_STALE"):
            fit(index, pairs, sample, sample, language="en", source_id=SOURCE_ID)
        return
    result = fit(index, pairs, sample, sample, language="en", source_id=SOURCE_ID)
    assert result.chapter_count == chapters
    assert result.count == sum(counts)
    assert min(size for _, size in result.counts) == 10


@pytest.mark.fast
@pytest.mark.parametrize(
    ("status", "exclude"),
    [("VERIFIED", True), ("PROPOSED", False), ("UNKNOWN", False), ("CONFLICTED", False)],
    ids=[f"T-F02-{number:04}" for number in range(227, 231)],
)
def test_tariff_filter_requires_verified_applicability(status: str, exclude: bool) -> None:
    """
    id: T-F02-0227
    title: Tariff filter requires verified applicability
    purpose: Tariff filter requires verified applicability
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    rule = Exclusion("SYN-RULE", "1101", "material", "polymer")
    index = TariffIndex.build(replace(PACK, exclusions=(rule,)))
    candidates = (Candidate("1101", 0), Candidate("1201", 0.1))
    retained, applied = index.filter(
        candidates, (FactEntry("material", "polymer", status, "DERIVED"),)
    )
    assert (retained, applied) == ((candidates[1:], (rule,)) if exclude else (candidates, ()))
