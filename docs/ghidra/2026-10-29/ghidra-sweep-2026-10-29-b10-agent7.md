# Ghidra sweep 2026-10-29 — batch 10, agent 7 (last `FUN_*` A)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.

Scope: `FUN_*` functions in `0x140000000–0x1401FFFFF` not in
`funclet-ownership-2026-10-29.tsv` and not the withheld / creation targets.
The withheld names (`0x14004c7e0`, `0x14017c780`, `0x14017c800`, agent 6) and
`0x14028b340` (renamed in batch 9) were excluded.

**Start: 35 `FUN_*` in the range; 32 in scope.** No entry of the 32 appears in
`funclet-ownership-2026-10-29.tsv`. **End: 0 renamed, 0 created, 32 skipped and
recorded below.** No `save_program`, tags, README/STATUS edit or commit.
No transactions were opened (all evidence came from `decompile_function`,
`disassemble_bytes`, `read_memory` and `search_instructions`), so nothing was
left to leak.

## Result

The batch-9 conclusion holds for every remaining body: the behaviour is proven
but the owning class / field meaning is not, and several are split fragments or
compiler artefacts rather than independent functions. Two new cross-reference
facts were established this pass (the literal `"ANYTIME"` in the NPC-flag
predicate, and the shop/`Joint` targets behind two thunks); they are recorded
below but are not sufficient for a name.

## Skipped and recorded (32)

### Split `CopyEscadraName` loop fragments (3) — not independent functions
* **0x14019ae0f** (49) / **0x14019ae66** (45) — two identical halves of one
  0x20-stride copy loop calling `CopyEscadraName` 0x140004d90; both end in
  `JMP 0x14019ae94`. The surrounding routine starts before 0x14019add0
  (`CALL 0x1401af3b0`, `CALL 0x14019d030`, `CALL 0x140011810`), so these are
  mid-function split points, not callable units.
* **0x14019ae94** (15) — the shared epilogue of that routine
  (`ADD RSP,0x60; POP R15/R14/R13/R12/RDI/RSI/RBX; RET`), followed by
  `CALL 0x1400056c0; INT3...`. Not a function.
Naming any of the three would describe a non-existent unit; repair (merge) is
outside the write set for this batch.

### Padding (1)
* **0x140118699** (6) — seven `INT3` bytes decoded as a 7-byte function.

### `__scrt_*` / CRT outline stubs — none in scope
The 32 in-scope entries contain no `__scrt_*`: the outlines found in earlier
passes live in the funclet range (`0x1403350xx`) and are agents 1/2/8 material.

### Small predicates / accessors whose fields stay unidentified (12)
* **0x140073340** (25) — re-read from ASM this pass:
  `CMP [RCX+0x48],0; JZ clear`, else `MOVSS XMM0,[0x140354834]; COMISS
  XMM0,[RCX+0x15f8]; JBE ret; clear: XOR AL,AL`. Confirms batch 8/9: the
  "true" path never writes AL, so the return value is the low byte of `this`,
  not a predicate result. Called from Body_Explode, BulletImpact?,
  World_ThermalPass, SCR_BOMBERS, deployFromReserve,
  Physics_ProcessContactRecord, FX_SpawnCloudPuff, Battle_SpawnQueuedShipForSlot.
  Unnameable.
* **0x140073530** (37) — `if (p=this+0x48) { (*(p->vtable+0x48))(p); this+0x48=0; }`.
  Callers `!ClickFunc` and `Scene_RebuildFromProfile`. `+0x48` is a child-object
  pointer; child class unproven.
* **0x140083d60** (4) — `return *(u8*)(this+0x10)`. Sole caller
  `handleAmmoInBattle?`; the flag's writer is unknown.
* **0x140049cd0** (34) — `if ((int)this+0x2e8 < arg) return 0;
  return (float)this+0x248 != 0.0;`. Callers pass arg=2 from `creatureLogic`,
  `mainDialogWithChoices`, `!ClickFunc`; a field scan shows `+0x2e8` is a float
  on `Body` (`Body_Explode` uses MOVSS) but compared as an int here, so the
  object is a different class. Neither field identified.
