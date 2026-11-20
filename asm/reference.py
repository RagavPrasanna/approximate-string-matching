"""Slow but transparent reference implementation and comparison helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from .algorithms import levenshtein_rolling
from .models import Match, as_dict


def brute_force_search(text: str, pattern: str, k: int) -> list[Match]:
    """Try every non-empty substring; intended only for tiny inputs.

    The empty pattern is a special case: it matches every end position,
    including position 0.  For a non-empty pattern, empty substrings are not
    reported; this is the convention used by every search algorithm here.
    """

    n, m = len(text), len(pattern)
    if m == 0:
        return [Match(end, 0) for end in range(n + 1)]

    best: dict[int, int] = {}
    for start in range(n):
        for end in range(start + 1, n + 1):
            distance = levenshtein_rolling(pattern, text[start:end])
            if distance <= k:
                old = best.get(end)
                if old is None or distance < old:
                    best[end] = distance
    return [Match(end, best[end]) for end in sorted(best)]


SearchFn = Callable[[str, str, int], Iterable[Match]]


def compare_to_reference(
    search: SearchFn,
    text: str,
    pattern: str,
    k: int,
) -> tuple[bool, str]:
    expected = as_dict(brute_force_search(text, pattern, k))
    actual = as_dict(search(text, pattern, k))
    if actual == expected:
        return True, ""
    missing = {end: dist for end, dist in expected.items() if end not in actual}
    extra = {end: dist for end, dist in actual.items() if end not in expected}
    wrong = {
        end: (actual[end], expected[end])
        for end in expected.keys() & actual.keys()
        if actual[end] != expected[end]
    }
    parts = []
    if missing:
        parts.append(f"missing={missing}")
    if extra:
        parts.append(f"extra={extra}")
    if wrong:
        parts.append(f"wrong_distance={wrong}")
    return False, "; ".join(parts)


def validate_structure(matches: Iterable[Match], n: int, k: int) -> None:
    """Raise AssertionError if a match violates the public contract."""

    values = list(matches)
    ends = [match.end for match in values]
    assert ends == sorted(ends), "matches are not sorted by end position"
    seen: set[int] = set()
    for match in values:
        assert 0 <= match.end <= n, f"end outside text: {match}"
        assert 0 <= match.distance <= k, f"distance outside threshold: {match}"
        assert match.end not in seen, f"duplicate end: {match.end}"
        seen.add(match.end)
