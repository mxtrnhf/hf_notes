# hf_ai v0.3.0, first run in game (2026-10-18, 14:30-14:36)

Status: **runs without errors; the tactic overrides waypoints, but the user reports "nothing feels different".** Data: `tuning_telemetry/hf_ai_v030_first_run/` (5 fights: 1 Lightning in Shipworks, 4 Navarin in campaign, 2 with an ally). Config: tactics on (defaults, `blend_weight` 1.0, allies off), ported `ai_flares` on with `log_panic`, qol `ai_flares` off. Tags: [data] measured.

## What works [data]
* Loads clean: no "other bytes" lines; 3 permanent patches installed (steering + flare + boost sites); qol flare-crash fix site `0x36bb5` reported patched.
* Arena bounds read live: x -1500..1500, y min -2000. Live `accel_est` equals `twr*9.82` for every ship logged (Slogger/Courageous 61, Navarin 49-52, Nimrod 42, Intrepid-class 61-71), so the f32 reads of `+0x1664/+0x1668/+0x15b8` and the 35 gate are right.
* Steer CSV (3841 rows, 12 ship series): states far 1578, stock 1386 (gated out: landed/takeoff/heavy/no target), band 438, close 378, panic 61. Overrides (`chosen_x/y` set) on 815 rows = 21%, of which band 377, close 377, panic 61. The chosen waypoint differs from the stock one by a median 34 deg (p90 81 deg).
* **close (back out diagonally): works**: in the 1 s after, ships follow the chosen direction more than the stock one in 70% of the cases with a >45 deg difference (median cos 0.82 vs 0.47).
* **band (strafe): does not visibly work**: ships follow the stock direction more (58% of cases; median cos 0.78 stock vs 0.57 chosen). In-band rows are only ~12% of enemy rows (the enemies spend 45% of the time `far`).
* Ported ai_flares: `hf_ai_panic_*.log` shows START / EXTEND / END / STEER (4 panics in the first battle log, side +-1 sidestep, boost 1); the quote of the first threat: "missile link points at the ship itself (distance 399, category 0x4000)".

## Reading [guess until tested]
Strafe flips fail to show because (a) the blend with the stock direction at weight 1.0 is cancelled or dominated by the stock orbit (the known risk), (b) ships have inertia: at 60-70 u/s2 a reversal needs ~1 s, longer than the 2-5 s timer feels, and (c) the band is narrow (300-550 u for a reach-1500 ship, 200-400 u for reach 800) so only ~12% of the time is spent in it. Next knobs: `blend_weight` 2.0, longer reversal period (4-8 s), wider band, and a metric based on the player's hit rate rather than on motion.

## Fight notes
Lightning 42 s vs Courageous + Slogger, lost 100 hp, win. Navarin campaign: 84 s vs Flower, Nimrod, Navarin, Slogger lost 1192 hp / 15 parts (the user reports the ship died; result unknown in the log, flagship alive at the end, no ally); 33/17/19 s fights won with 120-300 hp lost. Too few and too varied to measure the tactic's effect on the player; the A/B comparison still has to be flown in the same setup.
