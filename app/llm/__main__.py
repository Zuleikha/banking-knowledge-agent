"""Command-line entry point for the LLM layer.

::

    python -m app.llm prompt "<question>"   # show the exact prompt that is built
    python -m app.llm ask "<question>"      # retrieve, then answer
    python -m app.llm demo                  # the five seed questions, end to end

``prompt`` exists because context injection is the claim this stage makes, and a
claim you cannot see is a claim you cannot check. It prints the complete request:
the frozen system instructions, the fenced passages with their citation numbers,
and the question. What is *not* there -- the other 110 chunks of the knowledge
base -- is the part worth looking at.

Every command runs entirely offline against the mock provider. Nothing here can
make a paid call, because no provider capable of one exists yet.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.llm.factory import get_llm_service
from app.llm.models import GroundedAnswer
from app.llm.prompts import build_request, select_context
from app.llm.service import LLMService
from app.rag.pipeline import get_retriever
from app.rag.retriever import Retriever

DEMO_QUESTIONS: tuple[str, ...] = (
    "Why would an ATM transaction fail after card authentication?",
    "What component handles card authentication?",
    "Which API is used for payment authorisation?",
    "How would I troubleshoot a failed cash withdrawal?",
    "What configuration controls transaction limits?",
    # The sixth is the one that matters most: it must be refused, without a
    # model call, rather than answered from something adjacent.
    "What is the capital of France?",
)
"""The five seed questions from the project brief, plus one the corpus cannot answer."""

RULE = "=" * 78


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Argument list. Defaults to ``sys.argv[1:]``.

    Returns:
        A process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="python -m app.llm",
        description="Inspect prompts and generate answers from retrieved context.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prompt = subparsers.add_parser("prompt", help="Print the prompt that is built.")
    prompt.add_argument("question", help="The question to build a prompt for.")

    ask = subparsers.add_parser("ask", help="Retrieve and answer one question.")
    ask.add_argument("question", help="The question to answer.")

    subparsers.add_parser("demo", help="Answer the seed questions end to end.")

    args = parser.parse_args(argv)

    # Citations carry em dashes and middots; a cp1252 console would mangle them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    configure_logging()
    settings = get_settings()

    if args.command == "prompt":
        return _prompt(args.question, settings)
    if args.command == "ask":
        return _ask(args.question, settings)
    return _demo(settings)


def _prompt(question: str, settings: Settings) -> int:
    """Print the complete request that would be sent for ``question``."""
    retriever = get_retriever()
    retrieval = retriever.retrieve(question)
    selected = select_context(retrieval, settings)

    if not selected:
        print(f"No passage cleared the score floor ({retrieval.min_score}).")
        print("No prompt is built and no provider is called: there is nothing")
        print("to ground an answer in, so the service refuses instead.")
        return 0

    request = build_request(question, selected, settings)
    print(RULE)
    print("SYSTEM")
    print(RULE)
    print(request.system)
    print()
    print(RULE)
    print(f"USER  ({len(selected)} of {len(retrieval.chunks)} retrieved passages)")
    print(RULE)
    print(request.user_text)
    print()
    print(RULE)
    print(f"max_tokens {request.max_tokens}")
    print(f"characters system={len(request.system)} user={len(request.user_text)}")
    return 0


def _ask(question: str, settings: Settings) -> int:
    """Retrieve, answer and print one question."""
    service = get_llm_service(settings)
    retriever = get_retriever()
    _answer_one(service, retriever, question)
    return 0


def _demo(settings: Settings) -> int:
    """Answer every demo question end to end."""
    service = get_llm_service(settings)
    retriever = get_retriever()

    print(RULE)
    print(f"Provider: {service.provider.provider_id} / {service.provider.model_id}")
    print("Deterministic and in-process. No network call, no API key, no cost.")
    print(RULE)

    for question in DEMO_QUESTIONS:
        print()
        _answer_one(service, retriever, question)
    return 0


def _answer_one(service: LLMService, retriever: Retriever, question: str) -> None:
    """Retrieve for one question, answer it, and print the outcome."""
    retrieval = retriever.retrieve(question)
    answer = service.answer(question, retrieval)
    _print_answer(answer)


def _print_answer(answer: GroundedAnswer) -> None:
    """Print an answer with the provenance that makes it checkable."""
    print(f"Q  {answer.question}")
    print(f"A  {answer.text}")

    if answer.refused:
        print("   [refused: no passage cleared the score floor; no model call made]")
        return

    print(
        f"   [grounded: {answer.chunks_used} of {answer.chunks_available} "
        f"passages used · prompt v{answer.prompt_version}]"
    )
    for index, source in enumerate(answer.sources, start=1):
        print(f"   [{index}] {source}")
    if answer.response is not None:
        usage = answer.response.usage
        print(
            f"   [{answer.response.provider_id}/{answer.response.model_id} · "
            f"in≈{usage.input_tokens} out≈{usage.output_tokens} tokens]"
        )


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main())
