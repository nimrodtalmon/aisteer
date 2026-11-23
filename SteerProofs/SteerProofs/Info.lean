import Mathlib

/-!
# The information bound and indirect influence

* `Info`: the posterior Cramér–Rao recursion for a random-walk target observed through answers
  whose Fisher information is at most `I`, its fixed point, and the comparison with nudges.
* `Indirect`: how much an answer about a pair `(k, l)` can change the share of a third project.
-/

noncomputable section
open Real

namespace Steer

/-! ## The information recursion -/

/-- One step of the information recursion: drift with variance `Q`, then one answer with
information at most `I`. -/
def infoStep (Q I J : ℝ) : ℝ := 1 / (Q + 1 / J) + I

/-- The stationary error: the positive root of `I P^2 + I Q P - Q = 0`. -/
def statErr (Q I : ℝ) : ℝ := (-(I * Q) + Real.sqrt ((I * Q) ^ 2 + 4 * I * Q)) / (2 * I)

lemma disc_gt {Q I : ℝ} (hQ : 0 < Q) (hI : 0 < I) :
    I * Q < Real.sqrt ((I * Q) ^ 2 + 4 * I * Q) := by
  rw [show I * Q = Real.sqrt ((I * Q) ^ 2) by rw [Real.sqrt_sq (by positivity)]]
  apply Real.sqrt_lt_sqrt (by positivity)
  rw [Real.sq_sqrt (by positivity)]
  nlinarith [mul_pos hI hQ]

lemma statErr_pos {Q I : ℝ} (hQ : 0 < Q) (hI : 0 < I) : 0 < statErr Q I := by
  unfold statErr
  have := disc_gt hQ hI
  apply div_pos (by linarith) (by positivity)

/-- `statErr` solves the quadratic. -/
lemma statErr_quad {Q I : ℝ} (hQ : 0 < Q) (hI : 0 < I) :
    I * statErr Q I ^ 2 + I * Q * statErr Q I - Q = 0 := by
  unfold statErr
  have hs := Real.sq_sqrt (show (0:ℝ) ≤ (I * Q) ^ 2 + 4 * I * Q by positivity)
  generalize Real.sqrt ((I * Q) ^ 2 + 4 * I * Q) = s at hs ⊢
  have e : I * ((-(I * Q) + s) / (2 * I)) ^ 2 + I * Q * ((-(I * Q) + s) / (2 * I)) - Q
      = (s ^ 2 - ((I * Q) ^ 2 + 4 * I * Q)) / (4 * I) := by
    field_simp; ring
  rw [e, hs]; simp

/-- The stationary information `1 / statErr` is a fixed point of the recursion. -/
theorem fixed_point {Q I : ℝ} (hQ : 0 < Q) (hI : 0 < I) :
    infoStep Q I (1 / statErr Q I) = 1 / statErr Q I := by
  have hP := statErr_pos hQ hI
  have hq := statErr_quad hQ hI
  unfold infoStep
  rw [one_div_one_div]
  set P := statErr Q I
  have hQP : 0 < Q + P := by linarith
  field_simp
  nlinarith [hq]

