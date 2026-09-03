# Stage 3: eval set sizing

Use case risk (consequence of error) scored 2/5, which sets the confidence level for every statistical criterion at 90%. Higher-consequence use cases pay for their risk in sample size.

| Criterion | Metric | Threshold | Expected | Required n | SME hours | Verdict |
|---|---|---|---|---|---|---|
| R-02 | extraction accuracy | 95.0% | 97.0% | 148 | 59.2 | 9.9 SME-days at 2 reviewers |
| R-06 | citation integrity | 99.0% | 99.0% | not achievable | n/a | **Unprovable as written** |
| R-07 | refusal rate | 98.0% | 99.5% | 81 | 4.0 | 0.7 SME-days at 2 reviewers |

## Findings

**R-06 cannot be demonstrated at any sample size.** The threshold is 99.0% and the expected performance is 99.0%. A confidence bound on a sample can only clear a threshold the system beats with room to spare; when expected performance sits exactly on the line, roughly half of all honest test runs land below it. Either lower the threshold, or improve the system before writing the criterion. This is a design-time conversation that costs an hour. Discovering it during the acceptance test costs the test.


## What the risk classification costs

The confidence level is set by the use case's consequence-of-error score, not chosen by whoever writes the test plan. Same criterion, same threshold, three risk tiers:

| Confidence | Risk tier | Required n | SME hours (2 reviewers) |
|---|---|---|---|
| 90% | 1-2, no GxP scope | 148 | 59.2 |
| 95% | 3-4, GxP scope | 280 | 112.0 |
| 99% | 5, submission or safety pathway | 611 | 244.4 |

Shown for R-02 (extraction accuracy, 95% threshold, 97% expected). Moving this use case one risk tier up is not a paperwork change. It is a different project estimate.

Total labeled cases required across provable criteria: **229**.

This number belongs in the project estimate at intake, not in the test plan three months later. It is usually the largest single line of effort in an AI feature and it is the one most often left out.