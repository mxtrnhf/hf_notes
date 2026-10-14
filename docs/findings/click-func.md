# ClickFunc: the GUI click handler

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

Decompiled C (8,589 lines, default decompiler settings): 941 `if`, 121 `else`, 5 `else if`, 0 `switch`, 0 `case`, 324 `goto`, 67 labels, 48 while/do, 30 for. Nesting, real brace-depth measurement [observed, read-only Ghidra script]: maximum depth **40** (first reached at decompiled line 6838), final depth 0. Lines per depth cluster at depth 4 (610 lines), 5 (551), 12-14 (about 500-560 each), 33 (421) and 35 (588); `if` statements per depth go up to 140 (at depth 4). The earlier figure "maximum nesting about 79 levels" was measured from leading spaces and is **inflated** by the indentation of wrapped-line continuations; ignore it. The `if (name == X) {..}` tests are siblings in the chain at the same level (observed in the four branches in [click-func-branches.md](click-func-branches.md)). The deep clusters (depth 12-14, 33, 35) are not yet explained; whether the editor tests are nested under "no match yet" conditions is unchecked.

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

Next step: done, see [click-func-elements.md](click-func-elements.md) (catalog of 252 element names, 43 seen in probe logs). Decompiled example branches (BUY_BUY, fuel slider, mission fuel presets): [click-func-branches.md](click-func-branches.md).

## What the probe knows about it
`hf_probe` hooks its entry (26 stolen bytes) and logs `CLICK` lines. Arguments: RCX = ctx, RDX = `gui*`, R8D = button, R9 = `[gui+0xa80]`. The GUI element name is at `gui+0xa40`, its class string at `+0x8`, the fx/distortion name at `+0xad8`. Verified detail is in [ui-events-and-screens.md](ui-events-and-screens.md); not copied here.

## Live-test recipe
1. Run the game with probe v2.x and `hook_clicks` on.
2. Click a button on each screen (title, map, shop, editor).
3. Each accepted click gives one `CLICK` line in `probe.log` with the element name; that name is a case label (or string compare) inside this function. Use it to find the branch for a given button in the decompilation.

## Unknowns
- Dispatch structure: resolved, string-compare chain, no switch (see Structure above). Still unknown: which of the 476 strings are element names.
- Whether other callers appear in 1.163 through indirect calls (only the static caller is known).
