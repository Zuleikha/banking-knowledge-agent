"""Command-line entry point for the knowledge agent.

::

    python -m app.agent ask "<question>"   # answer one question
    python -m app.agent demo               # the five seed questions, end to end

**By default every run is offline and free**: the embedding model is local, and
the default provider is the in-process mock.

If ``BKA_LLM_PROVIDER`` names a paid vendor, both commands say so before doing
anything, and ``demo`` refuses outright unless ``--paid`` is passed. ``demo``
asks seven questions, so an accidental paid run is seven billed calls rather
than one -- the command that fans out is the one that needs the seatbelt. This
is a deliberate guard, not a formality: nothing else in the repository stands
between an exported key and a bill.

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
from app.llm.factory import is_paid_provider

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

    demo = subparsers.add_parser("demo", help="Answer the seed questions end to end.")
    demo.add_argument(
        "--paid",
        action="store_true",
        help="Allow the demo to run against a paid provider (7 billed calls).",
    )

    args = parser.parse_args(argv)

    # Citations carry em dashes and middots; a cp1252 console would mangle them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    configure_logging()
    settings = get_settings()

    if args.command == "ask":
        return _ask(args.question, settings)
    return _demo(settings, allow_paid=args.paid)


def _warn_if_paid(settings: Settings) -> bool:
    """Print a cost warning when a billed provider is configured.

    Returns:
        Whether the configured provider costs money.
    """
    if not is_paid_provider(settings):
        return False
    print(RULE)
    print(f"!! BKA_LLM_PROVIDER={settings.llm_provider} - this is a PAID API.")
    print("!! Every answered question is a billed call. Unset the variable, or")
    print("!! set BKA_LLM_PROVIDER=mock, to run free.")
    print(RULE)
    return True


def _ask(question: str, settings: Settings) -> int:
    """Answer and print a single question."""
    _warn_if_paid(settings)
    agent = get_agent(settings)
    _print_answer(agent.ask(question))
    return 0


def _demo(settings: Settings, allow_paid: bool = False) -> int:
    """Answer the seed questions and the two control questions."""
    questions = SEED_QUESTIONS + CONTROL_QUESTIONS
    if _warn_if_paid(settings) and not allow_paid:
        # Refused rather than warned: this command asks seven questions, so the
        # cost of getting it wrong is seven calls, and the user cannot take it
        # back once it has run.
        print(
            f"REFUSED: demo would make up to {len(questions)} paid calls. "
            "Re-run with --paid to confirm you accept the cost."
        )
        return 2

    agent = get_agent(settings)
    provider = agent.llm_service.provider

    print(RULE)
    print(f"Provider: {provider.provider_id} / {provider.model_id}")
    print(f"Retriever: {agent.retriever.embedder.model_id}")
    print(RULE)

    for question in questions:
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
