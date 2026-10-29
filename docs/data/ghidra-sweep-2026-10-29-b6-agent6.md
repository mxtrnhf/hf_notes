# Ghidra sweep 2026-10-29 — batch 6, agent 6 (large functions, set A)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the six assigned addresses only. All six were read to the point where the
behaviour was clear, so **6 renamed, 0 skipped, 0 created**. Every rename carries a
plate with summary / `Algorithm:` / `Parameters:` / `Returns:`.

| addr | size | new name |
|---|---|---|
| 0x14021cf40 | 8,696 | `Shipworks_BuildAutoRepairSteps` |
| 0x140211e60 | 1,404 | `Grid2D_MergeAdjacentCells` |
| 0x1402130b0 | 105 | `Gui_BlackoutOverlay_BeginClear` |
| 0x140213fc0 | 109 | `Gui_BlackoutOverlay_BeginOpaque` |
| 0x140216f00 | 356 | `Fleet_RebuildShipListByValue` |
| 0x14021b110 | 117 | `Scene_CloneNodeSubtreeByName` |

No `save_program`, no tags, no README/STATUS edit, no commit.

## Evidence per function

### 0x14021cf40 — `Shipworks_BuildAutoRepairSteps` (the 8.7 KB one)

Only call site is `repairSlider?` (0x140267b60), which plays the shipworks repair
screen: it calls this function as
`FUN(&DAT_1403ef4b0, <shipworks window>, Profile_GetFirstPlayerCreature(profile))`,
then tests `DAT_1403ef4b0 != DAT_1403ef4b8` (i.e. "did the vector become non-empty?")
and only then builds `AUTO_REPAIR_BACK / AUTO_REPAIR_TXT / AUTO_REPAIR_SLIDER /
AUTO_REPAIR_SLIDER_FRAME / _OK / _CANCEL / _HELP` (0x140267c08 onwards).

The consumer proves what the output is: `Gui_HandleSliderChange` (0x1401574b0) has an
`AUTO_REPAIR_SLIDER` branch that computes
`count = (DAT_1403ef4b8 - DAT_1403ef4b0) >> 3` and calls
`List_MoveCursor(&DAT_1403ef4b0, (int)(value*count) - 1 - DAT_1403ef4d8)` — i.e. the
vector is an ordered list of one step per list entry and `DAT_1403ef4d8` is the current
cursor. So the routine *rebuilds the auto-repair step list*; it applies no repairs.

Inside the body (decompiled 71 KB, read in windows):

* prologue (0x14021cf40–0x14021d03f) validates `param_2->+0x48` (ship linked to the
  widget), non-null `param_3`, `*(float*)(param_3+0xb60) != 0` and the type nibble
  `*(byte*)(node+0x28) & 0xf == 0xf` on two resolved nodes;
* it frees every element of the pointer vector at `param_1+0x00` (stride 8, `free`),
  sets `param_1[1] = param_1[0]`, frees the buffer at `param_1+0x18`,
  `*(int*)(param_1+0x28) = -1` (cursor), `param_1[6] = param_2` (+0x30 window),
  `param_1[7] = param_3` (+0x38 creature);
* `Body_RebuildSubtreeList` on the creature, then a walk of the part list. Per part it
  resolves the name string at `part+0x190` (`+0x1a8` is its SSO capacity), runs the
  profile lookup `0x140286ce0(Get_Profile_(), name)` and
  `0x1400f31c0(PLAYER_ESCADRA_, name)`, and on success does
  `GetValue(part)` (stats `+0x88`) into a price/float slot;
* the only `RepairStepNewBlock_Constructor` call in the binary is here
  (0x14021eca6): `new(0x28)` + `(this, R12, RDI, [RBX+0x20], [RBX+0x24], R15B)`,
  then `Vector8_PushBackRealloc(param_1, &step)`. `RBX+0x20` is used two blocks
  earlier as a bound-checked index into a pointer vector at `+0x350`
  (`([+0x358]-[+0x350])/8`), which is what raises the `CHECK ERROR: %s, %d`
  `main.cpp` line 0x691e (26910) — the strings `s_CHECK_ERROR:_%s,_%d_140352588`
  and `D:\!ESSENTIALS\PROJECTS\HYBRID_FLEET 2013EX\main.cpp` are the only strings in
  the function.

