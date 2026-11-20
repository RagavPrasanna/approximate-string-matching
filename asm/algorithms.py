"""Reference implementations of the algorithms studied in the project.

Every approximate-search function has the same interface::

    search(text, pattern, k) -> list[Match]

where a match is reported by its exclusive 0-based end position and its minimum
Levenshtein distance to the pattern.  The start of the matching substring is
not reported because the semi-global problem leaves it free.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lce import SuffixArrayLCE, naive_lce
from .models import Match, normalise

INF = 10**9


# ---------------------------------------------------------------------------
# Distances
# ---------------------------------------------------------------------------


def hamming_distance(a: str, b: str) -> int | None:
    """Hamming distance, or None when the strings have different lengths."""

    if len(a) != len(b):
        return None
    return sum(x != y for x, y in zip(a, b))


def levenshtein_full(a: str, b: str) -> int:
    """Wagner-Fischer distance with the complete (m+1) x (n+1) matrix."""

    m, n = len(a), len(b)
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j

    for i in range(1, m + 1):
        ai = a[i - 1]
        row = d[i]
        prev = d[i - 1]
        for j in range(1, n + 1):
            row[j] = min(
                prev[j] + 1,
                row[j - 1] + 1,
                prev[j - 1] + (ai != b[j - 1]),
            )
    return d[m][n]


def levenshtein_rolling(a: str, b: str) -> int:
    """Wagner-Fischer distance with two rolling rows, O(min(m, n)) space."""

    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    if m == 0:
        return n
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [0] * (n + 1)
        cur[0] = i
        ai = a[i - 1]
        for j in range(1, n + 1):
            cur[j] = min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (ai != b[j - 1]),
            )
        prev = cur
    return prev[n]


def levenshtein_banded(a: str, b: str, k: int) -> int:
    """Exact unit-cost distance if it is at most ``k``, else ``k + 1``.

    Only cells with ``|i - j| <= k`` are evaluated.  The band contains every
    optimal path whose total cost is at most k.  Two rows of width at most
    2k + 1 are kept, so space is O(k) and time is O(k * min(m, n)).
    """

    if k < 0:
        raise ValueError("k must be non-negative")
    if abs(len(a) - len(b)) > k:
        return k + 1
    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    if m == 0:
        return n if n <= k else k + 1

    # Row 0: D[0][j] = j, but only j <= k can belong to the band.
    prev_lo = 0
    prev_hi = min(n, k)
    prev = [j if j <= k else k + 1 for j in range(prev_lo, prev_hi + 1)]

    for i in range(1, m + 1):
        lo = max(0, i - k)
        hi = min(n, i + k)
        cur = [k + 1] * (hi - lo + 1)
        ai = a[i - 1]
        for j in range(lo, hi + 1):
            if j == 0:
                value = i
            else:
                up = (
                    prev[j - prev_lo]
                    if prev_lo <= j <= prev_hi
                    else k + 1
                )
                diag = (
                    prev[j - 1 - prev_lo]
                    if prev_lo <= j - 1 <= prev_hi
                    else k + 1
                )
                left = cur[j - 1 - lo] if j - 1 >= lo else k + 1
                value = min(
                    up + 1,
                    left + 1,
                    diag + (ai != b[j - 1]),
                )
                if value > k:
                    value = k + 1
            cur[j - lo] = value
        prev, prev_lo, prev_hi = cur, lo, hi

    return prev[n - prev_lo] if prev_lo <= n <= prev_hi else k + 1


# ---------------------------------------------------------------------------
# Exact matching baselines (k = 0)
# ---------------------------------------------------------------------------


def naive_exact(text: str, pattern: str) -> list[Match]:
    n, m = len(text), len(pattern)
    if m == 0:
        return [Match(end, 0) for end in range(n + 1)]
    return [
        Match(start + m, 0)
        for start in range(n - m + 1)
        if text[start : start + m] == pattern
    ]


def kmp_exact(text: str, pattern: str) -> list[Match]:
    """Knuth-Morris-Pratt exact matching in O(n + m)."""

    n, m = len(text), len(pattern)
    if m == 0:
        return [Match(end, 0) for end in range(n + 1)]

    lps = [0] * m
    length = 0
    for i in range(1, m):
        while length and pattern[i] != pattern[length]:
            length = lps[length - 1]
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length

    out: list[Match] = []
    j = 0
    for i, ch in enumerate(text):
        while j and ch != pattern[j]:
            j = lps[j - 1]
        if ch == pattern[j]:
            j += 1
        if j == m:
            out.append(Match(i + 1, 0))
            j = lps[j - 1]
    return out


# ---------------------------------------------------------------------------
# Sellers' semi-global dynamic program
# ---------------------------------------------------------------------------


def sellers_full(text: str, pattern: str, k: int) -> list[Match]:
    """Sellers' search with the complete DP matrix (pedagogical baseline)."""

    if k < 0:
        raise ValueError("k must be non-negative")
    n, m = len(text), len(pattern)
    if m == 0:
        return [Match(end, 0) for end in range(n + 1)]
    if n == 0:
        return []

    d = [[0] * (n + 1) for _ in range(m + 1)]
    # d[0][j] = 0: a match may begin at any text position.
    for i in range(1, m + 1):
        d[i][0] = i
        pi = pattern[i - 1]
        row = d[i]
        prev = d[i - 1]
        for j in range(1, n + 1):
            row[j] = min(
                prev[j] + 1,
                row[j - 1] + 1,
                prev[j - 1] + (pi != text[j - 1]),
            )

    return [
        Match(end, d[m][end])
        for end in range(1, n + 1)
        if d[m][end] <= k
    ]


