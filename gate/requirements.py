"""
Stage 2: turn business requirements into acceptance criteria.

Requirements arrive from stakeholders in the register they were written in,
which for AI features is almost always adjectival. "The system shall return
relevant documents." "The summary shall be accurate." Those sentences are
fine as statements of intent and useless as acceptance criteria, because no
observation could ever falsify them, which means no test can fail, which
means the release decision has nothing to stand on.

This module sorts requirements into three buckets and refuses to let the
third one through silently.

  DETERMINISTIC  conventional pass/fail. Logging, retention, access control,
                 field formats, latency ceilings. Test once, done.
  STATISTICAL    a claim about a rate. Needs a metric, a threshold, a labeled
                 set, and a sample size computed from the threshold.
  UNTESTABLE     an adjective with no measurement behind it. Goes back to the
                 stakeholder with a proposed rewrite attached.

The classifier is rule-based on purpose. A model could do this, but then the
analyst could not explain to an auditor why a given requirement was routed
the way it was, and the routing is the part that carries consequences.
"""

import re
from dataclasses import dataclass, field

# Adjectives that read as requirements and behave as opinions.
UNMEASURED_PREDICATES = {
    "accurate", "relevant", "appropriate", "correct", "high quality",
    "high-quality", "user friendly", "user-friendly", "intuitive", "seamless",
    "robust", "reasonable", "comprehensive", "meaningful", "sufficient",
    "adequate", "effective", "efficient", "as needed", "where applicable",
    "best effort", "state of the art", "state-of-the-art", "reliable",
    "consistent", "clear", "concise", "helpful", "useful", "readable",
}

# Verbs whose object is an event the system either did or did not do.
DETERMINISTIC_VERBS = {
    "log", "logs", "record", "records", "retain", "retains", "reject",
    "rejects", "require", "requires", "restrict", "restricts", "encrypt",
    "encrypts", "timestamp", "timestamps", "version", "versions", "expose",
    "exposes", "return within", "respond within", "prevent", "prevents",
    "capture", "captures", "display", "displays", "store", "stores",
}

METRIC_VOCAB = {
    "accuracy": "proportion of outputs judged correct by SME adjudication",
    "precision": "proportion of returned items that are relevant",
    "recall": "proportion of relevant items that were returned",
    "citation integrity": "proportion of cited sources that exist and support the claim",
    "extraction accuracy": "proportion of extracted fields matching the source document",
    "refusal rate": "proportion of out-of-scope prompts correctly declined",
    "hallucination rate": "proportion of outputs containing an unsupported factual claim",
    "classification accuracy": "proportion of items assigned the correct label",
}

QUANT = re.compile(r"(\d+(?:\.\d+)?)\s*%|\bwithin\s+(\d+)\s*(second|minute|hour|day)")


@dataclass
class Requirement:
    id: str
    use_case_id: str
    text: str
    source: str
    metric: str | None = None
    threshold: float | None = None
    expected: float | None = None
    minutes_per_label: float = 3.0


@dataclass
class Classified:
    req: Requirement
    kind: str
    reason: str
    proposed_rewrite: str = ""
    acceptance: dict = field(default_factory=dict)


def _found_predicates(text: str) -> list[str]:
    low = text.lower()
    return sorted(p for p in UNMEASURED_PREDICATES if re.search(rf"\b{re.escape(p)}\b", low))


def _is_deterministic(text: str) -> bool:
    low = text.lower()
    return any(re.search(rf"\b{re.escape(v)}\b", low) for v in DETERMINISTIC_VERBS)


def classify(req: Requirement) -> Classified:
    predicates = _found_predicates(req.text)
    quantified = bool(QUANT.search(req.text))
    deterministic = _is_deterministic(req.text)

    # Analyst override runs first, before any grammar rule.
    #
    # This ordering exists because of a failure the classifier makes on its
    # own. It routes by sentence structure, and sentence structure can hide a
    # rate claim inside a deterministic-sounding verb. "The system shall
    # reject documents that are not executed agreements" parses as an
    # observable behavior, so the rules would call it deterministic and send
    # it to a scripted test. But whether a document is an executed agreement
    # is a judgment the system will sometimes get wrong, and a scripted test
    # with two cases would never find out. An analyst who attaches a metric
    # has made that call deliberately, and the rules do not get to overrule it.
    if req.metric is not None:
        if req.metric not in METRIC_VOCAB:
            raise ValueError(f"{req.id}: unknown metric '{req.metric}'")
        if req.threshold is None or req.expected is None:
            raise ValueError(f"{req.id}: metric set without threshold and expected")
        note = ""
        if deterministic and not predicates:
            note = (
                " Grammar alone would have routed this to a scripted functional "
                "test; the metric was attached by analyst override."
            )
        return Classified(
            req, "STATISTICAL",
            f"Claim about a rate. Measured as {req.metric}: "
            f"{METRIC_VOCAB[req.metric]}.{note}",
            acceptance={
                "metric": req.metric,
                "definition": METRIC_VOCAB[req.metric],
                "threshold": req.threshold,
                "expected": req.expected,
            },
        )

    # A deterministic requirement with no adjectives is ordinary CSV work.
    if deterministic and not predicates:
        return Classified(
            req, "DETERMINISTIC",
            "States an observable system behavior with no rate claim. "
            "Testable with a conventional scripted case.",
            acceptance={
                "test_type": "scripted functional test",
                "sample": "1 positive and 1 negative case per branch",
                "evidence": "test script, screenshot or log extract, reviewer signature",
            },
        )

    # Has an unmeasured adjective and no metric attached: cannot be accepted.
    if predicates and req.metric is None:
        rewrite = _propose_rewrite(req, predicates)
        return Classified(
            req, "UNTESTABLE",
            f"Rests on unmeasured predicate(s): {', '.join(predicates)}. "
            f"No observation could falsify this as written, so no test of it "
            f"can fail and it cannot support a release decision.",
            proposed_rewrite=rewrite,
        )

    if quantified:
        return Classified(
            req, "DETERMINISTIC",
            "Quantified constraint with a single observable value. Testable "
            "with a scripted case.",
            acceptance={
                "test_type": "scripted functional test",
                "sample": "measured across 30 consecutive transactions",
                "evidence": "instrumented log extract",
            },
        )

    return Classified(
        req, "UNTESTABLE",
        "No measurable predicate and no observable system behavior. Reads as "
        "a statement of intent rather than a requirement.",
        proposed_rewrite=_propose_rewrite(req, predicates),
    )


def _propose_rewrite(req: Requirement, predicates: list[str]) -> str:
    """
    The rewrite is a template, not a finished sentence. The analyst fills the
    blanks with the stakeholder in the room; that conversation is the point.
    Handing back a rewrite the stakeholder did not choose is how requirements
    end up measuring something nobody wanted.
    """
    hint = predicates[0] if predicates else "the stated quality"
    return (
        f"On a held-out set of [N] cases labeled by [role], the system shall "
        f"achieve [metric] of at least [X]%, where [metric] is defined as "
        f"[operational definition of '{hint}']. Cases are drawn from [sampling "
        f"frame] and adjudicated by [number] reviewers with disagreements "
        f"resolved by [tiebreak]."
    )
