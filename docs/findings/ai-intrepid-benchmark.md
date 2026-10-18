# Stock INTREPID piloting benchmark and enemy behaviour (15 battles, 2026-10-18)

Status: **measured from hf_ally telemetry, nothing run on the AI yet.** Source data: `~/Development_Highfleet/tuning_telemetry/intrepid/` (15 sessions, 8.5 min of fighting; v0.12.8 / v0.12.9), full reports in `intrepid/report.md` (batch 1 + addendums), session ledger `tuning_telemetry/REVIEWED.tsv`. Player = expert user flying a stock INTREPID in Shipworks (2x 130mm guns, 2 missiles, no flares, 107 parts, 8250 hp). Design context: [ai-hf-ai-design.md](ai-hf-ai-design.md), telemetry format: [ai-telemetry.md](ai-telemetry.md). Tags: [data] measured, [guess].

## Player (expert) patterns [data]
* Speed p50 ~100, p90 ~200 u/s; boost held ~10% of the time in 0.4-0.7 s taps. Range to the nearest enemy p10/50/90 about 180/460/1250 u; while firing p50 about 200-270 u.
* Run in fast, nearly stop at 150-250 u and shoot, drift out; swing-out to 900-1300 u (1500-1900 u vs slow Gryphons); cycle 12-20 s, irregular. Motion vs nearest enemy: tangential ~33%, closing ~25%, stationary ~20%.
* LMB ~25-30% of the time, ~1 round/s, aim error while firing 2-3 deg median / 5-11 deg p90. RMB essentially never. Player shell hit proxy (70 u radius is a guess): <200 u ~85%, 200-400 ~70%, 400-700 ~50%, 700-1200 ~30%.
* Missiles: 2 per battle at ~1500 u; **0 of 8 hit flare carriers, 18 of 22 hit flare-less targets** (small n, strongest effect found).
* Dodging enemy missiles: peak lateral acceleration about 1 s (median 294 u) before the pass, heading change ~26-45 deg, boost in ~23% of the window. Enemy missiles hit only ~4-5% of real-course launches (4 hits in ~80 passes), so the dodge is not proven the cause.

## Enemies [data]
* Slow (p50 30-100 u/s, max ~190). Waypoint is always exactly 200 u from the ship. Radial speed toward the player: +45 u/s beyond 1000 u, +15 at 500-1000 u, -11 at 300-500 u, -19 inside 300 u; Gladiators keep closing to 300 u; Gryphons (29 u/s) park at 160-660 u. They drift tangentially 40-60 u/s, they do not spin.
* Missiles: launched at 870-1900 u (Paladin ~1360, Gladiator ~1600, Gryphon ~1500, MRL ~960), salvos of 1-3, 4-9 s apart (Gryphon 11-20 s); miss distance p50 ~80 u; speed ~250 u/s. Enemy flares go out when the player's missile is 290-365 u away.
* Shells: Gryphon is the main damage source (62% hit rate, fire range ~260 u); hit odds on the player: <200 u 97%, 200-400 40%, 400-700 28%, 700-1200 11%.
* Ammo: Gladiator 100mm <-> AP at 995-1006 u (the known stock rule); 180mm <-> PROXY switches show no clean range rule.
* Removed enemies still had 66-98% hp: the kill rule is not visible in the data.
* **qol missile dump:** 21 of ~100 enemy missiles die 0.7-1.9 s after launch within ~120 u of their launcher (Flower, Navarin, Paladin, Gladiator; Gryphon/MRL/Nimrod/Intrepid none); no predictor found; needs tuning.

## What cannot be learned from this data
Low-hp phase and break-off, finishing a fight, RMB/group-1 use, flares for the player, AP vs plain (confounded with target), and whether a dodge actually causes a miss.

## Suggested numbers for the hf_ai tactics (S = from data, G = guess)
kite: ~200 u while firing, swing out 900-1300 u every 10-20 s (S); missile boat: launch 900-1600 u, salvos of 2, 6-9 s apart (S); dodge: react at ~550 u (2.2 s) missile range, turn 45-90 deg off its track, tap boost ~0.4 s (S timing, G efficacy); flares: dump 2-6 per tick for ~1.5 s at <350 u (S, n small); fire missiles only at flare-less targets (S); enemy charge pace +45 u/s at long range (S).