def sellers_rolling(text: str, pattern: str, k: int) -> list[Match]:
    """Sellers' search with O(m) rolling rows."""

    if k < 0:
        raise ValueError("k must be non-negative")
    n, m = len(text), len(pattern)
    if m == 0:
        return [Match(end, 0) for end in range(n + 1)]
    if n == 0:
        return []

    prev = [0] * (n + 1)  # d[0][j] = 0 for every j
    for i in range(1, m + 1):
        cur = [0] * (n + 1)
        cur[0] = i
        pi = pattern[i - 1]
        for j in range(1, n + 1):
            cur[j] = min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (pi != text[j - 1]),
            )
        prev = cur

    return [
        Match(end, prev[end])
        for end in range(1, n + 1)
        if prev[end] <= k
    ]


def sellers_pruned(text: str, pattern: str, k: int) -> list[Match]:
    """Sellers' search restricted to cells whose value can still be <= k.

    If a DP cell exceeds k, no path through it can return to a value <= k
    because edit costs are non-negative.  The implementation therefore stores
    only active cells; active left neighbours can extend to the next column.
    This is a correctness-preserving threshold pruning.  Its worst case is
    still O(nm), but it can avoid most of the matrix on non-repetitive inputs.
    """

    if k < 0:
        raise ValueError("k must be non-negative")
    n, m = len(text), len(pattern)
    if m == 0:
        return [Match(end, 0) for end in range(n + 1)]
    if n == 0:
        return []
    cap = k + 1

    # Row 0 is active everywhere because D[0][j] = 0.
    prev: dict[int, int] = {j: 0 for j in range(n + 1)}

    import heapq

    for i in range(1, m + 1):
        pi = pattern[i - 1]
        base = sorted(set(prev) | {j + 1 for j in prev if j < n})
        if i <= k:
            base.append(0)
        base = sorted(set(base))

        cur: dict[int, int] = {}
        extras: list[int] = []
        idx = 0
        while idx < len(base) or extras:
            if extras and (idx >= len(base) or extras[0] < base[idx]):
                j = heapq.heappop(extras)
            else:
                j = base[idx]
                idx += 1
            if j in cur:
                continue

            if j == 0:
                value = i
            else:
                up = prev.get(j, cap)
                diag = prev.get(j - 1, cap)
                left = cur.get(j - 1, cap)
                value = min(up + 1, left + 1, diag + (pi != text[j - 1]))
            if value > k:
                continue

            cur[j] = value
            if j < n:
                heapq.heappush(extras, j + 1)

        prev = cur

    return [
        Match(end, prev[end])
        for end in range(1, n + 1)
        if end in prev and prev[end] <= k
    ]


