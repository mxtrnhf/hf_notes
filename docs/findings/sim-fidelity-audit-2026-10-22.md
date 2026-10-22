# Simulator fidelity audit, 2026-10-22

Scope: `hf_ml/sim` against nine logged battles (data/sim_runs28-30; Kormoran x2, Lightning x3, Gladiator, Wanderer, Intrepid, Fenek). Tools: `simdiff` (where does the sim leave the log, and which part is at fault), `simmetrics.py` (continuous errors, new). Mid-air only; windows within 120 u of the ground are skipped (see the sim-scope decision).
Tags: **[log]** measured on the logs, **[code]** from the game decompilation (ghidra-curator, player-thrust-keys-and-engine-heat.md sections 5-10), **[open]** not resolved.

## 1. Result in numbers
simdiff, 3 s windows re-seeded from the log: 91 of 292 windows off tolerance (31 %). Worst: Lightning 1792613596 22/41, Intrepid 15/31, Fenek 13/26. Kormoran 7/36 and 7/28, Wanderer 6/24, Gladiator 6/41, Lightning 4/34 and 11/31.
`simmetrics.py` (end-of-window error, medians; p90 in brackets), all sessions:

| window | angle deg | spin rad/s | velocity u/s | position u |
|---|---|---|---|---|
| 1 s (814 windows) | 0.08 (1.6) | 0.002 (0.05) | 0.09 (1.7) | 0.06 (1.1) |
| 3 s (269 windows) | 0.28 (6.6) | 0.002 (0.08) | 0.43 (5.4) | 0.61 (8.1) |

Engine lockout (trip) timing: 262 logged lock onsets, the sim reproduces 96 % within 1 s; lateness median +0.02 s (one tick), p10 -0.02 s, p90 +0.10 s (positive = sim late). Per session the median is +0.00 to +0.06 s. Missed onsets: 1792617339 has 6 of 12.
Open-loop 75-125 s drift is large (40-530 u, Intrepid 88 deg) but is a poor yardstick: it accumulates small window errors (1792619777: 351 u position with 3 u/s velocity error).
Verdict: good enough for calm mid-air movement of Kormoran-class ships; Lightning, Intrepid, Fenek and fast spins are not trustworthy yet. The remaining systematic risk is engine temperature just below 500: a policy can learn to ride the limit.

## 2. What flagged windows correlate with
* **Fast hull spin [log]:** windows with |w| > 2 rad/s: 29 of 44 flagged (66 %); calm windows: 62 of 248 (25 %). Fenek: 11 of 13 flagged windows are fast spin. In a 5-9 rad/s spin one tick is 0.1-0.2 rad of thrust direction, so tiny numerical differences grow.
* **Heat near the trip [log]:** Kormoran windows are engine HEAT. In 108 lock onsets (three sessions) the logged T is >= 500 on the tick before the lock appears (100 %, 500.0-502.8), the lock shows on the next tick and T then falls about 2.6 per tick. So the timing rule is right; the sim's engine temperature just before the trip is a few degrees low. An engine under steady thrust sits near an equilibrium (dose 1.4 + burn 0.8 against decay 0.8 + conduction), so a neighbour (truss) temperature error dT_n moves the engine by about 0.83 dT_n.
* **Lightning [open]:** unexplained hull-torque excess (about 9 % above rigid coupling, absorbed by `stab_share` 0.6, see hull-stabiliser-coupling.md); candidate: swivel-motor reaction torque on the Frame.

## 3. Checked and ruled out (do not repeat)
* **Float32 lock timer [log]:** the logged lock (+0x810) runs 149 ticks after its first sample (150 decrements: 3.0 - 150 x 0.02); this is the sim's double arithmetic. A float32 timer would take 151 ticks. Tried it: worse (+3 flagged), reverted.
* **Thermal step order [sim]:** reversing the order of Body_ThermalStep calls changes nothing in six sessions. Frame order (engine call with T of the previous frame, thermal pass, dose zeroed, Part_Tick lock decrement) is as in the sim [code, supported].
* **Onward conduction scale:** decoded 1.0 is worse than the fitted 0.8 (+3 flagged); the 0.8 hides an unknown cause [open].
* **Design tie (Lightning variants), hook coverage:** not the cause of the 617339 error.
* **Logs:** 50 Hz per tick, consistent lock/temperature traces; no sign of sampling problems. Missing: the game's slot-neighbour vector of non-engine bodies (the TT rows cover engines only; engine neighbours match the sim: one truss each).

## 4. Tool fixes made
* **diverge.py force injection:** the injected thrust angle is the logged swivel angle taken 2 ticks earlier (`ANGLE_LAG = 2`). With offset 0 the injected logged force was WORSE than the sim's own force in spin windows (617339: 17 -> 104, 65 -> 65); offsets -1..-4 all beat the base error. The classifier still says "NOT engine-side" for windows where only the mask / temperature ablation collapses the error (e.g. 617339 t 174.8-180.8: mask 7.0 / 10.9 against base 17 / 65): treat that label with care.
* **simmetrics.py:** new, see section 1. Use it for every A/B decision (flagged-window counts move by 1-3 windows on noise).
* Gladiator session 1792617546 (engines mapped 0/6, simdiff crash) deleted on the user's request.

## 5. Open items / next
1. sim.40 (`TO` rows: the game's body array order, in hf_ally_hook_<id>.csv) is installed in Modloader/mods (sim.39 in old_mod_backups); no session recorded with it yet. Then replay the logged order through the thermal pass.
2. Ask: log the slot-neighbour vector (+0x350) of every body at battle start, to replace the symmetric design-file graph and explain the 0.8 onward scale (truss about 80 in the game against 54 in the sim after an extinguisher use).
3. Power-satisfaction factor (+0x818, scales the servo speed as P squared): the logged power_f / power_i columns are constant per session except Intrepid; not enough to tell if Lightning / Intrepid / Fenek run short.
4. Lightning stabiliser excess; Intrepid 88 deg drift; Fenek fast-spin windows.
5. Rename of the .hftm files to battle_record_YYYY_MM_DD_HH-MM-SS.hftm requested from probe-dev; the sim loader must accept both names once built.
6. Logger SSD wear (probe-dev): negligible, about 610 KB/s of battle, 7.5 GB per 3 h, about 0.5 % of 600 TBW per year (write amplification inferred, not measured).
