# Combat missile launch: how enemy ships fire Zenith (1.163)

Status: **launch path found by reading plus in-game probes; one mod patch (burst) confirmed in game.** Tags: legend in `../../README.md`. Addresses are 1.163. Evidence date 2026-10-15 (qol fork debug build, three tactical battles).

## What a Zenith is
* `MDL_MISSILE_01` ("R-5 ZENITH"): stats index **130** (Body `+0x188`), `m_category=16384` (0x4000), anti-ship module, `m_missile_explosive=300`, `m_missile_ap=30` [game]. Its `m_launched_*` stats feed the map-level missile code; it has no `m_weapon_caliber`, so it is not fired through `FireGuns -> FireGun -> FireShell` [code].
* `FireGuns -> FireGun` (call at `0x140055a8c`) only fired ordinary guns in battle (stats 83, 88, 89, ammo slots 4, 1, 2) [game].

## The launch path [code, confirmed by effect in game]
* AI ship tick `FUN_140062f90`, branch with a target (`param_1[0x163]`) at distance between `radius(target)+radius(self)+100` and 2000. A launch is tried only when the ship cooldown float **Creature `+0xd60`** (`param_1[0x1ac]`) is 0 and a per-tick roll passes: `(dt*0.0099 + 0.99) - n*0.0002*n < random`, n = entries in the launcher list (about 1% per tick); plus conditions `DAT_147fc6fe0`, `FUN_1402213e0`, `FUN_14021ccb0`. In mode `+0xd70` = 2 a per-target budget (map `DAT_147fc7550`, float at node `+0x28`) must be > 0 and drops by 0.7 per launch (`SUBSS`, float at `0x140354700`).
* It loops over the launcher list **`+0x13d8`** (`param_1[0x27b..0x27c]`, stride 0x18, launcher part at entry+8) and calls **`FUN_14002ff60(launcher)` at `0x140065edb`** (`E8 80 A0 FC FF`) until one returns success (low byte of AL); then `+0xd60 = 2.0` (`0x140065efa`) and `break`. Hence one Zenith every few seconds per ship.
* `LaunchZenithAtOwnerTarget` (`FUN_14002ff60`): needs launcher `+0x848 == 0`, an owner (`+0xb8`), the owner's target `owner+0xb00` non-null and not an evac pod, and a special case on the body at the start of the launcher's vector (`+0x350`) when its logic id (`+0x3c4`) is 0x2ee; then `SetLink(launcher+0x490, target)`, `SetLink(launcher+0x4a8, owner)`, `+0x3c8 = 1`, and registers the launcher in the owner's active-missile list.
* Older notes called this "aircraft launch". The evidence says it launches Zenith for the AI and (by the same list and key 0x1012, [code]) the player. Whether aircraft/hangars also use it is **not established**.
* The part detaches in `creatureLogic` (`0x140033b90`) at the call `0x140037809` (`call 0x140048fc0`, RCX = RSI = the part) after a countdown; then the part has `+0x3c8 = 1`, `+0x3c0 = -1`.

* **Free flight and detection [data / guess]:** the telemetry shows about 4.1 s of free flight before a Zenith ends; a fixed self-destruct timer is a [guess]. `hf_ai` DETECTS a launch from the player's side with the target link (side < 0); the owner link (`+0x4b0`, confirmed side +1 on 18+ launches) is only logged. For the AI weapon controller's launch-list check, the list at `0x147fc73d8` is consulted only when it has more than one entry; that it is the player-side or ally set is a [guess].

## Evidence [game]
A probe wrapping the call at `0x140037809` logged every part leaving a ship: all stats=130, side from `owner+0xad4` (negative = enemy). One battle: 19 detaches, 15 enemy; per-ship gaps 2.6 to 8.7 s (owner A at t = 70.4, 76.9, 80.0, 83.4, 90.9). The player's own launches appear there too.

