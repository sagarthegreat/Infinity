"""forehear: look-ahead retrieval for voice agents.

Start retrieval while the user is still talking, cancel the guesses that turn
out wrong, and have context ready the moment they stop.
"""

from .controller import Cancel, Controller, ControllerStats, Deliver, Start
from .events import EventKind, TranscriptEvent
from .policies import Adaptive, EagerEndOfTurn, FinalOnly, FixedInterval, Policy, StablePrefix, TurnView
from .retrievers import BM25Index, DenseIndex, with_latency
from .runtime import Lookahead, Retriever
from .types import Delivery, Doc, SpecStatus, Speculation, TurnOutcome
from .validators import ExactMatch, ResultOverlap, TokenCoverage, Validator

__version__ = "0.1.0"

__all__ = [
    "Adaptive",
    "BM25Index",
    "Cancel",
    "Controller",
    "ControllerStats",
    "Deliver",
    "DenseIndex",
    "Delivery",
    "Doc",
    "EagerEndOfTurn",
    "EventKind",
    "ExactMatch",
    "FinalOnly",
    "FixedInterval",
    "Lookahead",
    "Policy",
    "ResultOverlap",
    "Retriever",
    "SpecStatus",
    "Speculation",
    "StablePrefix",
    "Start",
    "TokenCoverage",
    "TranscriptEvent",
    "TurnOutcome",
    "TurnView",
    "Validator",
    "__version__",
    "with_latency",
]
