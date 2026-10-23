# Enemy AI and combat: what the 2026-10-23 logs confirm (simulator session, v1.163)

Written by the simulator session from measurements on battle logs (`.hftm`), tools in `hf_ml/sim` (commits in `hf_ml`, see handover `hf_ml/handover/sim-enemy-combat-handover-2026-10-23.md`).
Tags: **[log]** measured on logs, **[code]** from the Ghidra notes by ghidra-curator and agreeing with the logs, **[model]** a simulator choice that reproduces the logs but is not read from the code.
Sessions: AI ships 1792760120, 1792771275, 1792772114, 1792773413/500/595 (hf_ai 0.7-0.8 steer/scan logs); combat 1792777340 (five ships) and 1792777398 (hf_ally sim.52 hit log).

## 1. AI engine command pipeline (AiShipTick inline copy)  [log]
Checked per tick against the hook EA rows of the AI engines (command angle + strength per bank), inputs from the logs, no physics.
* F = ((dir + A) * s * cmd_max * m - v * m) / ts - (0, m * 9.82); s = clamp(sqrt(dist + 0.1)/20, 0, 1) (dist = 200 -> 0.707); accel = (T1 + T2) / (m * 9.82); **cmd_max = accel * 25**; ts = 10 / min(accel, 4); **m = creature mass +0x15b8** (logged as `cmass`; NOT the Frame mass); v = root part velocity.
* Attitude pair (gate +0x180c / I > 0.02, I = Frame body inertia about origin, logged `g_I_origin`): k = wrap(-a) * I / 20 along h = (sin a, -cos a); bank 1 gets F + k h, bank 2 F - k h.
* Clamp per bank: |V| <= T keep, T < |V| <= 2T -> T, |V| > 2T -> 2T. This is the AiShipTick inline copy; `AiShip_SteerController` uses 3T and the v_des = 100 s (A + dir) form (ghidra-curator fixed the note). Then the recursive ring out = (V + 5 stored)/6, the OUTPUT is stored. Command angle = atan2(x, -y), strength = |out| / T. The command of EA step n is computed from the state of the tick before it (lag 1).
* Result: with the game's own logged A the command matches to median 0.006, p90 0.03 of bank thrust (three battles 1792773413/500/595); with no ship within about 1000 u it is exact (median 0.000).
* **`+0xc74` (AiRerollAmmoFlags)** [log + code]: for heavy ships (accel < 4) cmd_max = min(accel, 4) * 40 while the flag is set. Seen on a 9.7M ship (1792769824): flag on from the battle start to t = start + 61 s, off afterwards; each state reproduces the commands exactly (error 0.001) and the other state is wrong by 0.5. Rolls every 30 s, probability (armour mass / total mass of the TARGET * 2)^2 [code]; the simulator reads the flag from the logged commands, it cannot predict it.

## 2. Obstacle scan (hf_ai 0.8 `hf_ai_scan` / `hf_ai_obst` rows)  [log]
* Scan row at step m belongs to EA step m exactly (command error 1e-5).
* From the logged kept nodes: A = - sum w_i u_i and w = ((10 - t) / 10)^2, t = gap / closing speed (gap <= 0 -> 0.1; closing = 0, t > 10 or t <= 0 -> w = 0) reproduce the logged A to 1e-7. The weight is tiny at low closing speed: a ship creeping toward the ground at 3-5 u/s gets |A| about 0.1 against a waypoint pull of 0.9. **This is why stock AI flies heavy ships into the ground** (1792773595, 41M-mass ship, accel 2.46).
* Kept nodes are individual part bodies of other ships (class 15, compound recursion; the Frame is only the range gate): 2994 of 3000 sampled nodes match a reconstructed part (bbox centre, radius = half bbox diagonal) to a median 1.9 u, radii exactly.
* **Terrain bricks (`lnd_brick`, mass 0, radius about 90 = half diagonal of 175 x 48) are kept nodes.** World centre = brick position + R(angle) * BX local bbox centre.
* The scan's own position/radius: root part bbox centre and radius 4.85 (not the Frame union circle of about 23).
* A model with these facts matches the game's per-tick A to a median 0.03-0.06 (p90 0.27); the residual is probably the 10 Hz AI hull poses of the log.

