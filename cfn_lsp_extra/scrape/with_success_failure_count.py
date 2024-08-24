"""
Utilities from tracking total failures/successes over the lifespan of some process.

This would be so nice with a writer monad.
"""
from typing import Generic, Tuple, TypeVar

from attrs import frozen

E = TypeVar("E")
E2 = TypeVar("E2")


@frozen
class WithSuccessFailureCount(Generic[E]):
    """Wraps an object along with a success/failure count.

    Attributes
    ----------
    value : E
        The wrapped value
    successes : int
        The number of successes.
    failures : int
        The number of failures."""

    value: E
    successes: int
    failures: int

    @classmethod
    def zero(cls, e: E) -> "WithSuccessFailureCount[E]":
        return WithSuccessFailureCount(e, 0, 0)

    @classmethod
    def success(cls, e: E) -> "WithSuccessFailureCount[E]":
        return WithSuccessFailureCount(e, 1, 0)

    @classmethod
    def failure(cls, e: E) -> "WithSuccessFailureCount[E]":
        return WithSuccessFailureCount(e, 0, 1)

    def add_counts(
        self, other: "WithSuccessFailureCount[E2]"
    ) -> "WithSuccessFailureCount[E]":
        return WithSuccessFailureCount(
            self.value,
            self.successes + other.successes,
            self.failures + other.failures,
        )

    def to_tuple(self) -> Tuple[E, int, int]:
        return (self.value, self.successes, self.failures)
