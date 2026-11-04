# Ghidra sweep 2026-10-29 — batch 7, agent 5 (`rep_*` re-match, 0x140337000–0x140350510, non-funclet)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `rep_*` function whose entry is in **0x140337000–0x140350510** and
which is **not** listed in `funclet-ownership-2026-10-29.tsv` (agent 1 owns the
funclet set).

* `rep_*` in range at start: **157**
* of those, funclets owned by agent 1 (`funclet-ownership` TSV): **82** — not touched
* **in my scope: 75**, all in **0x14034ba30–0x140350410** (the whole of
  0x140337000–0x14034b02f is funclet territory)
* **75 renamed and plated**, **0 stale**, **0 unreadable**
* no `save_program`, no tags, no README/STATUS edits, no commits, no `create_function`

Audit table: `rep-audit-2026-10-29-q4.tsv` (appended 75 rows; file now 125 data rows).

## Result: this is the MSVC atexit static-destructor tail

Every one of the 75 is a **no-argument global destructor registered with the
atexit table**, and the tail already contained **62 functions named
`DtorGlobal_*`** (0x14034b780–0x14034fe40) from an earlier pass. So the naming
convention was not invented here — it was matched:

* `DtorGlobal_<Global>` when the destroyed global has an `InitGlobal_<Global>`
  constructor counterpart (28 of mine, 34 of the pre-existing 62),
* `DtorGlobal_Container_<addr>` for an anonymous heap-owned aggregate
  (vector / intrusive-tree sentinel / pool),
* `DtorGlobal_String_<addr>` for an anonymous `std::string`,
* semantic names where the global already carries one (`DeadJointList`,
  `GUI_ELEMENTS`, `PLANE_TLL`, `buildingCodes`, `aaDefenseList`,
  `ProfileListStart`, `KEYBOARD_LAYOUT_`, …).

Name-uniqueness check after the run: **0 duplicate `DtorGlobal_*` names**; the
range now holds **137** `DtorGlobal_*` = 62 pre-existing + 75 new.

## The three body shapes (all proven from the decompiled body)

1. **`std::vector` global** (begin/end/capacity at +0, +8, +16) — 40 of the 75.
   ```c
   if (begin != 0) {
     /* MSVC sized-delete header check */
     if (0xfff < (cap - begin) && bad_header(begin-8)) _invalid_parameter_noinfo_noreturn();
     free(begin);
   }
   begin = 0; end = 0; cap = 0;
   ```
   The `_invalid_parameter_noinfo_noreturn` reference in the *embedded* label is
   what makes the fake import name look plausible — the call is the MSVC
   `_Container_base`/sized-delete trap, not an import of that function.
2. **`std::string` global** (SSO buffer/size/capacity at +0, +0x10, +0x18) — 7.
   `if (cap > 0xf) free(ptr); size = 0; cap = 0xf; buf[0] = 0;`
   (`ShopDisplayString`, `contaminationShipName`, `DialogPath`,
   `LVL_BACKGROUND_LEN_`, and 3 anonymous ones).
3. **intrusive red-black container sentinel** — 22. Walks the node chain,
   `freeLinkMemory_`/`RbTree_DestroySubtree`/`NPC_DestroyRange`/
   `TreeNode_DestroyRecursive` per payload, frees each node, then the sentinel.
   Two are richer: `DtorGlobal_SliderStateLinks` (vector of pointers **and** a
   tree) and `DtorGlobal_KeyBindingLink` (`std::map<std::string,Link>`).
   Separately, two `ostream` globals (`Client.logStream`, `Error.logStream`) run the
   `basic_ostream`/`basic_ios` destructor chain instead.
4. **single-block pointer** — `DtorGlobal_Container_143a15a50`,
   `DtorGlobal_LogTextLink` (44 B each).

## How identity was established (not from the embedded address)

* **Thunk pairing.** Each destructor has a 7-byte thunk in the `.CRT` init band:
  `LEA RCX,[<dtor>]; JMP 0x14033447c` (atexit registrar), e.g. 0x140001230 →
  0x14034bbb0, 0x140001240 → 0x14034bc20. Those thunks are **not** function
  objects, which is why `getFunctionContaining` returns nothing for them.
* **Global pairing.** For 28 the destructor's global is exactly the global the
  `InitGlobal_<X>` constructor writes, so the pair is proven by address.
* Beware the noise trap: every destructor references the shared CRT stubs
  (`PTR__invalid_parameter_noinfo_noreturn_1403517c0`, 0x14033447c, 0x140334094)
  and low stack offsets, so a naive `getReferencesTo` link makes
  `InitGlobal_GraphicsBufferA/B/ChnVectorPool` match *all* 75. Restricting
  candidate globals to the writable data bands (0x1403a0000–0x140400000 and
  ≥0x143900000) collapses the match to exactly the right one. Worth remembering
  for the remaining `rep_*` agents.

## Confirmation of the batch-6 finding, for this sub-range

All 75 embedded labels are `ctx_0x14031f000–0x140324300` stale addresses
(`rep_14031fef0_…free` at 0x14034ba30, … `rep_140324290_…free` at 0x140350410).
The embedded targets are **not** copies of the bodies: the sizes are wrong for
the claimed imports (44–259 B "`free`"/"`_invalid_parameter_noinfo_noreturn`"),
and the targets lie in the live Box2D/HUD band that batch 6 proved is real code.
Same conclusion as batch 6: parse the embedded address only to record it; never
as evidence. Here **0 of 75** were left stale because the body + thunk pair was
always sufficient.

## Not touched / handed on

* The 82 in-range `rep_*` that **are** in `funclet-ownership-2026-10-29.tsv`
  (0x1403372d0–0x14034b02f) — agent 1.
* **68 `FUN_*` in the same tail** (0x14034b850–0x140350410) are the *same*
  destructor family — identical 12/101/105-byte shapes (`FUN_14034bc90`,
  `FUN_14034bf60`, `FUN_14034c610`, `FUN_14034cf60`, `FUN_14034d320`,
  `FUN_14034e150`, …). They are `FUN_*`, i.e. agent 8/9 territory, so they were
  left alone; whoever takes them can reuse this note and the `DtorGlobal_*`
  convention directly (each is a `LEA RCX,[global]` thunk pair one 0x10 earlier).
* No `create_function` was needed: all 75 already had function objects.

## Counts

* `rep_*` in scope: **75**
* renamed + plated: **75** (40 `std::vector`, 22 intrusive-tree/list + 1 tree+vector,
  1 `std::map`, 7 `std::string`, 2 `ostream`, 2 single-pointer)
* stale label: **0**
* unreadable: **0**
* left in scope: **0**
