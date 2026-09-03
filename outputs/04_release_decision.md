# Stage 4: acceptance test and release decision

Outcomes simulated by drawing each labeled case from a Bernoulli trial at a fixed true rate (seed 20260902). The true rates are set slightly below the design-time expectations, which is the ordinary case: teams estimate their own systems optimistically.

| Criterion | n | True rate | Observed | Lower bound | Threshold | Result |
|---|---|---|---|---|---|---|
| R-02 | 148 | 96.8% | 95.95% | 93.31% | 95.0% | **Inconclusive** |
| R-07 | 81 | 99.4% | 100.00% | 98.01% | 98.0% | **Pass** |

## Detail

- **R-02**: Inconclusive. Observed 95.9% is above the 95% threshold, but the 90% lower bound is 93.3%. The sample is too small to support the claim. Enlarge the eval set rather than reporting the point estimate.
- **R-07**: Pass. Observed 100.0% on n=81; 90% lower bound 98.0% clears the 98% threshold.

## Release decision

### HOLD

No criterion failed on the merits, but 1 is underpowered: R-02. Extend the eval set and rerun.

No monitoring plan is issued for a system that has not been released. The next action is on the criteria named above.