So: a step is `{body, part, index, index, flag}` built from the ship's live hull part
tree, priced with the same `GetValue` used by the shipworks shop.

### 0x140211e60 — `Grid2D_MergeAdjacentCells`

Sole caller is the ICF chunk `rep_1402169a0_tooLongError` (0x140234a50) at
0x14023511e; that chunk builds an RB-tree of grid entries and then, for every cell,
calls the ICF chunk at 0x140231550 with 12 neighbour flags (`x < w-1`, `0 < y`,
`y < h-1`, `y < h-2`, …) — i.e. a border/neighbour mask per cell. This function is the
compaction pass that runs first (the caller loops `while (FUN(...) != 0)`).

Descriptor is `param_1 = {int w, int h, cellNode*, vector<Entry>*}`; cell nodes carry
four neighbours at +0x10/+0x8/+0x18/+0x20 and an id at +0x28; `Entry` stride is 0x18
(`{int w, int h, void *data, pad}`). The routine merges a horizontal or vertical run
when the neighbouring cell's `Entry` still has the same width/height, checks that the
whole run shares the id, then zeroes the consumed Entry's w/h, accumulates the counts
into `param_1[0]/param_1[1]` and rewrites the id of every covered cell. Out-of-range
entries raise `std::out_of_range` (0x14019f9c0). Returns 1 if anything merged.

**Caveat recorded:** the *consumer* is an unnamed HUD chunk, so the grid's game meaning
(table cells vs. map cells) is not proven. The name stops at the algorithm, which is
fully proven by the body.

### 0x1402130b0 / 0x140213fc0 — `Gui_BlackoutOverlay_BeginClear` / `_BeginOpaque`

Both are get-or-create wrappers around the singleton `DAT_143a13b08`, and both are
called from ~40 places (`creatureLogic`, `creditsScreen?`, `VariousHUDDisplays?`,
`Camera_DeathCamFocus`, `Landing_BuildPrelandingPanel`, `!ClickFunc`, the big
`SomethingWithLevelSerias` switcher, …); several call sites inline the whole body
(e.g. 0x140251ed5, 0x1401dbe4e, 0x140230bae).

Constructor `rep_1401b50b0_New` (real entry 0x1401ca120) allocates 0xe70 bytes,
calls `GUI::GUI_2`, adds the element to `GlobalNode?` (+0x50), calls vtable +0x2c0 with
shader **"BLACK"** (0x140353818) and sprite **"flash_large_shadow"** (0x140353628) at
full frame width/height, then sets:
`+0x3cc = (mode^1)*2` (state), `+0x8f8 = mode ? 0.0 : 1.0` (alpha — the same `+0x11f`
slot the other GUI builders write 1.0/0.05 into), `+0x3d0 = float`, `+0x3d4 = colour`,
`+0x8f0`, `+0x8d8`, `+0xa38`, links at +0x490, +0x3c8=1.

State machine (provable from both bodies): wrapper A (mode 1) arms state 0 and returns
true when the state is already 1; wrapper B (mode 0) arms state 2 and returns true when
the state is already 3. Callers use it as the screen "BLACKOUT": the GUI event string
`"BLACKOUT"` (0x140370208, next to `SOUND`/`MUSIC`/`AMBIENT`) is dispatched to
`Gui_BlackoutOverlay_BeginOpaque` with duration 5.0 and colour `0xff000000` at
0x140230bae; `Camera_DeathCamFocus` uses 0.3, `Landing_BuildPrelandingPanel` 0.5.

**Why the names are "BeginClear"/"BeginOpaque" and not "FadeIn/FadeOut":** the initial
alpha is proven (0.0 vs 1.0), but which state (1 vs 3) means "fully black" is not
proven, so a directional name would be a guess. If a later pass establishes the
direction they should become `Gui_BlackoutOverlay_FadeToBlack` (the mode-1/state-0 one)
and `..._FadeFromBlack` (the mode-0/state-2 one) — do not assume, the "BLACKOUT" event
handler calls the mode-0 one.

### 0x140216f00 — `Fleet_RebuildShipListByValue`

