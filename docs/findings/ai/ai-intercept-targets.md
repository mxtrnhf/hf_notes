# How an AI ship picks what to intercept (1.163)

Status: **read from the decompilation (Ghidra, 2026-10-19). Nothing here was observed in play except what is tagged [game]. The one patch built on it, hf_ally's `intercept_ignore_oids`, is untested.** Tags: legend in `../../../README.md`. Addresses are 1.163, image base `0x140000000`. Several of these functions carry wrong Ghidra names; both are given.

## Why this page and the side patch exist
A modder (Discord, 2026-10-19) made the Sprint (an anti-air missile) strategic-launchable by editing its `m_category` in `OL.seria`. In the missile-vs-ship arcade scene the AI then defended against that Sprint as if it were an enemy strategic missile: the player's allies fired their CIWS and Sprints at the player's own Sprint (case 1), and one enemy ship's Sprint drew fire from the other enemy ships (case 2). Because the Sprint is launched near the squadron it won the priority race and the real strategic missile was left alone, which ruined the interception sequences.

The cause is in the game, not in the mod's data: the threat-list builder selects "strategic launches" by category bit only and never asks who launched the body (pass 1 below). There is no setting in the data files to say "this one is ours", so the only fixes are a new game-side test or a code patch. The maintainer's reply was to add a crutch, "just ignore Sprint always", and a second request asked for an editable list of `m_oid`s the AI ignores in that scene. That is `intercept_ignore_oids`. It is a **side patch**, not part of the mainline hf_ally: it fixes one modder's setup by name, it changes AI behaviour for a part the vanilla game never flags this way, and it is untested. The principled fix (give bodies an owner-side check in pass 1) is not built. Branch `side/ignore-intercept-oids`, never merged to master.

"Interception" here means two things that share one target: **guns firing at an incoming missile (CIWS-style)** and **anti-air launchers (Sprint class) firing at it**. A ship has two separate targets: the *ship target* (`+0xaf8` Link, node `+0xb00`, chosen by `FUN_140078b40`, see [../battle-ally.md](../battle-ally.md)) and the *missile target* (Link `+0xb10`, node `+0xb18`), which this page is about.

## The pipeline, once per AI tick [code]
`aiShipDriver` (`0x1400739c0`, Ghidra "shipKill?") runs it for every AI-run ship, enemy and ally alike. In the branch that starts at `0x140073bb4`:

1. **Clear** the ship's threat list (vector at creature `+0xca0`, end pointer `+0xca8` set back to begin).
2. **Build** it: `0x1400625a0` (Ghidra `rep_1400601a0_...free`) with `param_3 = 0` (no range limit) and `param_4 = 0`.
3. **Choose** one entry: `0x14006c100` (Ghidra `...atan2f`) returns a body pointer.
4. **Store** it: `SetLink(creature + 0xb10, body)` (`0x140194de0`, call at `0x140073c8a`). The body is then readable at `creature +0xb18`.
5. **Consume** it: `AiWeaponController` (`0x14007a8d0`, loads it into R14 at `0x14007a9bd`) and `AiShipTick` (`0x140062f90`, loads it into RDI at `0x1400657d9`).

The prize-ship branch of the driver (`+0xc19`) and the "no target at all" state change sit in between and are covered in battle-ally.md.

