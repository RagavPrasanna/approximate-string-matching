"""Core interfaces shared by every approximate-search implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Match:
    """One approximate occurrence.

    ``end`` is a 0-based *exclusive* end position, i.e. the occurrence is a
    substring ``text[start:end]``.  Returning the start is optional: the
    algorithms in this project solve the semi-global problem, where the start
    is free.  Add one to ``end`` to obtain a human-readable 1-based ending
    position.
    """

    end: int
    distance: int


def normalise(matches: Iterable[Match]) -> list[Match]:
    """Sort matches and keep the minimum distance reported for each end."""

    best: dict[int, int] = {}
    for match in matches:
        old = best.get(match.end)
        if old is None or match.distance < old:
            best[match.end] = match.distance
    return [Match(end, best[end]) for end in sorted(best)]


def as_dict(matches: Iterable[Match]) -> dict[int, int]:
    return {match.end: match.distance for match in normalise(matches)}
