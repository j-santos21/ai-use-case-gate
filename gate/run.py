"""
Runner. Produces the portfolio review, the requirements disposition, the
eval sizing plan, and the release decision for the worked example.

    python3 -m gate.run
"""

import json
import random
from pathlib import Path

from gate.intake import UseCase, score, EVIDENCE_FACTORS
from gate.requirements import Requirement, classify
from gate import evals

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

SEED = 20260902
WORKED_EXAMPLE = "UC-02"

# True performance rates used to simulate the acceptance test. Held separate
# from the `expected` figures in the requirements file on purpose: `expected`
# is what the team predicted at design time, this is what the system actually
# does. They differ, which is the entire reason the test exists.
TRUE_RATES = {
    "R-02": 0.968,
    "R-06": 0.988,
    "R-07": 0.994,
}


def load_use_cases() -> list[UseCase]:
    raw = json.loads((DATA / "use_cases.json").read_text())
    return [
        UseCase(
            id=u["id"], title=u["title"], function=u["function"],
            sponsor=u["sponsor"], scores=u["scores"], note=u.get("note", ""),
        )
        for u in raw["use_cases"]
    ]


def load_requirements() -> list[tuple[Requirement, dict]]:
    raw = json.loads((DATA / "requirements.json").read_text())
    out = []
    for r in raw["requirements"]:
        req = Requirement(
            id=r["id"], use_case_id=r["use_case_id"], text=r["text"],
            source=r["source"], metric=r.get("metric"),
            threshold=r.get("threshold"), expected=r.get("expected"),
            minutes_per_label=r.get("minutes_per_label", 3.0),
        )
        out.append((req, r))
    return out


# ---------------------------------------------------------------------------