* **0x1400a6210** (23) — `this+0xf8 == 0 && this+0xf6 != 0` on an NPC record.
  New proof this pass: it is exactly the inner test of `validateNpc?`
  0x140295250 (which does `GetNpcFromProfile` first), and the flag byte
  `+0xf6` is also read by `Dialog_BuildAttitudeList` 0x1401cf240 and
  `restOfEventsPrologueAntIsaiah` 0x14028f599. In the sole direct caller
  `Dialog_ExecuteChoiceActions` the fallback string compared with
  `stringCompLengthAndContent` is the literal **"ANYTIME"** at `0x14035b1f8`
  (`MOV RCX,[RBP-0x?]; CMP ...` at 0x1400b88b4-0x1400b88d8). That proves the
  test gates an ANYTIME dialog option, but not which of `+0xf6`/`+0xf8` is the
  ANYTIME flag (the shipped `validateNpc?` name is itself unproven), so a name
  such as `Npc_IsAnytime` would overstate the evidence. Skipped.
* **0x1400fdec0** (60) — clears `+0x1d0`, word `+0x1a4`, `+0x1b8` and the
  std::string at `+0x1a8/+0x1c0/+0x1c8`. Sole caller is the radio-event
  evaluator 0x140238460 (stale `sqrtf` label): it builds an event record from
  `PLAYER_ESCADRA_`/`Get_Profile_()`/`RadioBearing_`, dispatches it, then calls
  this routine before `CopyEscadraName`. It is clearly a radio-record reset,
  but the record type has no proven class name and `0x1400fdf00`
  `Escadra_ReportRadioEvent` is adjacent, so naming it after the record would
  be inference from position. Skipped.
* **0x1400f51c0** (51) — returns `1.0f` or `(*(vtbl+0x1d0))()` of
  `[[[this+0x288]+0x10]+0x50]`, guarded by `this+0x290 != 0`. Callers
  `VideoTask_RenderMapScene` and `Gui_DrawStatsLabel` use it as a screen-scale
  multiplier (same role as batch 9). Nested object unidentified.
* **0x1400bee20** (57) — zeroes `+0x128` on every element of the `this+0x8c0`
  vector whose byte `+0x71` is set. `+0x8c0` is a real `Body` member
  (`createNewBody`, `Body_Constructor`, `Body_Destructor`, `copyOverBody`),
  but the element type and the meaning of `+0x71`/`+0x128` are unknown.
  Sole caller `rep_14017a420_New` 0x140185ff0 (a body/part selection handler).
* **0x1400f8da0** (11) — thunk `MOV RCX,[RCX+0x520]; JMP 0x140221be0`
  (the decompiler renders the target as the stale label
  `rep_140204600__Init_thread_footer`; the byte target is 0x140221be0, a large
  unrenamed routine). Callers `rep_1401f3c10_APP:MoveVolume` and
  `DrawShopShipworksScreen?`. The obvious sibling at 0x1400f8d90 jumps to
  `Shop_ReturnItemToPlayer`; both adapt `this+0x520` as first argument, but the
  target's semantics are unproven, so the thunk is unnamed.
* **0x14018f910** (35) — byte-identical to 0x140017d10 (same doubly-indirect
  child release). Only a `.pdata` xref; no class.
* **0x1401941f0** (39) — `if (this+0x58) return 0x140280fa0(this+0x58, this) != 0`.
  Callee 0x140280fa0 is provably a `Joint` remover: `Joint_DestroyB2Joint` +
  `Joint_SetDeadFlagAndQueue(1)` + unlink from the `world+0x110` list + free.
  This confirms batch 9, but the holder class is still unknown, so neither the
  callee (out of scope) nor this wrapper can be named.

### Thunks / dispatch wrappers (4)
* **0x140017d10** (35) — `p = *(this->vtable[?]+4 + 0x48 + this); if (p)
  (*(p->vtable+0x10))(p);` doubly-indirect child release; no code xref
  (`.pdata` only).
* **0x140170210** (23) — `if (p) return (*(p->vtable+8))(p, this);` only
  callers in `rep_..._WriteToClientLog`; slot semantics unproven.
* **0x14016cf30** (21) — `(**(code**)*newValidHGE)();` i.e. slot 0 of the
  pointer global `newValidHGE`. HGE vtable slot 0 is `Release`
  (0x1403672f0 → 0x14017d360 `HGE_Impl::Release`), but the global symbol is not
  proven to be the HGE singleton, so the wrapper stays unnamed.
* **0x140027f90** (119) — walks the `Body` slot vector `+0x350/+0x358` and calls
  the stale `rep_1402b1a80_MakeGlobal_` on `element+0x58`; callee unproven.
  Callers include `memcmp_editor`, `?BuyPartShop`, `Frame_RemoveBody`.