/-- The recursion is monotone. -/
lemma infoStep_mono {Q I J J' : ℝ} (hQ : 0 < Q) (hJ : 0 < J) (h : J ≤ J') :
    infoStep Q I J ≤ infoStep Q I J' := by
  unfold infoStep
  have hJ' : 0 < J' := lt_of_lt_of_le hJ h
  have h1 : 1 / J' ≤ 1 / J := one_div_le_one_div_of_le hJ h
  have : 1 / (Q + 1 / J) ≤ 1 / (Q + 1 / J') :=
    one_div_le_one_div_of_le (by positivity) (by linarith)
  linarith

/-- **Information bound.** If the information after each answer obeys the recursion with
per-answer information at most `I` (the posterior Cramér–Rao recursion for a random walk), and
the prior information is at most the stationary one, then the information never exceeds the
stationary information; hence the mean-square error is at least `statErr Q I` at every step. -/
theorem info_bound {Q I : ℝ} (hQ : 0 < Q) (hI : 0 < I) (J : ℕ → ℝ)
    (hpos : ∀ k, 0 < J k)
    (hrec : ∀ k, J (k + 1) ≤ infoStep Q I (J k))
    (h0 : J 0 ≤ 1 / statErr Q I) :
    ∀ k, J k ≤ 1 / statErr Q I := by
  intro k
  induction k with
  | zero => exact h0
  | succ n ih =>
    calc J (n + 1) ≤ infoStep Q I (J n) := hrec n
      _ ≤ infoStep Q I (1 / statErr Q I) := infoStep_mono hQ (hpos n) ih
      _ = 1 / statErr Q I := fixed_point hQ hI

/-- The stationary error is at least `sqrt (Q / I) - Q / 2`. -/
theorem statErr_ge {Q I : ℝ} (hQ : 0 < Q) (hI : 0 < I) :
    Real.sqrt (Q / I) - Q / 2 ≤ statErr Q I := by
  have hP := statErr_pos hQ hI
  have hq := statErr_quad hQ hI
  set P := statErr Q I
  -- from the quadratic: (P + Q/2)^2 = Q/I + Q^2/4 ≥ Q/I
  have key : Q / I ≤ (P + Q / 2) ^ 2 := by
    have : (P + Q / 2) ^ 2 = Q / I + Q ^ 2 / 4 := by
      field_simp; nlinarith [hq]
    rw [this]; nlinarith [sq_nonneg Q]
  have hs : Real.sqrt (Q / I) ≤ P + Q / 2 := by
    rw [show P + Q / 2 = Real.sqrt ((P + Q / 2) ^ 2) by
      rw [Real.sqrt_sq (by linarith)]]
    exact Real.sqrt_le_sqrt key
  linarith

/-- The stationary error is at most `sqrt (Q / I)`. -/
theorem statErr_le {Q I : ℝ} (hQ : 0 < Q) (hI : 0 < I) :
    statErr Q I ≤ Real.sqrt (Q / I) := by
  have hP := statErr_pos hQ hI
  have hq := statErr_quad hQ hI
  set P := statErr Q I
  have : P ^ 2 ≤ Q / I := by
    rw [le_div_iff₀ hI]; nlinarith [mul_pos (mul_pos hI hQ) hP]
  rw [show P = Real.sqrt (P ^ 2) by rw [Real.sqrt_sq hP.le]]
  exact Real.sqrt_le_sqrt this

/-- With one answer every `1/q` days (`Q = vol^2 / q`) and direction answers of information
`4 dens^2`, the leading term `sqrt (Q / I)` is exactly the best error of nudges,
`vol / (2 dens sqrt q)`. -/
theorem leading_term {vol dens q : ℝ} (hv : 0 < vol) (hd : 0 < dens) (hq : 0 < q) :
    Real.sqrt ((vol ^ 2 / q) / (4 * dens ^ 2)) = vol / (2 * dens * Real.sqrt q) := by
  have hsq : Real.sqrt q ^ 2 = q := Real.sq_sqrt hq.le
  have hsqp : 0 < Real.sqrt q := Real.sqrt_pos.mpr hq
  rw [show (vol ^ 2 / q) / (4 * dens ^ 2) = (vol / (2 * dens * Real.sqrt q)) ^ 2 by
    rw [div_pow, mul_pow, mul_pow, hsq]; field_simp; ring]
  exact Real.sqrt_sq (by positivity)

/-- The information of a direction answer at the answerers' median is `4 dens^2`. -/
theorem info_at_median (dens : ℝ) : dens ^ 2 / ((1 / 2) * (1 - 1 / 2)) = 4 * dens ^ 2 := by
  ring

/-- For Laplace noise (scale 1), the information of a direction answer whose comparison point is
`y ≥ 0` away from the median, `e^{-y} / (2 - e^{-y})`, is largest at the median (where it is 1). -/
theorem laplace_info_max {y : ℝ} (hy : 0 ≤ y) : exp (-y) / (2 - exp (-y)) ≤ 1 := by
  have h1 : exp (-y) ≤ 1 := by rw [exp_le_one_iff]; linarith
  have h2 : 0 < 2 - exp (-y) := by linarith
  rw [div_le_one h2]; linarith

/-! ## Indirect influence -/

/-- After a nudge toward `k` on the pair `(k, l)` with shares `sk, sl`, the normalizer changes by
the factor `1 + sk (e^a - 1) + sl (e^{-a} - 1)`, `a = step / 2`; every other project's share is
divided by it. The change is at most `(e^a - 1) * max sk sl`. -/
theorem indirect_bound {a sk sl : ℝ} (ha : 0 ≤ a) (hk : 0 ≤ sk) (hl : 0 ≤ sl) :
    |sk * (exp a - 1) + sl * (exp (-a) - 1)| ≤ (exp a - 1) * max sk sl := by
  have e1 : 0 ≤ exp a - 1 := by linarith [one_le_exp ha]
  have e2 : 0 ≤ 1 - exp (-a) := by
    have : exp (-a) ≤ 1 := by rw [exp_le_one_iff]; linarith
    linarith
  have e3 : 1 - exp (-a) ≤ exp a - 1 := by
    have h := add_one_le_exp (-a)
    have h' := add_one_le_exp a
    -- 1 - e^{-a} ≤ a ≤ e^a - 1
    linarith
  have hmk : sk ≤ max sk sl := le_max_left _ _
  have hml : sl ≤ max sk sl := le_max_right _ _
  have A : sk * (exp a - 1) ≤ (exp a - 1) * max sk sl := by nlinarith
  have B : sl * (1 - exp (-a)) ≤ (exp a - 1) * max sk sl := by nlinarith
  have A0 : 0 ≤ sk * (exp a - 1) := mul_nonneg hk e1
  have B0 : 0 ≤ sl * (1 - exp (-a)) := mul_nonneg hl e2
  rw [abs_le]; constructor <;> nlinarith

/-- Pushing toward the smaller project of a pair lowers the normalizer, so every other project's
share rises: if `sk * e^a < sl`, then the factor is below 1. -/
theorem push_small_helps {a sk sl : ℝ} (ha : 0 < a) (h : sk * exp a < sl) :
    sk * (exp a - 1) + sl * (exp (-a) - 1) < 0 := by
  have hea : 0 < exp a := exp_pos a
  have key : sk * (exp a - 1) + sl * (exp (-a) - 1) = (1 - exp (-a)) * (sk * exp a - sl) := by
    have : exp (-a) * exp a = 1 := by rw [← exp_add]; simp
    linear_combination sk * this
  rw [key]
  have : 0 < 1 - exp (-a) := by
    have : exp (-a) < exp 0 := exp_lt_exp.mpr (by linarith)
    rw [exp_zero] at this
    linarith
  nlinarith

end Steer
