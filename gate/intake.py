"""
Stage 1: use-case intake scoring.

The question this stage answers is not "can we build it." Assume we can; the
model is a vendor API call and the plumbing is a solved problem. The question
is whether we can afford to prove it works to the standard this use case's
risk profile demands, and whether the value on the other side justifies that.

Two composite axes come out of six scored factors:

  VALUE          how much the organization gets if the thing works
  EVIDENCE COST  how much work it takes to demonstrate that it does

Disposition falls out of the pair. Nothing here is a judgment about model
quality. It is a judgment about verifiability.
"""

from dataclasses import dataclass, field
from typing import Literal

Disposition = Literal["BUILD", "PILOT", "REFRAME", "DECLINE"]


# ---------------------------------------------------------------------------
# Factor definitions
# ---------------------------------------------------------------------------
# Each factor is scored 1-5 by the analyst during intake, against an anchored
# rubric. Anchors matter more than weights: two analysts scoring the same use
# case should land within a point of each other, or the model is decoration.

VALUE_FACTORS = {
    "volume": {
        "weight": 0.35,
        "prompt": "How often is this task performed today?",
        "anchors": {
            1: "Ad hoc, a few times a year",
            2: "Monthly, single team",
            3: "Weekly across a function",
            4: "Daily across a function",
            5: "Continuous, multiple functions, currently a staffing constraint",
        },
    },
    "time_displaced": {
        "weight": 0.35,
        "prompt": "How much qualified human time does one instance consume?",
        "anchors": {
            1: "Under 5 minutes",
            2: "15 to 30 minutes",
            3: "1 to 2 hours",
            4: "Most of a day",
            5: "Multiple days of specialist time",
        },
    },
    "strategic_pull": {
        "weight": 0.30,
        "prompt": "Who is asking, and what does it unblock?",
        "anchors": {
            1: "Nobody asked; technology-led idea",
            2: "One team's convenience request",
            3: "Named business owner with a budget line",
            4: "Blocks a committed program milestone",
            5: "Named in functional strategy with executive sponsorship",
        },
    },
}

EVIDENCE_FACTORS = {
    "consequence_of_error": {
        "weight": 0.30,
        "prompt": "What happens downstream when the output is wrong and nobody catches it?",
        "anchors": {
            1: "Internal inconvenience, self-correcting",
            2: "Rework by the requesting team",
            3: "Decision made on bad information, recoverable",
            4: "Feeds a controlled document or a GxP record",
            5: "Reaches a regulatory submission or a patient-safety pathway",
        },
    },
    "ground_truth": {
        "weight": 0.25,
        "prompt": "Can we assemble a labeled set that a subject matter expert will sign off as correct?",
        "anchors": {
            1: "Yes, labels already exist in a system of record",
            2: "Yes, SME can label a few hundred cases in under a week",
            3: "Labeling requires scarce SME time, weeks of effort",
            4: "Experts disagree with each other on the right answer",
            5: "No defensible ground truth exists; the task is genuinely open-ended",
        },
    },
    "verifiability": {
        "weight": 0.25,
        "prompt": "Can the person receiving the output check it faster than doing the task themselves?",
        "anchors": {
            1: "Trivially, the output cites its source and the check is a glance",
            2: "Yes, with a defined review step",
            3: "Only by spot-checking a sample",
            4: "Checking costs nearly as much as doing the work",
            5: "Not checkable in practice; errors are invisible until they surface elsewhere",
        },
    },
    "regulatory_scope": {
        "weight": 0.20,
        "prompt": "What validation regime does this fall under?",
        "anchors": {
            1: "No GxP scope, productivity tool",
            2: "GxP-adjacent, output is an input to a validated process",
            3: "GxP scope, low-risk category",
            4: "GxP scope, high-risk category, ALCOA+ applies to training data",
            5: "GxP high risk plus intended-use claims requiring documented SME review",
        },
    },
}


@dataclass
class UseCase:
    id: str
    title: str
    function: str
    sponsor: str
    scores: dict = field(default_factory=dict)
    note: str = ""

    def validate(self) -> None:
        expected = set(VALUE_FACTORS) | set(EVIDENCE_FACTORS)
        missing = expected - set(self.scores)
        extra = set(self.scores) - expected
        if missing:
            raise ValueError(f"{self.id}: missing factor scores {sorted(missing)}")
        if extra:
            raise ValueError(f"{self.id}: unrecognized factors {sorted(extra)}")
        for k, v in self.scores.items():
            if v not in (1, 2, 3, 4, 5):
                raise ValueError(f"{self.id}: {k} scored {v}, must be 1-5")


