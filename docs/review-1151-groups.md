# 1.151 annotation review, by function group (working file)

Local branch `review-1151-annotations` only. Continuation of `review-1151.md`: one section per group of 1.151 functions I read, with the 1.163 counterpart and what it adds to our notes.
Read-only on both Ghidra programs. Tags: **[code]** read from a decompilation, **[guess]**, **[tool]** fuzzy match. 1.151 names are logdot's.

<!-- MOVE: each group section goes to the doc named in its own MOVE comment; delete this file afterwards. Track progress in REINTEGRATION.md. -->

## Profile remap, 1.151 -> 1.163 (the world singleton): +0x48 for the vector block [code]
`Get_Profile` (1.163 `0x140292a90`, `Get_Profile_`) returns the `Profile`. The Ghidra `Profile` struct is the same size (1,380 bytes) and identical in both programs, which is a stale copy:
its vectors moved in 1.163.

| Vector | 1.151 (Ghidra name, offset) | 1.163 offset | Evidence |
|---|---|---|---|
| Escadras (fleets): begin/end | `escadras` `+0x1b0`/`+0x1b8` | `+0x1f8`/`+0x200` | `structures.md` already lists the friendly-fleet list at `+0x1f8/+0x200` [notes] |
| Missiles (map missiles): begin/end | `Missiles`/`MissileEnd` `+0x1e0`/`+0x1e8` | `+0x228`/`+0x230` | the map-launch consumer `FUN_1400eced0` pushes the new Missile at `+0x228` (end `+0x230`, cap `+0x238`) [code]; `structures.md` already says "missiles +0x228/+0x230" |
| MapCrafts (map aircraft groups): begin/end | `mapCrafts` `+0x228`/`+0x230` | `+0x270`/`+0x278` | 1.163 `CreateMapAircraftGroup` (`0x14010f8e0`) pushes the new group at `+0x270` (end `+0x278`, cap `+0x280`) [code] |
| `explosions`, `designs`, `items`, ... | `+0x1f0`, `+0x210`, `+0x278` | +0x48 presumably | [guess] |

* **Consequence for `structures.md`:** it says "fleets +0x270/+0x278". By this table `+0x270` is the **MapCraft** vector, and the fleet vector is the `+0x1f8` one. Two different readings of the same code
  gave "fleets" for `+0x270`; check one writer or iterator of `+0x270` before editing the notes. (A MapCraft stores its target at `+0x270` as well, which may have caused the mix-up; that is a field of the
  MapCraft object, not of the Profile.)
* Ghidra's stale label `mapCrafts` at `Profile+0x228` in the 1.163 program is really the Missile vector; the real MapCraft vector has no name there.
* Same method as the `Body` remap (`review-1151.md`): pair a function present in both versions, compare the offsets it uses.

<!-- MOVE: this section -> structures.md ("Map missile" section, world singleton line) after the "+0x270 is fleets or MapCrafts" check. Also add to the 'Version differences' subsection. FLAG for logdot. -->

## Group 1: strategic AI aircraft launch

### `TryLaunchAiAircraftGroup` (1.151 `0x1400ea210`, 1.163 `0x1400ef910`) [code]
Present in both versions and almost identical; the 1.163 copy is still named by the machine-propagated `rep_1400ea210_...` and is a good name to apply. What it does (it decides when an AI fleet launches its
aircraft against a detected target):

* Preconditions (all must hold): a target exists; the fleet has aircraft (`count` > 0, 1.151 `+0x4e8`, 1.163 `+0x4ec`); distance to the target `< range * 0.45`
  (range at 1.151 `+0x4f0`, 1.163 `+0x4f4`); the aircraft cooldown is 0 (1.151 `+0x50c`, 1.163 **`+0x510`**); the fleet state float at `+0x188` is 0; the target's field `+0x78` is below a limit; and distance `> 200`.
* **The limit on the target's `+0x78` was raised from `480.0` (1.151) to `1200.0` (1.163).** Whatever that field is (a detection or range value of the target), the AI now launches against much
  more distant targets.
* **How many aircraft:** all of them (`count`). If `count > 10`, a coin flip (`Random_Int(0,1)`) halves it. The loop then builds the list of aircraft, picking loadouts by weight from the `PLANE_TLL` table, until
  `count` is used up, and passes the whole list to `CreateMapAircraftGroup`. So the AI launches **one group containing all (or half of) its aircraft at once**: this is exactly the roadmap bug
  "Strategic AI deploys all aircraft upon player detection within strike range, leaving none for defensive interception". A fix is a limit on the group size (for example keep a reserve) at that loop.
* After the launch: cooldown `1800.0` (`0x44e10000`) is written to the aircraft cooldown, and a time stamp `hourCount + 24` (1.151 `+0x518`, 1.163 `+0x528`) is stored.
* **Fleet field shifts** in this function: count `+0x4e8 -> +0x4ec`, range `+0x4f0 -> +0x4f4`, aircraft cooldown `+0x50c -> +0x510`, time stamp `+0x518 -> +0x528`, state `+0x188 -> +0x188`. The missile-launch
  cooldown (`+0x50c` in 1.163, which `highfleet-salvo` patches) is therefore a **different** field from the aircraft cooldown (`+0x510`); in 1.151 the missile cooldown is `+0x508`.

<!-- MOVE: -> roadmap.md (Strategic AI item 1: "all aircraft launched" with the location and the knobs) and systems.md (new subsection "Strategic AI aircraft launch"); the fleet field shifts -> structures.md fleet row. -->

### `CreateMapAircraftGroup` (1.151 `0x140109de0`, 1.163 `0x14010f8e0`) [code]
Matcher found no counterpart (score < 0.7), but the 1.163 call from `TryLaunchAiAircraftGroup` reaches `0x14010f8e0` (still named `rep_140109de0_...free`), so that is it.
* Same shape in both: `New(0x340)`, `Mark` constructor, group speed and range taken as the **maximum `launched_speed` (stats `+0x158`) and `launched_range` (stats `+0x160`)** over the members, start point from
  the launching fleet or the given target, constants set on the new object (1.163: turn rate `4.0` at `+0x2ac`, `60.0` at `+0x250`, `1.56` at `+0x254`, `30.0` at `+0x2b0`, `9000.0` at `+0x168`,
  `100.0`/`1000.0`/`20.0` at `+0x174/+0x178/+0x17c`, `type = 4` at `+0x29c`), then the group is added to the MapCraft vector and `loadAircraftWeaponsFromBotMenu` (1.151 `ComputeMapAircraftWeaponStrength`) fills the
  group's weapon totals at `+0x2fc/+0x304`.
* **New in 1.163:** if the group has no linked target, it scans the profile's `designs` list for an entry within distance 1.0 with `+0x2e8 > 1` and `+0x248 != 0` and links it. Unexplained; probably a
  base/landing target.
* The group's `+0x29c` type is `4`; map missiles use `1` to `3` (`3` = ground), so `+0x29c` is the map-object kind.

<!-- MOVE: -> structures.md (MapCraft row details) and systems.md (air raid subsection). -->
