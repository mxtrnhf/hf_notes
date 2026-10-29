# Ghidra sweep 2026-10-29 — batch 5, agent 8 (app/input/precombat tail, HGE media, ZIP/zlib)

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`).
Range: `0x140170000–0x1401FFFFF`. Only `FUN_*` names were touched; every rename
carries a doc plate (summary / `Algorithm:` / `Parameters:` / `Returns:`).
No function was created and no `rep_*` was renamed.

Start: 48 `FUN_*` + 341 `rep_*`. End: **35 `FUN_*`** + 341 `rep_*`.
**13 renames applied, 0 created, 13 skipped families** (the 35 remaining are the
previously-adjudicated skips listed below).

## Renames

### ZIP / zlib layer (0x140181000–0x140182d50) — the "large builders" of this range

| addr | new name | description |
|---|---|---|
| 0x140181000 | `Inflate_Init2` | zlib `inflateInit2_`: version/size check (`'1'`, 0x58), allocates the 0x1bc0-byte `inflate_state` through the stream's zalloc hook, decodes windowBits into wrap count + window size (8..15), returns 0 / `Z_VERSION_ERROR` 0xfffffffa / `Z_STREAM_ERROR` 0xfffffffe / `Z_MEM_ERROR` 0xfffffffc. |
| 0x140181b60 | `Zip_ReadNextCentralEntry` | advances the central-directory cursor: bumps entry index +0x54 and running offset +0x58 by the previous entry's name/extra/comment lengths + 0x2e, then calls the entry reader; 0xffffff9a null state, 0xffffff9c end of list. |
| 0x140182d50 | `Zip_ReadCentralDirectoryEntry` | parses one central-directory header (signature 0x02014b50), all fixed fields plus name/extra/comment copied into caller buffers with truncation; out header = 10 qwords, out disk-start; -0x67 bad signature. |

That completes the ZIP reader half: `Zip_OpenArchive` (b3 a4) +
`Zip_ReadLocalFileHeader` / `Zip_ReadInt32BE` / `Zip_ReadUInt16BE` (b2) +
these two + `Inflate_Init2` / `Inflate_BuildFixedTables` / `Inflate_FreeState`.

### HGE audio (0x14017c220, 0x14017c7c0)

| addr | new name | description |
|---|---|---|
| 0x14017c220 | `Sound_ScaleChannelFrequency` | `BASS_ChannelGetInfo` then `BASS_ChannelSetAttribute(chan, BASS_ATTRIB_FREQ = 1, info.freq * scale)`. HGE vtable slot +0x1e8. |
| 0x14017c7c0 | `Music_GetAmplify` | `BASS_ChannelGetAttribute(chan, 0x100 = BASS_ATTRIB_MUSIC_AMPLIFY)`, float -> int; -1 when no device. HGE vtable slot +0x180, pairs with `Music_SetAmplify` (+0x178). |

### Media proxies

| addr | new name | description |
|---|---|---|
| 0x140179460 | `Media_EnsureTexture` | lazy get-or-create through HGE slot +0x310 (0x14016cd50 = **Texture_Load**, not MessageBoxA): data ptr at proxy+0xa0, size 0, flag at +0x120, handle cached at +0x90. |

### Editor / locale / containers

| addr | new name | description |
|---|---|---|
| 0x14018c320 | `Editor_RebuildGlobalLinkLists` | frees the current global Link (0x1403c0d88) and the two global containers 1439e9368/1439e9378, refreshes the profile, classifies with `Frame_ClassifyPartMix`, then re-registers every valid class-0xf body (excluding the old link and the player escadra leader) through body vtable +0x278 or `FUN_1400458c0` depending on the class (1..3 vs 4..6); ends with `Editor_UndoZoom`. Structural name, behaviour exactly as decompiled. |
| 0x14018f410 | `Locale_GetCtypeFacet` | `std::ctype<char>` facet of a `std::locale`: locked lookup by static id, global-locale fallback, `_Getcat` + `_Facet_Register` on first use. |
| 0x140170a60 | `Thunk_DestroyStringRange40` | forwards to `Array_DestroyStringRange40`. |
| 0x140170a80 | `Relocate_MoveConstruct40String` | move-constructs 0x28-byte string records, resetting sources to empty SSO strings. |
| 0x140192040 | `Thunk_LinkVectorInsertAt` | forwards to `LinkVector_InsertAt` (was mislabelled an atoi64 replica). |
| 0x1401a8510 | `Property_ScalarDeletingDestructorAlt` | scalar-deleting destructor of a Property-derived class (vtable 0x140369248) calling `Property_Destructor`. |

### Graphics quad state

| addr | new name | description |
|---|---|---|
| 0x140172b10 | `Gfx_QuadSetFlip` | mirrors a four-corner textured quad: swaps u coords when the +0x1a0 flag changes, v coords for +0x1a1, re-mirrors cached origins +0x198/+0x19c about extents +0x188/+0x18c when the +0x1a2 active flag is set. Corner records are 0x58-stride. |

## HGE vtable findings (HGEVFTABLE 0x1403672f0)

Batch 4 agent 5 resolved the media slots; the rest of the table adds:

| slot | target | meaning / note |
|---|---|---|
| +0x180 | 0x14017c7c0 | `Music_GetAmplify` (now named). |
| +0x1e8 | 0x14017c220 | `Sound_ScaleChannelFrequency` (now named). |
| +0x2e0 | 0x14016cc80 | **quad/geometry render**: `INC dword [0x1403ef304]`, accumulates `abs(u2-u0)*abs(v2-v0)` into `0x1403ef30c`, `JMP 0x140085f40`. No function object. |
| +0x300 | 0x14016cbb0 | `ADD RCX,8; JMP 0x1400839d0` — factory `rep_14007f180_New`, builds a 0x60-byte object (vtable 0x140356768) from two read hooks. No function object. |
| +0x308 | 0x14016cba0 | `ADD RCX,8; JMP 0x1400838e0`. No function object. |
| +0x310 | 0x14016cd50 | **`Texture_Load`**: `(this, data, size, flag)`; size!=0 -> `D3DX11CreateTextureFromMemory(this+8, data, size, 0)`, size==0 -> disk path. The `rep_..._MessageBoxA` name for this address is wrong. No function object. |
| +0x320 | 0x14016cd10 | `vtable+0x10` float -> int adapter, one line. |

These targets are in agent 7's range, so creation was requested on the blackboard
instead of done here (`Gfx_RenderQuad`, `Gfx_CreateResourceObject`, `Texture_Load`).

## `rep_*` ICF names are not evidence

Two counter-examples found while resolving calls:

* `0x140184430` is `rep_140184430_..._atoi64` by name, but its body is
  `LinkVector_InsertAt` (vector of 0xf0-stride Links).
* `0x14025ecf0` is `rep_14025ecf0_..._free` by name, but its body is a ~1.5 KB
  `somethingRadio` string builder.

So `rep_<addr>_<API>` labels come from a matching pass that can pick the wrong
donor. Any earlier conclusion that rested on one of these names should be
re-checked; `0x1401941f0` in this range is such a case (it "calls
rep_14025ecf0" = somethingRadio with an incompatible signature) and was therefore
left unnamed.

## Skipped / open (35 remaining `FUN_*`)

| addr / group | why left |
|---|---|
| 0x140170140, 0x140170190, 0x1401787a0, 0x1401787f0, 0x140178840, 0x140178890, 0x1401788e0, 0x1401a82c0, 0x1401a8340, 0x1401a8480, 0x1401a84b0, 0x1401a84e0, 0x14018f940 | 20–70-byte scalar-deleting destructors; each only installs a vtable (PTR_FUN_140366650 / 140369200 / 140369218 / 1403691e0 …) and frees on flag bit 0. Per-class names would be guesses (same reason b3 a4 / b4 a5 skipped the twins). |
| 0x1401701e0 | same, but the vtable symbol is `PTR_Texture_ScalarDeletingDestructor_140356718` — a *generic* Texture deleting destructor; duplicate naming risk. |
| 0x140170210 | 24-byte thunk: `if (p) return (*(*p+8))(p, this); return 0` — release through vtable slot 1. Owning container/element type not proven. |
| 0x1401783c0 | 0x98-byte compiler-generated struct copy (b3 a4). |
| 0x140172550, 0x1401725c0, 0x140172aa0, 0x140172ee0 | the four-corner quad family around `Gfx_QuadSetFlip`: set 9 fields + render (550), place at (x,y) from cached extents + render (5c0), `sinf` + render (aa0), write one of the four 0x58-stride corner records or all four (+8/+0x60/+0xb8/+0x110) (ee0). Behaviour is clear, but whether each is "set" or "render" depends on the exact meaning of HGE slot +0x2e0, which is still an uncreated function. Left for after agent 7 creates `Gfx_RenderQuad`. |
| 0x140179410 | proxy on HGE slot +0x300: `(HGE, dword proxy+0xa0, dword proxy+0xa4, 0x1c, 1)` -> factory 0x1400839d0. Which resource type the factory builds is not proven, so no name (b4 a5 left it too). |
| 0x140187890, 0x1401878b0, 0x1401ae820 | three-argument free wrappers (compiler/allocator adapters). |
| 0x14018f910 | 36-byte facet decref: fetch facet by locale id index and call its vtable +0x10. Owner (which locale-derived class) not proven. |
| 0x140191f40 | destructor that calls `(**vtable)(this, 1)` only when `(byte[+0x28] & 7) == 7` — variant/union-like object, class unknown. |
| 0x140193090 | clamps the float at +0xd8 between +0xdc/+0xe0 and pushes it into the Box2D joint at +0xc8 (type 3 -> +0xa4, type 10 -> +0x90, x0.05). Motor speed vs target angle still unresolved (b3 a4 left it). |
| 0x1401941f0 | calls the mislabelled `rep_14025ecf0` (= somethingRadio) with an incompatible signature; can't decide the wrapper's role. |
| 0x14019ae0f, 0x14019ae66, 0x14019ae94 | split pieces of one 0x20-stride `CopyEscadraName` loop (0f+66 are the two halves, 94 is the empty tail) — function-split artefacts, not independent functions. |
| 0x1401a4210, 0x1401a47c0, 0x1401a47f0 | small record constructors (8-field 0x28 record; vtable 0x140369328 object; 4-field sub-object). No owning class name available. |
| 0x1401a4b40 | destructor freeing `*(this+8)+0x20` then `*(this+8)` — a two-level allocation owner, type unknown. |
| `rep_*` (341) | ICF duplicates, left as-is. |

## Notes for the docs

* `Media_EnsureTexture` closes the batch-3 "unknown media proxy" item: the family
  at 0x140178xx/0x140179xx is sound/music/stream/file-data/texture, and the
  texture one is the only one that goes through `D3DX11CreateTextureFromMemory`.
* The HGE renderer keeps running draw statistics: `0x1403ef304` = quad count,
  `0x1403ef30c` = accumulated quad area. Useful if a profiler overlay is ever
  wanted.
* `Zip_ReadCentralDirectoryEntry` + `Zip_ReadNextCentralEntry` are the mod-facing
  pair for enumerating archive contents (the reader state keeps entry index at
  +0x54 and byte offset at +0x58).
