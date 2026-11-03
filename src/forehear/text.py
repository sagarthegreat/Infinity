"""Small, dependency-free text helpers shared by policies, validators and retrievers."""

from __future__ import annotations

import re

__all__ = [
    "STOPWORDS",
    "content_words",
    "drop_last",
    "normalize",
    "words",
]

_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

#: A compact English stopword list: function words, question words and the
#: filler words people say to voice agents. Content words are everything else.
STOPWORDS: frozenset[str] = frozenset(
    """
    a about above after again against all am an and any are aren't as at be because been
    before being below between both but by can can't could couldn't did didn't do does
    doesn't doing don't down during each few for from further had hadn't has hasn't have
    haven't having he he'd he'll he's her here here's hers herself him himself his how
    how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most
    mustn't my myself no nor not of off on once only or other ought our ours ourselves out
    over own same shan't she she'd she'll she's should shouldn't so some such than that
    that's the their theirs them themselves then there there's these they they'd they'll
    they're they've this those through to too under until up very was wasn't we we'd
    we'll we're we've were weren't what what's when when's where where's which while who
    who's whom why why's with won't would wouldn't you you'd you'll you're you've your
    yours yourself yourselves um uh uhm hmm er like okay ok well yeah also just tell
    know please many much name named called
    """.split()  # noqa: SIM905
)


def normalize(text: str) -> str:
    """Lower-case, strip punctuation and collapse whitespace.

    >>> normalize("  What's   the capital of France? ")
    "what's the capital of france"
    """
    return " ".join(_WORD_RE.findall(text.lower()))


def words(text: str) -> list[str]:
    """Tokenise into normalised words."""
    return _WORD_RE.findall(text.lower())


def content_words(text: str) -> list[str]:
    """Words that are not stopwords, in order, duplicates preserved."""
    return [w for w in words(text) if w not in STOPWORDS]


def drop_last(text: str, n: int) -> str:
    """Drop the last ``n`` words of ``text`` (after normalisation).

    The trailing words of a streaming ASR hypothesis are the ones most likely
    to be revised, so policies can hold them back before querying.

    >>> drop_last("who founded red bull", 1)
    'who founded red'
    """
    if n <= 0:
        return normalize(text)
    toks = words(text)
    return " ".join(toks[: max(0, len(toks) - n)])