def portfolio_review(results) -> str:
    lines = ["# Stage 1: portfolio intake review", ""]
    lines.append(f"{len(results)} requests, scored against the intake rubric. Value and")
    lines.append("evidence cost are both on a 0-100 scale; margin is value minus cost.")
    lines.append("Binding constraint names the evidence factor contributing most above")
    lines.append("its floor, which is the thing to change if the use case is to move.")
    lines.append("")
    lines.append("| ID | Use case | Function | Value | Evidence cost | Margin | Disposition | Binding constraint |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in sorted(results, key=lambda x: -(x.value - x.evidence_cost)):
        margin = r.value - r.evidence_cost
        lines.append(
            f"| {r.use_case.id} | {r.use_case.title} | {r.use_case.function} | "
            f"{r.value:.0f} | {r.evidence_cost:.0f} | {margin:+.0f} | "
            f"**{r.disposition}** | {r.binding_constraint} |"
        )

    counts = {}
    for r in results:
        counts[r.disposition] = counts.get(r.disposition, 0) + 1
    lines += ["", "## Disposition counts", ""]
    for k in ("BUILD", "PILOT", "REFRAME", "DECLINE"):
        lines.append(f"- {k}: {counts.get(k, 0)}")

    lines += ["", "## Rationale by use case", ""]
    for r in sorted(results, key=lambda x: x.use_case.id):
        lines.append(f"**{r.use_case.id} — {r.use_case.title}** ({r.disposition})")
        lines.append("")
        lines.append(r.rationale)
        lines.append("")
    return "\n".join(lines)


def requirements_report(classified) -> str:
    lines = ["# Stage 2: requirements disposition", ""]
    lines.append(f"Worked example: {WORKED_EXAMPLE}. Eight requirements as submitted.")
    lines.append("")
    counts = {}
    for c in classified:
        counts[c.kind] = counts.get(c.kind, 0) + 1
    lines.append("| Kind | Count |")
    lines.append("|---|---|")
    for k in ("DETERMINISTIC", "STATISTICAL", "UNTESTABLE"):
        lines.append(f"| {k} | {counts.get(k, 0)} |")
    lines.append("")

    for c in classified:
        lines.append(f"### {c.req.id} — {c.kind}")
        lines.append("")
        lines.append(f"> {c.req.text}")
        lines.append("")
        lines.append(f"*Source: {c.req.source}*")
        lines.append("")
        lines.append(c.reason)
        lines.append("")
        if c.proposed_rewrite:
            lines.append("**Proposed rewrite to take back to the stakeholder:**")
            lines.append("")
            lines.append(f"> {c.proposed_rewrite}")
            lines.append("")
    return "\n".join(lines)


def sizing_report(classified, risk_score: int) -> tuple[str, dict]:
    conf = evals.CONFIDENCE_BY_RISK[risk_score]
    lines = ["# Stage 3: eval set sizing", ""]
    lines.append(
        f"Use case risk (consequence of error) scored {risk_score}/5, which sets "
        f"the confidence level for every statistical criterion at {conf:.0%}. "
        f"Higher-consequence use cases pay for their risk in sample size."
    )
    lines.append("")
    lines.append("| Criterion | Metric | Threshold | Expected | Required n | SME hours | Verdict |")
    lines.append("|---|---|---|---|---|---|---|")

    plan = {}
    notes = []
    for c in classified:
        if c.kind != "STATISTICAL":
            continue
        n = evals.required_sample_size(c.req.threshold, c.req.expected, conf)
        if n is None:
            lines.append(
                f"| {c.req.id} | {c.req.metric} | {c.req.threshold:.1%} | "
                f"{c.req.expected:.1%} | not achievable | n/a | **Unprovable as written** |"
            )
            notes.append(
                f"**{c.req.id} cannot be demonstrated at any sample size.** The "
                f"threshold is {c.req.threshold:.1%} and the expected performance is "
                f"{c.req.expected:.1%}. A confidence bound on a sample can only clear a "
                f"threshold the system beats with room to spare; when expected "
                f"performance sits exactly on the line, roughly half of all honest "
                f"test runs land below it. Either lower the threshold, or improve the "
                f"system before writing the criterion. This is a design-time "
                f"conversation that costs an hour. Discovering it during the "
                f"acceptance test costs the test."
            )
            continue
        burden = evals.labeling_burden(n, c.req.minutes_per_label, reviewers=2)
        plan[c.req.id] = {"n": n, "confidence": conf, "metric": c.req.metric,
                          "threshold": c.req.threshold}
        lines.append(
            f"| {c.req.id} | {c.req.metric} | {c.req.threshold:.1%} | "
            f"{c.req.expected:.1%} | {n} | {burden['sme_hours']} | "
            f"{burden['sme_days']} SME-days at 2 reviewers |"
        )

    if notes:
        lines += ["", "## Findings", ""]
        lines += [n + "\n" for n in notes]

    # Risk sensitivity. The point of showing this is that the confidence level
    # is not a statistical preference, it is a risk decision made by the
    # business, and it has a price tag that the business should see before it
    # is asked to approve the risk classification.
    lines += ["", "## What the risk classification costs", ""]
    lines.append(
        "The confidence level is set by the use case's consequence-of-error "
        "score, not chosen by whoever writes the test plan. Same criterion, "
        "same threshold, three risk tiers:"
    )
    lines.append("")
    lines.append("| Confidence | Risk tier | Required n | SME hours (2 reviewers) |")
    lines.append("|---|---|---|---|")
    demo = next((c for c in classified if c.kind == "STATISTICAL"
                 and evals.required_sample_size(c.req.threshold, c.req.expected, 0.90)), None)
    if demo:
        tiers = {0.90: "1-2, no GxP scope", 0.95: "3-4, GxP scope",
                 0.99: "5, submission or safety pathway"}
        for conf_level, label in tiers.items():
            n = evals.required_sample_size(demo.req.threshold, demo.req.expected, conf_level)
            if n is None:
                lines.append(f"| {conf_level:.0%} | {label} | not achievable | n/a |")
                continue
            b = evals.labeling_burden(n, demo.req.minutes_per_label, reviewers=2)
            lines.append(f"| {conf_level:.0%} | {label} | {n} | {b['sme_hours']} |")
        lines.append("")
        lines.append(
            f"Shown for {demo.req.id} ({demo.req.metric}, {demo.req.threshold:.0%} "
            f"threshold, {demo.req.expected:.0%} expected). Moving this use case "
            f"one risk tier up is not a paperwork change. It is a different "
            f"project estimate."
        )

    total = sum(v["n"] for v in plan.values())
    lines += ["", f"Total labeled cases required across provable criteria: **{total}**.", ""]
    lines.append(
        "This number belongs in the project estimate at intake, not in the test "
        "plan three months later. It is usually the largest single line of "
        "effort in an AI feature and it is the one most often left out."
    )
    return "\n".join(lines), plan


def acceptance_test(plan: dict) -> tuple[str, list]:
    rng = random.Random(SEED)
    lines = ["# Stage 4: acceptance test and release decision", ""]
    lines.append(
        "Outcomes simulated by drawing each labeled case from a Bernoulli trial "
        f"at a fixed true rate (seed {SEED}). The true rates are set slightly "
        "below the design-time expectations, which is the ordinary case: teams "
        "estimate their own systems optimistically."
    )
    lines.append("")
    lines.append("| Criterion | n | True rate | Observed | Lower bound | Threshold | Result |")
    lines.append("|---|---|---|---|---|---|---|")

    results = []
    for cid, spec in plan.items():
        true_rate = TRUE_RATES[cid]
        n = spec["n"]
        successes = sum(1 for _ in range(n) if rng.random() < true_rate)
        r = evals.run_criterion(
            cid, spec["metric"], spec["threshold"], successes, n, spec["confidence"]
        )
        results.append(r)
        mark = "Pass" if r.passed else ("Inconclusive" if r.observed >= r.threshold else "Fail")
        lines.append(
            f"| {cid} | {n} | {true_rate:.1%} | {r.observed:.2%} | {r.lower_bound:.2%} | "
            f"{r.threshold:.1%} | **{mark}** |"
        )

    lines += ["", "## Detail", ""]
    for r in results:
        lines.append(f"- **{r.criterion_id}**: {r.verdict}")

    decision, why = evals.release_decision(results)
    lines += ["", "## Release decision", "", f"### {decision}", "", why, ""]

    if decision == "RELEASE":
        lines.append("## Post-release monitoring")
        lines.append("")
        lines.append("Thresholds derived from the release evidence rather than chosen.")
        lines.append("")
        lines.append("| Criterion | Alert below | Escalate below | Monthly sample |")
        lines.append("|---|---|---|---|")
        for r in results:
            b = evals.monitoring_band(r)
            lines.append(
                f"| {b['criterion']} | {b['alert_below']:.2%} | "
                f"{b['escalate_below']:.2%} | {b['monthly_sample']} |"
            )
        lines.append("")
        lines.append(f"On alert: {evals.monitoring_band(results[0])['action_on_alert']}")
        lines.append("")
        lines.append(f"On escalation: {evals.monitoring_band(results[0])['action_on_escalation']}")
    else:
        lines.append(
            "No monitoring plan is issued for a system that has not been "
            "released. The next action is on the criteria named above."
        )
    return "\n".join(lines), results


def main() -> None:
    cases = load_use_cases()
    intake_results = [score(c) for c in cases]
    (OUT / "01_portfolio_review.md").write_text(portfolio_review(intake_results))

    reqs = load_requirements()
    classified = [classify(r) for r, _ in reqs if r.use_case_id == WORKED_EXAMPLE]
    (OUT / "02_requirements.md").write_text(requirements_report(classified))

    worked = next(r for r in intake_results if r.use_case.id == WORKED_EXAMPLE)
    risk = worked.use_case.scores["consequence_of_error"]
    sizing, plan = sizing_report(classified, risk)
    (OUT / "03_eval_sizing.md").write_text(sizing)

    test_report, results = acceptance_test(plan)
    (OUT / "04_release_decision.md").write_text(test_report)

    print(f"Intake: {len(cases)} use cases scored.")
    for d in ("BUILD", "PILOT", "REFRAME", "DECLINE"):
        n = sum(1 for r in intake_results if r.disposition == d)
        print(f"  {d}: {n}")
    print(f"\nWorked example {WORKED_EXAMPLE} ({worked.use_case.title})")
    print(f"  value {worked.value} / evidence cost {worked.evidence_cost} -> {worked.disposition}")
    kinds = {}
    for c in classified:
        kinds[c.kind] = kinds.get(c.kind, 0) + 1
    print(f"  requirements: {kinds}")
    print(f"  provable statistical criteria: {len(plan)}")
    print(f"  total labeled cases required: {sum(v['n'] for v in plan.values())}")
    decision, why = evals.release_decision(results)
    print(f"  release decision: {decision} - {why}")
    print(f"\nWrote 4 reports to {OUT}")


if __name__ == "__main__":
    main()
