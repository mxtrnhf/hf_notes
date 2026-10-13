# Mouse sensitivity path and the A220 slowdown (1.163, partial)

Status: **partial. The sensitivity path is read; the code that lowers it while A220 rockets are selected is NOT found. Nothing run in game.** Tags as in `../README.md`: **[game]** · **[code]** read from the decompilation · **[guess]** · **[not read]**.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: roadmap QoL item "remove the mechanic by which rockets (A220) lower mouse sensitivity globally".

## What is established [code]
* The config key `TITLE_MOUSE_SENS` is parsed in `FUN_1401574b0` (`0x140157e7d`) and stored into the global float `0x1403c0df4` (the only writer; `TITLE_WHEEL_SENS` follows it). The options screen (`FUN_1401e60d0`) and `InitializeAppProperties` only read it.
* `SomethingInputTask` (`0x14018e2a8` reads it) is the per-frame input task. For the first input device (`DAT_1439e9388`, array of `0xf0`-byte records, mouse first) it computes `scale = MOUSE_SENS * device[+0xc8]` and multiplies the accumulated mouse delta (`+0x80`/`+0x84`) by it before `FUN_140187260`.
* `device[+0xc8]` is a per-device float scale. `FUN_140188c00` (`0x140188c62`) initialises it to `1.0`; the only other writer found is the record copy in the vector-grow routine `0x140184870` (`0x140184aaf`).

## What this rules out [code, by instruction search]
* No `MOVSS`/`MOV` store to `[reg+0xc8]` exists in the input module (`0x140184000`-`0x14018c000`) apart from the two above. So the A220 slowdown is **not** a write to the device scale or to `0x1403c0df4`.

## Second pass: the consumer of the delta [code], A220 link still [guess]
* A220 is the RSZO 220 mm rocket (`MDL_RSZO_220`, ammo `ITEM_AMMO_220MM`); there is no string "A220" in the binary, so the weapon cannot be found by name. [code]
* `FUN_140187260(device, delta)` (called from `SomethingInputTask` with the already scaled delta) applies a **second, distance-ratio rescale** of the delta: when `DAT_1403c0d88` (a GUI/view object, writers not found) has `(+0x28 & 0x4000f) == 0x4000f` and its byte `+0x884` is set, the delta is multiplied by `|cursor offset in one space| / |offset in the other|`, built from `FUN_1402151e0` conversions and the cursor vector at `DAT_1403c0d40 + 0x128`. This is the only place found that rescales the mouse delta by a state-dependent factor. [code]
* `+0x884` is set and cleared around `UpdateZoom`'s zoom-step block (`0x14026b0c3`, `0x14026b1b2`) and in several GUI routines, so it looks like a "view is being re-projected" flag, not an A220 flag. **[guess]** that the A220 slowdown is this rescale, reached because the extended reticle changes one of the two spaces. Not tested.
* `UpdateZoom` also contains the camera lead / cursor offset logic (`0x14026b000`); it divides the cursor offset by `ZOOM_LEVEL` and clamps it (`500`, `550`, `700`, `1000`, `3000` constants). Not read in detail.

## Open [not read]
* Where the slowdown lives. Next: who sets `+0x884`/`+0x28` of `DAT_1403c0d88` while an A220 is selected; the A220 branch of `creatureLogic`. Earlier candidates, none checked: the cursor/aim code that consumes the delta after `FUN_140187260`; the weapon-selection or reticle code for A220 (`creatureLogic` branches); the zoom path (`UpdateZoom`, `ZOOM_LEVEL`). A write watch in game on the delta (`device +0x80`) while switching to A220 would settle it faster than reading.
