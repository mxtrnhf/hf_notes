# Tactical AI: close-range cutoff, stand-off, ammo choice (1.163) and their patch sites

Status: **read from the decompilation; none of the patches applied or run in game.** Tags as in `../README.md`: **[game]** verified on the real game files · **[code]** read from the decompilation · **[guess]** inferred · **[not read]** known gap.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: roadmap tactical AI items ("closing to very short range disables all weapons", "AI consistently gives way to the player", "AP only at extremely short range / LG and INC not used"). Working notes: `review-1151-groups.md` groups 16 and 17.

## Where the AI lives
* **`FUN_140062f90`** (`0x140062f90`-`0x140065f99`) is the **per-ship AI tick**: steering, launching aircraft and missiles, and the call to the weapon controller. Its one caller is `0x1400739c0`, which Ghidra mislabels `shipKill?`.
* **`FUN_14007a8d0`** (`0x14007a8d0`-`0x14007bfb1`) is the **AI weapon controller**: aims every gun on an AI ship, picks the ammo, decides to fire. 1.151 twin: `0x140076300` (mislabelled `...::atan2f`). Called by the tick when the ship has a target.
* **`creatureLogic`** (`0x140033b90`) is *not* the ship AI: it is the per-body behaviour dispatcher for projectiles, missiles and aircraft, keyed by the `logic` id (`BulletImpact__` stores `ammo->caliber` there). It was never decompiled in one piece [not read].
* Side convention [guess, from where the difficulty byte applies]: the float at `Creature +0xad4`, negative and non-zero = AI side, positive = player's, 0 = neutral. `FUN_140220170(a, b)` is just `a == b` on the int-truncated sides ("same side").

## 1. The close-range cutoff (all guns fall silent when ships touch) [code]
In `FUN_14007a8d0`, after the target's position is read, the function returns before any aiming or `FireGuns` when
`radius(target) + radius(self) + 30.0 > distance`. 1.151's version has no such test (callers not compared), so this is, as far as this function goes, a 1.163 addition.

| Address | Bytes | Instruction |
|---|---|---|
| `0x14007b011` | `f3 0f 10 83 50 18 00 00` | `MOVSS XMM0,[RBX+0x1850]` (target radius) |
| `0x14007b019` | `f3 0f 58 87 50 18 00 00` | `ADDSS XMM0,[RDI+0x1850]` (own radius) |
| `0x14007b021` | `f3 0f 58 05 b3 74 2d 00` | `ADDSS XMM0,[rip+0x2d74b3]` -> the float `30.0` at `0x1403524dc` |
| `0x14007b029` | `41 0f 2f c6` | `COMISS XMM0,XMM14` (XMM14 = centre distance) |
| `0x14007b02d` | `0f 87 0c 0f 00 00` | `JA 0x14007bf3f` (the function's return) |

* `Creature +0x1850` is the ship's **bounding radius** [code]: its only writer is `CalculateStats` at `0x14007ffaa`, from `0x140071120`, the maximum over the root parts of (distance from the centre `+0x1840/+0x1844` + the part's own radius, `Body +0x20c`).
* **Do not patch the constant at `0x1403524dc`**: a pooled `30.0f` with about 60 other users (the `hooks.md` rule).
* **Make the margin adjustable:** operand repoint, change the disp32 at `0x14007b025` (bytes `b3 74 2d 00`) so the `ADDSS` reads a private float in the mod's memory (allocate within +-2 GB of the image). `30.0` is vanilla.
* **Disable the cutoff:** set that float to a large negative value (for example `-1e9`); the sum then never exceeds the distance. (Alternative: overwrite the six `JA` bytes with the 6-byte nop `66 0f 1f 44 00 00`; the float route keeps the knob adjustable.)
* Version guard: compare the 40 bytes from `0x14007b011` to `0x14007b039`. Not owned by any mod in `hooks.md`. Effect untested; the margin only matters when two ships nearly touch.

## 2. Stand-off distance and the "AI gives way" mechanism [code; effect untested]
The steering sums weighted unit vectors. The stand-off is `0.35 x` the larger of two weapon-reach floats (`Creature +0x1838`, `+0x183c`), capped at 1000 (660 if the flag at `+0xc74` is set). The radial weight is `clamp((distance - standoff)/600, -1, 1)` toward the target, so inside the stand-off the weight turns negative and the AI **backs away**, fully retreating 600 units inside it
(a 2000-reach ship starts backing off at 700). A perpendicular **orbit** term with weight `1 - |radial|` makes it circle at the stand-off. Other terms: separation from **allies** (same int side; it does *not* push away from the player unless two mode flags are set, `DAT_147fc6fe0` and a reach >= 6000 condition), cohesion toward the group, a waypoint pull, map-edge push.
This retreat, not separation, is the likely reason the AI "consistently gives way to the player": nothing steers the player. **[guess]**

