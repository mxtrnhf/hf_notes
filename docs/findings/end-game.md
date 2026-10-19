# The end game: `spawnEndgameShips_` and what it sets (1.151 read, 1.163 located)

Status: **read from the 1.151 decompilation; 1.163 counterpart located (see [the Khiva crash section below](#the-khiva-end-game-crash-unguarded-list-writes-1163-probable-cause)); not run in game.** Tags: legend in `../../README.md`.

Present in 1.151 as a named function; **not matched** by the fuzzy tool, **located by hand in 1.163 as `FUN_140261a20` (the Khiva crash section below)**. It is the scripted collapse that begins the "nuclear war" and closes the campaign. Read from the
1.151 decompilation (very long: three-way list sorting plus spawns).

* **Cities used by name:** `KHIVA` (the capital) and `BASRA`. Everything is positioned relative to `KHIVA`'s position.
* **Phase 1, sort the garrisons:** it walks the profile's city list (the vector at Ghidra offset 456/464) and drops those that already have a hostile fleet with `side > 0` within `700.0`. The remaining cities (with
  `moid+0xc != 0`, i.e. an active flag) are split into **four lists by quadrant relative to Khiva** (x below/above, y below/above) and each list is sorted by distance (`MergeSortObjectListByScratchKeyDescending`,
  key at `+0xf8`). The first city of each list gets state `2` at `+0x19c`.
* **Phase 2, strike groups:** from the cities with state `2` it picks one at random and spawns `spawnEndgameStrikeGroups_(strength 100.0, -1.0, position, name, 1)` for each; every fleet gets type `6`, its
  target set to Khiva's position, and enters the profile fleet vector; their `moid+0xc` is set to `3`.
* **Phase 3, reinforcement search:** up to **100 tries** to find a city (`+0x2e8 > 1`, active, 2000 to 4000 units from Khiva, not already occupied by a hostile fleet) and spawn another strike group
  there with strength `200.0` (normal) or `300.0` (hard mode, `Profile.hardMode`). Fleets from this phase get ships `Tarantul` (66%) or `Tarantul ARM` (34%).
* **Phase 4, garrison ships:** for every city with garrison strength it spawns ships through `somethingSpawnShips` (divides the strength by `20.0` or `50.0` depending on the city kind) and copies up to 3 of
  the generated names into the city record.
* **Finale:** `BASRA`'s record is cleared; then, **"Start the nuclear war"** (logdot's comment): if `Profile.escalation == 0` it shows `THE_BEGINNING` / `NUCLEAR_WAR`, plays `dram_hit_01`, and sets
  `escalation = max(escalation, 1)`; finally **`Profile.endWar = true`**. This is what `GetPartPrice` (version-differences.md, stats record) checks, so after this function runs, part prices become 0.

* **Lead for the Khiva crash/loop bug: superseded.** The first write to each of the four quadrant lists is **unguarded**, in both versions; the 1.163 counterpart `FUN_140261a20` is located. Cause, patch recipe and confirmation: [the Khiva crash section below](the Khiva crash section below).

## Other differences between the 1.151 and 1.163 versions of the function [code]
The phase structure, the `100.0/200.0/300.0` strike strengths (`hardMode`), the `2000`-`4000` search ring, the `700` exclusion and the `Tarantul` split (66%) are unchanged. 1.163 adds `CopyEscadraName` calls with a state flag set through bit marks (`local_234 |= 1/2/4`, unused locals as far as seen). The Ghidra names `escalation`/`enigmaKey10` at offsets 660/744 come from the stale 1.151 `Profile` struct: at the shifted layout they line up with 1.151 `escalation`/`endWar`; the two names are not resolved.

## The Khiva end-game crash: unguarded list writes (1.163, probable cause)

Status: **probable cause found in the code; not reproduced in game; no patch applied.** Tags: legend in `../../README.md`.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe) unless marked 1.151. Origin: roadmap bug "capturing all cities around Khiva before the end-game event causes a crash loop / infinite loading".

### Short answer
The end-game function builds four lists of eligible cities (one per quadrant around Khiva) and then writes `city.state = 2` to the **first element of each list without checking that the list is non-empty**. An empty list holds only a sentinel node whose payload slot is uninitialised heap, so the write goes through a stale pointer. If the player has captured every city in one quadrant, that quadrant's list is empty.

