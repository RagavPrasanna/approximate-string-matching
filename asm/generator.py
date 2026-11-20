"""Controlled data generation for correctness tests and benchmarks."""

from __future__ import annotations

import random
from dataclasses import dataclass

ALPHABETS = {
    "binary": "01",
    "dna": "ACGT",
    "english": "etaoinshrdlucmfwypvbgkjqxz",
}

ENGLISH_WORDS = (
    "approximate string matching dynamic programming pattern text edit "
    "distance insertion deletion substitution algorithm sequence search "
    "correctness complexity experiment threshold mutation repetitive data "
    "window matrix diagonal benchmark performance memory analysis"
).split()


def random_string(n: int, alphabet: str, rng: random.Random) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


def random_pattern(m: int, alphabet: str, rng: random.Random) -> str:
    return random_string(m, alphabet, rng)


def mutate_once(
    value: str,
    alphabet: str,
    rng: random.Random,
    edit_type: str | None = None,
) -> str:
    """Apply one edit, returning a string that differs by one operation."""

    chars = list(value)
    choices = ["substitution", "insertion", "deletion"]
    if edit_type is None:
        edit_type = rng.choice(choices)

    if edit_type == "substitution":
        if not chars:
            return rng.choice(alphabet)
        pos = rng.randrange(len(chars))
        old = chars[pos]
        replacement = rng.choice(alphabet)
        while replacement == old and len(alphabet) > 1:
            replacement = rng.choice(alphabet)
        chars[pos] = replacement
    elif edit_type == "insertion":
        pos = rng.randrange(len(chars) + 1)
        chars.insert(pos, rng.choice(alphabet))
    elif edit_type == "deletion":
        if chars:
            del chars[rng.randrange(len(chars))]
    else:
        raise ValueError(f"unknown edit type: {edit_type}")
    return "".join(chars)


def mutate(
    pattern: str,
    edits: int,
    alphabet: str,
    rng: random.Random,
    mix: str = "mixed",
) -> str:
    """Apply ``edits`` operations, cycling through requested edit types."""

    value = pattern
    for i in range(edits):
        if mix == "mixed":
            edit_type = ("substitution", "insertion", "deletion")[i % 3]
        elif mix in ("substitution", "insertion", "deletion"):
            edit_type = mix
        else:
            edit_type = None
        value = mutate_once(value, alphabet, rng, edit_type)
    return value


@dataclass(frozen=True)
class Planted:
    start: int
    end: int
    requested_edits: int


@dataclass(frozen=True)
class Dataset:
    name: str
    text: str
    pattern: str
    k: int
    alphabet: str
    planted: tuple[Planted, ...] = ()


def planted_dataset(
    n: int,
    m: int,
    k: int,
    alphabet_name: str = "dna",
    seed: int = 0,
    copies: int | None = None,
    mix: str = "mixed",
) -> Dataset:
    """Background text with mutated copies of a random pattern inserted."""

    rng = random.Random(seed)
    alphabet = ALPHABETS[alphabet_name]
    pattern = random_pattern(m, alphabet, rng)
    text = list(random_string(n, alphabet, rng))

    if copies is None:
        copies = max(1, n // max(1, 3 * max(m, 1)))
    planted: list[Planted] = []

    if m == 0:
        return Dataset(
            name=f"planted-{alphabet_name}-n{n}-m{m}-k{k}",
            text="".join(text),
            pattern=pattern,
            k=k,
            alphabet=alphabet_name,
        )

    for copy_index in range(copies):
        edits = rng.randint(0, k)
        copy = mutate(pattern, edits, alphabet, rng, mix)
        if len(copy) > n:
            continue
        # Spread copies over the text.  Copied spans are kept disjoint so the
        # planted record remains a valid witness even when a caller asks for
        # many copies on a small text.
        base = (copy_index * n) // max(1, copies)
        slack = max(0, n - len(copy))
        pos = min(slack, base + rng.randint(0, max(0, n // max(1, 4 * copies))))
        end = pos + len(copy)
        if any(not (end <= old.start or pos >= old.end) for old in planted):
            continue
        text[pos:end] = list(copy)
        planted.append(Planted(pos, end, edits))

    return Dataset(
        name=f"planted-{alphabet_name}-n{n}-m{m}-k{k}",
        text="".join(text),
        pattern=pattern,
        k=k,
        alphabet=alphabet_name,
        planted=tuple(planted),
    )


def random_dataset(
    n: int,
    m: int,
    k: int,
    alphabet_name: str = "dna",
    seed: int = 0,
) -> Dataset:
    rng = random.Random(seed)
    alphabet = ALPHABETS[alphabet_name]
    return Dataset(
        name=f"random-{alphabet_name}-n{n}-m{m}-k{k}",
        text=random_string(n, alphabet, rng),
        pattern=random_pattern(m, alphabet, rng),
        k=k,
        alphabet=alphabet_name,
    )


def repetitive_dataset(n: int, m: int, k: int, char: str = "A") -> Dataset:
    if not char:
        raise ValueError("char must be non-empty")
    text = (char * (n // len(char) + 1))[:n]
    pattern = (char * (m // len(char) + 1))[:m]
    return Dataset(
        name=f"repetitive-n{n}-m{m}-k{k}",
        text=text,
        pattern=pattern,
        k=k,
        alphabet="repetitive",
    )


def prefix_trap_dataset(n: int, m: int, k: int, seed: int = 0) -> Dataset:
    """Text made from a shared prefix, producing many candidate alignments."""

    rng = random.Random(seed)
    alphabet = ALPHABETS["dna"]
    pattern = random_pattern(m, alphabet, rng)
    half = max(1, m // 2)
    unit = pattern[:half]
    text = (unit * ((n // len(unit)) + 2))[:n]
    if k >= 2 and n > 2:
        chars = list(text)
        for _ in range(max(1, n // 100)):
            chars[rng.randrange(n)] = rng.choice(alphabet)
        text = "".join(chars)
    return Dataset(
        name=f"prefix-trap-n{n}-m{m}-k{k}",
        text=text,
        pattern=pattern,
        k=k,
        alphabet="dna",
    )


def english_dataset(
    n: int,
    m: int,
    k: int,
    seed: int = 0,
) -> Dataset:
    """Natural-language-like text assembled from a public-domain word list."""

    rng = random.Random(seed)
    words: list[str] = []
    length = 0
    while length < n:
        word = rng.choice(ENGLISH_WORDS)
        words.append(word)
        length += len(word) + 1
    text = " ".join(words)[:n]
    start = rng.randrange(max(1, len(text) - m + 1)) if m <= len(text) else 0
    pattern = text[start : start + m]
    if k and pattern:
        pattern = mutate(
            pattern,
            min(k, max(1, len(pattern) // 5)),
            "etaoinshrdlucmfwypvbgkjqxz",
            rng,
        )
        # Keep the experimental pattern length exactly m.  Mixed mutations may
        # change the length; trimming or padding does not affect the purpose of
        # this natural-language-like benchmark, which is to measure algorithms
        # on realistic character distributions and overlaps.
        if len(pattern) > m:
            pattern = pattern[:m]
        elif len(pattern) < m:
            pattern += random_string(m - len(pattern), "etaoinshrdlucmfwypvbgkjqxz", rng)
    return Dataset(
        name=f"english-n{n}-m{m}-k{k}",
        text=text,
        pattern=pattern,
        k=k,
        alphabet="english",
    )