| Knob | Instruction (address, bytes) | Constant | Other users of the constant |
|---|---|---|---|
| stand-off = `0.35` x reach | `0x1400631a6` `f3 0f 59 1d 0e 15 2f 00` and `0x1400631ec` `f3 0f 59 1d c8 14 2f 00` (`MULSS XMM3,[rip+d]`; with / without a ship target) | `0.35f` at `0x1403546bc` | 6 (`SomethingWithLevelSerias` x4, `FUN_14012f120`, one more) |
| stand-off cap 1000 | `0x14006320d` `f3 0f 10 35 2f f6 2e 00` (`MOVSS XMM6,[rip+d]`, then `MINSS XMM3,XMM6` at `0x14006321e`) | `1000.0f` at `0x140352844` | many (also the AP range threshold below) |
| stand-off cap 660 (flag `+0xc74`) | `0x1400631fe` `f3 0f 5d 1d ce 33 2f 00` (`MINSS XMM3,[rip+d]`) | `660.0f` at `0x1403565d4` | not checked |
| radial width 600 | `0x140064723` `f3 0f 5e 05 11 e1 2e 00` (`DIVSS XMM0,[rip+d]`; result clamped to +-1) | `600.0f` at `0x14035283c` | about 24 |

Recipes (operand repoint to a private float, with a version guard around each site): a smaller `0.35` makes the AI hold a shorter range (it closes in); a larger `600` flattens the retreat; a very large `600` means it almost never backs away. Orbit and separation are unchanged by these.

## 3. AI ammo choice (AP only close; never LG or INC) [code, same rule in 1.151]
For guns whose part caliber index is 15, 20, 25 or 30 (100, 130, 180, 203mm) the controller sets the gun's ammo slot (1.163 gun `+0x850`) with `FindAmmoIndex(name)`: **`_AP` only if two creature flags (`+0xc7c`/`+0xc74`) are set and the target is closer than 1000** (`0x14007b449`: `COMISS XMM6,XMM14` with the pooled `1000.0f`); otherwise the proximity variant under other flags (`+0xc7d`, `+0xc75`/`+0xc76`); otherwise the plain shell. It **never selects `_INC` or `_LG`**, the cause of "the AI cannot use LG/INC shells".
* **Latent bug in both versions:** for caliber index 30 it looks up `ITEM_AMMO_230MM` (and `_PROXY`, `_AP`) but the table has `ITEM_AMMO_203MM`; `FindAmmoIndex` returns 0 on a miss (the undefined entry, a `FireShell` default: muzzle flash only). Harmless in vanilla: no `OL.seria` part has `m_weapon_caliber=30` [game].
* [game] `m_weapon_caliber` equals the ammo `index`: `MDL_CANNON_30_6` 5, `MDL_CANNON_57_2` 10, `MDL_CANNON_100_2` 15, `MDL_CANNON_130` / `_LOW` 20, `MDL_CANNON_180` / `_180_2` 25, **`MDL_CANNON_305_2` also 25** (180mm shells), `MDL_RSZO_220` 52, `MDL_TORPEDO_300` 54, `MDL_CANNON_HARPOON` 90, `MDL_KAZ` 100.
* Other differences from 1.151 in the controller: a 0.025 rad aim tolerance before firing (not in 1.151's version); range for firing at strategic missiles 1.151 unlimited -> 1.163 3500; aircraft 2x range -> at least 3000; tactical missiles 0.75x in both; a creature flag caps range at 700; guns of part caliber <= 10 are limited to 1500 under a global flag.

## 4. Launching from the AI tick [code]
The tick launches aircraft (`FUN_14002ff60`) when the target is between `radius(target) + radius(self) + 100` and 2000 away, on a roughly 1% random roll per tick, with a 2.0 s ship cooldown (`+0xd60`) and a 6.0 s timer (`+0xcb8`). Missiles go through `FUN_14002e3a0` (the multicharge combat launch, see `hooks.md`) from the ship's second launch list (`+0x13f0`). Per-ship caps against special targets: **3 launches vs a strategic launch, 1 vs an aircraft** (counter `+0xc98`, 0.5 s apart at `+0xd64`).
`FUN_14002e3a0` adds, for **AI-side launchers only** (owner side negative and non-zero): at most **1 launch per second at the same target** (`target +0x8b0` holds the last time), at most **10** missiles in flight at one target, **2 at a tactical missile (`0x4000`), 1 at an aircraft (`0x400`)**, minus those already tracking it (compared at `+0x498`); and the launcher timer `+0x3c0` is `FUN_1401af7b0(8)`, or `(6)` when `Profile +0x164` is set. Player-side launchers skip all of this.

## Not read
Where the launch counter `+0xc98` resets; the contents of the ship's launch list `+0x13f0`; the meaning of the mode flags `DAT_147fc6fe0` and `BOOL_147fc6fdb`; the flag bytes `+0xc06..+0xc77` that choose AP / proximity; the addresses of the 1.151 twin's constants. Flares are covered separately in `ai-flares.md`.
