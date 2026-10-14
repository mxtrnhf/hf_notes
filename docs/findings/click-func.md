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

[observed] in Ghidra, read-only. Same shape, same caller name and same string, so `FUN_14012f120` is the 1.163 version of `ClickFunc` [code, strong; matched by shape, not a byte-for-byte diff]. Suggested name for the 1.163 database: `ClickFunc`. Renaming is left to the user (the database is treated as read-only here).

Size [observed, v1.163, read-only Ghidra script]: decompiling `FUN_14012f120` gives **8,589 lines** of C, **538,685 characters**, from a function body of 62,272 addresses. The user had heard "10,000+ lines"; Ghidra's line count depends on decompiler width settings, so this is the same order of magnitude. The decompiler needed its payload limit raised (default fails with "Response buffer size exceeded"); it took about 45 s with max payload 1000 MB.

Source file [observed]: the string xref shows Gui.cpp's `__FILE__` string (`0x140363628`) is referenced from `FUN_14012f120` (`0x14012f120`), so ClickFunc lives in Gui.cpp. See [source-file-names.md](source-file-names.md).

How to decompile a huge function through the Ghidra MCP [observed that it worked]: scripting enabled with `GHIDRA_MCP_ALLOW_SCRIPTS=1` when starting Ghidra, then a Java script with `DecompileOptions.setMaxPayloadMBytes(1000)` and `DecompInterface.setOptions`.

## What the probe knows about it
`hf_probe` hooks its entry (26 stolen bytes) and logs `CLICK` lines. Arguments: RCX = ctx, RDX = `gui*`, R8D = button, R9 = `[gui+0xa80]`. The GUI element name is at `gui+0xa40`, its class string at `+0x8`, the fx/distortion name at `+0xad8`. Verified detail is in [ui-events-and-screens.md](ui-events-and-screens.md); not copied here.

## Live-test recipe
1. Run the game with probe v2.x and `hook_clicks` on.
2. Click a button on each screen (title, map, shop, editor).
3. Each accepted click gives one `CLICK` line in `probe.log` with the element name; that name is a case label (or string compare) inside this function. Use it to find the branch for a given button in the decompilation.

## Unknowns
- Dispatch structure (string compares vs. switch).
- Whether other callers appear in 1.163 through indirect calls (only the static caller is known).
