# SteerProofs

Lean 4 (Mathlib) proofs of the exact results in the aisteer brief. All in `SteerProofs/Basic.lean`; no `sorry`.

- Theorem 1: `nudge_bounded`, `nudges_bounded`, `rest_iff_median`, `belief_scales`, `agenda_free`
- Theorem 2 / 5(b): `recusal_rest`, `capture`
- Theorem 3 (optimum only): `best_step`
- Theorem 4: `pair_prob`, `flags_sooner`
- Theorem 5(a): `characterization`
- Theorem 6 (optimum only): `best_allocation`
- Theorem 7: `one_question_gain`, `gain_monotone`

Build: `lake exe cache get && lake build`.
