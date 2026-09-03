# AI Use-Case Gate

A four-stage model for deciding which AI use cases an enterprise should build,
what their requirements have to say before they can be accepted, how much
labeled data it takes to prove they work, and whether the evidence supports a
release.

Written by Jason Santos. Runs on Python 3.11 standard library, no dependencies.

**Case study write-up: [j-santos21.github.io/ai-use-case-gate](https://j-santos21.github.io/ai-use-case-gate/)**

```
PYTHONPATH=. python3 -m gate.run          # produces the four reports in outputs/
PYTHONPATH=. python3 -m unittest discover tests -v
```

## The problem it addresses

A business systems analyst working on conventional software writes a
requirement, and the requirement implies its own test. "The system shall
prevent submission when the effective date precedes the contract date" is one
test case, and it either passes or it does not.

That relationship breaks on a system whose output is a probability
distribution. "The system shall extract payment terms accurately" implies no
test. It is not that the test is hard to write; it is that no observation
could falsify the sentence. Two people can look at the same output and
disagree about whether the requirement was met, and both can defend their
position, because the requirement never said what accurate meant or how often
it had to hold.

What happens next is predictable. The requirement goes into the spec unchanged
because it sounds reasonable. UAT becomes a demo. Somebody runs forty examples,
thirty-eight look good, and the number 95% enters the record. The system ships
on a sample too small to support the claim, and the first real evidence about
its accuracy arrives from a downstream process that was not expecting to be the
control.

The gap is not a data science gap. Data scientists know how to evaluate models.
It is an analysis gap: nobody translated the business requirement into a claim
that could be measured, priced, and tested. That translation is the job this
model does.

## What it does

**Stage 1, intake.** Thirteen requests scored on six anchored factors, which
roll up into two numbers: what the organization gets if it works, and what it
costs to demonstrate that it does. The second axis is the one most intake
frameworks get wrong. They score feasibility, meaning "can we build it," and
in 2026 the answer is almost always yes. The binding constraint is evidence,
not engineering.

Two hard gates run before the tradeoff. A use case with no defensible ground
truth and no practical way for a human to check the output is not an expensive
use case; it is one where no acceptance criterion could ever fail, so there is
nothing to decide. Value does not rescue it. In the sample portfolio, UC-11
clears the value threshold with a positive margin and is still gated, which is
the point of having gates rather than a single score.

**Stage 2, requirements.** Eight requirements as a stakeholder actually wrote
them, sorted into deterministic, statistical, and untestable. Three of the
eight cannot be accepted as worded. Each of those comes back with a rewrite
template rather than a finished sentence, because the blanks are what the
analyst and the stakeholder need to argue about.

The classifier is rule-based on purpose. A language model would do this well
enough, but the analyst then cannot explain to an auditor why a given
requirement was routed the way it was, and the routing carries consequences.
The rules have a known failure mode: they read grammar, and grammar can hide a
rate claim inside a deterministic-sounding verb. R-07 is that case, and the
analyst override that catches it is documented in `gate/requirements.py`.

**Stage 3, sizing.** Every statistical criterion gets a sample size computed
from its threshold, the expected performance, and a confidence level set by
the use case's risk score rather than by whoever writes the test plan. The
sample size converts to reviewer hours, which is the form the number has to be
in before it can enter a project estimate.

Two findings come out of this stage on the sample data:

- R-06 asks for 99% citation integrity from a system expected to deliver 99%.
  That criterion cannot be demonstrated at any sample size. When expected
  performance sits exactly on the threshold, roughly half of all honest test
  runs land below it. The requirement needs a lower threshold or a better
  system, and that is a design-time conversation, not a discovery to make
  during acceptance testing.
- The same criterion at the same threshold needs 148 labeled cases at the
  lowest risk tier and 611 at the highest. Moving a use case one risk tier up
  is not a documentation change. It is a different project estimate.

**Stage 4, release.** The acceptance test runs against a labeled set,
simulated here by drawing from a fixed true rate. Each criterion is judged on
the lower confidence bound, not the point estimate. One criterion failing
blocks release; there is no aggregate score, because an aggregate lets a good
accuracy number offset a failed citation-integrity criterion, and nobody would
approve that trade if it were stated out loud.

The worked example returns HOLD. Nothing failed on the merits. R-02 observed
95.9% against a 95% threshold, which reads as a pass and is not one: the lower
bound is 93.3%, so the sample cannot support the claim. A team without this
step ships that result and reports 96% accuracy in the closure memo. The model
sends it back for more data.

## Regulatory alignment

The structure follows GAMP 5 Second Edition Appendix D11 on AI and machine
learning in GxP systems: validation intensity proportional to intended use and
risk, quantitative acceptance criteria defined before testing rather than
inferred from results, training and test data held to ALCOA+ with documented
partitioning, subject matter expert adjudication of labels, and continuous
performance monitoring after release rather than a one-time qualification.

The monitoring bands in `gate/evals.py` are derived from the release evidence
rather than chosen. The alert line sits at the release lower bound, which
means the system is flagged when it drops below the performance it was
actually approved at, not below a round number somebody liked.

## Files

```
gate/intake.py        scoring rubric, hard gates, disposition
gate/requirements.py  requirement classification and rewrite templates
gate/evals.py         Wilson bounds, sample sizing, release logic, monitoring
gate/run.py           runner, report generation
data/use_cases.json   13 simulated intake requests
data/requirements.json 8 simulated requirements for the worked example
outputs/              generated reports, four stages
tests/test_gate.py    20 tests, weighted toward the statistics
```

## On the data

All use cases, requirements, and test outcomes are simulated. They are
constructed to exercise the model across its full range and to resemble the
kind of request an R&D technology intake process actually receives. No real
program, system, vendor, or scoring session is represented, and no proprietary
information from any employer appears anywhere in this repository.

## What this model does not do

It does not evaluate models, choose architectures, or write prompts. It does
not tell you whether a system is good. It tells you whether you are in a
position to find out, what finding out will cost, and whether the evidence you
have supports the decision you are about to make.

It also separates the ends of a portfolio better than the middle. In the
sample run, seven of thirteen use cases land in PILOT, which is a wide band and
a real limitation. For those seven, the binding-constraint column is more
useful than the disposition: it names the one factor to change if the use case
is going to move, which is the conversation worth having anyway.
