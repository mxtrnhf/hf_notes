# The pre-combat screen: where an "ally yes/no" control would go

Steam 1.163, image base `0x140000000`. Why it matters: `hf_ally` needs a player choice ("do I want an ally in this fight"), and the beta clip the player showed (a per-ship ORDER button with a bomb/shell icon list) suggests the same kind of screen once existed for roles. Tags as in [../../README.md](../../README.md). Written 2026-10-16; **nothing here has been built or run**.

## The screen exists in campaign fights [game]
The probe logs of 2026-10-14 show `PRECOMBAT_OK` clicked twice per run: once after `EDC_TEST_FIGHT` (the editor test fight) and once after `MAP_LOCATION` / `MAP_ESCADRA` clicks (a campaign engagement), e.g. `hf_probe_build/logs/2026-10-14_1801_v2.2/probe.log` lines 868 and 4024. So every fight passes through it. Its GUI strings: `PRECOMBAT_BACK`, `PRECOMBAT_OK`, `PRECOMBAT_LEVEL`, `PRECOMBAT_PLAYER_1..4`, `PRECOMBAT_A/B`, `PRECOMBAT_SPAWN(_NUM)`, `PRECOMBAT_MAP`; sprites `precombat_back`, `precombat_front`, `precombat_button`, `precombat_up_01`, `precombat_drop(_01)`, `precombat_slide`, `precombat_capital` (strings at `0x14035af18` .. `0x14036ebc8`).

## The builder: `FUN_1402d7620` [code]
Decompiled (read-only). It is the 1.163 function that **builds the whole screen in code**; there is no layout file. Other GUI-building variants reference the same strings (`FUN_1401e8da0`, `FUN_1401ea500`, `mainMap` at `0x14014332c`): not read yet, probably the skirmish and PvP versions. No static caller: it is reached through a pointer.

What it does, in order:
1. `DAT_147fc6fd3 = 1`; frees the old GUI objects; creates the background GUI named `PRECOMBAT_BACK` with the sprites `precombat_back` / `precombat_front`.
2. Creates **`PRECOMBAT_OK`**, the start button (sprite `precombat_button`).
3. When `BOOL_147fc6f80` or `DAT_147fc6f81` is set it creates `PRECOMBAT_LEVEL`, a text with "Level: N" in a coloured string.
4. Lays out one **card per player side** (`DAT_143a158e0..e8`, 0x18-byte entries; up to 4), each card a column of ship preview objects (`PRECOMBAT_PLAYER_<n>`); positions start at x = -800 and step by the object width; y depends on the number of sides (350, 300 or 250 apart). The ships shown come from the per-side lists at `0x147fc7510 + 0x10*n`, filled from the player's profile.
5. Ends with `CopyString("cursor_main")`, `SetBackground_(... "PRECOMBAT")`, `SetLink(0x143a1c260, 0)` (clears the controlled-ship link), zoom levels 1/1/1, then `TarkhanGUIDispatchOperator()` (`0x140275850`, call at **`0x1402d88bb`**, bytes `E8 90 CF F9 FF`).

## How a GUI element is made [code, from the disassembly of the PRECOMBAT_OK block, `0x1402d78c3`..`0x1402d798f`]
```
gui = New(0xe70)                      ; operator new, 0x140334094, ECX = 0xe70 (size of GUI)
gui = GUI_2(gui, 0)                   ; constructor, 0x14012a910 (RCX = memory, EDX = 0)
gui->vtable[0x2c0](gui, "NAME")       ; set the element name (what ClickFunc reads at gui+0xa40)
node = *(0x147fc6f88)                 ; the global node every GUI is added to
node->vtable[0x50](node, gui, 0, 0)   ; add to the node
SetBackground_(gui, 0, "sprite", xmm3 = -1.0 ...)   ; 0x14001be50, sprite name in R8, float args in XMM2/XMM3 and on the stack
gui->vtable[0x88](gui)                ; finish/refresh
0x14015cc30(gui)                      ; (CopyString-like helper, role not confirmed)
setXposYpos(gui, Vec2*)               ; position, virtual 1920x1080 coordinates (the card code uses x -800.., y -50..)
```
Text on an element: `gui->vtable[0x2d8](gui, std::string)` as in `PRECOMBAT_LEVEL`. Names in this database are guesses [guess]: the sequence is what matters.

## What a mod would need [guess, design only]
1. **A seam**: wrap the call at `0x1402d88bb` (after every control exists, before the dispatcher runs the screen) with a patchy trampoline, check the 5 bytes first, and there create an own GUI with the sequence above (name `ALLY_TOGGLE`, sprite `precombat_button`, a position next to `PRECOMBAT_OK`, text "ALLY: ON/OFF").
2. **A click catch**: hook `ClickFunc` (`0x14012f120`, entry, the same 26 stolen bytes the probe uses; arguments RCX = ctx, RDX = `gui*`, R8D = button; name at `gui+0xa40`). If the name is `ALLY_TOGGLE`, flip the setting, update the text, and return without running the original; otherwise run the original. No new branch inside the 62 kB function is needed.
3. **The setting** is a static read by the battle hook (`spawn_ally` becomes "default for the toggle"; remembered between fights, optionally persisted in `ally.json`).
Risks: the GUI object layout (`0xe70` bytes) and the vtable slots are read from one block, so the first build should log every step and only create the element when a prologue check of `GUI_2`, `SetBackground_` and `setXposYpos` passes; text rendering of a custom string and the click hit-box (sized by the sprite) are untested. The screen is rebuilt on every entry, so the element must be created on every pass.

## The beta clip (what the player showed)
A beta-era screen: four "WANDERER MK2 / ARTILLERY FRIGATE" ship cards, each with a round **ORDER UNSET** button; clicking it opens an icon list (shells, bomb, possibly more), after which every ship shows the chosen icon. The mission HUD then reads **DAMAGE BEFORE RETREAT** and shows HP tags on ground installations (`1200 HP`, `NO POWER`, `POWER 92%`). So the beta had a per-ship role order chosen before the fight. **1.163 still holds it** (found 2026-10-16): `orderSelect1` `0x1401e82f0` builds the per-ship ORDER menu from a role table (1 unset, 2 bombing, 3 support) stored in ship `+0xd70`, `ClickFunc` handles `ORDER_SELECT` / `ORDER_SELECT2`, and `PRESELECT_BORDER_ROLES` / `ORDER_SELECT_TXT` are present; the menu is probably switched off by data or a flag. Details: [battle-ally.md](battle-ally.md) "Roles". Where it is shown (`mainMap` references `ORDER_SELECT` at `0x14014309c`) is not read.

## Open
* `FUN_1401e8da0`, `FUN_1401ea500`, `mainMap` references (other versions of the screen).
* Role of `0x14015cc30`, the extra stack arguments of `SetBackground_` (`0x14001be50`), the hit-box size source.
* Whether `ClickFunc` can be intercepted before the probe's hook (hf_probe owns that site: [../hooks.md](../hooks.md); the ally mod would need the probe off or a shared hook).
* The battle-side ship status panels (bottom left own ship, bottom right enemy) for a health readout: a separate rendering job, see [../rendering/README.md](../rendering/README.md) seams B21 to B24.
