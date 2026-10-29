# Ghidra sweep 2026-10-29 — batch 5, agent 7 (0x140120000–0x14016FFFF)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Only previously unnamed `FUN_*` functions were touched; every name carries a
plate (summary / `Algorithm:` / `Parameters:` / `Returns:`). **No
`create_function` was needed** — every function in the range already had an
object, and no vtable slot in the range pointed at unowned code.
`rep_*` ICF replicas were left alone per §4.

Before: 37 `FUN_*` + 107 `rep_*`. After: 12 `FUN_*` + 107 `rep_*`
(25 renamed, 12 skipped).

## Renames (25)

### Container / sort internals (0x14012xxxx)

| addr | new name | description |
|---|---|---|
| 0x140123530 | `VectorBool_InsertRange` | `std::vector<bool>::insert` for a bit range: copies bits word-by-word, trims the trailing word, updates the bit size and returns the insertion iterator. |
| 0x140129040 | `VectorCaptain_InsertOne` | insert one 0x58-byte (value, `Captain`) record: 1.5x reallocation with over-alignment recovery, head/tail move via `Array_CopyConstruct88Captain`, old block destroyed/freed. |
| 0x140129360 | `RbTree_FindIntKey` | `std::_Tree` lower/upper-bound on an int key at node+0x20, returning `{node, hint, matched/direction flag}`. |
| 0x1401295c0 | `Sort_Median9IntKey114` | median-of-3 / median-of-9 pivot selection for the introsort keyed by the int at pointee+0x114. |
| 0x140129a10 | `Sort_IntrosortBy114` | introsort loop (insertion cutoff, 3-way equal-key partition, depth budget) over pointer arrays keyed by pointee+0x114. |
| 0x140129ed0 | `Array_RelocateString48` | move-constructs 0x30-byte records holding an MSVC `std::string` (+0/+0x10/+0x18) plus two trailing qwords, resetting each source to the empty string. |
| 0x140129f70 | `Map_InsertU64KeyIntValue` | insert-or-find in a u64-keyed map whose node value is an int at +0x28 (0x30-byte node + `RbTree_Insert`). |
| 0x14012a080 | `Map_InsertU64KeyCharValue` | same map template with a single-byte value at +0x28. |
| 0x14012a1c0 | `PairCaptain_ConstructOne` | constructs one (byte, `Captain`) record: leading byte copy + `Captain_Constructor` at +8. |
| 0x14012a1f0 | `List_CopyCircular` | deep copy of a circular sentinel list (0x18-byte nodes, value at +0x10) into a new header. |
| 0x14012a570 | `StringRecord30_Constructor` | initialises a 0x30-byte record: dword, empty `std::string` at +8 (capacity 0xf), trailing dword. |
| 0x14012a590 | `Record32_Zero` | zeroes a 0x20-byte record. |
| 0x14012c830 | `Vector12_At` | element address `base + index * 0xc`, unchecked. |
| 0x140128c70 | `PtrFloatFlag_Copy` | copies a {pointer, float} pair and derives the flag byte at +8 from the float being non-zero. |

### Effects / stats / map-mode props

| addr | new name | description |
|---|---|---|
| 0x140126530 | `Effect_SetColour4f` | stores four floats at +0x15c..+0x168 of a newly built effect object; callers (`Engine_ApplyThrustForce`, `Body_SpawnFireEffect`, `Body_Explode`, `World_ThermalPass`) pass three equal components plus one differing value — an RGBA colour. |
| 0x14015f7b0 | `ShipStats_GetAmmobox` | Stats +0xe8. |
| 0x14015f7e0 | `ShipStats_GetAmmoboxPriority` | Stats +0xf0. |
| 0x14015f840 | `ShipStats_GetPower` | Stats +0xdc. |
| 0x14015f8a0 | `ShipStats_GetRotation` | Stats +0x108. |
| 0x14015f6f0 | `MapModeProps_HalveFloat8f8` | one-shot halving of object+0x8f8 guarded by byte +0xc7c. |
| 0x14016c2a0 | `MapModeProps_RestoreFloat8f8` | inverse of the above (doubles when the guard is set). |
| 0x14016a040 | `Profile_ResetMapInstruments` | clears the map-instrument state at `Profile+0x530`: vtable+0x48 destroy of the element, two circular list resets, 0x40-stride vector free. |
| 0x14016a100 | `Gui_DrawScaledShapeThunk` | forwarder to `Gui_DrawScaledShape` used as a callback slot. |
| 0x14016f010 | `Font_SetGlyphValue16c` | stores a float at font+0x102c and writes it to +0x16c of all 256 glyph sprites. |
| 0x14016f230 | `Font_SetGlyphValue8` | stores a float at font+0x1024 and pushes it through the four-cell setter 0x140172ee0 to +8 of each glyph sprite's four 0x58-byte cells. |

