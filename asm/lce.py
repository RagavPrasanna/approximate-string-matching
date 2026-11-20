"""Deterministic longest-common-extension (LCE) queries.

The implementation concatenates the pattern and text with two integer
separators, builds a suffix array, the Kasai LCP array, and a sparse table for
range-minimum queries.  After preprocessing, LCE(i, j) is O(1).

The suffix-array construction below uses prefix doubling with Python's
comparison sort.  It is therefore O(N log^2 N) in the worst case, although the
constant is small for the input sizes used in this project.  The important
property for the Landau-Vishkin experiment is that each LCE query is O(1).
"""

from __future__ import annotations

from dataclasses import dataclass


def _suffix_array(sequence: list[int]) -> list[int]:
    n = len(sequence)
    if n == 0:
        return []
    sa = list(range(n))
    rank = sequence[:]
    k = 1
    tmp = [0] * n

    while True:
        sa.sort(key=lambda i: (rank[i], rank[i + k] if i + k < n else -1))

        tmp[sa[0]] = 0
        for pos in range(1, n):
            a = sa[pos - 1]
            b = sa[pos]
            prev_key = (rank[a], rank[a + k] if a + k < n else -1)
            cur_key = (rank[b], rank[b + k] if b + k < n else -1)
            tmp[b] = tmp[a] + (cur_key != prev_key)

        rank, tmp = tmp, rank
        if rank[sa[-1]] == n - 1:
            break
        k <<= 1
    return sa


def _lcp_array(sequence: list[int], sa: list[int]) -> list[int]:
    """lcp[r] = LCP(sa[r - 1], sa[r]); lcp[0] = 0."""

    n = len(sequence)
    rank = [0] * n
    for r, pos in enumerate(sa):
        rank[pos] = r

    lcp = [0] * n
    h = 0
    for i in range(n):
        r = rank[i]
        if r == 0:
            continue
        j = sa[r - 1]
        while i + h < n and j + h < n and sequence[i + h] == sequence[j + h]:
            h += 1
        lcp[r] = h
        if h:
            h -= 1
    return lcp


@dataclass
class SuffixArrayLCE:
    """O(1) LCE queries between suffixes of a pattern and a text."""

    pattern_length: int
    text_length: int
    _text_offset: int
    _n: int
    _sa: list[int]
    _rank: list[int]
    _logs: list[int]
    _sparse: list[list[int]]

    @classmethod
    def build(cls, pattern: str, text: str) -> "SuffixArrayLCE":
        values: list[int] = [ord(ch) for ch in pattern]
        separator = max(values + [ord(ch) for ch in text] + [0]) + 1
        text_start = len(pattern) + 1
        sequence = (
            values
            + [separator]
            + [ord(ch) for ch in text]
            + [separator + 1]
        )

        sa = _suffix_array(sequence)
        lcp = _lcp_array(sequence, sa)
        n = len(sequence)
        rank = [0] * n
        for r, pos in enumerate(sa):
            rank[pos] = r

        logs = [0] * (n + 1)
        for i in range(2, n + 1):
            logs[i] = logs[i // 2] + 1

        sparse: list[list[int]] = [lcp]
        width = 1
        while (width << 1) <= n:
            prev = sparse[-1]
            half = width
            width <<= 1
            row = [
                min(prev[i], prev[i + half])
                for i in range(n - width + 1)
            ]
            sparse.append(row)

        return cls(
            pattern_length=len(pattern),
            text_length=len(text),
            _text_offset=text_start,
            _n=n,
            _sa=sa,
            _rank=rank,
            _logs=logs,
            _sparse=sparse,
        )

    def _rmq(self, left: int, right: int) -> int:
        """Minimum on the inclusive interval [left, right]."""

        length = right - left + 1
        level = self._logs[length]
        row = self._sparse[level]
        return min(row[left], row[right - (1 << level) + 1])

    def lce(self, pattern_pos: int, text_pos: int) -> int:
        """Longest common prefix of P[pattern_pos:] and T[text_pos:]."""

        if pattern_pos >= self.pattern_length or text_pos >= self.text_length:
            return 0
        i = pattern_pos
        j = self._text_offset + text_pos
        ri = self._rank[i]
        rj = self._rank[j]
        if ri == rj:
            return min(self.pattern_length - i, self.text_length - text_pos)
        if ri > rj:
            ri, rj = rj, ri
        # LCP of suffixes with ranks ri < rj is min(lcp[ri+1..rj]).
        return self._rmq(ri + 1, rj)


def naive_lce(pattern: str, text: str, i: int, j: int) -> int:
    length = 0
    while (
        i + length < len(pattern)
        and j + length < len(text)
        and pattern[i + length] == text[j + length]
    ):
        length += 1
    return length
