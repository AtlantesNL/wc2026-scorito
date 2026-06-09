# Scoreline pool-leverage calibration — finding (2026-06-09)

## What we tested

The pool-aware scoreline feature discounts each candidate scoreline's points by how crowded the
outcome is in a modelled amateur field (`L(own)=1/(1+own·(N−1))^γ`), driven by a **draw-averse**
field model (`field.scoreline_ownership`, draws down-weighted by `DRAW_AVERSION=0.4`). The premise
(from the code review + pool-strategy research): amateurs under-predict draws, so predicting
under-owned draws should separate us and raise P(finishing 1st).

We swept `γ` and scored the resulting full entry through the existing pool-win evaluator
(`pool.score_field` + `champion_win_probs`, champion fixed = Spain, 5000 sampled worlds,
MC std-error ≈ ±0.36%), against **two** modelled fields: a *chalk* field (rivals weight scorelines
by raw exact prob) and a *draw-averse* field (rivals down-weight draws like we assume they do).

## Result

| γ    | draws picked | P(win) vs chalk field | P(win) vs draw-averse field |
|------|--------------|-----------------------|-----------------------------|
| 0.00 | 0/72         | 0.0724                | 0.0728                      |
| 0.05 | 0/72         | 0.0724                | 0.0728                      |
| 0.08 | 0/72         | 0.0724                | 0.0728                      |
| 0.10 | 2/72         | 0.0706                | 0.0716                      |
| 0.15 | 4/72         | 0.0616                | 0.0722                      |
| 0.20 | 8/72         | 0.0586                | **0.0732**                  |
| 0.30 | 29/72        | 0.0240                | 0.0252                      |
| 0.50 | 64/72        | 0.0002                | 0.0002                      |

## Conclusion: scoreline draw-differentiation is ≈neutral at a 32-person pool

- Against a chalk field, picking draws **monotonically hurts** (0.0724 → 0.0586 → collapse) — clear,
  not noise. If rivals pick draws at the realistic rate, our draws don't separate us; they only cost
  the EV of the modal score.
- Against the draw-averse field, the best point (γ=0.20, 8 draws) is **0.0732 vs the 0.0728 chalk
  baseline = +0.04%**, which is **inside the ±0.36% MC noise**. Every draw-picking γ lands at or
  below chalk on the point estimate.
- Mechanism: a draw pays off only in the ~25% of worlds the match actually draws; in the other ~75%
  we forfeit the modal score's points. Across a ~1600-point entry decided by a full-tournament rank,
  those few separations don't move P(1st). **The review's "biggest lever" is, at this pool size, a
  wash** — which reinforces the lean-chalk-for-small-weak-pools science rather than contradicting it.
- `γ ≥ 0.3` is an active blowup (draws everywhere → entry value craters).

## What we shipped

`SCORELINE_LEVERAGE_GAMMA = {max_ev: 0.0, balanced: 0.1, aggressive: 0.2}` — tuned **low**:
- `balanced 0.1` grabs only the 1-3 highest-conviction under-owned draws (a near-free, documented-bias
  hedge; ~chalk in expectation).
- `aggressive 0.2` is the empirical peak against a draw-averse field, for users who want to bet harder
  on the amateur draw-aversion being real and the field being more clustered than modelled.
- `max_ev 0.0` is pure EV.

The draw-averse field model and leverage-adjusted objective are kept and tested: they cost ~nothing at
this size and **become a real lever for larger pools** (differentiation value grows with pool size and
field clustering) and for revisiting if we get actual field/ownership data.

## Caveats / where this could be wrong
- Real amateur fields may be *more* clustered on identical market scorelines than `FIELD_SHARPNESS=2.0`
  models; if so the draw benefit is larger than measured (but still small).
- 5000 worlds can't resolve sub-0.4% differences; the *sign* against a chalk field is solid, the
  small draw-averse-field edge is not. Either way the magnitude is negligible at 32 people.
- This is a group-phase-only analysis; the conclusion is about scoreline picks, not the champion
  leverage (which the evaluator does move materially — see the champion slice).