### Where
* **The function** [code]: 1.163 `FUN_140261a20` (`0x140261a20`-`0x140263534`, unnamed in Ghidra). 1.151 counterpart: `spawnEndgameShips_` (`0x14023fa80`). Found by following the strings `NUCLEAR_WAR` and `dram_hit_01` and confirmed by an almost identical callee set and body (`KHIVA`, `BASRA`, the 100-try search, `Tarantul` / `Tarantul ARM`, `THE_BEGINNING`).
* **Its caller** [code]: `0x1402b8af2`, inside the level-script (`SCR_MAP`) handler. No function is defined in Ghidra at that address range (the same gap as `0x140117840`). The call is preceded by a gate on three values (bytes `0x1402b8a27`-`0x1402b8a47`): profile `+0x2ec` non-zero, profile `+0x2e9` zero, global byte `0x147fc6fca` zero. These look like `escalation` and `endWar` at their shifted 1.163 positions (the Ghidra `Profile` struct is the stale 1.151 layout, `+0x58`: `endRace` `0x2e8`, `endWar` `0x2e9`, `escalation` `0x2ec`). **[guess]** that reading is unverified and sits oddly with the function's own `if escalation == 0` branch; do not rely on it.

### The unguarded writes [code]
At `0x140262226`-`0x140262279` (84 bytes, four blocks of 21 bytes), straight after the four sorts:

| Block | Bytes | Meaning |
|---|---|---|
| 1 | `48 8b 45 f8` `48 8b 00` `48 8b 40 10` `c7 80 9c 01 00 00 02 00 00 00` | `rax = [rbp-0x8]` (list head); `rax = [rax]` (first node); `rax = [rax+0x10]` (payload, the city); `[rax+0x19c] = 2` |
| 2 | same, `[rbp-0x18]` | list 2 |
| 3 | same, `[rbp-0x28]` | list 3 |
| 4 | same, `[rbp-0x38]` | list 4 |

1.151 has the same four writes at `0x140240266` (decompile: `*(int*)(*(longlong*)(first_node + 0x10) + 0x19c) = 2` for each of the four lists, immediately after the four `MergeSortObjectListByScratchKeyDescending` calls).

### Why an empty list is the trigger
* The lists are circular with a sentinel: each is `New(0x18)` (a plain `operator new` wrapping `malloc`, no zeroing) with only its two link fields set (`next = prev = self`). For an empty list `first_node` is the sentinel itself, and `[sentinel + 0x10]` is whatever the heap held.
* A list is empty when no city in that quadrant passes the filter. The filter, in the first loop: the city's state `+0x19c` must be non-zero, and no fleet on the player's side (side float `> 0`) may be within 700 units of it. The quadrant is chosen by comparing the city position with Khiva's (`+0x150/+0x154`).
* **[guess]** "captured cities have state 0 or a friendly fleet within 700, so they drop out of every list". Capturing all cities of one quadrant therefore empties that list. Only one empty list is needed.
* **[guess]** If this function runs on load of such a save, the game would crash on every load, which looks like a crash loop. The hypothesis fits "crash loop / infinite loading" but was not run.
* What the stale pointer does is undefined: a crash if it is bad, silent heap corruption if it is not.

### What is *not* the cause
Everything after those four writes is guarded (the later loops test emptiness and null). The 100-try city search is bounded.

### Patch recipe (not applied, untested)
A function-entry-style detour (`hooks.md` technique: a 14-byte `FF 25 00000000 <abs64>` jump, trampoline in a `VirtualAlloc` page) at `0x140262226` over those 84 bytes, returning to `0x14026227a`. The stub, for each of the four list pointers at `[rbp-0x8]`, `[rbp-0x18]`, `[rbp-0x28]`, `[rbp-0x38]`:
`first = *list; if (first != list && first[2] != 0) first[2]->+0x19c = 2;`
Version guard: compare the 84 bytes before patching. What the game *should* do when a quadrant is empty is a design question; the guard only stops the wild write.

### How to confirm before patching
1. Take a save with Khiva reachable; capture every city in one quadrant around it (or edit the save so those cities are captured) and trigger the end-game event. Expect the crash at the faulting address near `0x140262231`-`0x14026226d`.
2. Better: with the crash-capture tool from the roadmap tooling list, log the faulting RVA once. A hit inside the four blocks above confirms this note.
3. Or, with no game launch: read the list-building loop in the first part of the function (`0x140261a20` up to about `0x140261f16`; exact start not pinned) and the city record layout (`+0x19c` state, `+0xf8` scratch distance key) to confirm that captured cities leave the lists.
