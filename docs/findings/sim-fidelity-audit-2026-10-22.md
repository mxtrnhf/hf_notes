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

## 6. sim.41 sessions (three flights 2026-10-22 11:48-11:53: Fenek, Gladiator, Kormoran), ship from the dump
* Loader: the dump was rejected by a part-count check that counted oid-less ANTENNA_PART markers; fixed (oid multiset is the check), and a rejected dump no longer falls back silently to a matched design (HFSIM_ALLOW_MATCH=1 allows it). The six sessions of sim_runs28/29 have no dump and were matched designs in the audit above.
* Kormoran 1792659121: landed at 265.7 s, the touchdown removed engines 84 and 147 (265.78, 266.0 s); trimmed to 264.8 s in sim/session_trims.json.
* Results (simmetrics, 3 sessions): 3 s windows median angle 0.10 deg (p90 5.0), velocity 0.16 u/s (p90 2.2); 40 logged lockouts, 2 missed, lateness median +0.00 s (p10 -0.04, p90 +0.08). Flagged 3 s windows: Fenek 8/17, Gladiator 7/40, Kormoran 3/24.
* **Slot graph, TS rows (sim.41): the game's conduction graph is the SAME as the sim's design-file graph** (Kormoran: 604 directed edges in both, 0 one-way). An earlier version of this analysis reported a quarter of the edges as one-way; that was a parsing bug (the entry count of the row was glued to the first occupant, dropping every body's first neighbour). The directed-graph hypothesis for the 0.8 onward-conduction fudge is therefore refuted; the cause of the fudge is still unknown. Decoded onward scale 1.0 is still worse than 0.8 (lateness +0.04 s, 3 of 40 missed).
* TO rows (body array order) are present (Kormoran: 20 dumps); not yet used by the thermal pass (reversing the order changed nothing earlier).

## 7. The fire suppression system resets the whole ship (found from the user's screenshot of the engine temperature chart)
* The cold engine (Kormoran 1792659121, part 84) cooled slower in the log than in the sim after each FSS use (224.72, 227.88, 234.84). The TT rows show why: its truss neighbour (part 83) is reset to 99 together with the engine and then tracks it (93.5 / 93.5, 86.2 / 86.5), while the sim truss stayed at about 28 and drained the engine.
* TA rows (every part, 1 Hz): after a use all 222 parts are at the same 97.4 (0.3 s after the reset from 100). The sim reset engines only. Notes said "engines within 30 u of the module"; in the Kormoran every body part is within 25 u of one of the 4 FSS modules (design frame), so this ship cannot tell a 30 u radius from "everything". **Radius and reset set are being looked up in the code (ghidra-curator); OL.seria has no radius** (MDL_FSS_02 has only m_mdl_fss_capacity = 1).
* Fix (sim/hfsim/flight.py extinguish): every part to 100. Before / after: Kormoran 1792659121 3-s p90 velocity error 4.0 -> 0.85 u/s, missed lockouts 2 -> 0, lateness median +0.04 -> +0.02 s; flagged 3-s windows 1792619777 7 -> 2 of 28, 1792613461 7 -> 2 of 36, 1792659121 3 -> 2 of 24. Provisional for big ships until the radius is known (HFSIM_EXT_ENGINES_ONLY=1 restores the old behaviour).
* Box2D world settings (ghidra-curator, box2d-world-settings-for-sim.md): 10/10 iterations, dt 0.02, gravity 9.82, damping 0.05/0.05, stock constants: the sim already matches; no hull-spin clamp or damping found in the game.

## 8. End of day 2026-10-22: what was fixed and where the sim stands (12 dump-based sessions, 990 one-second and 327 three-second windows)
Fixes (all in hf_ml/sim, commits on 2026-10-22): FSS rule (every part within 30 u of every module still in the creature's list, first module consumed per use, destroyed modules leave the list, state seeded at window start); heat: onward conduction back to the decoded 1.0, burn heat 1.0 (log 0.99, +0.2 over the decoded 0.8 unexplained); command ANGLE from the previous EA record and key state one tick earlier (the servo of tick k uses the command of record k with the angle of tick k; the sim reacted a tick early, a swing reversal made the engine lead by 0.23 rad); guns as separate b2 bodies (free_guns); log loader: per-step bank sums from the hook S rows for step-rate P rows; simdiff: verdicts fixed (tolerance counts as collapsed, worse-than-base injection is INCONCLUSIVE), end errors and a bias line per report; force-injection angle lag 2.
Checked and clean: the decoded one-tick engine heat equation reproduces the log to +-0.003 deg per tick on every engine (Kormoran and Lightning, close or far apart); the logged swivel obeys Frame change + 3 x wrap(cmd - angle) x dt to 0.01 rad per tick; swivel engine b2 mass / inertia / damping equal the game's; the logs have no ghost keys (99.7-99.9 % agreement of key bits and engine commands); dt is exactly 0.02 s on every logged step regardless of frame rate.
Result (re-seeded windows, median / p90): 1 s: angle 0.038 / 1.05 deg, velocity 0.040 / 0.91 u/s, position 0.033 / 0.55 u; 3 s: angle 0.098 / 3.4 deg, velocity 0.18 / 1.9 u/s, position 0.31 / 3.5 u, engine temperature 1.4 / 6.9 deg; lockouts: 140 logged, 1 missed, lateness median 0.00 s.
Flagged 3 s windows now (before the day): 1792619777 Kormoran 2/28 (7), 1792659121 Kormoran 2/24 (3), 1792661603 Kormoran 3/39 (4), 1792661896 Lightning 6/18 (11), 1792664811 12 engines 0/32, 1792664987 2/30, 1792665108 ENGINE_03 3/18, 1792658979 Gladiator 6/40 (7), 1792661776 Fenek 7/34 (11), 1792619889 Intrepid 14/31 (15), 1792620006 Fenek 14/26 (13), 1792658910 Fenek 10/17 (8).
Still open: the Fenek (2 x ENGINE_04) sessions: 3 s median angle error 3.3-3.5 deg and a consistent spin bias (1792620006: -0.022 rad/s); Intrepid 14/31; ENGINE_03 ship velocity error about 1.2 u/s per 3 s; W-only spin bias about -0.0008 rad/s per second after free_guns (legs still rigid); the +0.2 per tick burn term; open-loop drift in long runs (tens to hundreds of u).
