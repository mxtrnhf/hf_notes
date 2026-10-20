# Combat simulator research: what is established, what is not (2026-10-20)

Purpose: the facts a combat simulator (and any learned AI trained in it) can be built on, with the corrections made along
the way. Work lives in `hf_ml` (local repo, not published): `DESIGN_NOTES.md` is the full running log, `handover/simulator.md`
the handover, `out/opus-review/REPORT.md` the audit that decides what to trust. Tags: **[code]** read in the 1.163 decompile,
**[data]** measured from telemetry, **[fit]** fitted, **[guess]** unproven. Details of single mechanisms are in the notes
linked below; this page only collects and cross-checks them.

## Physics (the game uses Box2D, see [box2d-physics-setup.md](box2d-physics-setup.md))
* Step 0.02 s (1/50), 10 iterations, gravity 9.82 game units (+y down), position scale 0.05, linear and angular damping 0.05, friction 0.6, restitution 0.001 [code].
* One convex polygon fixture per part from the `Mesh` in each Body node (<= 8 vertices); mass = min(w,h) x m_density x polygon area = seria `m_mass`; inertia is Box2D's own [code].
* The moving mass is `cmass` (creature +0x15b8, the sum of all part masses), not the logged `frame_mass`: jointed parts (engines, guns on slot types 146/162/282) are separate bodies that the Frame drags. a = F / cmass [data, 3 designs].
* Drag: Box2D damping gives 0.05/s. The game's quadratic air-drag force exists (F = -v_hat x 0.5 x 1.29 x c x |v|^2) but `c` = save key `m_drag_lin` is set only on level objects (City, Land, Town), never on ships, so hulls have none [code + file]. The measured coefficient also grows with speed (0.06 at rest, 0.27 at 400 u/s); that term is therefore not drag and is unexplained: a speed falloff of engine force or a measurement artefact; an engines-off high-speed coast would settle it.
* **CORRECTION 2026-10-21 [code]: hulls DO have a hardcoded quadratic air drag.** The Frame (class 0x1f) branch of `Body_PreStepUpdate` (`0x14001d440`, Body vtable `+0x168`, run for every live body before each `b2World_Step`) applies `F = -v_hat x A x min(W,H) x |v|^2 x 1.29 x 0.5` with `v` = Frame `+0x130/+0x134`, `W,H` = Frame bbox `+0x218/+0x21c`, `A = |H(-sin th n.x + cos th n.y)| + |W(cos th n.x + sin th n.y)|` (silhouette across the velocity, `th` = Frame `+0x138`, `n` = v_hat rotated -90 degrees), through `Body_AddForceAtPoint` at the Frame point `+0x210/+0x214`, so it also makes a torque about the COM that depends on the hull angle relative to the velocity. This is the speed-dependent term the audit found (a = -C2 |v| v); the statement above that hulls have no drag is wrong for Frames (it holds for the `m_drag_lin` branch only).

## Engines
* Force per engine = Stats+0xf8 x strength x cos(command - engine angle), dropped if cos <= 0, along (sin a, -cos a) ([contact-damage-and-fire.md](contact-damage-and-fire.md) has the surrounding handler) [code]. `eng_840` in the logs is a force readout (0.5 + 1e-8 x force), not a throttle [code + data].
* The engine angle (part +0x138) follows the command angle through a Box2D motor: speed = wrap(cmd - angle) x power^2 x Stats+0x108 (3.0, so tau = 1/3 s), max torque mass/100 [code]. It is logged in the simparts Q rows.
* Engine names: `MDL_ENGINE_01` RD-59 (swivel), `02` RD-59S (static), `03` D-30 (swivel), `04` NK-25 (swivel), `05` D-30S (static) (S = static; user). Swivel is data: `m_slot_type` 146/162 rotate, 1105/1121 are rigid. `06` has no placeable prototype.
* Fuel: two code paths. Every ship: Stats+0xd0 x eng_840 x dt x 50 (x50 under the arcade flags) while 0 < eng_840 < 1. Player-controlled ships also: Stats+0xd0 x (cos x strength)^2 x dt x 50 [code + data].

## AI
* The waypoint formula of `AiShipTick` is ported exactly (agreement is at the 0.1-unit log resolution, which is a transcription check, not a behaviour test) [code + data].
* The force: F = m x k_a x (c x u - v) - (0, m x 9.82), two bank vectors with a norm clamp and a 6-sample average. There is no fixed delivery factor: each of the two banks carries the full tick vector, so the delivered force is about 2|F| when aligned and unclamped (checked on 11,761 enemy rows, structural model median 1.000); the attitude-hold term (gate: 2 x min bank angular thrust / hull inertia > 0.02) and the avoidance term are not ported [code].
* Enemy ammo doctrine is rolled once at spawn (first group-0 gun's calibre and rating): see [firing-and-shells.md](firing-and-shells.md), [ai/](ai/) and `hf_ml/out/ds2-ammo-writer`. AP needs c7c AND c74 AND distance < 1000; proximity needs c7d AND (c75 OR c76) [code, seen in play].

## Damage and kill
* Contact damage = 0.8 x the Box2D PostSolve maximum normal impulse, equal on both sides; tear-off above impulse 4e6 (8e6 arcade) on Frame children has no damage call ([contact-damage-and-fire.md](contact-damage-and-fire.md)).
* Fire is a heat model; only fuel tanks and engines can burn.
* Ship removal rules (engine bank sum 0, TWR < 1, fuel 0, power 0, parts ratio < 0.65 with c48 == 0 or rating <= 40, no active gun) and bridge death (no REMOVE line) are in `hf_ml/DESIGN_NOTES.md`.

## Corrections made during this work (do not repeat the old claims)
* "Thrust falls off with speed" - it is drag plus the swivel transient. "k = 0.879/0.807 delivered fraction" - it is the frame_mass/cmass ratio. "eng_840 is the throttle" - a force readout. "Engine angle equals hull angle" - false, the engine angle is its own logged field. "The gimbal is not logged" - it is, in simparts Q rows. "There is no gravity" - 9.82. The old names RD-59 (static) / RD-59S (manoeuvre) were swapped.
* The 0.0087 deg waypoint match, the 0.004 deg servo angle and the 0.00 deg force reconstruction are measurement floors or self-comparisons, not accuracy.
* The first replays of the servo model used oracle inputs (logged hull angle every tick, logged initial engine angles); a standalone simulator needs its own hull rotation model.

## Unknown / next
* Source of the |v|-dependent drag; lambda 1.7; hull rotation and torque (Q/E, attitude hold); break-up against a logged break-up; campaign behaviour (all logged battles are arcade); the dice of the 25 collision-filter rules (bit meanings of +0x1c0 partly decoded); planes, missiles, flares.
