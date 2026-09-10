"""Command-line entry point for the knowledge agent.

::

    python -m app.agent ask "<question>"   # answer one question
    python -m app.agent demo               # the five seed questions, end to end

Every run is offline and free: the embedding model is local, and the default
provider is the in-process mock. ``python -m app.agent demo`` prints the provider
it is using, so a run against a real adapter is never mistaken for a mock run.

What the output is designed to show is the *provenance*, not the prose. The mock
provider's answer text is a wiring check, not a generated answer — the parts
worth reading are which route was taken, how many passages were considered, how
many reached the prompt, and which documents they came from.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from app.agent.factory import get_agent
from app.agent.models import AgentAnswer
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging

SEED_QUESTIONS: tuple[str, ...] = (
    "Why would an ATM transaction fail after card authentication?",
    "What component handles card authentication?",
    "Which API is used for payment authorisation?",
    "How would I troubleshoot a failed cash withdrawal?",
    "What configuration controls transaction limits?",
)
"""The five worked examples from ``prompt.md`` §13."""

CONTROL_QUESTIONS: tuple[str, ...] = (
    # Answerable-looking, and outside the corpus: it must be refused after a
    # search rather than answered from something adjacent.
    "What is the capital of France?",
    # Nothing to search for at all: refused without a search and without a model
    # call, by the routing policy rather than by the score floor.
    "!!! ???",
)
"""Two questions the agent must decline, for two different reasons."""

RULE = "=" * 78


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Argument list. Defaults to ``sys.argv[1:]``.

    Returns:
        A process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="python -m app.agent",
        description="Ask the knowledge agent a technical question.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser("ask", help="Answer one question.")
    ask.add_argument("question", help="The question to answer.")

    subparsers.add_parser("demo", help="Answer the seed questions end to end.")

    args = parser.parse_args(argv)

    # Citations carry em dashes and middots; a cp1252 console would mangle them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    configure_logging()
    settings = get_settings()

    if args.command == "ask":
        return _ask(args.question, settings)
    return _demo(settings)


def _ask(question: str, settings: Settings) -> int:
    """Answer and print a single question."""
    agent = get_agent(settings)
    _print_answer(agent.ask(question))
    return 0


def _demo(settings: Settings) -> int:
    """Answer the seed questions and the two control questions."""
    agent = get_agent(settings)
    provider = agent.llm_service.provider

    print(RULE)
    print(f"Provider: {provider.provider_id} / {provider.model_id}")
    print(f"Retriever: {agent.retriever.embedder.model_id}")
    print(RULE)

    for question in SEED_QUESTIONS + CONTROL_QUESTIONS:
        print()
        _print_answer(agent.ask(question))
    return 0


def _print_answer(answer: AgentAnswer) -> None:
    """Print one answer with the execution record that makes it checkable."""
    print(f"Q  {answer.question}")
    print(f"A  {answer.text}")
    print(f"   [decision: {answer.decision.reason} — {answer.decision.explanation}]")

    retrieval = answer.retrieval
    if retrieval.performed:
        top = "none" if retrieval.top_score is None else f"{retrieval.top_score:.3f}"
        print(
            f"   [retrieval: {retrieval.chunks_returned} of "
            f"{retrieval.candidates_considered} passages cleared "
            f"{retrieval.min_score} · top score {top}]"
        )
    else:
        print("   [retrieval: not performed]")

    if answer.refused:
        print("   [refused: no supporting evidence; no model call was made]")
        return

    print(
        f"   [grounded: {answer.chunks_used} passage(s) in the prompt · "
        f"prompt v{answer.prompt_version}]"
    )
    for index, source in enumerate(answer.sources, start=1):
        print(f"   [{index}] {source}")


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main())
