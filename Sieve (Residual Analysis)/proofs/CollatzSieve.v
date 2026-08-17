(* ========================================================================= *)
(*  CollatzSieve.v                                                           *)
(*                                                                           *)
(*  A machine-checked correctness proof of the Terras residue sieve          *)
(*  implemented in Residual_Analysis.py.                                     *)
(*                                                                           *)
(*      https://github.com/RobinCodes/Collatz                                *)
(*                                                                           *)
(*  Verified with the Rocq Prover.                                           *)
(* ========================================================================= *)

From Stdlib Require Import NArith.
From Stdlib Require Import PeanoNat.
From Stdlib Require Import Lia.
From Stdlib Require Import List.
From Stdlib Require Import Bool.
Import ListNotations.

Local Open Scope N_scope.

(* ========================================================================= *)
(* 0.  Powers of two                                                          *)
(* ========================================================================= *)

Definition pow2 (k : nat) : N := 2 ^ N.of_nat k.

Lemma pow2_O : pow2 0 = 1.
Proof. reflexivity. Qed.

Lemma pow2_S : forall k, pow2 (S k) = 2 * pow2 k.
Proof.
  intros k. unfold pow2.
  rewrite Nat2N.inj_succ, N.pow_succ_r by lia. reflexivity.
Qed.

Lemma pow2_pos : forall k, 0 < pow2 k.
Proof.
  intros k. unfold pow2.
  assert (2 ^ N.of_nat k <> 0) by (apply N.pow_nonzero; lia). lia.
Qed.

Lemma pow2_nz : forall k, pow2 k <> 0.
Proof. intros k. pose proof (pow2_pos k). lia. Qed.

Lemma pow2_even : forall k, (1 <= k)%nat -> N.even (pow2 k) = true.
Proof.
  intros k Hk. destruct k as [|k']; [lia|].
  rewrite pow2_S. apply N.even_spec. exists (pow2 k'). reflexivity.
Qed.

Lemma pow2_dvd_mono : forall a b, (a <= b)%nat -> (pow2 a | pow2 b).
Proof.
  intros a b Hab. exists (pow2 (b - a)). unfold pow2.
  rewrite <- N.pow_add_r. f_equal. lia.
Qed.

(* ========================================================================= *)
(* 1.  The accelerated Collatz map  T                                         *)
(*                                                                            *)
(*        T n = n / 2          if n is even                                   *)
(*        T n = (3n + 1) / 2   if n is odd                                    *)
(*                                                                            *)
(*  Each application of T performs exactly one division by 2, which is why    *)
(*  the Python program's "score" (total accumulated 2-adic valuation) is      *)
(*  precisely the number of T-steps taken.                                    *)
(* ========================================================================= *)

Definition T (n : N) : N := if N.even n then n / 2 else (3 * n + 1) / 2.

Fixpoint Tp (k : nat) (n : N) : N :=
  match k with
  | O    => n
  | S k' => T (Tp k' n)
  end.

Lemma Tp_add : forall a b n, Tp (a + b) n = Tp a (Tp b n).
Proof.
  induction a as [|a IH]; intros b n; simpl; [reflexivity|].
  rewrite IH. reflexivity.
Qed.

(* --- small arithmetic helpers ------------------------------------------- *)

Lemma even_half : forall x, N.even x = true -> 2 * (x / 2) = x.
Proof.
  intros x Hx. apply N.even_spec in Hx. destruct Hx as [m ->].
  rewrite (N.mul_comm 2 m), N.div_mul by lia. lia.
Qed.

Lemma three_plus_one_even : forall m, N.odd m = true -> N.even (3 * m + 1) = true.
Proof.
  intros m Hm. apply N.odd_spec in Hm. destruct Hm as [p ->].
  apply N.even_spec. exists (3 * p + 2). lia.
Qed.

Lemma odd_add_even2 : forall m x, N.odd (m + 2 * x) = N.odd m.
Proof.
  intros m x. rewrite N.odd_add, N.odd_mul.
  replace (N.odd 2) with false by reflexivity.
  rewrite andb_false_l, xorb_false_r. reflexivity.
Qed.

Lemma even_add_even2 : forall m x, N.even (m + 2 * x) = N.even m.
Proof.
  intros m x. rewrite <- !N.negb_odd, odd_add_even2. reflexivity.
Qed.

Lemma odd_not_even : forall n, N.odd n = true -> N.even n = false.
Proof.
  intros n Hn. rewrite <- N.negb_odd, Hn. reflexivity.
Qed.

Lemma not_even_odd : forall n, N.even n = false -> N.odd n = true.
Proof.
  intros n Hn. rewrite <- N.negb_even, Hn. reflexivity.
Qed.

Lemma T_even : forall n, N.even n = true -> T n = n / 2.
Proof. intros n Hn. unfold T. rewrite Hn. reflexivity. Qed.

Lemma T_odd : forall n, N.odd n = true -> T n = (3 * n + 1) / 2.
Proof. intros n Hn. unfold T. rewrite (odd_not_even _ Hn). reflexivity. Qed.

(* --- positivity ---------------------------------------------------------- *)

Lemma T_pos : forall n, n <> 0 -> T n <> 0.
Proof.
  intros n Hn. unfold T. destruct (N.even n) eqn:He.
  - apply N.even_spec in He. destruct He as [m Hm]. subst n.
    rewrite (N.mul_comm 2 m), N.div_mul by lia. lia.
  - assert (Hge : 0 < 2 <= 3 * n + 1) by lia.
    pose proof (N.div_str_pos _ _ Hge). lia.
Qed.

Lemma Tp_pos : forall k n, n <> 0 -> Tp k n <> 0.
Proof.
  induction k as [|k IH]; intros n Hn; simpl; [assumption|].
  apply T_pos, IH, Hn.
Qed.

(* ========================================================================= *)
(* 2.  The affine decomposition                                               *)
(*                                                                            *)
(*        2^k * T^k(n) = A_k(n) * n + C_k(n)                                  *)
(*                                                                            *)
(*  where A_k(n) = 3^(number of odd steps) and C_k(n) >= 0.                   *)
(* ========================================================================= *)

Fixpoint AC (k : nat) (n : N) : N * N :=
  match k with
  | O    => (1, 0)
  | S k' =>
      let (A, c) := AC k' n in
      if N.even (Tp k' n) then (A, c) else (3 * A, 3 * c + pow2 k')
  end.

Definition Acoef (k : nat) (n : N) : N := fst (AC k n).
Definition Ccoef (k : nat) (n : N) : N := snd (AC k n).

Lemma AC_pair : forall k n, AC k n = (Acoef k n, Ccoef k n).
Proof.
  intros k n. unfold Acoef, Ccoef. destruct (AC k n). reflexivity.
Qed.

(* Recursion equations.  Everything below uses these; [AC] is never unfolded
   again, which keeps the proofs stable under [simpl]/[cbn]. *)

Lemma Acoef_O : forall n, Acoef 0 n = 1.
Proof. reflexivity. Qed.

Lemma Ccoef_O : forall n, Ccoef 0 n = 0.
Proof. reflexivity. Qed.

Lemma AC_S : forall k n,
  AC (S k) n = if N.even (Tp k n)
               then (Acoef k n, Ccoef k n)
               else (3 * Acoef k n, 3 * Ccoef k n + pow2 k).
Proof.
  intros k n. unfold Acoef, Ccoef. cbn [AC].
  destruct (AC k n) as [A c]. reflexivity.
Qed.

Lemma Acoef_S : forall k n,
  Acoef (S k) n = if N.even (Tp k n) then Acoef k n else 3 * Acoef k n.
Proof.
  intros k n. unfold Acoef at 1. rewrite AC_S.
  destruct (N.even (Tp k n)); reflexivity.
Qed.

Lemma Ccoef_S : forall k n,
  Ccoef (S k) n = if N.even (Tp k n) then Ccoef k n else 3 * Ccoef k n + pow2 k.
Proof.
  intros k n. unfold Ccoef at 1. rewrite AC_S.
  destruct (N.even (Tp k n)); reflexivity.
Qed.

Lemma A_odd : forall k n, N.odd (Acoef k n) = true.
Proof.
  induction k as [|k IH]; intros n.
  - rewrite Acoef_O. reflexivity.
  - rewrite Acoef_S. destruct (N.even (Tp k n)).
    + apply IH.
    + rewrite N.odd_mul, IH. reflexivity.
Qed.

Lemma A_pos : forall k n, 1 <= Acoef k n.
Proof.
  intros k n. pose proof (A_odd k n) as H.
  destruct (Acoef k n) eqn:E; [discriminate|lia].
Qed.

(** The central affine identity. *)
Theorem affine : forall k n, pow2 k * Tp k n = Acoef k n * n + Ccoef k n.
Proof.
  induction k as [|k IH]; intros n.
  - rewrite pow2_O, Acoef_O, Ccoef_O. cbn [Tp]. lia.
  - specialize (IH n).
    cbn [Tp]. rewrite Acoef_S, Ccoef_S, pow2_S.
    destruct (N.even (Tp k n)) eqn:Hm.
    + rewrite (T_even (Tp k n)) by exact Hm.
      replace (2 * pow2 k * (Tp k n / 2)) with (pow2 k * (2 * (Tp k n / 2))) by lia.
      rewrite (even_half (Tp k n) Hm). exact IH.
    + assert (Ho : N.odd (Tp k n) = true) by (apply not_even_odd; exact Hm).
      rewrite (T_odd (Tp k n)) by exact Ho.
      replace (2 * pow2 k * ((3 * Tp k n + 1) / 2))
        with (pow2 k * (2 * ((3 * Tp k n + 1) / 2))) by lia.
      rewrite (even_half _ (three_plus_one_even _ Ho)).
      replace (pow2 k * (3 * Tp k n + 1)) with (3 * (pow2 k * Tp k n) + pow2 k) by lia.
      rewrite IH. lia.
Qed.

(* ========================================================================= *)
(* 3.  The shift lemma                                                        *)
(*                                                                            *)
(*  Terras' theorem in constructive form: the first k steps of T depend only  *)
(*  on n mod 2^k, and moving n by one full period 2^k moves T^k(n) by exactly *)
(*  A_k(n).                                                                   *)
(* ========================================================================= *)

Theorem shift : forall k n j,
  Tp k (n + j * pow2 k) = Tp k n + Acoef k n * j
  /\ AC k (n + j * pow2 k) = AC k n.
Proof.
  induction k as [|k IH]; intros n j.
  - cbn [Tp]. rewrite pow2_O, Acoef_O.
    split; [lia | reflexivity].
  - rewrite pow2_S.
    replace (n + j * (2 * pow2 k)) with (n + 2 * j * pow2 k) by lia.
    destruct (IH n (2 * j)) as [Ht Hac].
    remember (n + 2 * j * pow2 k) as n' eqn:Hn'.
    assert (Hm' : Tp k n' = Tp k n + 2 * (Acoef k n * j)) by (rewrite Ht; lia).
    assert (HeqE : N.even (Tp k n') = N.even (Tp k n))
      by (rewrite Hm'; apply even_add_even2).
    assert (HAC : AC (S k) n' = AC (S k) n).
    { rewrite !AC_S, HeqE. unfold Acoef, Ccoef. rewrite Hac. reflexivity. }
    split; [| exact HAC].
    cbn [Tp]. rewrite Hm', Acoef_S.
    destruct (N.even (Tp k n)) eqn:Hm.
    + rewrite (T_even (Tp k n + 2 * (Acoef k n * j)))
        by (rewrite even_add_even2; exact Hm).
      rewrite (T_even (Tp k n)) by exact Hm.
      replace (Tp k n + 2 * (Acoef k n * j))
        with (Tp k n + Acoef k n * j * 2) by lia.
      rewrite N.div_add by lia. reflexivity.
    + assert (Ho : N.odd (Tp k n) = true) by (apply not_even_odd; exact Hm).
      rewrite (T_odd (Tp k n + 2 * (Acoef k n * j)))
        by (rewrite odd_add_even2; exact Ho).
      rewrite (T_odd (Tp k n)) by exact Ho.
      replace (3 * (Tp k n + 2 * (Acoef k n * j)) + 1)
        with ((3 * Tp k n + 1) + 3 * (Acoef k n * j) * 2) by lia.
      rewrite N.div_add by lia. lia.
Qed.

Corollary shift_val : forall k n j,
  Tp k (n + j * pow2 k) = Tp k n + Acoef k n * j.
Proof. intros k n j. apply (shift k n j). Qed.

(* ========================================================================= *)
(* 4.  Descent: soundness of testing the least representative                 *)
(* ========================================================================= *)

(** If the least representative does not increase, the multiplier is small. *)
Lemma A_lt_pow2 : forall k r,
  1 <= r -> (1 <= k)%nat -> Tp k r <= r -> Acoef k r < pow2 k.
Proof.
  intros k r Hr Hk Hle.
  pose proof (affine k r) as Haff.
  assert (Hmul : pow2 k * Tp k r <= pow2 k * r)
    by (apply N.mul_le_mono_l; assumption).
  rewrite Haff in Hmul.
  assert (Hc : 0 <= Ccoef k r) by lia.
  assert (Hle2 : Acoef k r * r <= pow2 k * r) by lia.
  assert (HA : Acoef k r <= pow2 k).
  { apply N.mul_le_mono_pos_r with (p := r); [lia | lia]. }
  assert (Hne : Acoef k r <> pow2 k).
  { intros Heq.
    pose proof (A_odd k r) as Hodd.
    pose proof (pow2_even k Hk) as Heven.
    rewrite Heq in Hodd. rewrite <- N.negb_even, Heven in Hodd. discriminate. }
  lia.
Qed.

(** Every member of a non-increasing class strictly descends. *)
Theorem descent : forall k r j,
  1 <= r -> (1 <= k)%nat -> Tp k r <= r ->
  (Tp k r < r \/ 1 <= j) ->
  Tp k (r + j * pow2 k) < r + j * pow2 k.
Proof.
  intros k r j Hr Hk Hle Hstrict.
  pose proof (A_lt_pow2 k r Hr Hk Hle) as HA.
  rewrite shift_val.
  destruct Hstrict as [Hs | Hj].
  - assert (Acoef k r * j <= pow2 k * j) by (apply N.mul_le_mono_r; lia).
    lia.
  - assert (Acoef k r * j < pow2 k * j).
    { apply N.mul_lt_mono_pos_r; lia. }
    lia.
Qed.

(* ========================================================================= *)
(* 5.  Reaching 1, and the minimal-counterexample argument                    *)
(* ========================================================================= *)

Definition reaches1 (n : N) : Prop := exists k, Tp k n = 1.

Lemma reaches1_pull : forall k n, reaches1 (Tp k n) -> reaches1 n.
Proof.
  intros k n [j Hj]. exists (j + k)%nat. rewrite Tp_add. exact Hj.
Qed.

(** A class that the sieve discards contains no minimal counterexample. *)
Theorem no_minimal_counterexample : forall k r j,
  1 <= r -> (1 <= k)%nat -> Tp k r <= r ->
  (Tp k r < r \/ 1 <= j) ->
  (forall m, 1 <= m -> m < r + j * pow2 k -> reaches1 m) ->
  reaches1 (r + j * pow2 k).
Proof.
  intros k r j Hr Hk Hle Hstrict Hmin.
  set (n := r + j * pow2 k) in *.
  assert (Hn : 1 <= n) by (unfold n; lia).
  assert (Hlt : Tp k n < n) by (apply descent; assumption).
  assert (Hnz : Tp k n <> 0) by (apply Tp_pos; lia).
  apply reaches1_pull with (k := k).
  apply Hmin; lia.
Qed.

(* ========================================================================= *)
(* 6.  The implementation: 2-adic valuation and the truncated shift loop      *)
(*                                                                            *)
(*  Python:                                                                   *)
(*      y  = 3*n + 1                                                          *)
(*      v2 = (y & -y).bit_length() - 1                                        *)
(*      d  = min(v2, q - score)                                               *)
(*      n  = y >> d ; score += d                                              *)
(* ========================================================================= *)

Fixpoint v2p (p : positive) : nat :=
  match p with
  | xO q => S (v2p q)
  | _    => O
  end.

Definition v2 (y : N) : nat :=
  match y with N0 => O | Npos p => v2p p end.

Lemma v2p_spec : forall p,
  exists m, N.odd m = true /\ Npos p = pow2 (v2p p) * m.
Proof.
  induction p as [p IH|p IH|].
  - exists (Npos (xI p)). split; [reflexivity|].
    cbn [v2p]. rewrite pow2_O. lia.
  - destruct IH as [m [Hm Heq]].
    exists m. split; [assumption|].
    replace (Npos (xO p)) with (2 * Npos p) by reflexivity.
    cbn [v2p]. rewrite pow2_S, Heq. lia.
  - exists 1. split; [reflexivity|].
    cbn [v2p]. rewrite pow2_O. lia.
Qed.

Lemma v2_spec : forall y, y <> 0 ->
  exists m, N.odd m = true /\ y = pow2 (v2 y) * m.
Proof.
  intros [|p] Hy; [lia|]. apply v2p_spec.
Qed.

Lemma v2_dvd : forall y, y <> 0 -> (pow2 (v2 y) | y).
Proof.
  intros y Hy. destruct (v2_spec y Hy) as [m [_ Heq]].
  exists m. lia.
Qed.

Lemma v2_quot_odd : forall y, y <> 0 -> N.odd (y / pow2 (v2 y)) = true.
Proof.
  intros y Hy. destruct (v2_spec y Hy) as [m [Hm Heq]].
  rewrite Heq at 1.
  rewrite (N.mul_comm (pow2 (v2 y)) m), N.div_mul by apply pow2_nz. exact Hm.
Qed.

Lemma v2_ge1 : forall y, y <> 0 -> N.even y = true -> (1 <= v2 y)%nat.
Proof.
  intros [|p] Hy He; [lia|].
  destruct p as [p|p|]; simpl; try lia.
  - discriminate He.
  - discriminate He.
Qed.

(** Chained halving: for odd m, dividing 3m+1 by 2^d realises exactly d
    steps of T, provided 2^d actually divides 3m+1. *)
Lemma step_chain : forall d m,
  N.odd m = true -> (pow2 (S d) | 3 * m + 1) ->
  Tp (S d) m = (3 * m + 1) / pow2 (S d).
Proof.
  induction d as [|d IH]; intros m Hm Hdvd.
  - simpl. rewrite T_odd by assumption. rewrite pow2_S, pow2_O. reflexivity.
  - assert (Hdvd' : (pow2 (S d) | 3 * m + 1)).
    { eapply N.divide_trans; [| exact Hdvd]. apply pow2_dvd_mono. lia. }
    specialize (IH m Hm Hdvd').
    change (Tp (S (S d)) m) with (T (Tp (S d) m)). rewrite IH.
    destruct Hdvd as [t Ht].
    assert (Hx : (3 * m + 1) / pow2 (S d) = 2 * t).
    { rewrite Ht, (pow2_S (S d)).
      replace (t * (2 * pow2 (S d))) with ((2 * t) * pow2 (S d)) by lia.
      rewrite N.div_mul by apply pow2_nz. reflexivity. }
    rewrite Hx.
    assert (Heven : N.even (2 * t) = true)
      by (apply N.even_spec; exists t; reflexivity).
    rewrite T_even by exact Heven.
    rewrite (N.mul_comm 2 t), N.div_mul by lia.
    rewrite Ht, N.div_mul by apply pow2_nz. reflexivity.
Qed.

(** The Python inner loop, with an explicit structural fuel argument.        *)
Fixpoint sim_aux (fuel rem : nat) (n : N) : N :=
  match fuel with
  | O    => n
  | S f  =>
      match rem with
      | O   => n
      | S _ =>
          let y := 3 * n + 1 in
          let d := Nat.min (v2 y) rem in
          sim_aux f (rem - d) (y / pow2 d)
      end
  end.

Definition sim (q : nat) (n : N) : N := sim_aux q q n.

(* Controlled unfolding: [simpl] would inline the let-bindings and the binary
   representation of [3*n+1], so we use explicit equations instead. *)

Lemma sim_aux_rem0 : forall f x, sim_aux f 0 x = x.
Proof. intros [|f] x; reflexivity. Qed.

Lemma sim_aux_S : forall f r n,
  sim_aux (S f) (S r) n =
    sim_aux f (S r - Nat.min (v2 (3 * n + 1)) (S r))
              ((3 * n + 1) / pow2 (Nat.min (v2 (3 * n + 1)) (S r))).
Proof. reflexivity. Qed.

Lemma sim_aux_correct : forall fuel rem n,
  (rem <= fuel)%nat -> N.odd n = true -> sim_aux fuel rem n = Tp rem n.
Proof.
  induction fuel as [|f IH]; intros rem n Hle Hn.
  - assert (rem = O) by lia. subst. reflexivity.
  - destruct rem as [|r]; [reflexivity|].
    rewrite sim_aux_S.
    remember (3 * n + 1) as y eqn:Hy.
    remember (Nat.min (v2 y) (S r)) as d eqn:Hd.
    assert (Hyeven : N.even y = true)
      by (rewrite Hy; apply three_plus_one_even; assumption).
    assert (Hynz : y <> 0) by lia.
    assert (Hv : (1 <= v2 y)%nat) by (apply v2_ge1; assumption).
    assert (Hd1 : (1 <= d)%nat) by lia.
    assert (Hdv : (d <= v2 y)%nat) by lia.
    assert (Hdvd : (pow2 d | y)).
    { eapply N.divide_trans; [| apply v2_dvd; assumption].
      apply pow2_dvd_mono. exact Hdv. }
    assert (Hstep : y / pow2 d = Tp d n).
    { rewrite Hy in Hdvd |- *.
      destruct d as [|d']; [lia|].
      symmetry. apply step_chain; assumption. }
    rewrite Hstep.
    destruct (Nat.eq_dec d (S r)) as [Heq | Hne].
    + rewrite Heq, Nat.sub_diag, sim_aux_rem0. reflexivity.
    + assert (Hdlt : (d < S r)%nat) by lia.
      assert (Hdeq : d = v2 y) by lia.
      assert (Hodd : N.odd (Tp d n) = true).
      { rewrite <- Hstep, Hdeq. apply v2_quot_odd; assumption. }
      assert (Hrec : sim_aux f (S r - d) (Tp d n) = Tp (S r - d) (Tp d n))
        by (apply IH; [lia | exact Hodd]).
      rewrite Hrec, <- Tp_add. f_equal. lia.
Qed.

(** The bit-twiddling loop in Residual_Analysis.py computes exactly T^q. *)
Theorem sim_correct : forall q n, N.odd n = true -> sim q n = Tp q n.
Proof. intros q n Hn. apply sim_aux_correct; [lia | assumption]. Qed.

(** collatz_sim returns True exactly when T^q(n) > n. *)
Definition collatz_sim (q : nat) (n : N) : bool := n <? sim q n.

Theorem collatz_sim_correct : forall q n,
  N.odd n = true -> collatz_sim q n = (n <? Tp q n).
Proof. intros q n Hn. unfold collatz_sim. rewrite sim_correct; auto. Qed.

(* ========================================================================= *)
(* 7.  The sieve itself                                                       *)
(*                                                                            *)
(*  Rl k is the list relevant_residues at level q = k+1.                      *)
(* ========================================================================= *)

Definition survives (q : nat) (r : N) : bool := r <? Tp q r.

Fixpoint children (q : nat) (l : list N) : list N :=
  match l with
  | []      => []
  | y :: l' => y :: (y + pow2 q) :: children q l'
  end.

Fixpoint Rl (k : nat) : list N :=
  match k with
  | O    => [1]
  | S k' => children (S k') (filter (survives (S k')) (Rl k'))
  end.

Lemma in_children : forall q l x,
  In x (children q l) <-> exists y, In y l /\ (x = y \/ x = y + pow2 q).
Proof.
  intros q l x. induction l as [|a l IH]; simpl.
  - split; [contradiction | intros [y [[] _]]].
  - split.
    + intros [Ha | [Hb | Hin]].
      * exists a. auto.
      * exists a. auto.
      * apply IH in Hin. destruct Hin as [y [Hy Hx]]. exists y. auto.
    + intros [y [[Hy | Hy] Hx]].
      * subst y. destruct Hx; auto.
      * right; right. apply IH. exists y. auto.
Qed.

Lemma Rl_odd : forall k x, In x (Rl k) -> N.odd x = true.
Proof.
  induction k as [|k IH]; intros x Hin; simpl in Hin.
  - destruct Hin as [<- | []]. reflexivity.
  - apply in_children in Hin. destruct Hin as [y [Hy Hx]].
    apply filter_In in Hy. destruct Hy as [Hy _].
    specialize (IH y Hy).
    destruct Hx as [-> | ->]; [exact IH|].
    rewrite pow2_S, odd_add_even2. exact IH.
Qed.

Lemma Rl_range : forall k x, In x (Rl k) -> 1 <= x /\ x < pow2 (S k).
Proof.
  induction k as [|k IH]; intros x Hin; simpl in Hin.
  - destruct Hin as [<- | []]. rewrite pow2_S, pow2_O. lia.
  - apply in_children in Hin. destruct Hin as [y [Hy Hx]].
    apply filter_In in Hy. destruct Hy as [Hy _].
    specialize (IH y Hy). destruct Hx as [-> | ->].
    + rewrite (pow2_S (S k)). lia.
    + rewrite (pow2_S (S k)). pose proof (pow2_pos (S k)). lia.
Qed.

Lemma children_nodup : forall q l,
  NoDup l -> (forall x, In x l -> x < pow2 q) -> NoDup (children q l).
Proof.
  intros q l. induction l as [|a l IH]; intros Hnd Hb; simpl.
  - constructor.
  - inversion Hnd as [|z zs Hnin Hnd' Heq]; subst.
    assert (Ha : a < pow2 q) by (apply Hb; simpl; auto).
    assert (Hb' : forall x, In x l -> x < pow2 q) by (intros; apply Hb; simpl; auto).
    pose proof (pow2_pos q) as Hp.
    constructor.
    + simpl. intros [Hc | Hc].
      * lia.
      * apply in_children in Hc. destruct Hc as [y [Hy [Hz | Hz]]].
        -- subst y. contradiction.
        -- specialize (Hb' y Hy). lia.
    + constructor.
      * intros Hc. apply in_children in Hc. destruct Hc as [y [Hy [Hz | Hz]]].
        -- specialize (Hb' y Hy). lia.
        -- assert (a = y) by lia. subst y. contradiction.
      * apply IH; assumption.
Qed.

(** Distinctness: len(set(surviving_residues)) = len(surviving_residues). *)
Theorem Rl_nodup : forall k, NoDup (Rl k).
Proof.
  induction k as [|k IH]; simpl.
  - constructor; [intros [] | constructor].
  - apply children_nodup.
    + apply NoDup_filter, IH.
    + intros x Hx. apply filter_In in Hx. destruct Hx as [Hx _].
      exact (proj2 (Rl_range k x Hx)).
Qed.

(* ========================================================================= *)
(* 8.  Coverage: nothing is dropped without a descent certificate             *)
(* ========================================================================= *)

Theorem coverage : forall k n,
  1 <= n -> N.odd n = true ->
     (exists r j, In r (Rl k) /\ n = r + j * pow2 (S k))
  \/ (exists q r j, (1 <= q <= S k)%nat /\ In r (Rl (pred q))
                    /\ Tp q r <= r /\ n = r + j * pow2 q).
Proof.
  induction k as [|k IH]; intros n Hn Hodd.
  - left. apply N.odd_spec in Hodd. destruct Hodd as [p Hp].
    exists 1, p. split; [simpl; auto|]. rewrite pow2_S, pow2_O. lia.
  - destruct (IH n Hn Hodd) as [[r [j [Hr Heq]]] | [q [r [j [Hq Hrest]]]]].
    + destruct (survives (S k) r) eqn:Hs.
      * left.
        assert (Hin : In r (filter (survives (S k)) (Rl k)))
          by (apply filter_In; auto).
        destruct (N.Even_or_Odd j) as [[j' Hj'] | [j' Hj']].
        -- exists r, j'. split.
           ++ simpl. apply in_children. exists r. auto.
           ++ rewrite Heq, Hj', (pow2_S (S k)). lia.
        -- exists (r + pow2 (S k)), j'. split.
           ++ simpl. apply in_children. exists r. auto.
           ++ rewrite Heq, Hj', (pow2_S (S k)). lia.
      * right. exists (S k), r, j.
        unfold survives in Hs. apply N.ltb_ge in Hs.
        repeat split; try lia; simpl pred; assumption.
    + right. exists q, r, j. destruct Hq as [Hq1 Hq2].
      split; [lia | assumption].
Qed.

(* ========================================================================= *)
(* 9.  Main theorem                                                           *)
(* ========================================================================= *)

(** Soundness of the sieve.

    For every odd n >= 1, at least one of the following holds:

      (a) n's residue class is still present in relevant_residues -- the
          sieve has not made any claim about n; or
      (b) n reaches 1, given that every smaller positive integer does -- so
          n is not a minimal counterexample; or
      (c) n is a fixed point of T^q for some q <= k+1, i.e. n lies on a
          cycle.  These are exactly the values the program collects in its
          `cycles` list.

    Consequently, discarding a residue class never discards a potential
    minimal counterexample, except for genuine cycle elements, which are
    reported. *)
Theorem sieve_sound : forall k n,
  1 <= n -> N.odd n = true ->
  (forall m, 1 <= m -> m < n -> reaches1 m) ->
     (exists r j, In r (Rl k) /\ n = r + j * pow2 (S k))
  \/ reaches1 n
  \/ (exists q, (1 <= q <= S k)%nat /\ Tp q n = n).
Proof.
  intros k n Hn Hodd Hmin.
  destruct (coverage k n Hn Hodd) as [Hleft | [q [r [j [Hq [Hin [Hle Heq]]]]]]].
  - left. exact Hleft.
  - pose proof (Rl_range (pred q) r Hin) as [Hr1 _].
    destruct (N.eq_dec j 0) as [Hj0 | Hjn].
    + subst j. rewrite N.mul_0_l, N.add_0_r in Heq. subst r.
      destruct (N.le_gt_cases n (Tp q n)) as [Hge | Hlt].
      * right; right. exists q. split; [lia | lia].
      * right; left.
        apply reaches1_pull with (k := q).
        apply Hmin.
        -- assert (Tp q n <> 0) by (apply Tp_pos; lia). lia.
        -- lia.
    + right; left. subst n.
      apply no_minimal_counterexample; try assumption; try lia.
Qed.

(* ========================================================================= *)
(* 10.  The cycles list                                                       *)
(* ========================================================================= *)

Fixpoint cyc (k : nat) : list N :=
  match k with
  | O    => filter (fun r => Tp 1 r =? r) (Rl O)
  | S k' => cyc k' ++ filter (fun r => Tp (S (S k')) r =? r) (Rl (S k'))
  end.

Lemma cyc_mono : forall k m r,
  (m <= k)%nat -> In r (Rl m) -> Tp (S m) r = r -> In r (cyc k).
Proof.
  induction k as [|k IH]; intros m r Hmk Hin Hfix.
  - assert (m = O) by lia. subst m. cbn [cyc].
    apply filter_In. split; [assumption|]. apply N.eqb_eq. exact Hfix.
  - destruct (Nat.eq_dec m (S k)) as [-> | Hne].
    + cbn [cyc]. apply in_or_app. right.
      apply filter_In. split; [assumption|]. apply N.eqb_eq. exact Hfix.
    + cbn [cyc]. apply in_or_app. left. apply IH with (m := m); auto; lia.
Qed.

(** The exceptional case of [sieve_sound] is always reported in `cycles`. *)
Theorem cycles_complete : forall k n,
  1 <= n -> N.odd n = true ->
  (forall m, 1 <= m -> m < n -> reaches1 m) ->
     (exists r j, In r (Rl k) /\ n = r + j * pow2 (S k))
  \/ reaches1 n
  \/ In n (cyc k).
Proof.
  intros k n Hn Hodd Hmin.
  destruct (coverage k n Hn Hodd) as [Hleft | [q [r [j [Hq [Hin [Hle Heq]]]]]]].
  - left. exact Hleft.
  - pose proof (Rl_range (pred q) r Hin) as [Hr1 _].
    destruct (N.eq_dec j 0) as [Hj0 | Hjn].
    + subst j. rewrite N.mul_0_l, N.add_0_r in Heq. subst r.
      destruct (N.le_gt_cases n (Tp q n)) as [Hge | Hlt].
      * right; right.
        assert (Hfix : Tp q n = n) by lia.
        destruct q as [|q']; [lia|].
        apply cyc_mono with (m := q'); [lia | exact Hin | exact Hfix].
      * right; left.
        apply reaches1_pull with (k := q).
        apply Hmin.
        -- assert (Tp q n <> 0) by (apply Tp_pos; lia). lia.
        -- lia.
    + right; left. subst n.
      apply no_minimal_counterexample; try assumption; try lia.
Qed.

(* ========================================================================= *)
(* 11.  Sanity checks by computation                                          *)
(* ========================================================================= *)

Example Rl_0  : Rl 0 = [1].            Proof. reflexivity. Qed.
Example Rl_1  : Rl 1 = [1; 3].         Proof. reflexivity. Qed.
Example surv_1_1 : survives 1 1 = true.   Proof. reflexivity. Qed.
Example surv_2_1 : survives 2 1 = false.  Proof. reflexivity. Qed.
Example surv_2_3 : survives 2 3 = true.   Proof. reflexivity. Qed.
Example cycle_one : Tp 2 1 = 1.           Proof. reflexivity. Qed.
Example sim_matches : sim 4 3 = Tp 4 3.   Proof. reflexivity. Qed.
Example sim_4_3 : sim 4 3 = 2.            Proof. reflexivity. Qed.

(* Print Assumptions on the main results: must report "Closed under the
   global context", i.e. no axioms and no admitted proofs. *)
Print Assumptions affine.
Print Assumptions shift.
Print Assumptions descent.
Print Assumptions sim_correct.
Print Assumptions no_minimal_counterexample.
Print Assumptions sieve_sound.
Print Assumptions cycles_complete.
Print Assumptions Rl_nodup.
