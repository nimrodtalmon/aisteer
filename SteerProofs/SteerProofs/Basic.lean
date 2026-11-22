import Mathlib

/-!
# Steering a living allocator: the exact results, checked in Lean

Log-ratios are real numbers. An answer is a direction: +1 (more to `a`),
-1 (more to `b`) or 0 (about right). A nudge moves the log-ratio by `step`
in the answered direction.
-/

set_option linter.style.header false
set_option linter.flexible false
set_option linter.unusedSimpArgs false

noncomputable section
open Finset

namespace Steer

/-- The direction of a report `r` relative to the current log-ratio `g`. -/
def dir (g r : ℝ) : ℝ := if g < r then 1 else if r < g then -1 else 0

/-- The nudge with a given step. -/
def nudge (step g r : ℝ) : ℝ := g + step * dir g r

/-! ## Theorem 1(a): bounded influence -/

theorem dir_abs_le (g r : ℝ) : |dir g r| ≤ 1 := by
  unfold dir; split_ifs <;> simp

/-- One answer moves a log-ratio by at most `step`. -/
theorem nudge_bounded {step : ℝ} (hs : 0 ≤ step) (g r : ℝ) :
    |nudge step g r - g| ≤ step := by
  unfold nudge
  rw [add_sub_cancel_left, abs_mul, abs_of_nonneg hs]
  calc step * |dir g r| ≤ step * 1 := mul_le_mul_of_nonneg_left (dir_abs_le g r) hs
    _ = step := mul_one step

/-- `k` answers move a log-ratio by at most `k * step`. -/
theorem nudges_bounded {step : ℝ} (hs : 0 ≤ step) (g : ℕ → ℝ) (r : ℕ → ℝ)
    (hg : ∀ n, g (n + 1) = nudge step (g n) (r n)) (k : ℕ) :
    |g k - g 0| ≤ k * step := by
  induction k with
  | zero => simp
  | succ n ih =>
    have h1 := nudge_bounded hs (g n) (r n)
    rw [← hg n] at h1
    calc |g (n + 1) - g 0| = |(g (n + 1) - g n) + (g n - g 0)| := by ring_nf
      _ ≤ |g (n + 1) - g n| + |g n - g 0| := abs_add_le _ _
      _ ≤ step + n * step := add_le_add h1 ih
      _ = ((n + 1 : ℕ) : ℝ) * step := by push_cast; ring

/-! ## Theorem 5(a): the axioms force nudges -/

/-- Typing-proof: stretching the report away from the current log-ratio
(any strictly increasing map fixing `g`) never changes the result. -/
def TypingProof (U : ℝ → ℝ → ℝ) : Prop :=
  ∀ g r (τ : ℝ → ℝ), StrictMono τ → τ g = g → U g (τ r) = U g r

/-- Level-free: only the position of the report relative to `g` matters. -/
def LevelFree (U : ℝ → ℝ → ℝ) : Prop := ∀ g r c, U (g + c) (r + c) = U g r + c

/-- Neutral: swapping the two projects mirrors the rule. -/
def Neutral (U : ℝ → ℝ → ℝ) : Prop := ∀ g r, U (-g) (-r) = -U g r

/-- Responsive: a report above `g` never moves the log-ratio down. -/
def Responsive (U : ℝ → ℝ → ℝ) : Prop := ∀ g r, g < r → g ≤ U g r

theorem nudge_typingProof (step : ℝ) : TypingProof (nudge step) := by
  intro g r τ hτ hfix
  unfold nudge dir
  have h1 : g < τ r ↔ g < r := by
    have := hτ.lt_iff_lt (a := g) (b := r); rwa [hfix] at this
  have h2 : τ r < g ↔ r < g := by
    have := hτ.lt_iff_lt (a := r) (b := g); rwa [hfix] at this
  simp only [h1, h2]

theorem nudge_levelFree (step : ℝ) : LevelFree (nudge step) := by
  intro g r c; unfold nudge dir
  have h1 : g + c < r + c ↔ g < r := add_lt_add_iff_right c
  have h2 : r + c < g + c ↔ r < g := add_lt_add_iff_right c
  simp only [h1, h2]; ring

