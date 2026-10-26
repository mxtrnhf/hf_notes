# Elevation rules, gun-arc blocking and KAZ angles: 1.151 vs 1.163

Question from testers (2026-10-26): "port the 1.151 elevation logic into 1.163: engines and guns don't block gun arcs; the KAZ (Palash) angle checks are not as strict." Two DeepSeek agents read both builds (reports `~/Development_Highfleet/elevation_port/a-blocking/REPORT.md` and `b-kaz-angles/REPORT.md`, ~650 and ~720 lines). Claude re-read the key bytes below. Everything else is **[agent]**.

"Elevation" here is the part floor `m_floor`: 1.163 `Body+0x9b8` (type `+0x9b0`), 1.151 `Body+0x980` (type `+0x978`). **[code]** 1.151 `Deserealize` writes the save key `m_floor_type` to `[RSI+0x978]` (`0x140024679`) and `m_floor` to `[RSI+0x980]` (`0x1400246bf`). So the shift is **+0x38**, not +0x30 as `version-differences.md` had it (fixed there).

## 1. Who blocks a gun's arc: one predicate differs [code]
Both builds scan 360 sectors (1.163 `Body_ScanSectors` `0x140052340`, 1.151 `CalculateSectors` `0x14004fe20`) and call one ray predicate (1.163 `World_RaycastBodies` `0x140239f30`, 1.151 `0x14021be40`, which Ghidra had named after a `sqrtf` symbol collision). A candidate body is **skipped** when `shooterFloor > candidateFloor` (`COMISS XMM7,XMM0; JA skip`), or the "skip floor test" argument is nonzero.

| term | 1.151 | 1.163 |
|---|---|---|
| shooter floor | `(float)(+0x980)`, +1 if shooter's master (`Body+0x88`) is null or `master+0x28 == 7` (`0x14021be6b..0x14021bea9`) | same with `+0x9b8` (`0x140239f5b..0x140239f99`) |
| candidate floor | `(float)(+0x980)`, no addition (`0x14021bff2..0x14021c000`) | **+1 when the candidate's master is null or type 7** (`0x14023a0dd..0x14023a103`: `LEA EDX,[RAX+1]; CMOVZ EDX,EAX`) |

Effect: a free-standing part (own physics body: swivel guns, engines, legs) blocks a gun at the same nominal floor in 1.163, but not in 1.151. This is the "guns don't block each other, engines don't block guns" difference. Welded parts are unchanged. The floor solver is not the cause (the 1.151 engine bit `0x100` works the other way; 1.163 adds a `m_floor_type & 0x10 -> floor 3` branch that stock saves do not use) **[agent]**.

Port idea, not applied: at `0x14023a103` replace `0F 44 D0` (`CMOVZ EDX,EAX`) with `89 C2 90` (`MOV EDX,EAX; NOP`).

## 2. The KAZ is a module, not a gun [agent, user-confirmed]
`MDL_KAZ` (category bit 25) never calls `FireGun`; its burst is `Weapon_FlakInterceptScan` (1.163 `0x14002f480`, 1.151 `0x14002fca0`). The QoL FireGun detour therefore has no effect on it. Two independent strictness terms:

* **Target cone [code]:** accept a target when `|bearing| < C`. 1.151 `C = 1.2` rad (68.75 deg); 1.163 `C = 0.7853982` (pi/4, float at `0x1403527ac`), loaded at `0x14002f864` and `0x14002faf8`. The constant is shared by many functions: repoint the two `MOVSS` displacements to the existing 1.2f at `0x140354758` (new bytes `F3 0F 10 0D EC 4E 32 00` and `F3 0F 10 0D 58 4C 32 00`), do not change the constant.
* **"Covered" gate [agent, partly file]:** the burst needs `m_mdl_covered` (`+0x848`) == 0. `UpdateEngineCovered` (`0x14001c4a0`) sets it from the part's own `m_sectors` over a cone chosen by `m_mdl_sectors_type`. 1.163 `OL.seria` has `MDL_KAZ` `m_mdl_sectors_type=5` (rear 90 deg, unique to the KAZ) and `m_mdl_sectors_threshold=0.15`. 1.151 had type 3 (rear +-0.3 rad = 34 deg) and 0.5 (from `explosion-damage-1151-vs-1163.md`; a Hara Vera mod file shows 0.55; no vanilla 1.151 `OL.seria` on this machine, so medium confidence). About 8.7 times more sensitive under a uniform-blockage model.
* Secondary: 1.163's scan adds a half-degree pre-pass and a `min` with the previous entry, so blocked arcs spread about 1 degree (1.151 writes each sector once). Not planned for porting (global effect on every part).

## 3. Regular guns
1.151 `FireGun` (`0x140032fa0`) tests one sector (blocked iff entry is exactly 0.0); 1.163 `FireGun` has none (the QoL mod re-adds it at `0x140032f22`). 1.163's AI weapon controller also gains a 0.025 rad aim tolerance. With QoL's gun blocking on, the detour is why 1.163 blocks guns where vanilla 1.163 would not; the rule in section 1 decides who blocks.

## Update 2026-10-26 (evening): what blocks the KAZ, and `classic_kaz` [code]
* For a non-gun shooter (category bit 5 clear, so also the KAZ) `World_RaycastBodies` skips the floor test: **every** part fixture of the same ship counts as a blocker, empty hull blocks (`MDL_BLOCK*`, category 64) as well as armor (2), modules and trusses/hardpoints (128). The candidate-floor +1 therefore affects guns only. Same in 1.151 (`0x14021be40`, `R15B` skips the floor test). The only per-category escape is the `param_8` mask (`GetPartFlagsWord & mask`), which 1.163 uses with `0x80` for type-2 sensors; the KAZ scan passes 0.
* So 1.151's KAZ was not "transparent to hull"; it tolerated up to 50% of a 34 degree cone being blocked. A ray that starts inside a fixture reports no hit in Box2D, which may explain fire from inside a hull block (not tested).
* Truss (`MDL_FERMA*`, price 5 to 80: 1x1 (4 variants), 2x1, 2x2 (4), 4x4) and hardpoint (`MDL_HARD*`, price 50 to 200: 1x1 (4), 2x1, 2x2 (4)) share category 128, so the mask cannot tell them apart; the mod matches the oid prefix `MDL_FERMA` (body `+0x190` std::string).
* Mod: one config key `elevation_rules` = `vanilla` | `classic` | `modern` | `classic_kaz` (QoL fork, `elevation_rules.rs`). `classic` = gun candidate +1 removed, KAZ cone 1.2 rad, KAZ covered test as type 3 with threshold 0.5 (all three applied and logged in the 2026-10-26 18:58 game run, byte checks matched). `classic_kaz` = `classic` plus trusses skipped in the KAZ scan (detour pair: shooter noted at `0x140239f5b`, candidate test at `0x14023a120`); blocks, command bridge, hardpoints, armor, modules still block. Truss part not yet run in the game.

## Not determined
* No game test of any patch. Whether (1) alone gives the testers' feeling is open.
* 1.151 KAZ data are from notes and a mod file, not an original file.
* Ghidra annotations (1.163 only, 2026-10-26): plate comments on `World_RaycastBodies`, `Weapon_FlakInterceptScan`, `Body_ScanSectors`; line comments at `0x14023a103`, `0x14002f864`, `0x14002faf8`, `0x14001c685`.
