# Ghidra sweep 2026-10-29 — batch 9, agent 8 (created-but-unnamed finish)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the 32 created-but-unnamed functions — the 31 `.rdata` targets that batch-8
agent 2 created + plated with the name withheld (`docs/data/ghidra-sweep-2026-10-29-b8-agent2.md`)
and `FUN_14004c7e0` (Body vtable slot +0x240, left unnamed by batch-8 agent 9).

**Result: 29 renamed + re-plated, 3 still unnamed (plates sharpened, reasons below),
0 skipped, 0 out-of-scope renames.** No `save_program`, no tags, no README/STATUS edits,
no commits.

## Method

1. For every target, all references to its address were taken from the reference manager
   and each `.rdata` reference was resolved mechanically:
   scan back qword by qword for the nearest qword that points at an MSVC Complete Object
   Locator (signature `1` at `COL+0x00`), take `vtable = that qword address + 8`, read the
   class name from the TypeDescriptor at `imagebase + *(int*)(COL+0x0c) + 0x10`
   (the batch-8 agent-1 method), and compute `slot = ref - vtable`.
   All 32 resolved to a class and a slot — no ambiguity, no target turned out to be
   non-vtable data (`0x148xxxxx` refs are `.pdata`, ignored).
2. The slot index was then compared against the *named* functions that already sit in the
   same slot of the sibling tables (a 15-table × 26-slot matrix dump of `Gui`, `Gauge`,
   `Slider`, `List`, `ObjectList`, `Panel`, `Replica`, `GuiMapMap`, `GuiMapSky`,
   `GuiBinding`, `GuiBindingHotseat`, `GuiBindingHotseatType`, `Creature`, `Body`,
   `HGE_Impl`). That is what turned most of the withheld names into provable ones: the
   GUI tables name the slot role, the Body tables name the base implementation.
3. Callers were found with `search_instructions` on `CALL qword ptr [reg + 0xNNN]`
   (much better signal than the general xref list, which is all vtables) and the calling
   function was disassembled around the call.