## Resolved: the four undocumented Stats getters

Batch 3/4 left 0x14015f7b0 / 0x14015f7e0 / 0x14015f840 / 0x14015f8a0 unnamed
because `structures.md` does not list +0xe8, +0xf0, +0xdc, +0x108. Two
independent proofs:

1. **Property display in `setupPropsSecondaryMapModes`** — the getter is called
   immediately before `vtable+0x2f0` on the props object, in the branch that
   matched a property name by string:

   | getter | offset | branch string |
   |---|---|---|
   | 0x14015f840 | +0xdc | `ED_PROP_POWER` |
   | 0x14015f7b0 | +0xe8 | `ED_PROP_AMMOBOX` |
   | 0x14015f7e0 | +0xf0 | `ED_PROP_AMMOBOX_PRI` |
   | 0x14015f8a0 | +0x108 | `ED_PROP_ROTATION` |

2. **Stats loader** — `populateObjects` registers each seria key against the
   stats field pointer, e.g. `m_mdl_power_need` → +0xe0 (already documented),
   `m_mdl_power_priority` → +0xe4, `m_mdl_ammobox` → +0xe8. So +0xe8 is the
   ammo-box stat and +0xdc is generated power (its +0xe0 neighbour is
   power_need). +0xf0 is the second ammo-box property and +0x108 the rotation
   stat.

## Font family context (for the two new names)

`0x14016e9f0 Font_MeasureString`, `0x14016eaf0 Font_GetCharWidth`,
`0x14016f0c0 Font_SetGlyphParam` (+0x168/+0x1028), `0x14016f120 Font_SetColor`
(+0x1020 colour via `setSpriteFields`), `0x14016f170 Font_SetGlyphColour`
(+0x168 + colour) are already named. The font loader at 0x140179030 fills a
0x1038-byte font object from a descriptor and calls, in order, `Font_SetColor`
(+0x128), `Font_SetGlyphValue8` (+0x12c float) and `Font_SetGlyphParam`
(+0x124). The TextGrid layout passes `element+0xa14` (a float) to
`Font_SetGlyphValue16c`, and caches the same float at grid+0x1a4.

## Skipped (12, with reasons)

| addr | size | why skipped |
|---|---|---|
| 0x14012b4f0 | 220 | constructor of a 0x118-byte stack record in `lootBoxCoins` (three 0x58 groups, float 1.0 at +0x54/+0xac/+0x104, +0x118 dword 0, +0x10c..); owning type not provable from the single call site. |
| 0x14012d1a0 / 0x14012d370 / 0x14012d600 | 26 / 154 / 95 | GUI-element base vtable callbacks (same skip as batch 3); which of hover/press/release is still not provable. |
| 0x14015c1c0 / 0x14015c1e0 | 20 / 20 | thin forwarders to two different `_invalid_parameter_noinfo_noreturn` replicas with reordered args — compiler `vector` `_Xlen`/`_Xrange` twins; which is which cannot be proven. |
| 0x140162fe0 | 24 | `[obj+0x88]==0 || [[obj+0x88]+0x28]==7`; the object comes from a 0x40-class filter list in `ClickFunc` / map-mode setup, but what "7" denotes is unknown. |
| 0x14016cd10 / 0x14016cd30 | 22 / 22 | one-line adapters calling vtable +0x10 / +0x8 and truncating the float result to int; no semantic name possible. |
| 0x14016cf30 | 22 | forwarder through `newValidHGE` to its vtable slot 0. |
| 0x14016dde0 / 0x14016ddf0 | 9 / 7 | bare setters of text-grid +0x1a4 / +0x1a0; values come from `element+0xa14` (float) and from a sprite field +0x148 (int) in 0x140178f3c, meaning not proven. |

`rep_*` (107) remain untouched: ICF duplicates whose embedded target already
carries the real name (CRT mem*/math/free, `New`, `CopyString`, `GUI::GUI_2`,
`Property::Property`, `loadMediaByName?`, `SetBackground?`,
`MessageBoxA`, ...).

## Remaining work in the range

Only the 12 skips above. No GUI screen builder, no vtable slot and no
unowned-code pointer is left in 0x140120000–0x14016FFFF.
