# Piloting benchmark and enemy behaviour: stock INTREPID (15 battles) and Lightning (11 usable sessions), 2026-10-18

Status: **measured from hf_ally telemetry, nothing run on the AI yet.** Source data: `~/Development_Highfleet/tuning_telemetry/{intrepid,lightning}/` (15 INTREPID sessions, 8.5 min of fighting, v0.12.8 / v0.12.9; 11 Lightning sessions, v0.12.3-v0.12.7), full reports in `intrepid/report.md` and `lightning/report.md` (batch 1 + addendums), session ledger `tuning_telemetry/REVIEWED.tsv`. Player = expert user flying a stock INTREPID in Shipworks (2x 130mm guns, 2 missiles, no flares, 107 parts, 8250 hp). Design context: [ai-hf-ai-design.md](../findings/ai/ai-hf-ai-design.md), telemetry format: [ai-telemetry.md](../findings/ai/ai-telemetry.md). Tags: [data] measured, [guess].

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

## Lightning (fast glass cannon; 11 usable sessions, 1064 s, 10 Hz player row) [data]
Source: `tuning_telemetry/lightning/report.md`. Lightning: 2x CANNON_100_2, no missiles, no flares, 6510 hp. Compared with INTREPID:
* Speed p50/p90/max 148/263/421 u/s (INTREPID 105/206/255); boost ~10% of the time in 0.3-0.5 s taps (same). Range to nearest enemy 206/451/1155 u, while firing p50 306 u; min-range p50 239 u, swing-out p50 849 u (508-1534), max-to-max cycle 16 s (n=110). LMB 21%, ~1.3 rounds/s, RMB never. Aim error 3 / 11 deg (same as INTREPID).
* Enemies vs this fast target: radial speed -23 (<200 u), -13 (200-400), +15 (400-700), +54 (700-1200), +60 u/s (>1200): they back off inside ~400 u, never spin. They lead only partly (lead fraction median ~0.4-0.6, [guess], wide spread). Their shells hit 41% under 400 u, 14% at 400-700, 10% at 700-1200.
* **Enemies fire missiles point-blank at a fast target**: 19 of 90 launches under 500 u (as low as 211 u); INTREPID data never below ~870 u.
* Incoming missiles (90 = 45 salvos): every track ends at closest approach (60-180 u); only 1 salvo did clean damage (1339 hp, 4 Flower missiles). Pilot reaction in the 3 s before the pass (vs baseline): peak lateral accel 135 vs 86 u/s2, heading change 70 vs 43 deg, speed 192 vs 140, boost in 87% of windows vs 44%; peak accel ~1.1 s before the pass at ~414 u (INTREPID 1.0 s / 294 u). Correlation only.
* qol missile dump: 8 early deaths within 1.5 s of launch, mostly Kormoran and Sarma (new victim classes) at 76-113 u from the launcher.
* Damage: missiles ~8% of lost hp (up to ~35% counting ambiguous cascades; "27%" is unsupported). Near-death exists in one session only (39% raw hp); the pilot did not break off (kept closing, one 5 s move-away, re-engaged within 4-8 s). Two sessions lose 12 hp-100 items at a fixed world point near spawn plus other parts (not weapon damage; 16 parts left at once with no enemy within 1.7 km in 1792314721).
* Caveats: 10 Hz player row (acceleration window ~0.4 s, shell tracks 95 u steps), early builds lack hp/names/bodies, every session ends abruptly with no result marker.

## Navarin (campaign, 7 sessions = 6 battles, no ally) [data]
Source: `tuning_telemetry/navarin/report.md`. Four different Navarin hulls (75-96 parts, 5370-7310 hp, 2x 57mm; some with 2 missiles, 3 bombs, 180 flares). First campaign data; the 70 u shell-hit radius is a home-made guess.
* Guns: LMB only, fired from p50 250-750 u (wider than INTREPID); aim error 2-5 / 5-12 deg; bouts 2-6 s. Boost taps 0.5-0.9 s at 3-21%. Kite swing 500-1000 u, half-period 6-15 s.
* **Ground targets are enemy ships landed on their legs** (enemy `mode` 3, altitude 24-50 u above terrain, speed ~0; takeoff mode 3 -> 0 -> 1 takes ~2.5 s). **All 10 bomb drops were onto landed enemies; none onto an airborne ship**, even with bombs aboard and airborne enemies from t+0. Drops from altitude 210-1490 u at speed 140-251, no boost, no hard turn; 3-4 of 10 happened with an enemy missile within ~800 u, so bombing while dodging does occur. 9 of 10 landed within 19-33 u of a landed ship (2 one-shot removals at full hp). Landed enemies shoot back (13 missiles, 178 shells in 247 ship-seconds). n=10, one pilot.
* Missiles: 3 of 5 player missiles hit (all launched below ~1000 u). Flares: 3-5 pulses 0.3 s apart (6 bodies per pulse), first pulse at missile distance 190-680 u, in ~75% of salvos. Dodge: peak lateral accel ~77 u/s2 about 0.9 s / 440 u before the pass; 1 of 22 enemy missiles hit.
* Low hp: one case (session 716: 5410 -> 4143 hp while burning, crew 60 -> 15, speed fell to 34-50 u/s; the ship vanished at 43% hp: retreat/handover or destruction unknown). No break-off manoeuvre.
* New enemy classes: Kadesh Mk1 (14.6k hp, 3-6 missiles), Kastor (14.9k hp, 4 missiles), enemy Navarin (flares + missiles), landed-start fleets. The win flag fires with 1-2 enemies still alive.
* Telemetry gaps found: bomb release is invisible in `f2` (the byte clears within a frame), bomb owner_id -1, no altitude/landed/target-class columns, enemy control bytes always 0.

## What cannot be learned from this data
Low-hp phase and break-off (one Lightning near-death shows none), finishing a fight, RMB/group-1 use, flares for the player, AP vs plain (confounded with target), and whether a dodge actually causes a miss.

## Suggested numbers for the hf_ai tactics (S = from data, G = guess)
kite: ~200 u while firing (Lightning ~300 u), swing out 850-1300 u every 10-20 s (S); missile boat: launch 900-1600 u, salvos of 2, 6-9 s apart (S); dodge: react at ~550 u (2.2 s) missile range, turn 45-90 deg off its track, tap boost ~0.4 s (S timing, G efficacy); flares: dump 2-6 per tick for ~1.5 s at <350 u (S, n small); fire missiles only at flare-less targets (S); enemy charge pace +45 u/s at long range (S).