4. Bodies: `batch_decompile` in groups of ≤5 (two 33 KB / 2771 B / 1938 B bodies were over
   the 0x2000 limit and were analysed from the listing's callee/string map instead).

## Renames (29)

Class and slot are proven by the COL scan; `why` is the independent body/caller proof.

| addr | new name | class / vtable | slot | why |
|---|---|---|---|---|
| 0x140104a80 | **`Escadra_OnElementRemoved`** | Escadra `0x14035e4e0` | +0x60 (`remove`) | body of the "remove" virtual: `Node::verifyNodeRemoval_` gate, clears the Link at linked-object+0x15c, `setMissionBackground_` when `this == PLAYER_ESCADRA_` |
| 0x14011bda0 | **`Frame_EnableBodyAndChildren`** | Frame `0x140360670` | +0x130 (base `Creature_EnableBody`) | copies frame+0x8d8 into every child's +0x8dc, then calls `Creature_EnableBody` 0x1400192b0 |
| 0x14011caa0 | **`Frame_IsStatic`** | Frame `0x140360670` | +0x1a8 (base `Body_IsStatic`) | `p=*(+0x178); p && *p==2 -> false`, i.e. static unless the b2Body is type 2 (dynamic) |
| 0x14012cf20 | **`Gui_StartElementDrag`** | Gui `0x140360ed8` | +0x110 | base Body impl 0x140018fa0 is `{Frame_ResetCounter(); return 0}` (no capture); this one does `Gui_SetupSpecialElement`, the pickup `0x14017a420_New` and `Global_SetLinkNode(target,this)`; the two binding tables use `AlwaysReturn1` |
| 0x14012d210 | **`Gui_ActivateElement`** | Gui `0x140360ed8` | +0x318 | sets +0xc7d = 1, recurses into children `+0x320(child,arg,1)`; `GUI::_HandleClick` calls +0x318 when +0xc7d == 0 and +0x320 when set |
| 0x14012da30 | **`Gui_OnHoverEnter`** | Gui `0x140360ed8` | +0x120 (base `Body_OnHoverEnter`) | identical skeleton to 0x140019310 (IsActive gate, `+0x7c8 -> vtable+0x280`, frame stamp); slot's only caller is `Scene_UpdateHoveredNode` |
| 0x14012dd90 | **`List_SetupSliderRows`** | List `0x140361990` | +0x348 (base `Gui_SetupPropsSecondaryMapModes`) | per-row sprite "slider_std"/"slider_green", row value via `+0x2f0`, paired button "list_remove"/"list_add", then tail-calls the base |
| 0x14012e1e0 | **`ObjectList_SetupGridLayout`** | ObjectList `0x140361d08` | +0x348 | grid layout from the page offset (`+0xeb8` cell vector, +0xee0 cols, +0xee4 rows, +0xee8 step), `_SUB_LIST` special case, `repairPartsStats` overlay reset |
| 0x14012e7e0 | **`Gui_DrawElement`** | Gui `0x140360ed8` | +0x350 | `Gauge_Draw`/`Panel_Draw`/`Slider_Draw` all call `0x14004bed0` then this slot as their last action; the body is `0x14014f370(this)` — the per-element render pass (fonts, `Text_DrawSingleLineFormat`, `Gui_DrawScaledShape`, `Gfx_QuadRenderEx`, `Gui_ApplyLensDistortion`) |
| 0x14012e7f0 | **`Gui_DragValueByDelta`** | Gui `0x140360ed8` | +0x338 | only `.text` caller of the slot is `Input_HandleMouseMove` 0x140187569; adds `(float)(arg3>>32)` to `+0xa80`, clamps to `[+0xa84,+0xa88]`, sets via `+0x2f0`, calls `Gui_HandleSliderChange` |
| 0x14012e8d0 | **`Slider_DragValueToCursor`** | Slider `0x1403615c8` | +0x338 (base above) | projects the hovered node's screen pos on the slider axis, clamps to [0,1], maps into the value range, rounds when +0x469 clear |
| 0x14012ece0 | **`Gui_DeactivateElement`** | Gui `0x140360ed8` | +0x320 | mirror of +0x318: clears +0xc7d, `handleRadioPanelSounds_`, name at +0xab8 instead of +0xb18 |
| 0x14015de50 | **`GuiMapMap_RegisterHudMarkers`** | GuiMapMap `0x1403627a0` | +0xb0 (base `Creature_RegisterInWorldLists`) | callees: `Hud_MarkerInitType1/2/4`, `Body_GetInheritedStage/Shadow`, `SetShipZoom___`, `Body_IsBadlyDamaged`; slot broadcast by `Node_ChildCallB0` |
| 0x14015e930 | **`GuiMapSky_RegisterHudMarkers`** | GuiMapSky `0x140362b00` | +0xb0 | same family, positioned from `TARGET_SCREEN_X/Y?` and the profile |
| 0x14015f0d0 | **`Gui_DrawStatsLabel`** | Gui `0x140360ed8` | +0x2a0 | draws the stats text at a screen pos: `rep_14002e9e0_GetStats` + ZOOM_LEVEL-1 shadow correction (`pow`, `SetShipZoom___`), label string at +0xa40; slot broadcast by `Node_BroadcastCall2A0`, also called by `Scene_PickNodeAtScreenPoint` |
| 0x14015f8d0 | **`Gui_GetNormValue`** | Gui `0x140360ed8` | +0x2f8 | `return *(float*)(this+0xa80)` — the field the +0x2e8/+0x2f0 setters write |
| 0x14015f8e0 | **`List_GetItemAt`** | List `0x140361990` | +0x360 | returns `[[+0xe88]+8+index*0x18]`, negative index = current row +0xee8 |
| 0x14015f930 | **`Gui_GetText`** | Gui `0x140360ed8` | +0x300 | char* of the std::string at +0xa60 (SSO-aware) |
| 0x14015f950 | **`List_GetItemText`** | List `0x140361990` | +0x368 | char* of the std::string in the 0x20-stride records at +0xe70 |
| 0x14015f990 | **`List_GetCurrentText`** | List `0x140361990` | +0x300 (base `Gui_GetText`) | `vtable+0x368(this, +0xee8)` — the getter over the current row |
| 0x140165860 | **`Replica_SetSpecialProperty`** | Replica `0x140362420` | +0x2e0 | parses the page special properties `"time"` -> float +0xe88 and `"emo"` -> int +0xeb0, gated on `pageSpecialEffect_()` |
| 0x14016bd10 | **`ObjectList_SetLinkedObject`** | ObjectList `0x140361d08` | +0x368 | `ADD RCX,0xe88; JMP 0x140150490` and the decompiler resolves 0x140150490 as **`SetLink(Link*,void*)`** — smart-ref assignment on member +0xe88 |
| 0x14016bdf0 | **`Gauge_SetValueClamped`** | Gauge `0x140361238` | +0x2f0 (base `Gui_SetValueAndText`) | `clamp(arg,0,1) -> +0xa80`, no text reformat |
| 0x14016be10 | **`Gui_SetValueAndText`** | Gui `0x140360ed8` | +0x2f0 | `+0xa80 = v; sprintf(0x1403637dc); CopyString(+0xa60)` |
| 0x14016bea0 | **`Gui_SetTextAndValue`** | Gui `0x140360ed8` | +0x2e8 | `CopyString(+0xa60, text); +0xa80 = atof(...)` — the inverse of the above |
| 0x14016bf00 | **`Slider_SetValue`** | Slider `0x1403615c8` | +0x2f0 | value + formatted text + moves the thumb child (+0x8c0 vector, index +0x498) along X (+0x58) or Y (+0x5c) by `(size-thumb)*t` |
| 0x14016c6d0 | **`Gui_Update`** | Gui `0x140360ed8` | +0xa8 (base `Part_UpdateDispatch`/`CreatureUpdate`) | calls the +0x348 layout slot, runs the text-typing throttle (`type_01`, cursor +0xd7c vs +0xee4), then `Part_UpdateDispatch` |
| 0x140170b80 | **`TextureArray_GetFixedDimension`** | TextureArray `0x140366628` | +0x8 **and** +0x10 | both float getters (the two `TextureSingle` width/height slots, HGE +0x318/+0x320) return the constant 0x45800000 = 4096.0f |
| 0x140190c10 | **`lProperty_WriteField`** | lProperty `0x140354b38` | +0x8 | same slot as the eight existing `<type>Property_WriteField`; writes the name via `Node::WriteParameter_`, returns 1 when +0x30 is null |

Naming warnings only (project convention is `Class_VerbObject`, the validator wants
PascalCase); every rename was accepted.

## Still unnamed (3)

| addr | class / slot | what is proven | why no name |
|---|---|---|---|
| 0x14017c780 | HGE_Impl `0x1403672f0` +0x268 | `(*DAT_1439e89b0)(channel, params)`, twin of `Sound_FXSetParameters` (+0x260) | `0x1439e89b0` is in an uninitialised ram block with exactly one xref (this jump), so nothing in the image writes it. It is the IAT slot right after `BASS_FXSetParameters`, so it is *probably* `BASS_FXGetParameters`, but the name is absent from the import table and `BASS_FXSetPriority` has the same 2-arg shape. Not provable. |
| 0x14017c800 | HGE_Impl `0x1403672f0` +0x188, +0x1a8, +0x1b8 | `return -1`, shared by three audio slots between `Music_GetAmplify` (+0x180) and `Stream_Load` (+0x1c0) | the three slots have no named sibling in any table and no caller that says which channel property is stubbed; `-1 = unavailable` is all that is provable (naming it would only restate "return -1"). |
| 0x14004c7e0 | Body `0x140352a30` +0x240 | `JMP [[this]+0x238](this, 0.0f)`; nothing overrides it in the 16 Body-derived tables | unchanged from batch-8 agent 9: the +0x238 draw declares no float parameter and never reads XMM1, so the fixed 0.0 (alpha / time / placeholder) is not verifiable. Plate kept and confirmed by the 12-table dump. |

## Structural facts for agent 10 (`docs/structures.md`)

* **GUI slot map is now proven for the input/render block** (`Gui` base `0x140360ed8`, 12 tables
  share the same body unless noted):
  `+0x60` `remove`, `+0xa8` update (`Gui_Update`, base `Part_UpdateDispatch`),
  `+0xb0` world registration (`Creature_RegisterInWorldLists`; `GuiMapMap`/`GuiMapSky` override
  it with the HUD-marker pass), `+0x108` click (`GUI::_HandleClick`), `+0x110` element
  drag/input latch, `+0x120` hover enter (`Body_OnHoverEnter`), `+0x130` enable body,
  `+0x1a8` `Body_IsStatic`, `+0x238` draw, `+0x240` draw-with-0, `+0x248` mesh-polygon draw,
  `+0x268` draw link sprites, `+0x2a0` stats label, `+0x2e0` special property setter,
  `+0x2e8` text setter, `+0x2f0` value setter, `+0x2f8` value getter, `+0x300` text getter,
  `+0x318`/`+0x320` activate/deactivate, `+0x338` drag, `+0x348` secondary layout,
  `+0x350` element draw, `+0x360`/`+0x368` List item accessors.
* **GUI element value block**: `+0xa60` std::string (text), `+0xa80` float (normalised value;
  the same field is the `+0x2f8` getter), `+0xa84`/`+0xa88` float min/max (clamped by the drag
  handler), `+0xca0` class/type flag byte, `+0xc98` linked flag, `+0xc7d` active/on state,
  `+0xc7c` editor-load latch, `+0xa39`/`+0x9e1`/`+0xa3a` editor drag flags, `+0xee4` rows /
  `+0xee0` columns / `+0xee8` current row / `+0xeec` column-major flag for ObjectList,
  `+0xedc` visible count, `+0xed8` slider element, `+0xea0`/`+0xea8` slider-row records (0x18 B),
  `+0xe70`/`+0xe78` row-name strings (0x20 B), `+0xeb8`/`+0xec0` paired-button records,
  `+0xe88`/`+0xe90` item records (0x18 B, object at +8).
* **`Slider` (+0x2f0 `Slider_SetValue`)**: thumb child = `[+0x8c0 + index*8]` with
  `index = *(int*)(slider+0x498)`; X offset at child+0x58, Y offset at child+0x5c; the axis is
  the larger of `+0x218` / `+0x21c`; `+0x91c` = "move the slider with the thumb" flag.
* **`Frame` overrides**: `+0x130` propagates `+0x8d8` (saved position) into children `+0x8dc`
  before `Creature_EnableBody`; `+0x1a8` `Frame_IsStatic` returns false only for b2Body type 2.
* **`TextureArray`** (`0x140366628`) slots +0x8/+0x10 are both 4096.0f — the array is
  fixed 4096×4096; it does not store the size in the object.
* **`Replica`** `+0x2e0` names: `"time"` -> float +0xe88, `"emo"` -> int +0xeb0.

## Cross-references for other agents

* **Misleading name found (out of my scope, not renamed):** `lootBoxCoins` **0x14014f370** is
  a 33 064-byte GUI **render** routine with exactly one caller (`Gui_DrawElement` 0x14012e7e0)
  that calls `Font_SetupByName`, `Text_DrawSingleLineFormat`, `Text_DrawWrappedFormat`,
  `Gui_DrawScaledShape`, `Gfx_QuadRenderEx`, `Gfx_DrawWorldLine`, `Color_SetAlpha`,
  `Gui_ApplyLensDistortion`, `Node_GetScreenPosition`. It is the per-element draw pass, not a
  coin animation. Ghidra merged 0x14014f370–0x1401574a4 into it, which swallowed at least
  `SetLink` (0x140150490) — see the next point. **Report for the owner / a future rename.**
* **0x140150490 = `SetLink(Link*, void*)`** — proven through `ObjectList_SetLinkedObject`
  (the thunk `ADD RCX,0xe88; JMP 0x140150490` decompiles to `SetLink(this+0xe88, arg)`), but the
  address has no function object because it lies inside the 0x14014f370 blob. A future
  creation/partition pass should split 0x14014f370 first; this closes batch-8 agent 2's note
  "0x14016bd10 thunk targets 0x140150490 which still has no function object".
* **0x140151420 = `SetShipZoom___`**-family helper used by Slider drag and value-set; also
  inside the blob (no function object).
* **`Gui_HandleSliderChange` 0x1401574b0** is called by both drag handlers and by the value
  setter path; it is the single notification point for a value change (not in my scope, already
  named).
* **batch-9 agent 2's blocked funclets**: `0x14016bf00` is **`Slider_SetValue`**, a real Slider
  method `(Slider*, float)` in vtable `0x1403615c8` slot +0x2f0 — it is not a funclet owner and
  has no local EH region.
* **`GuiMapMap`/`GuiMapSky` +0xb0** are *registration* passes (marker init), not draw passes;
  the previous plates called them "registration/draw".
* **`0x1439e89b0`** = the IAT slot between `BASS_FXSetParameters` (0x1439e89a8) and `nRef`;
  it is never written in the image (runtime import), which is why Ghidra shows it as `DAT_`.

## Tool notes

* `batch_decompile` needs the `functions:` key (comma-separated addresses); a 3-function batch
  that included the 33 KB routine timed out — keep batches ≤5 and short bodies only.
* `run_script_inline` wraps the code in a method body: no local method declarations, and
  `SymbolIterator`/`Function`/`Instruction` need their own imports (`symbol.*`, `listing.*`).
  `getSymbolTable().getSymbols(lo, hi)` is broken (Address vs String overload) — iterate
  `getAllSymbols(true)` and filter by address.
* `search_instructions` with `mnemonic:"CALL", operand_pattern:"+ 0x318]"` is the fastest way to
  find the `.text` users of a virtual slot; `operand_pattern:"0x110"` alone is useless (stack
  frames).