# ---------------------------------------------------------------------------
# Landau-Vishkin diagonal-band search
# ---------------------------------------------------------------------------


def landau_vishkin_search(
    text: str,
    pattern: str,
    k: int,
    lce: SuffixArrayLCE | None = None,
    *,
    use_naive_lce: bool = False,
) -> list[Match]:
    """Exact semi-global search using farthest-reaching diagonal states.

    This is the Landau-Vishkin diagonal-transition idea: one error layer at a
    time, one farthest-reaching state per diagonal, and a longest-common-
    extension jump over the following exact run.  ``use_naive_lce`` is useful
    for tiny tests and for demonstrating the role of the LCE structure.

    Endpoint reporting note: after each exact run, the code also reports
    stopping points at which the remaining pattern characters are deleted.
    That is necessary for a *semi-global* search because every end position,
    not just the farthest one, has to be reported.
    """

    n, m = len(text), len(pattern)
    if k < 0:
        raise ValueError("k must be non-negative")
    if m == 0:
        return [Match(end, 0) for end in range(n + 1)]
    if n == 0:
        return []

    if lce is None and not use_naive_lce:
        lce = SuffixArrayLCE.build(pattern, text)

    def extend(row: int, col: int) -> int:
        if row >= m or col >= n:
            return 0
        if use_naive_lce:
            return naive_lce(pattern, text, row, col)
        assert lce is not None
        return lce.lce(row, col)

    best: dict[int, int] = {}

    def report_run(start_row: int, start_col: int, length: int, edits: int) -> None:
        """Report all valid stopping points inside one greedy exact run.

        Stopping at q matched characters and deleting the remaining pattern
        suffix costs ``edits + (m - (start_row + q))``.
        """

        min_q = max(0, m - start_row - (k - edits))
        for q in range(min_q, length + 1):
            row = start_row + q
            end = start_col + q
            distance = edits + (m - row)
            if end >= 1 and distance <= k:
                old = best.get(end)
                if old is None or distance < old:
                    best[end] = distance

    # Zero-error states: one free start at every text position.
    prev: dict[int, int] = {}
    for start in range(n):
        length = min(extend(0, start), m, n - start)
        diagonal = start  # h = column - row
        prev[diagonal] = length
        report_run(0, start, length, 0)

    for edits in range(1, k + 1):
        candidates: set[int] = set()
        for diagonal in prev:
            candidates.add(diagonal - 1)
            candidates.add(diagonal)
            candidates.add(diagonal + 1)

        cur: dict[int, int] = {}
        for diagonal in candidates:
            if diagonal < -m or diagonal > n:
                continue

            best_row = -1

            # Substitution: stay on the same diagonal.
            row = prev.get(diagonal)
            if row is not None and row < m and row + diagonal < n:
                best_row = row + 1

            # Insertion: consume a text character, diagonal + 1.
            row = prev.get(diagonal - 1)
            if row is not None and row + diagonal - 1 < n:
                if row > best_row:
                    best_row = row

            # Deletion: consume a pattern character, diagonal - 1.
            row = prev.get(diagonal + 1)
            if row is not None and row < m:
                if row + 1 > best_row:
                    best_row = row + 1

            if best_row < 0:
                continue
            col = best_row + diagonal
            if col < 0 or col > n:
                continue

            length = min(extend(best_row, col), m - best_row, n - col)
            cur[diagonal] = best_row + length
            report_run(best_row, col, length, edits)

        prev = cur
        if not prev:
            break

    return normalise(Match(end, distance) for end, distance in best.items())
