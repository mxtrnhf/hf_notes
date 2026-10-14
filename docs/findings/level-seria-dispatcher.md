# SomethingWithLevelSerias: the SCR_* scenario dispatcher

Status: partial. Names, addresses and string references only; the body was NOT read.

Source: read-only Ghidra scripts over the v1.151 and v1.163 programs.

## Name

The function a task called `HandleSomethingLevelSeria` is named `SomethingWithLevelSerias` in both Ghidra databases. Nothing in either is named `Handle*`.

Earlier notes mention it: [version-differences.md](../version-differences.md) (level-script labels, "very likely" the 1.163 `FUN_1402ac970`), [porting-1151-1163.md](../porting-1151-1163.md) ("probable") and [open-questions.md](../open-questions.md) (unread). This finding upgrades the 1.163 identification: the function at `0x1402ac970` is now named `SomethingWithLevelSerias` in the 1.163 program, and every SCR_* string below is referenced exactly once, from that function. The address-trend guess is no longer needed.

## v1.151

* Entry `0x140289850`; the main piece is 6,031 bytes.
* Ghidra also labels about 30 pieces that appear to belong to the same dispatcher (`SomethingWithLevelSerias_<name>`):

| label | address |
|---|---|
| SCR_INTERMEDIA_01 / _02 / _03 | `0x14028acc5` / `0x14028ba38` / `0x14028d09f` |
| SCR_HALL | `0x14028dd1d` |
| SCR_PRESELECT | `0x14028e742` |
| SCR_REINFORCE | `0x14028fad7` |
| SCR_EDITOR / SCR_EDITOR_EXTENDED | `0x140290869` / `0x1402908e8` |
| SCR_MAP | `0x140290a60` (32,981 bytes) |
| SCR_LEVEL_EDIT | `0x140298b46` |
| SCR_EMPTYWORLD | `0x140298c13` |
| SCR_BUILDER | `0x140298c61` |
| SCR_CITY_GENERATED | `0x1402990a8` |
| case_01 .. case_10 (no case_07) | `0x14029af1c` .. `0x14029cd14` |
| SCR_RUINS | `0x14029cdd9` |
| SCR_COMBAT | `0x14029d3df` |
| SCR_COMBAT_TEST | `0x14029e84b` |
| SCR_MISSILE | `0x14029ebaf` |
| SCR_CRAFTS_VS_MISSILE | `0x14029f112` |
| SCR_BOMBERS | `0x14029f2ed` |
| SCR_CRAFTS_VS_CRAFTS | `0x14029f89e` |
| SCR_CREDITS | `0x14029fa8d` (6,849 bytes) |

* Together they span roughly `0x140289850..0x1402a154e` (about 96 KB), computed from the label addresses. They are labels in one flow; not verified as one function.

## v1.163

* One function, `SomethingWithLevelSerias`, at `0x1402ac970`, 29,456 bytes.
* String references (each referenced once, all from this function): SCR_HALL `0x140375030`, SCR_PRESELECT `0x1403750f8`, SCR_REINFORCE `0x140375148`, SCR_EDITOR `0x140375168`, SCR_MAP `0x1403751a0`, SCR_BUILDER `0x140375618`, SCR_COMBAT `0x1403758b8`, SCR_CREDITS `0x140375aa0`.
* Size mismatch (labelled span about 96 KB in 1.151 vs 29 KB): either Ghidra split the flow differently or the code changed. Not verified which.

## Neighbours

| | 1.151 | 1.163 |
|---|---|---|
| `SetLevelSeriaToLoad?` | `0x140239190` (695 bytes) | `0x14025afd0` (711 bytes) |
| `rep_..._SetLevelSeriaToLoad?` | n/a | `0x140223870` (45 bytes) |
| `LoadLevelSeria?` | `0x140221b50` | n/a |
| `LoadSeriaFile` | `0x140207d50` | n/a |
| `loadSeriaForLibraries?` | `0x1400cba90` | n/a |
| `seriaLoadRenderer?` | `0x14022b6a0` | n/a |

"n/a" means not looked up, not absent.

## What it is [guess from names only]

A dispatcher over level-script / screen identifiers (`SCR_*`): hall, preselect, reinforce, editor, map, builder, combat, credits, and in 1.151 also the test / ruins / missile / bombers / crafts-vs-crafts scenes. Untested whether it selects by a string compare, an id, or the value `SetLevelSeriaToLoad?` stores.

## Tooling note

The Ghidra MCP `search_functions_enhanced` `name_pattern` does not do substring matching (it missed `!ClickFunc` and these names). A read-only Java script iterating all functions finds them.