Iterates `DAT_143a13a70->+0x100` (scene root children). A child qualifies when
`+0x108 != 0` and its property chain (`child+0x100 -> [+0x10] -> +0xb8`) yields a
creature with `*(float*)(creature+0x1604) != 0` (the battle TWR) and
`compData(Get_Profile_(), creature) != 0`. `compData` (0x140293940) looks up the
creature name `+0xa90` in the active profile's unlocked-ship tree (`+0x430`) — the same
`Fleet_SetCompData` family.

For each hit it writes `*(int*)(child+0xf8) = *(int*)(creature+0x15d0)` and appends the
child to `param_1` (a std::list of 0x18-byte nodes). Then it sorts:
`List_MergeSortByCreatureKeyAsc` sorts by `element->+0xf8` as a float ascending;
`Sort_MedianOfNByCompData` is used when `BOOL_147fc6f80` / `DAT_147fc6f81` are set.

Call site 0x140138991 (`ED_SHPWRK_BUY_SHIPS` handler in `!ClickFunc`): clears the list
with 0x1400a16d0, rebuilds it here, then calls `Fleet_FindSevastopol` on the same list
(to exclude the flagship from the purchase list) and copies the shipworks colour
globals. So the list is the player fleet's scene nodes ordered by ship value.

**Field bonus:** `+0x15d0` is written in exactly one place in the whole program —
`Creature_AccumulatePartStats` (0x14007171d), as a running sum of
`GetValue(part)` (0x140048b80 = `Stats+0x88`) over all parts. `CalculateStats`
(0x14007fcf0) saves it before recalc and, when it dropped, adds the delta to `+0xc94`.
Naming it **ship total value** is safe for docs; it is not health.

### 0x14021b110 — `Scene_CloneNodeSubtreeByName`

`param_1` = source object, `param_2` = key, `param_3` = destination container.
It calls `[param_1->vtable + 0xb8](param_1, param_2)` (a "get linked object by key"
accessor — the same slot `GetPropertyLinkedObject` reads), and if that returns an
object calls 0x1401bfa10, which flattens the node tree via `Creature_CountSubtree` /
`Creature_FlattenTreeIntoVector` / `CopyObject`, re-links the copies with `Node::add`
and re-ids the root. Finally, when `param_3 != 0`, it adds the copy with
`[param_3->vtable + 0x50](param_3, copy, 0, 0)`.

Only caller is `rep_14006f720_New` at 0x140073242:
`RCX = [0x143a13a70]` (scene root), `RDX = this+0xa90` (the string name), `R8 = 0`,
followed by 0x14021b070 / 0x1402199e0 on the returned copy — i.e. "find the scene node
with this name and clone its subtree". The two `[DATA]` xrefs from 0x14039f09c /
0x14039f0ac are `.pdata`, not a vtable (matches the batch-5 observation).

## Cross-batch notes

1. `+0x8f8` (= `[obj+0x11f]` in the GUI builder style) is the GUI element **alpha**
   (1.0 opaque, 0.05 fades). `+0x3cc` is a common int state on the same elements.
2. `DAT_143a13b08` (blackout singleton), `DAT_1403ef4b0` (auto-repair state block) and
   `DAT_143a13a70` (scene root) are now identified; the auto-repair block layout is
   `+0x00 vector<RepairStepNewBlock*>`, `+0x28 int cursor`, `+0x30 GUI window`,
   `+0x38 creature`.
3. `RepairStepNewBlock` (vtable 0x140369328, RTTI `.?AURepairStepNewBlock@@`,
   0x28 bytes) = `{+0x08 body, +0x10 part, +0x18 int, +0x1c int, +0x20 byte}`.
4. The `rep_*` chunks 0x140234a50 and 0x140231550 in this window are not standalone
   functions — they are ICF replicas of HUD/`main.cpp` code; 0x140231550 is inside
   `VariousHUDDisplays?` (0x14022c980), so do not rename them on the embedded label.

## Open questions

* Which blackout state (1 or 3) is "fully black"? Needed to replace
  `BeginClear`/`BeginOpaque` with directional names.
* Who consumes `Grid2D_MergeAdjacentCells`' grid? The caller chain is
  `VariousHUDDisplays?` chunks only.