def _weighted(scores: dict, factors: dict) -> float:
    """Weighted mean on the 1-5 scale, rescaled to 0-100."""
    raw = sum(scores[name] * spec["weight"] for name, spec in factors.items())
    return round((raw - 1) / 4 * 100, 1)


@dataclass
class IntakeResult:
    use_case: UseCase
    value: float
    evidence_cost: float
    disposition: Disposition
    rationale: str
    binding_constraint: str

    def row(self) -> dict:
        return {
            "id": self.use_case.id,
            "title": self.use_case.title,
            "function": self.use_case.function,
            "value": self.value,
            "evidence_cost": self.evidence_cost,
            "disposition": self.disposition,
            "binding_constraint": self.binding_constraint,
        }


def _binding_constraint(uc: UseCase) -> str:
    """The single highest-scoring evidence factor, weighted. This is the thing
    to fix if the use case is to move, and it is what the intake conversation
    should actually be about."""
    # Measured as weight * (score - 1), the amount each factor adds above its
    # floor. Using the raw weighted score instead would just name whichever
    # factor carries the heaviest weight, in every use case, which tells the
    # reader nothing they could not have read off the rubric.
    contributions = {
        name: spec["weight"] * (uc.scores[name] - 1)
        for name, spec in EVIDENCE_FACTORS.items()
    }
    worst = max(contributions, key=contributions.get)
    return f"{worst} ({uc.scores[worst]}/5)"


def score(uc: UseCase) -> IntakeResult:
    uc.validate()
    value = _weighted(uc.scores, VALUE_FACTORS)
    cost = _weighted(uc.scores, EVIDENCE_FACTORS)

    # Hard gate, applied before the value/cost tradeoff. A use case with no
    # defensible ground truth and no practical human check is not a use case
    # with a high evidence cost; it is a use case that cannot be accepted,
    # because there is no test that would ever fail. Value does not rescue it.
    if uc.scores["ground_truth"] >= 4 and uc.scores["verifiability"] >= 4:
        return IntakeResult(
            uc, value, cost, "REFRAME",
            "No defensible ground truth and no practical human check. "
            "There is no acceptance criterion that could fail, so there is no "
            "release decision to make. Narrow the scope to a slice that has a "
            "checkable answer, or accept it as an unvalidated assistive tool "
            "with no process dependency.",
            _binding_constraint(uc),
        )

    # Second hard gate: consequence and verifiability together. High blast
    # radius plus an output nobody can check is a control problem, not a
    # scoring problem.
    if uc.scores["consequence_of_error"] >= 4 and uc.scores["verifiability"] >= 4:
        return IntakeResult(
            uc, value, cost, "REFRAME",
            "Errors reach a controlled record and are not practically "
            "checkable at the point of use. Insert a review step that makes "
            "the output verifiable, or move the AI upstream of the controlled "
            "record rather than into it.",
            _binding_constraint(uc),
        )

    margin = value - cost

    if margin >= 20:
        return IntakeResult(
            uc, value, cost, "BUILD",
            "Value clears the cost of proving it works with room to spare. "
            "Proceed to requirements and eval design.",
            _binding_constraint(uc),
        )
    if margin >= 0:
        return IntakeResult(
            uc, value, cost, "PILOT",
            "Value and evidence cost are close. Run a bounded pilot with a "
            "real eval set before committing to a validated build; the pilot "
            "is there to move one of the two numbers, not to demo the model.",
            _binding_constraint(uc),
        )
    if margin >= -20:
        return IntakeResult(
            uc, value, cost, "REFRAME",
            "Evidence cost exceeds value at the current scope. Either narrow "
            "the scope to lower the evidence burden or find the higher-volume "
            "version of the same problem.",
            _binding_constraint(uc),
        )
    return IntakeResult(
        uc, value, cost, "DECLINE",
        "Evidence cost substantially exceeds value. Declining here is the "
        "cheap decision; declining after six months of pilot is not.",
        _binding_constraint(uc),
    )
