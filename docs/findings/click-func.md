# ClickFunc: the GUI click handler (structure, element names, decompiled branches)

The function that decides what an accepted GUI click does. It is huge, and it is where every button, list row and slider reaction lives.

## What it is
| | v1.151 | v1.163 |
|---|---|---|
| Entry | `0x1401261d0` | `0x14012f120` |
| Ghidra name | `!ClickFunc` (a real name; the leading `!` is only how this database shows it) | `FUN_14012f120` (not renamed) |
| Body | `0x1401261d0`-`0x14013435f`, 0xE190 = 57,744 bytes | `0x14012f120`-`0x14013e45f`, 0xF33F = 62,271 bytes |
| Only caller | `?HandleClick` at `0x140124300` | `?HandleClick` at `0x14012d050` |
| String reference | "GL_CLICK_AND_CLOSE" (`0x1403383c8`) at `0x1401262ba` | "GL_CLICK_AND_CLOSE" (`0x140364618`) at `0x14012f207` |

[game] in Ghidra, read-only. Same shape, same caller name and same string, so `FUN_14012f120` is the 1.163 version of `ClickFunc` [code, strong; matched by shape, not a byte-for-byte diff]. Suggested name for the 1.163 database: `ClickFunc`. Renaming is left to the user (the database is treated as read-only here).

Size [observed, v1.163, read-only Ghidra script]: decompiling `FUN_14012f120` gives **8,589 lines** of C, **538,685 characters**, from a function body of 62,272 addresses. The user had heard "10,000+ lines"; Ghidra's line count depends on decompiler width settings, so this is the same order of magnitude. The decompiler needed its payload limit raised (default fails with "Response buffer size exceeded"); it took about 45 s with max payload 1000 MB.

Source file [game]: the string xref shows Gui.cpp's `__FILE__` string (`0x140363628`) is referenced from `FUN_14012f120` (`0x14012f120`), so ClickFunc lives in Gui.cpp. See [source-file-names.md](source-file-names.md).

How to decompile a huge function through the Ghidra MCP [observed that it worked]: scripting enabled with `GHIDRA_MCP_ALLOW_SCRIPTS=1` when starting Ghidra, then a Java script with `DecompileOptions.setMaxPayloadMBytes(1000)` and `DecompInterface.setOptions`.

## Structure (measured 2026-10-14, v1.163 FUN_14012f120 = ClickFunc)
All [game], from a read-only Ghidra script.

| Measure | Value |
|---|---|
| Instructions | 13,172 |
| Basic blocks | 4,343 |
| Conditional jumps | 1,358 |
| Unconditional jumps | 381 |
| Computed jumps | 0 (so no jump tables: no compiled `switch`) |
| Calls | 2,276 (162 indirect) |
| Returns | exactly 1 |
| Distinct string constants referenced | 476 |
| Distinct callees | 294 |