## What it is not [game unless marked]
* `FUN_14002e3a0(part, target)` / `FUN_14002e590(part)` (formerly "the combat launch"; call sites in the AI tick `0x140065880`, `0x140065f7f`; the two stores of the target's last-launch time `target+0x8b0` at `0x14002e557` and `0x14002e797`) were hooked and **never executed in three battles**, not even for the player's Zenith launches that the detach probe saw. They check target category bits `0x4000` (tactical missile) and `0x400` (aircraft) and cap missiles in flight per target, so they look like the **anti-air (interceptor) launchers**, for example Triumph class [guess; code read, not run]. Multicharge's working Triumph hooks fit this.
* The data references Ghidra shows to these functions (`0x14807974c`, `0x148079758`, `0x148079794`, `0x1480797a0`, `0x1480797ac`) come from consecutive 12-byte entries and are most likely the `.pdata` exception table, not a vtable or function-pointer table [guess, strong]. Other notes citing `0x1480xxxxx` as a vtable (for example `ai-flares.md`, `0x14807b2d0`) may have the same mistake; not checked here.
* The only writers of `target+0x8b0` in the exe are those two stores [code, instruction search].
* The map-level launch (`FUN_1400eced0`, timer `fleet+0x50c` = 300.0, store at `0x1400ed598`) is strategic-map missiles only and does not affect combat launches.

## Our patch: burst (qol fork branch `ai-flares`, local only; the original branch is kept as tag `old/ai-missile-dump`)
`ai_missile_dump_chance` (0.0 = vanilla). Replaces the 5-byte call at `0x140065edb` with a patchy `patch_call` wrapper (`ReturnType::Rax`, arguments pass through) that calls `FUN_14002ff60` and, when the launcher's owner has side < 0 (`owner+0xad4`) and a random roll is below the chance, returns 0 although the launch succeeded (the roll site is `0x140065c6c`, the wrapped call `0x140065edb`). The loop then goes on to the next launcher in the same tick. **Confirmed in game: a ship launched 4 missiles at the same moment.** Caveats: a burst that uses the whole list never starts the 2.0 s cooldown; no cap on burst size. Site owner: highfleet-qol fork, branch `ai-missile-dump`.

## Method notes
1. Wrapping a call site with `patch_call` and logging is a quick test of whether a function is reached; the arguments arrive as at the original call (up to four register arguments verified, stack arguments not).
2. Wrap-then-observe beat trusting the old notes: three sites were hooked for hours before the real one. Confirm a launch path by observing it; the detach probe at `0x140037809` sees every launched part, player and AI.
3. Offset search: list every instruction that writes a field (for example `+0x8b0`) with the `search_instructions` tool to see which functions really use it.

## Open [guess]
The ship launch gate reads the cooldown at `0x140065dac` (`MOVSS XMM0,[R14+0xd60]`, 9 bytes). A controlled short delay between burst launches would need that gate (and the ~1% roll) changed; not done.

## Player input, list rebuilds, anti-air launchers and part copies
Moved from the retired `systems.md` (2026-10-19).

* Player input `FUN_14018a530`: code 0x1012 uses the list at ship+0x13d8 with `FUN_14002ff60` [code, player path not hooked; the detach probe saw the player's Zenith launches]. Lists are rebuilt by the stats routine `FUN_14007fcf0` -> `FUN_140071380`.
* The part then detaches in the logic update `FUN_140033b90`: the call at `0x140037809` (`call 0x140048fc0`, RCX = the part) is the probe point [game]; disassembled [code]: `0x140037806 MOV RCX,RSI`, `0x140037809 CALL 0x140048fc0`, `0x140037811..0x140037817 CALL [RDX+0x68]` (`vtbl+0x68`, remove from its master), then `level->vtbl+0x50` adds it to the world (the `0x147fc6f88` level node is loaded at `0x14003781a`).
**Anti-air launchers (interceptors, for example S-4 Triumph) [code, not observed for Zenith]**
* `FUN_14002e590(part)` (player) / `FUN_14002e3a0(part, target)` (AI) need a target (`FUN_14006c0e0`/`FUN_14006c440`), the owner (+0xb8), the owner's cooldown (+0xad4) and in-flight limit (owner+0x17b0). They store target/owner refs at part+0x490/+0x4a8, set `+0x3c8`, start a timer, register the part in the owner's active-missile list. They were hooked at their AI call sites and never ran in three battles that included Zenith launches by both sides; multicharge's Triumph results ([mods/multicharge.md](../mods/multicharge.md)) fit the AA reading [guess].
* Player input `FUN_14018a530`: code 0x1013 walks the ship's second list (ship+0x13f0, stride 0x18, entry+8 = part) and launches until one succeeds (one missile per press) [code].
* The multicharge page reports that the AI retries every frame (hundreds of failures per fight). That can only hold for ships with AA launchers and a missile or aircraft target: the AI call sites of this pair never ran in the three Zenith battles. It does not describe Zenith, which is rate-limited by the 1% roll and the 2.0 s cooldown [guess].

* Only the **low byte** of the return value is the success flag (both paths).
* A copy of a part is made like the editor does it: `FUN_1401bfd00` copy, `vtbl+0x80`, `FUN_140280840(c,1)`, set position/angle (`FUN_1400521f0`/`FUN_140051850`, world
  coordinates through the master `vtbl+0xe8/+0xe0`), `FUN_140027f90`, `vtbl+0x88`, count=1, blueprint=0, owner ref, then **add to the level node `*(0x147fc6f88)`** (only objects in the tree are updated).