## 3. Shells  [log]
* Plain shells (logic 100): straight line, no gravity, no aerodynamic drag (ammo ap_drag 0), **only Box2D linear damping 0.05 /s** (996/1100 = exp(-0.05 * 2.0)); lifetime = ammo ttl. 110 timed-out shells (1792612053): end position error median 19 u = one frame of flight at 1000 u/s (107 u without the damping).
* 226 of 365 shells ended by a hit: 138 end within about 11 u of another ship's part polygon, 69 of the other 88 within 40 u of the ground polyline; timed-out shells end about 1000 u from everything.
* Ammo table: probe live dump parsed (`hf_ml/data/ammo_dump_1.163.txt`): 37 mm speed 1000 ttl 2.0 expl 0.30, 57 mm 700 / 3.0 / 2.0, 100 mm 700 / 4.0 / 14, 130 mm 700 / 7.0 / 20, 180 mm 700 / 30 / 82, 203 mm 10 s / 118, 305 mm 400; AP rounds speed 1500 ttl 1.0 expl 1.0 pen 16-34 drag 0.0007; rockets 130 speed 150 ttl 10.

## 4. Contacts and blasts (hit log sim.52, 104 + 25 shell contacts, 179 blasts)  [log]
* Shell arming threshold `arm` (+0x38c) = 25 * shell mass exactly (all 129 armed projectiles). Every contact with I = raw * 160000 > arm detonated in the same step (104 of 104 and 24 of 25).
* **Contact damage from a shell to a ship part is zero in practice**: the contact-handler damage calls on the touched part have d <= 0.19 (median 0.01). All part damage is blast damage.
* Blast: **R = sqrt(E) exactly** (665 offered parts, error 0.0000). **Scale = visibility * 2 sqrt(E) * 0.66, with 1.0 instead of 0.66 when the shooter is the player**: scale / (2 sqrt E) never exceeds 0.66 (AI shooter) or 1.0 (player), 64% / 94% of offered parts sit exactly at the cap. The Zenith blast E = 300 gives R = 17.32, scale 22.86.
* Blast damage calls have `p3` (armour-check flag) = 0 in all 926 calls: **the armour threshold gate of Body_ApplyDamage is NOT applied to blast damage** (it applies to calls with p3 != 0). Damage d / (5 scale) lies in (0, 1] as (1 - edge/R)^2 requires.
* The M-row centre is the centre the area-damage routine receives (the blast centre); the K-row x,y (+0x148/+0x14c) is about 10 u off and only informational.
* Mass: the creature mass (+0x15b8) drops by exactly the removed part's mass one step after each removal (child modules appear as their own removals; 16 checks, ratio 1.000). A missile launch drops it by 5495.

## 5. Flight model facts for damaged ships  [log, model]
* The landing gear never moves in these battles: leg hinge angle stays at about 1.5 rad (1.44-1.57) for the whole battle (torque rows, leg bodies mass 2.249 b2), leg part state constant; the simulator flies the legs folded at that pose and the report draws them that way.
* Replaying the logged part losses (simparts X rows) on the simulated ship (fixture destroyed, mass/COM/inertia recomputed, engine thrust lost) improved the heavily shot-up AI ship 1 of 1792777340 from 11 to 8 flagged 3 s windows and 896 to 660 u open loop; the player's ship 3 -> 2 flagged windows (open loop 182 -> 233 u); two other ships unchanged. Remaining error: engine lock-outs (fire/heat damage), jointed parts keep their mass. A jointed body given a negligible mass makes the Box2D solver explode (2000 u/s): do not do that.
* Y rows (b2 mass, inertia, local centre of the Frame after a removal) were NaN in sim.52 (fixed in sim.53, not yet read).

## 6. Not established
* Direct-hit scale of the part the shell touches; why part hp drops match the blast damage in only part of the contacts (other damage calls, e.g. fire, in the same step).
* Whether the AI waypoint (target choice, orbit side) is reproduced by the port: only the old 11.8 deg median / 47 deg p90 check exists.
* `+0xc74` first-roll timing beyond the one flip seen; prediction needs the target's armour fraction.
