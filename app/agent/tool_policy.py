"""Deciding which MCP tools, if any, a question calls for.

Kept in its own module rather than folded into :mod:`app.agent.policy`, because
the two answer genuinely different questions and will diverge sharply in Stage 7:
the retrieval decision stays a single rule, while tool selection becomes the
stage's whole subject.

**The rule: route on identifiers, not on topics.** A tool is selected when the
question contains something that tool can actually act on — an error code, a
transaction reference, a configuration key, a component name. Nothing else
selects a tool.

This is a deliberately different kind of rule from the keyword classifier Stage 5
rejected for retrieval, and the difference is what makes it defensible:

* A *topic* keyword is a guess about meaning. ``"payment"`` in *"what is a
  payment in cricket?"* looks exactly like ``"payment"`` in a real question, and
  a list of banking words is a guess about the corpus wearing the costume of a
  decision.
* An *identifier* is a fact about form. ``LIM-4001`` matches ``PREFIX-NNNN``, a
  shape the platform defines and the error-code reference documents. A string of
  that shape in a question is not evidence about what the user meant; it is the
  argument a tool needs, sitting in plain sight.

And the tools force the issue: ``look_up_error_code`` cannot be called without an
error code. Argument availability, not intent, is what makes a tool callable at
all — so extraction and selection are the same act, and a rule that pretended
otherwise would select tools it then could not call.

**Why no LLM router here.** Stage 5 argued that paying a model call to choose
between one option and itself was not worth it. That argument is weaker now —
there are real options — but the honest position is that this rule is
deterministic, free, offline and testable, and Stage 7 is explicitly the stage
that weighs a model-driven selector against it. Building the LLM router here
would spend Stage 7's design decision early, and quietly make the whole tool
layer untestable without a provider.

**False positives are cheap; false negatives are not.** Calling a tool that finds
nothing costs an in-process dictionary lookup and gives the model a true
statement — *no transaction has that reference*. Failing to call a tool that
would have found something produces an answer from documentation alone that reads
as authoritative and may be stale. The thresholds below lean accordingly.
"""

from __future__ import annotations

import re

from app.core.tracing import traced
from app.mcp.models import ToolInvocation

ERROR_CODE_PATTERN = re.compile(r"\b([A-Z]{3})-(\d{4})\b")
"""The documented platform error-code form, ``PREFIX-NNNN``.

Uppercase only, and that is intentional. A question mentioning ``lim-4001`` in
lower case is rare, whereas matching case-insensitively would fire on ordinary
prose that happens to contain three letters, a hyphen and four digits. The tool
itself accepts either case; this pattern decides only whether to call it.
"""

TRANSACTION_REFERENCE_PATTERN = re.compile(r"\bTXN-\d{8}-\d{6}\b", re.IGNORECASE)
"""The documented transaction reference form, ``TXN-YYYYMMDD-NNNNNN``."""

CONFIGURATION_KEY_PATTERN = re.compile(
    r"\b([a-z][a-z_]*(?:\.[a-z][a-z_]*){1,3})\b"
)
"""A dotted lower-case configuration key, e.g. ``limits.atm.per_transaction_amount``.

Requires at least one dot and allows at most three, which is the shape every key
in the configuration reference takes. The bound matters: without an upper limit
this pattern would happily match a sentence written without spaces after its full
stops.
"""

COMPONENT_NAMES: tuple[str, ...] = (
    "TransactionSwitch",
    "AuthorizationService",
    "CardSecurityModule",
    "LimitService",
    "CoreBankingAdapter",
    "PaymentEngine",
    "DigitalGateway",
    "DeviceManager",
    "ConfigurationStore",
)
"""The nine documented runtime components.

Matched case-insensitively as whole words. Listed here rather than imported from
a tool because this module decides *whether* to call a tool and must not depend
on any particular tool's internals — the same separation that let the six tools
be built independently. ``tests/test_mcp_agent.py`` asserts this list agrees with
what the tools actually accept.
"""

_COMPONENT_PATTERN = re.compile(
    r"\b(" + "|".join(COMPONENT_NAMES) + r")\b", re.IGNORECASE
)

_CANONICAL_COMPONENTS = {name.casefold(): name for name in COMPONENT_NAMES}

_HEALTH_WORDS = re.compile(
    r"\b(health|healthy|unhealthy|up|down|degraded|outage|responding|"
    r"probe|liveness|readiness)\b",
    re.IGNORECASE,
)

_VERSION_WORDS = re.compile(
    r"\b(version|versions|release|build|patch|upgraded|running)\b", re.IGNORECASE
)

MAX_TOOL_CALLS = 4
"""Ceiling on tool calls for a single question.

A question naming four components and three error codes would otherwise fan out
into a dozen calls, and the prompt would arrive at the model as a wall of tool
output with the actual question buried at the bottom. The calls are cheap; the
model's attention is not. Deterministic ordering plus a hard ceiling keeps the
prompt bounded and reproducible.
"""


def _first_component(question: str) -> str | None:
    """Return the canonical name of the first component mentioned, if any."""
    match = _COMPONENT_PATTERN.search(question)
    if match is None:
        return None
    return _CANONICAL_COMPONENTS[match.group(1).casefold()]


@traced
def select_tools(question: str) -> tuple[ToolInvocation, ...]:
    """Choose the tool calls ``question`` warrants, with their arguments.

    Selection and argument extraction happen together because they are the same
    act: a tool is callable exactly when the question contains the identifier it
    needs.

    Args:
        question: The user's question, in natural language.

    Returns:
        The invocations to make, in a deterministic order, capped at
        :data:`MAX_TOOL_CALLS`. Empty when the question names nothing a tool can
        act on — which is the common case, and not a failure.
    """
    invocations: list[ToolInvocation] = []
    seen: set[tuple[str, tuple[tuple[str, str], ...]]] = set()

    def add(tool: str, arguments: dict[str, str], reason: str) -> None:
        """Append an invocation unless the identical call is already queued."""
        key = (tool, tuple(sorted(arguments.items())))
        if key in seen:
            return
        seen.add(key)
        invocations.append(
            ToolInvocation(
                tool=tool,  # type: ignore[arg-type]
                arguments=arguments,
                reason=reason,
            )
        )

    for match in ERROR_CODE_PATTERN.finditer(question):
        code = match.group(0)
        add(
            "look_up_error_code",
            {"error_code": code},
            f"The question names the error code {code}.",
        )

    for match in TRANSACTION_REFERENCE_PATTERN.finditer(question):
        reference = match.group(0).upper()
        add(
            "check_transaction_status",
            {"transaction_reference": reference},
            f"The question names the transaction reference {reference}.",
        )

    component = _first_component(question)

    for match in CONFIGURATION_KEY_PATTERN.finditer(question):
        key = match.group(1)
        # A configuration key is only actionable with a component to scope it
        # to, and the tool requires both. Without one named, the question is
        # about what the key means -- which the documentation answers -- rather
        # than what it is currently set to.
        if component is None:
            continue
        add(
            "get_system_configuration",
            {"component": component, "key": key},
            f"The question names the configuration key {key}.",
        )

    if component is not None:
        if _HEALTH_WORDS.search(question):
            add(
                "check_service_health",
                {"component": component},
                f"The question asks about the health of {component}.",
            )
            add(
                "get_component_status",
                {"component": component},
                f"The question asks about the operational state of {component}.",
            )
        if _VERSION_WORDS.search(question):
            add(
                "retrieve_system_version",
                {"component": component},
                f"The question asks about the version of {component}.",
            )

    return tuple(invocations[:MAX_TOOL_CALLS])