### Setters / record initialisers with no proven owner type (7)
* **0x14016dde0** (8) — `*(float*)(this+0x1a4) = arg`. Called from
  `TextGrid_LayoutProjected`/`TextGrid_LayoutLocal` with the grid's `+0xa14`
  float, on the loop element; the element type is unknown.
* **0x14016ddf0** (6) — `*(int*)(this+0x1a0) = arg`. Called from
  `TextGrid_CreateObject` with the source record's `+0x148` int.
  `+0x1a0`/`+0x1a4` are TextGrid element fields; the element class is unproven.
* **0x140088950** (20) — 0x28-byte record init `[0]=arg; [1]=[3]=[4]=0`, used
  inline in `CSGlitch_Constructor` and
  `ShaderDeferringCloseAndPrebloom_Constructor`; record type unproven.
* **0x14012b4f0** (219) — ctor of a 0x118-byte record in `lootBoxCoins`
  (two `1.0f` defaults at +0x54/+0xac/+0x104, `[0x22]=2`); type unproven.
* **0x1401a4210** (59) — 0x20-byte record ctor (qword + 7 dwords) inlined in
  `displayCityOnMap` and a CRT twin; type unknown.
* **0x1401a47f0** (21) — 0x18-byte record ctor inside `memmoveMAIN`; type
  unknown.
* **0x1401a4b40** (56) — frees `*(this+8)+0x20` via 0x1401a5090 then
  `free(*(this+8))`; no caller, no owner type.

### Larger / unclassified bodies (5)
* **0x1400458c0** (3341) — editor "collect and lay out the selected ship's
  mounted parts" pass; body > 0x2000, skipped per ground rule 6 (batch 8/9
  verdict kept). References `?AVLink@@` vtable 0x140352310.
* **0x140092e70** (43) — releases `this[7]` through vtable `+0x20` with the
  not-self flag, then clears it. Only real caller 0x14034aa47 (cleanup region);
  element type unknown.
* **0x1401783c0** (987) — compiler-generated byte copy from `src+8` onward in
  the HGE media layer; type unknown (batch-3 verdict re-confirmed).
* **0x1400bc5c0** (31) — `if (!IsInEditor) return 0; <call 0x1400c12a0>;
  return 1`. Only caller `Input_HandleMouseMove` ignores the result; 0x1400c12a0
  is the 3236-byte editor body-collection pass, so the wrapper's responsibility
  is not proven.
* **0x14010f1a0** (68) — trims the `0x1403ef580` global vector through the
  stale 0x1400d9a10 and copies `DAT_1403ef578` → `DAT_1403ef57c`; the original
  is a real unnamed helper, so the operation is a global-list reset with no
  proven owner.
* **0x1401102c0** (116) — picks state 5 vs 7 from `dist*1000/+0x494 < 7200`
  and calls the stale `rep_14010b1e0_MakeGlobal_`; the 5/7 meaning remains
  unresolved (batch 4/6/7/8/9 all left it).

## Out-of-scope findings for the `rep_*` owners (report only)

* **0x140280fa0** — labelled `rep_14025ecf0_..._free` but is a real
  `Joint` removal routine (`Joint_DestroyB2Joint`, `Joint_SetDeadFlagAndQueue`,
  unlink from `world+0x110`, free). Used by 0x1401941f0 above.
* **0x140221be0** — labelled `rep_140204600__Init_thread_footer`; a large real
  routine (TLS guard, 0x18-node list, median sort) and the target of the
  `this+0x520` thunk 0x1400f8da0.
* **0x140295250** `validateNpc?` and **0x1400a6210** are duplicate copies of
  the `+0xf8 == 0 && +0xf6 != 0` NPC test; if a later pass proves the flag,
  both should get the same stem.

## New structure facts for agent 10

* NPC record: bytes `+0xf6` (flag read by `Dialog_BuildAttitudeList`,
  `restOfEventsPrologueAntIsaiah` and both copies of the NPC validity test) and
  `+0xf8` (must be 0 for the test to pass). The dialog handler also accepts the
  literal NPC label **"ANYTIME"** (`0x14035b1f8`) as an alternative.
* HGE vtable 0x1403672f0 slot 0 = `HGE_Impl::Release` 0x14017d360 (confirmed by
  reading the table).
* TextGrid element fields: `+0x1a0` int (from source `+0x148`), `+0x1a4` float
  (from grid `+0xa14`).
* `Body+0x8c0/+0x8c8` is a vector member; element byte `+0x71` and dword
  `+0x128` are reset by 0x1400bee20.