theorem nudge_neutral (step : ℝ) : Neutral (nudge step) := by
  intro g r; unfold nudge dir
  by_cases h : g < r
  · have h' : ¬ (-g < -r) := by linarith
    have h'' : -r < -g := by linarith
    simp [h, h', h'']; ring
  · by_cases h2 : r < g
    · have h' : -g < -r := by linarith
      simp [h, h2, h']; ring
    · have h' : ¬ (-g < -r) := by linarith
      have h'' : ¬ (-r < -g) := by linarith
      simp [h, h2, h', h'']

theorem nudge_responsive {step : ℝ} (hs : 0 ≤ step) : Responsive (nudge step) := by
  intro g r h; unfold nudge dir; simp [h]; exact hs

/-- **Theorem 5(a).** A responsive rule is typing-proof, level-free and neutral
if and only if it is a nudge with some step `δ ≥ 0`. -/
theorem characterization (U : ℝ → ℝ → ℝ) :
    (Responsive U ∧ TypingProof U ∧ LevelFree U ∧ Neutral U) ↔
      ∃ δ ≥ 0, ∀ g r, U g r = nudge δ g r := by
  constructor
  · rintro ⟨hR, hT, hL, hN⟩
    -- the move from 0 towards a positive report is the same for all reports
    have pos : ∀ x : ℝ, 0 < x → U 0 x = U 0 1 := by
      intro x hx
      have hmono : StrictMono (fun y : ℝ => y * x) := fun a b hab => by
        simp only; exact mul_lt_mul_of_pos_right hab hx
      have := hT 0 1 (fun y => y * x) hmono (by simp)
      simpa using this
    have zero : U 0 0 = 0 := by
      have := hN 0 0; simp at this; linarith
    have neg : ∀ x : ℝ, x < 0 → U 0 x = - U 0 1 := by
      intro x hx
      have h1 := hN 0 (-x); simp only [neg_zero, neg_neg] at h1
      rw [h1, pos (-x) (by linarith)]
    have shift : ∀ g r, U g r = g + U 0 (r - g) := by
      intro g r
      have := hL 0 (r - g) g
      simp only [zero_add, sub_add_cancel] at this
      rw [this]; ring
    refine ⟨U 0 1, ?_, ?_⟩
    · have := hR 0 1 one_pos; simpa using this
    · intro g r
      rw [shift g r]; unfold nudge dir
      by_cases h : g < r
      · simp [h, pos (r - g) (by linarith)]
      · by_cases h2 : r < g
        · simp [h, h2, neg (r - g) (by linarith)]
        · have : r = g := le_antisymm (not_lt.mp h) (not_lt.mp h2)
          simp [h, h2, this, zero]
  · rintro ⟨δ, hδ, hU⟩
    have hU' : U = nudge δ := funext fun g => funext fun r => hU g r
    subst hU'
    exact ⟨nudge_responsive hδ, nudge_typingProof δ, nudge_levelFree δ, nudge_neutral δ⟩

/-! ## Theorem 1(b) and Theorem 2: where nudges rest

A random answerer's wanted log-ratio (relative to consensus) has distribution
function `F`. At the current log-ratio `x`, the answer is "down" with
probability `M x` and "up" with probability `1 - M x`, so the expected move is
`step * (1 - 2 * M x)`. The split rests where this is zero. -/

def drift (step : ℝ) (M : ℝ → ℝ) (x : ℝ) : ℝ := step * (1 - 2 * M x)

theorem rest_iff_median {step : ℝ} (hs : 0 < step) (M : ℝ → ℝ) (x : ℝ) :
    drift step M x = 0 ↔ M x = 1 / 2 := by
  unfold drift
  constructor
  · intro h
    have := (mul_eq_zero.mp h).resolve_left (ne_of_gt hs)
    linarith
  · intro h; rw [h]; ring

/-- Answers from maintainers (a fraction `f`) want the log-ratio higher by `bias`. -/
def mixture (F : ℝ → ℝ) (f bias : ℝ) (x : ℝ) : ℝ := (1 - f) * F x + f * F (x - bias)

/-- **Theorem 2 / 5(b), recusal part.** With no maintainer answers (`f = 0`) the
rest point is the honest median, whatever the bias. -/
theorem recusal_rest {F : ℝ → ℝ} (hF : StrictMono F) (hmed : F 0 = 1 / 2)
    (bias x : ℝ) : mixture F 0 bias x = 1 / 2 ↔ x = 0 := by
  unfold mixture; simp only [sub_zero, one_mul, zero_mul, add_zero]
  constructor
  · intro h; rw [← hmed] at h; exact hF.injective h
  · intro h; rw [h, hmed]

/-- **Theorem 2 / 5(b), capture part.** If maintainers give a positive fraction of
the answers and want their project higher (`bias > 0`), then every rest point
lies above the honest median: the maintainers move it. -/
theorem capture {F : ℝ → ℝ} (hF : StrictMono F) (hmed : F 0 = 1 / 2)
    {f bias : ℝ} (hf : 0 < f) (hf1 : f ≤ 1) (hb : 0 < bias) (x : ℝ)
    (hx : mixture F f bias x = 1 / 2) : 0 < x := by
  by_contra hneg
  push_neg at hneg
  have h1 : F x ≤ 1 / 2 := by rw [← hmed]; exact hF.monotone hneg
  have h2 : F (x - bias) < 1 / 2 := by rw [← hmed]; exact hF (by linarith)
  unfold mixture at hx
  have : (1 - f) * F x + f * F (x - bias) < 1 / 2 := by
    have e1 : (1 - f) * F x ≤ (1 - f) * (1 / 2) := mul_le_mul_of_nonneg_left h1 (by linarith)
    have e2 : f * F (x - bias) < f * (1 / 2) := mul_lt_mul_of_pos_left h2 hf
    linarith
  linarith

/-- **Theorem 2 / 5(b), bound.** Maintainers never move the rest point beyond their bias. -/
theorem capture_lt_bias {F : ℝ → ℝ} (hF : StrictMono F) (hmed : F 0 = 1 / 2)
    {f bias : ℝ} (hf0 : 0 ≤ f) (hf1 : f < 1) (hb : 0 < bias) (x : ℝ)
    (hx : mixture F f bias x = 1 / 2) : x < bias := by
  by_contra h
  push_neg at h
  have h1 : 1 / 2 < F x := by rw [← hmed]; exact hF (by linarith)
  have h2 : 1 / 2 ≤ F (x - bias) := by rw [← hmed]; exact hF.monotone (by linarith)
  unfold mixture at hx
  have e1 : (1 - f) * (1 / 2) < (1 - f) * F x := mul_lt_mul_of_pos_left h1 (by linarith)
  have e2 : f * (1 / 2) ≤ f * F (x - bias) := mul_le_mul_of_nonneg_left h2 hf0
  linarith

/-- **Theorem 2 / 5(b), monotonicity.** More maintainer answers, a higher rest point. -/
theorem capture_mono {F : ℝ → ℝ} (hF : StrictMono F)
    {f f' bias : ℝ} (hf0 : 0 ≤ f) (hff : f < f') (hf1 : f' ≤ 1) (hb : 0 < bias) {x x' : ℝ}
    (hx : mixture F f bias x = 1 / 2) (hx' : mixture F f' bias x' = 1 / 2) : x < x' := by
  by_contra h
  push_neg at h
  unfold mixture at hx hx'
  have m1 : F x' ≤ F x := hF.monotone h
  have m2 : F (x' - bias) ≤ F (x - bias) := hF.monotone (by linarith)
  have d : F (x - bias) < F x := hF (by linarith)
  have e1 : (1 - f') * F x' ≤ (1 - f') * F x := mul_le_mul_of_nonneg_left m1 (by linarith)
  have e2 : f' * F (x' - bias) ≤ f' * F (x - bias) := mul_le_mul_of_nonneg_left m2 (by linarith)
  have e3 : (f' - f) * F (x - bias) < (f' - f) * F x := mul_lt_mul_of_pos_left d (by linarith)
  nlinarith

/-- **Theorem 1(b), belief exaggeration.** If wanted log-ratios are exaggerated by
`bel > 0`, the median is exaggerated by `bel`: the rest point moves from `m` to
`bel * m`. (`G` is the distribution function of the exaggerated values.) -/
theorem belief_scales {F : ℝ → ℝ} {m bel : ℝ} (hbel : 0 < bel) (hm : F m = 1 / 2) :
    (fun y => F (y / bel)) (bel * m) = 1 / 2 := by
  show F (bel * m / bel) = 1 / 2
  rw [mul_div_cancel_left₀ m (ne_of_gt hbel)]; exact hm

/-! ## Theorem 1(c): the agenda is not the verdict

Nudges descend the loss `∑ rate * φ (gap)`, where each `φ` is the expected
distance to the pair's wanted log-ratios. If one split attains every pair's
minimum, it minimizes the loss for every choice of nonnegative rates. -/

theorem agenda_free {ι : Type*} (pairs : Finset ι) (rate : ι → ℝ) (hrate : ∀ p, 0 ≤ rate p)
    {X : Type*} (gap : ι → X → ℝ) (φ : ι → ℝ → ℝ) (xstar : X)
    (hmin : ∀ p y, φ p (gap p xstar) ≤ φ p y) (x : X) :
    ∑ p ∈ pairs, rate p * φ p (gap p xstar) ≤ ∑ p ∈ pairs, rate p * φ p (gap p x) :=
  sum_le_sum fun p _ => mul_le_mul_of_nonneg_left (hmin p _) (hrate p)

/-! ## Theorem 3, the optimization step: the best step

Mean-square error of nudges (small steps): `(q*step^2 + vol^2) / (4*q*step*dens)`.
Its minimum over `step > 0` is at `step = vol / sqrt q`. -/

def mse (q vol dens step : ℝ) : ℝ := (q * step ^ 2 + vol ^ 2) / (4 * q * step * dens)

theorem best_step {q vol dens : ℝ} (hq : 0 < q) (hv : 0 < vol) (hd : 0 < dens)
    {step : ℝ} (hs : 0 < step) :
    mse q vol dens (vol / Real.sqrt q) ≤ mse q vol dens step := by
  unfold mse
  have hsq : 0 < Real.sqrt q := Real.sqrt_pos.mpr hq
  have hsq2 : Real.sqrt q ^ 2 = q := Real.sq_sqrt hq.le
  rw [div_le_div_iff₀ (by positivity) (by positivity)]
  -- after clearing denominators the claim is AM-GM: q step^2 + vol^2 ≥ 2 sqrt q vol step
  have key : 0 ≤ (Real.sqrt q * step - vol) ^ 2 := sq_nonneg _
  have e : q * (vol / Real.sqrt q) ^ 2 + vol ^ 2 = 2 * vol ^ 2 := by
    rw [div_pow, hsq2]; field_simp; ring
  rw [e]
  have : 2 * vol ^ 2 * (4 * q * step * dens) * Real.sqrt q
      ≤ (q * step ^ 2 + vol ^ 2) * (4 * q * dens * vol) := by
    have h3 : q * step ^ 2 + vol ^ 2 - 2 * Real.sqrt q * vol * step = (Real.sqrt q * step - vol) ^ 2 := by
      nlinarith [hsq2]
    have h4 : 2 * Real.sqrt q * vol * step ≤ q * step ^ 2 + vol ^ 2 := by nlinarith [key, h3]
    have hpos : 0 < 4 * q * dens * vol := by positivity
    calc 2 * vol ^ 2 * (4 * q * step * dens) * Real.sqrt q
        = (2 * Real.sqrt q * vol * step) * (4 * q * dens * vol) := by ring
      _ ≤ (q * step ^ 2 + vol ^ 2) * (4 * q * dens * vol) :=
          mul_le_mul_of_nonneg_right h4 hpos.le
  calc 2 * vol ^ 2 * (4 * q * step * dens)
      = 2 * vol ^ 2 * (4 * q * step * dens) * Real.sqrt q / Real.sqrt q := by field_simp
    _ ≤ (q * step ^ 2 + vol ^ 2) * (4 * q * dens * vol) / Real.sqrt q :=
        div_le_div_of_nonneg_right this hsq.le
    _ = (q * step ^ 2 + vol ^ 2) * (4 * q * (vol / Real.sqrt q) * dens) := by field_simp

/-! ## Theorem 4: when flags find problems sooner

With `m` projects and uniform random pairs, a question involves a given project
with probability `2 / m`; at `A` answers a day, the first question about it comes
after `m / (2A)` days on average. With flags, after `1 / notice` days. -/

theorem pair_prob {m : ℕ} (hm : 2 ≤ m) :
    ((m - 1 : ℕ) : ℝ) / ((m.choose 2 : ℕ) : ℝ) = 2 / m := by
  have hm' : (2 : ℝ) ≤ m := by exact_mod_cast hm
  rw [Nat.choose_two_right, Nat.cast_div (by
      rcases Nat.even_mul_pred_self m with ⟨k, hk⟩; exact ⟨k, by omega⟩) (by norm_num)]
  rw [Nat.cast_mul, Nat.cast_sub (by omega)]
  push_cast
  have h1 : (m : ℝ) - 1 ≠ 0 := by linarith
  have h2 : (m : ℝ) ≠ 0 := by linarith
  field_simp

theorem flags_sooner {m A notice : ℝ} (hm : 0 < m) (hA : 0 < A) (hn : 0 < notice) :
    1 / notice < m / (2 * A) ↔ A < m * notice / 2 := by
  rw [div_lt_div_iff₀ hn (by positivity), lt_div_iff₀ (by norm_num : (0:ℝ) < 2)]
  constructor <;> intro h <;> nlinarith

/-! ## Theorem 7: the value of one question

A project's log error is `e ≥ step`. The answer says "less" with probability `p`
(= `F e`, the chance the answerer wants less than the current amount) and "more"
with probability `1 - p`. The expected absolute error after one nudge is
`e - step * (2p - 1)`: the gain is `step * (2p - 1)`, larger for larger errors. -/

theorem one_question_gain {e step p : ℝ} (hs : 0 ≤ step) (he : step ≤ e) :
    p * |e - step| + (1 - p) * |e + step| = |e| - step * (2 * p - 1) := by
  rw [abs_of_nonneg (by linarith : 0 ≤ e - step), abs_of_nonneg (by linarith : 0 ≤ e + step),
    abs_of_nonneg (by linarith : 0 ≤ e)]
  ring

theorem gain_monotone {step p p' : ℝ} (hs : 0 ≤ step) (hp : p ≤ p') :
    step * (2 * p - 1) ≤ step * (2 * p' - 1) :=
  mul_le_mul_of_nonneg_left (by linarith) hs

/-! ## Theorem 6, the optimization step: where to spend attention

Project `j` is asked about at rate `q j = u j ^ 4`; its error costs `c j / u j`
(= `c j * q j ^ (-1/4)`, Theorem 3). For a fixed total `∑ q`, the cost is smallest
when `c j` is proportional to `v j ^ 5`, i.e. `q j` proportional to `c j ^ (4/5)`. -/

lemma tangent {u v : ℝ} (hu : 0 < u) (hv : 0 < v) : 5 * v ^ 4 * u - u ^ 5 ≤ 4 * v ^ 5 := by
  nlinarith [sq_nonneg (u - v), mul_pos hu hv, pow_pos hu 2, pow_pos hv 2, pow_pos hu 3, pow_pos hv 3,
    mul_nonneg (sq_nonneg (u - v)) (by positivity : (0:ℝ) ≤ u ^ 3 + 2 * u ^ 2 * v + 3 * u * v ^ 2 + 4 * v ^ 3)]

theorem best_allocation {ι : Type*} (s : Finset ι) (c u v : ι → ℝ) {lam : ℝ} (hlam : 0 < lam)
    (hu : ∀ j, 0 < u j) (hv : ∀ j, 0 < v j) (hopt : ∀ j, c j = 4 * lam * v j ^ 5)
    (hsum : ∑ j ∈ s, u j ^ 4 = ∑ j ∈ s, v j ^ 4) :
    ∑ j ∈ s, c j / v j ≤ ∑ j ∈ s, c j / u j := by
  have term : ∀ j, c j / v j - lam * (u j ^ 4 - v j ^ 4) ≤ c j / u j := by
    intro j
    have hu' := hu j
    have hv' := hv j
    have h1 := tangent hu' hv'
    rw [hopt j]
    have e : 4 * lam * v j ^ 5 / v j = 4 * lam * v j ^ 4 := by
      rw [div_eq_iff hv'.ne']; ring
    rw [e, le_div_iff₀ hu']
    nlinarith [mul_le_mul_of_nonneg_left h1 hlam.le]
  have := sum_le_sum fun j (_ : j ∈ s) => term j
  rw [sum_sub_distrib, ← mul_sum, sum_sub_distrib, hsum, sub_self, mul_zero, sub_zero] at this
  exact this

end Steer
