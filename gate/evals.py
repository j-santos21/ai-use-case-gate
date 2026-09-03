"""
Statistics behind the acceptance criteria.

An acceptance criterion on a probabilistic system is a claim about a
population, tested on a sample. That means it has a sample size, and the
sample size is not a detail to be settled later by whoever runs the test.
It is part of the requirement, and it has a cost in expert labeling hours
that belongs in the project estimate.

Everything here uses the Wilson score interval on a proportion. It behaves
sensibly at the small sample sizes and high accuracy rates that real
acceptance testing actually runs at, where the textbook normal approximation
produces intervals that extend past 1.0 and quietly mislead people.
"""

import math
from dataclasses import dataclass

# Two-sided z for common confidence levels, used one-sided here for the
# lower bound. Risk-based: higher-consequence use cases get a tighter level,
# which shows up directly as a larger required sample.
Z = {0.90: 1.2816, 0.95: 1.6449, 0.99: 2.3263}

CONFIDENCE_BY_RISK = {
    1: 0.90,
    2: 0.90,
    3: 0.95,
    4: 0.95,
    5: 0.99,
}


def wilson_lower_bound(successes: int, n: int, confidence: float = 0.95) -> float:
    """One-sided lower confidence bound on a proportion."""
    if n == 0:
        return 0.0
    z = Z[confidence]
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, center - margin)


def required_sample_size(
    threshold: float,
    expected: float,
    confidence: float = 0.95,
    cap: int = 20000,
) -> int | None:
    """
    Smallest n such that, if the system performs at `expected`, the lower
    confidence bound on the observed rate clears `threshold`.

    Returns None when the criterion is unprovable at any sample size, which
    happens whenever expected <= threshold. This is the most useful thing the
    function does. A requirement that says "95% accurate" written against a
    system the team expects to hit 95% cannot be demonstrated, ever, because
    half the time the sample will land below the line. The requirement needs
    either a lower threshold or a better system, and that conversation is
    much cheaper before the eval set is built than after.
    """
    if expected <= threshold:
        return None
    for n in range(10, cap + 1):
        successes = round(expected * n)
        if wilson_lower_bound(successes, n, confidence) >= threshold:
            return n
    return None


def labeling_burden(n: int, minutes_per_label: float, reviewers: int = 1) -> dict:
    """Convert a sample size into the thing a project manager can act on."""
    total_minutes = n * minutes_per_label * reviewers
    return {
        "labels": n * reviewers,
        "sme_hours": round(total_minutes / 60, 1),
        "sme_days": round(total_minutes / 60 / 6, 1),  # 6 productive hours
    }


@dataclass
class EvalResult:
    criterion_id: str
    metric: str
    threshold: float
    n: int
    successes: int
    confidence: float
    observed: float
    lower_bound: float
    passed: bool
    verdict: str


def run_criterion(
    criterion_id: str,
    metric: str,
    threshold: float,
    successes: int,
    n: int,
    confidence: float = 0.95,
) -> EvalResult:
    observed = successes / n if n else 0.0
    lb = wilson_lower_bound(successes, n, confidence)
    passed = lb >= threshold

    if passed:
        verdict = (
            f"Pass. Observed {observed:.1%} on n={n}; "
            f"{confidence:.0%} lower bound {lb:.1%} clears the {threshold:.0%} threshold."
        )
    elif observed >= threshold:
        verdict = (
            f"Inconclusive. Observed {observed:.1%} is above the {threshold:.0%} "
            f"threshold, but the {confidence:.0%} lower bound is {lb:.1%}. The sample "
            f"is too small to support the claim. Enlarge the eval set rather than "
            f"reporting the point estimate."
        )
    else:
        verdict = (
            f"Fail. Observed {observed:.1%} on n={n} is below the "
            f"{threshold:.0%} threshold."
        )

    return EvalResult(
        criterion_id, metric, threshold, n, successes,
        confidence, observed, lb, passed, verdict,
    )


def release_decision(results: list[EvalResult]) -> tuple[str, str]:
    """
    One failing criterion blocks release. This is deliberate. The alternative,
    an aggregate score across criteria, lets a strong accuracy number offset a
    failed safety or citation-integrity criterion, which is exactly the trade
    nobody would approve if it were stated out loud.
    """
    failed = [r for r in results if not r.passed and r.observed < r.threshold]
    inconclusive = [r for r in results if not r.passed and r.observed >= r.threshold]

    if failed:
        ids = ", ".join(r.criterion_id for r in failed)
        return "HOLD", f"{len(failed)} criterion/criteria failed on the merits: {ids}."
    if inconclusive:
        ids = ", ".join(r.criterion_id for r in inconclusive)
        return "HOLD", (
            f"No criterion failed on the merits, but {len(inconclusive)} is "
            f"underpowered: {ids}. Extend the eval set and rerun."
        )
    return "RELEASE", "All criteria met with the required confidence."


def monitoring_band(baseline: EvalResult, alert_drop: float = 0.05) -> dict:
    """
    Post-release monitoring thresholds, derived from the release evidence
    rather than picked. The alert line sits at the release lower bound; the
    escalation line at a fixed drop below it. Sampling frequency scales with
    how tight the release evidence was.
    """
    return {
        "criterion": baseline.criterion_id,
        "alert_below": round(baseline.lower_bound, 4),
        "escalate_below": round(max(0.0, baseline.lower_bound - alert_drop), 4),
        "monthly_sample": max(50, baseline.n // 4),
        "action_on_alert": "Sample 2x, notify process owner, no change control yet.",
        "action_on_escalation": (
            "Suspend automated path, revert to human step, open a deviation "
            "and a change control for retraining or prompt revision."
        ),
    }