## Step 2: how the list is built (`0x1400625a0`) [code]
Entry = 0x20 bytes: `+0` kind (u32), `+4` flag byte, `+8` **count** (how many of this ship's own missiles already track this body), `+0xc` distance (f32, from the ship centre to the body), `+0x10` body pointer, `+0x18` a flag byte set for kind 1.

**Prelude: the count map.** The function first walks the ship's own list of launched missiles (`+0xa58`, a std::list; dead nodes are unlinked and freed here), and counts, per target pointer found at each missile's `+0x498`, how many of them aim at it. That is the `count` field. It is what spreads the ship's interceptors over several threats.

Then up to three candidate passes:

| Pass | Condition | Candidate | Kind | Side / owner test |
|---|---|---|---|---|
| 1 | `DAT_147fc6fda != 0` | every active body in the global body array `0x143a33c90` (count `0x143a51150`, limit 15000) where `GetStats(body+0x188)->+0xb0 & 0x8000000` (via `checkShipPartFlagActive` `0x140049470`, call at `0x140062812`) | 0 | **none** |
| 2 | list still empty | for each creature of a *different* side (`FUN_140220170` on the int-truncated `+0xad4`): the nodes of a list it owns (`0x14006b5c0`, name unresolved; likely the bodies it launched [guess]) that are active | 2 | other side only; flag byte = the body's `+0xa20` owner link points at this ship |
| 3 | list still empty | every active body with logic id `+0x3c4 == 500` whose owner link `+0xa20` is set, the owner's side is not "same fleet" (`FUN_140220120`), and the owner is alive (`FUN_14000b360`: its state `+0x190` is not 6 or 7) | 1 | owner not same side; flag byte = owner is this ship or this ship's root creature |

`FUN_140220120(a, b)` is the "same fleet" test on integer sides: both non-zero and `a == b`, or one is the other divided by 100 (a sub-squadron code). `FUN_140220170` is plain equality of the int-truncated sides.

**What this means:** only pass 2 and 3 look at who launched the body. **Pass 1 is the only one that checks the stats category, and it has no side test at all.** In the scene where it applies, anything flagged "strategic launch" is a candidate for every AI ship, friend or foe. Pass 2 and 3 only run when pass 1 found nothing, so in a strategic-missile defence scene they are usually skipped. The meaning of `DAT_147fc6fda` is [guess]: one of the arcade/battle flags (`DAT_147fc6fc8`, `fd4`, `IS_IN_ARCADE_BATTLE`, `f82`, `fda`, `BOOL_147fc6fdb/dc/dd`, see [../rendering/render-pipeline.md](../rendering/render-pipeline.md)); it must be the missile-vs-ship defence scene given the pass it gates.

## Step 3: how one entry is chosen (`0x14006c100`) [code]
Two modes, on `BOOL_147fc6fdb` (another arcade flag; presumably the defence scene as well [guess]):

* **Flag set:** among entries with distance `<= 1500`, pick the smallest score `count * 10000 + distance`. So: the threat fewest of our own missiles already track, and nearest among equals. A new Sprint with count 0 at 300 units beats a strategic missile with count 1 at 100 units.
* **Flag clear:** walk the list in order. Skip an entry unless its distance is `<= ship radius (+0x1850) + 500` (kind 0 is exempt from the distance cut). For kinds 0 and 2, test that the body is **heading at this ship**: the angle between the body's velocity (`+0x130/+0x134`) and the vector from the body (`+0x128/+0x12c`) to the ship is under 90 degrees. The first such kind-0 entry is returned at once; kind 1 entries are returned if their flag byte is set; otherwise the first acceptable entry is kept as a fallback. Returns 0 (no missile target) when nothing qualifies.

The sort helper the builder can call (`0x1400598c0`, `param_4 != 0`) is not used by the driver (it passes 0) and was not read.

## Step 5: what the target is used for [code]
* **Guns** (`AiWeaponController`): the category of the target body decides the engagement range. `0x8000000` (strategic launch): a long fixed range (1.163: 3500, 1.151: unlimited, see [ai-tick-patch-sites.md](ai-tick-patch-sites.md) section 3). `0x4000` (tactical missile): the gun's reach times 0.75. `0x400` (aircraft): at least 3000 (twice reach). A creature flag caps it at 700. Then the usual aim, the 0.025 rad tolerance, the friendly-fire segment test (`0x14021c790`) and `FireGuns`. So a body with the strategic bit gets shot at from much farther than an ordinary tactical missile would be.
* **Anti-air launchers** (`AiShipTick`, calls `FUN_14002e3a0`): the target must have category `0x8000000` or `0x400`; a `0x4000` tactical missile is **not** a launch target at this site. Ship cooldown `+0xd64` must be 0. Cap on launches per target: 3 against `0x8000000`, 1 against an aircraft (counter `+0xc98`). `FUN_14002e3a0` adds per-target limits of its own (see ai-tick-patch-sites.md section 4).

## Consequence: the modded Sprint [game report + code]
The report (Discord, 2026-10-19): a Sprint (`MDL_MISSILE_03`, vanilla category 16384 = `0x4000`) modded to be strategic-launchable by adding bit `0x8000000`. Then, in pass 1, it is a candidate for every AI ship on both sides regardless of who launched it; in the "flag set" selection it has count 0 and is closest to the squadron, so it beats the real strategic missile; the guns open up on it at the strategic range; and the AA launchers may fire up to 3 interceptors at it. That is exactly "CIWS and Sprint at my own Sprint", on the player's side (allies) and the enemy side alike. [Not reproduced by us.]

## The fix and its limits (hf_ally branch `side/ignore-intercept-oids`)
Wrap the call at `0x140062812`: if the stock test says "strategic launch" and the body's `m_oid` (Body `+0x190`, MSVC `std::string`: inline up to 15 bytes, length `+0x1a0`, capacity `+0x1a8`) is in `intercept_ignore_oids`, answer "no". The body never enters the list, so steps 3 to 5 are unchanged for everything else. The two AI-tick tests at `0x1400657e9` and `0x140065828` read the already-chosen `+0xb18` node, so they need no patch. Limits:
* Pass 2 and 3 are not filtered. If pass 1 yields nothing (the real strategic missile gone), a Sprint could re-enter through pass 2 (any enemy-launched body) or pass 3 (logic id 500) [guess whether it does].
* The check compares the *flying* body's `m_oid`. A launched part is the mounted part itself (hf_aa_missile NOTES: "in vanilla the mounted part itself becomes the flying missile"), so the part name should match; a clone with its own `m_oid` needs its own entry.
* An alternative that also covers passes 2 and 3 would filter the chosen body in step 3 (`0x14006c100`) or clear the `+0xb18` link after step 4. Not built.

## Not read
The name and contents of the list function `0x14006b5c0` (pass 2); what logic id 500 is (pass 3); the sort helper `0x1400598c0`; which scene sets `DAT_147fc6fda` and `BOOL_147fc6fdb`; whether the player's own ship (not AI-run) uses any of this (its gunnery is manual); the AA launch code `FUN_14002e3a0` beyond what ai-tick-patch-sites.md already records.