Decompiled C (8,589 lines, default decompiler settings): 941 `if`, 121 `else`, 5 `else if`, 0 `switch`, 0 `case`, 324 `goto`, 67 labels, 48 while/do, 30 for. Nesting, real brace-depth measurement [observed, read-only Ghidra script]: maximum depth **40** (first reached at decompiled line 6838), final depth 0. Lines per depth cluster at depth 4 (610 lines), 5 (551), 12-14 (about 500-560 each), 33 (421) and 35 (588); `if` statements per depth go up to 140 (at depth 4). The earlier figure "maximum nesting about 79 levels" was measured from leading spaces and is **inflated** by the indentation of wrapped-line continuations; ignore it. The `if (name == X) {..}` tests are siblings in the chain at the same level (observed in the four branches in [click-func.md](click-func.md#decompiled-branches-v1163)). The deep clusters (depth 12-14, 33, 35) are not yet explained; whether the editor tests are nested under "no match yet" conditions is unchecked.

Most-called callees (names in `?` are Ghidra database names, a [guess] about meaning):
| Address | Name | Calls |
|---|---|---|
| `0x140004a70` | stringCompLengthAndContent | 256 (the element-name comparison: about 256 name tests) |
| `0x140006d70` | FUN_140006d70 | 185 |
| `0x140292a90` | Get_Profile? | 103 |
| `0x140015390` | copyIntoEscadraName? | 103 |
| `0x1401a9170` | FindGuiElement | 89 |
| `0x1400530e0` | diffArrayDivBy24 | 73 |
| `0x1402e30e0` | playSFXSound? | 60 (the sound hook of the probe) |
| `0x140049e00` | FUN_140049e00 | 52 |
| `0x14033659a` | memcmp | 42 |
| `0x140023940` | escadraStringToStr? | 40 |
| `0x1400188e0` | multElementsBy24 | 39 |
| `0x14012a4b0` | FUN_14012a4b0 | 37 |
| `0x140194de0` | SetLink | 33 |

Interpretation [code, from the numbers above]: this is one huge chain of independent `if (name == "...")` style tests plus deeply nested logic, not a switch and not a table; it reaches its single return through gotos. A click walks the tests until its element name matches; the cost is negligible. The Ghidra names (Get_Profile?, copyIntoEscadraName?, diffArrayDivBy24, multElementsBy24) are guesses [guess], but they suggest the handler does fleet/profile work directly (shop, fleet naming, etc.), i.e. it contains game logic, not only UI dispatch. (Giant if-chain functions like this are common in other games too.)

## What the probe knows about it
`hf_probe` hooks its entry (26 stolen bytes) and logs `CLICK` lines. Arguments: RCX = ctx, RDX = `gui*`, R8D = button, R9 = `[gui+0xa80]`. The GUI element name is at `gui+0xa40`, its class string at `+0x8`, the fx/distortion name at `+0xad8`. Verified detail is in [ui-events-and-screens.md](ui-events-and-screens.md); not copied here.

## Element-name catalog
The GUI element names that `ClickFunc` compares a clicked element against: 252 unique names from 256 compare calls, in [../data/clickfunc-elements.tsv](../data/clickfunc-elements.tsv) (columns: group by name prefix, address of the first test, name, number of `CLICK` lines that carried it, mod idea). It is a **lower bound**, not the full list of clickable elements.

**Method [code]:** a read-only Ghidra script collected every call to `stringCompLengthAndContent` (`0x140004a70`) in `FUN_14012f120` and took the string literal found within 10 instructions before the call as the compared name. A literal is paired with the nearest preceding string reference, so a few pairings could be wrong; not hand-verified per entry [guess about accuracy]. Groups are by prefix, not by verified screen [guess]. Names tested twice or more carry `(xN)` in the table (`ED_SHPWRK_EXIT` x3, `KEY_SPACE` x2, `KEY_ESC` x2). One test at `0x140135d75` had no readable string nearby and is listed as `<none>`.

**Numbers [game]:** 43 of the 252 names appear in the CLICK logs of the 4 probe runs (`hf_probe_build/logs/*/probe.log`) plus the current `probe.log`; 209 were never seen. The function also calls `FindGuiElement` x89, `memcmp` x42 and `FUN_140006d70` x185, so other elements are matched by other means (prefix compares or similar) [guess].

Names relevant to mod ideas (buy/refuse, supplies, landing, map, test buttons):

| First test | Name | Seen |
|---|---|---|
| `0x1401328f9` | `MAP_LOCATION` | 4 |
| `0x140132e1b` | `MAP_ESCADRA` | 5 |
| `0x140134722` | `MAPMODE_MISSION_FULLTANK` | - |
| `0x1401347fe` | `MAPMODE_MISSION_HALFTANK` | - |
| `0x1401351c1` | `EDC_TEST_LANDING` | - |
| `0x1401355c8` | `PRELANDING_OK` | 2 |
| `0x140136a49` | `LANDMODE_SHIPWORKS` | - |
| `0x1401370b1` | `LANDMODE_EXIT` | 6 |
| `0x1401370db` | `SUPPLIES_EXIT` | 5 |
| `0x1401370fa` | `SUPPLIES_AMMO` | 4 |
| `0x14013712d` | `AMMO_BUY_ENTRY` | - |
| `0x140137140` | `FUEL_BUY_SLIDER` | 3 |
| `0x140138564` | `BUY_BUY` | 4 |
| `0x1401386ff` | `BUY_REFUSE` | - |
| `0x14013d7b7` | `EDC_TEST_FIGHT` | 2 |

### Names seen in CLICK logs but not in the catalog [game]
`?`, `BUY_SLIDER`, `EDC_SAVELOAD`, `EDC_TEST`, `EDC_TEST_DIF`, `ED_CREATE`, `ED_IMAGE_MASK`, `ED_IMAGE_SCALEX`, `ED_OBJECT`, `ED_OBJECT_PANEL`, `ED_OBJ_IMAGE`, `ED_OBJ_MESH`, `ED_OBJ_PROP`, `ED_OBJ_SLOTS`, `ED_SAVELOAD`, `GL_LIST_BUTTON`, `INV_SLIDER`, `INV_SLOT`, `LOOT_BOX`, `MAPMODE_LAND`, `pN#8`.

These are handled by something other than a plain `stringCompLengthAndContent` against a literal (prefix test, `FindGuiElement` lookup, `memcmp`, or a pointer compare) [guess]. Several look like containers, sliders or lists (`*_SLIDER`, `*_SLOT`, `ED_OBJ_*`, `*_PANEL`), which fits a different matching path.

## Decompiled branches (v1.163)
Four branches of `FUN_14012f120`: BUY_BUY, FUEL_BUY_SLIDER and the MAPMODE_MISSION fuel presets. Code blocks are cleaned by hand from the Ghidra decompilation [observed, read-only]; decompiled line numbers are for the default decompiler setting.

### BUY_BUY (compare at `0x140138564`, decompiled lines 4119-4174)
```c
if (stringCompLengthAndContent(name, "BUY_BUY")) {
    panel  = FindGuiElement("BUY_PNL");
    slider = FindGuiElement("BUY_SLIDER");
    CopyEscadraName(buf, panel + 0xc10);
    ammo   = filterAmmos(escadraStringToStr?(buf));
    wanted = (int) slider->vtable[+0x2f8]();
    owned  = FUN_14028c460(Get_Profile?(), escadraStringToStr?(buf));
    delta  = wanted - owned;
    if (delta == 0) {
        sound = "switch_press"; volume = 0x42a00000;   // 80.0f
    } else {
        <adjust location stock>(CURRENT_LOCATION, name, -delta);
        if (delta < 1) <profile remove>(profile, name, abs(delta));  // Ghidra: ...free
        else           loadAmmoForLocation?();
        price = *(int *)(ammo + 0x170);
        FUN_1400ba3a0(Get_Profile?(), price * delta, 0);   // gold change
        sound = "sold_01"; volume = 0x41c80000;        // 25.0f
    }
    playSFXSound?(0xb, sound, GlobalNode?, volume);
    <gui virtual +0x48>();
    supplyRoom();
    free(buf);
    goto LAB_14013e3fe;   // end of click handler
}
```
Interpretation [code for the data flow, guess for the names]: the shop slider is a **target total**. BUY_BUY applies `delta = slider - owned`, so it both buys (delta > 0) and sells (delta < 0). The gold change is `ammo+0x170` (unit price, matches the structures/ammo notes) times `delta`; this ties to the GOLD lines of the probe log (-18660 etc).

### FUEL_BUY_SLIDER (`0x140137140`, decompiled lines 3504-3556)
```c
if (stringCompLengthAndContent(name, "FUEL_BUY_SLIDER")) {
    if (CURRENT_LOCATION == 0) goto end;
    value = *(float *)(gui + 0xc0c);
    // tutorial path
    if (DAT_143a11880 == value && profile.cash(+0x2a8) == 0) {
        CreateTriggerBlank(&profile + 0x3f0);      // trigger "TUTORIAL_FUNDS"
        validateNpc?(profile, "PETR");
        formDialogStrings?(... "TUTORIAL_FUNDS_1" ...);   // dialog
    }
    if (*(float *)(CURRENT_LOCATION + 0x274) == value) goto end;
    sound = "sold_01"; volume = 25.0f;
    goto LAB_140131632;     // shared fuel-apply code, not decompiled yet
}
```
Interpretation [guess] (superseded in part: [systems.md](../systems.md) Refueling and [structures.md](../structures.md) read `+0x274` as the station's fuel stock [game]; the slider compare below fits that): `CURRENT_LOCATION+0x274` (f32, previously unexplained in [open-questions.md](../open-questions.md), item "Location and click fields") is compared against the fuel slider value, so it likely holds the fuel amount currently set/bought at the location. The actual apply code is at `LAB_140131632` (not read). Note `structures.md` and `systems.md` already call `+0x274` the station fuel stock (it feeds the fleet refuel formula); both readings may hold, unchecked.

### MAPMODE_MISSION_FULLTANK (`0x140134722`, lines 2362-2382) and MAPMODE_MISSION_HALFTANK (`0x1401347fe`, lines 2383-2387)
```c
// FULLTANK
if (stringCompLengthAndContent(name, "MAPMODE_MISSION_FULLTANK")) {
    el = FindGuiElement("MAPMODE_MISSION_FUEL");
    if (el) {
        el->vtable[+0x2f0]();
        CopyString(el + 0x195 * 8, &DAT_140364d08);
    }
    addShipsToSilentStrikeGRP?();
LAB_14013476f:
    **(param_2[0x118]) + 0x114 = 0;
    if (param_2[0x17b])
        genericPressButton(param_2[0x17b], "button_01_check", 0, 0);
    // clears locals, then goes to the common tail LAB_1401347c8
}
// HALFTANK
if (stringCompLengthAndContent(name, "MAPMODE_MISSION_HALFTANK")) {
    memcmp(...);          // Ghidra: VCRUNTIME140.DLL::memcmp, probably a mislabel
    goto LAB_14013476f;   // same code as FULLTANK's tail
}
```
Interpretation [guess from names]: mission-planning fuel-load presets for a strike group ("SilentStrike"), NOT the fleet refuel rate. The refuel rate lives in the Escadra.cpp fleet update at `0x140111ff0` (see [mods/refuel.md](../mods/refuel.md)).

## Live-test recipe
1. Run the game with probe v2.x and `hook_clicks` on.
2. Click a button on each screen (title, map, shop, editor); each accepted click gives one `CLICK` line in `probe.log` with the element name, which is a string compare inside this function. Use it to find the branch for a given button in the decompilation.
3. To confirm a catalog pairing: pick a never-seen name from the TSV (e.g. `TITLE_CREDITS` or `PROFILE_RESET_NO`), reach its screen, click it, and compare the `CLICK` line (`gui+0xa40`) with the catalog name. A different name, or no line, means the literal was paired wrongly or the element is not clickable. Record the count in the TSV `seen` column.

## Unknowns
* Dispatch structure is resolved (string-compare chain, no switch). Still unknown: which of the 476 strings are element names, which branch each catalog name leads to (only the test address is known), and how the 21 non-catalog names are matched.
* Whether other callers appear in 1.163 through indirect calls (only the static caller is known).
