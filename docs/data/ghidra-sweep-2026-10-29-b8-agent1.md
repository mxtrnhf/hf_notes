# Ghidra sweep 2026-10-29 — batch 8, agent 1 (`.rdata` creation A)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `.rdata` qword in `0x140352000–0x14036A000` that points into
`0x140070000–0x1400FFFFF` and has **no function object** — create, name, plate.
Source list: `docs/data/ghidra-sweep-2026-10-29-b7-agent8.md` (the 170-target find).

**Created 46 / 46, named 46, plated 46. Skipped 0.** One side-effect creation
(`0x140049ea0`, the real body behind the `0x140073520` thunk).

Verification after the pass: re-running the scan (`.rdata` qwords in
`0x140352000–0x14036A000` → `0x140070000–0x1400FFFFF`) reports
**`remaining functionless: 0`**, and no target is left as `FUN_*`/`LAB_*`.
Program function count at the end of this pass: **5,692** (5,251 after batch 7;
the other batch-8 agents account for most of the increase).

## Method

The b7 note listed the targets but not their owners. The class of each target was
resolved mechanically instead of guessed:

1. For each `.rdata` reference, scan backwards for the nearest preceding qword that
   points at an MSVC **RTTI Complete Object Locator** (signature `1` at `COL+0`),
   then read the class name out of the TypeDescriptor at
   `imagebase + *(int*)(COL+0xc) + 0x10`. That gives the vtable base and the exact
   class for all 46 (e.g. `.?AVEffect@@`, `.?AVMapShip@Escadra@@`,
   `.?AV?$_Func_impl_no_alloc@V<lambda_...>@@XM@std@@`).
2. The slot index `(ref - vtable)/8` then gives the virtual, and the body (pseudo-
   disassembly, plus the decompiler once the function object existed) gives the
   behaviour. The shader slots line up exactly with the class map that batch 3
   agent 1 recovered from the constructors, which is an independent confirmation.

Everything below is `[code]` unless marked otherwise.

## What the 46 are, by family

### 1. D3D11 / shader layer (`0x140082b60–0x1400a0000`)

| addr | name | vtable / slot | why |
|---|---|---|---|
| `0x140083e70` | `TextureSingle_GetField20` | `TextureSingle` `0x140356740` slot 1 | `CVTSI2SS XMM0,[this+0x20]`; `Texture` slots 1–3 are `JMP [__imp__purecall]`, so these are the three pure-virtual overrides. `RenderTarget` (`0x140356768`) carries the identical three bodies. |
| `0x140083d50` | `TextureSingle_GetField24` | slot 2 | `CVTSI2SS XMM0,[this+0x24]`. |
| `0x140083c40` | `TextureSingle_IsSameObject` | slot 3 | `CMP RCX,RDX; SETZ AL`. |
| `0x140088410` | `Effect_GetProjectionMatrix` | `Effect` `0x140356a08` slot 18 | copies `this+0xc0..+0xff` (16 floats) to the out buffer; `Effect_SetProjectionMatrix` (slot 17) fills exactly that block and pushes it through the property at `+0xb8`. |
| `0x140088440` | `IShader_GetProjectionMatrix` | `IShader` `0x140356968` slot 18 | same signature, writes 16 zero floats — the base/default implementation. |
| `0x1400887f0` | `Effect_SetProjectionMatrixRaw` | `Effect` slot 16 | copies the caller's 16 floats into `+0xc0` then tail-calls `Property_SetFloat16(*(this+0xb8), this+0xc0)`. |
| `0x14008b260` | `ShaderClouds_Init` | `ShaderClouds` slot 2 | binds uniforms via `Effect_SetMatrixParam` `0x140088650`. |
| `0x14008c9c0` | `ShaderDefault_Init` | `ShaderDefault` slot 2 | same, 0x27 params. |
| `0x14008d290` | `ShaderDefault_SetFlag118` | `ShaderDefault` slot 14 | `AND DL,1; MOV [this+0x118],DL`. Slot 14 is the `_guard_check_icall` stub in every other shader table. |
| `0x14008d6e0` | `ShaderDeferringClose_Init` | slot 2 | same, 0x33 params. |
| `0x14008d880` | `ShaderDeferringClose_EmitVerticesA` | slot 8 | walks `+0x20` vertex cursor, emits 4 at a time. |
| `0x140092580` | `ShaderDeferringSubscreen_EmitVerticesA` | slot 8 | `CMP [this+0x50],[this+0x20]` then emit 4. |
| `0x1400928b0` | `ShaderDepth_Init` | slot 2 | uniform bind. |
| `0x1400942b0` | `ShaderGlitch_Init` | slot 2 | uniform bind, 0x39 params, then three name lookups from the literals at `0x140356c10/0x140356c18`. |
| `0x140094780` | `ShaderGlitch_EmitInstances` | slot 15 | forward `this+0x180` to `*(this+0x18)` vtable `+0x40` (flags 1,1). |
| `0x140095810` | `ShaderLightingMap_Init` | slot 2 | uniform bind. |
| `0x1400976e0` | `ShaderPrebloom_EmitVerticesA` | slot 8 | vertex emit. |
| `0x1400995c0` | `ShaderPrebloomAndOutlineLOD_EmitVerticesA` | slot 8 | vertex emit. |
| `0x14009fff0` | `ShaderParamFloatNew_GetValue` | `ShaderParamFloatNew` `0x1403591e0` slot 2 | `return *(float*)*(this+0x18)`. |
| `0x1400a0000` | `ShaderParamTextureNew_CommitValue` | `ShaderParamTextureNew` `0x140359150` slot 1 (also `…TextureArrayNew` `0x140359168`, `…TextureVectorNew` `0x140359190`) | `p=*(this+0x18); p->0x28 = p->0x20`. |

All the `Shader*_Init`/`EmitVerticesA` names come from the batch-3 agent 1 class map
(`docs/data/ghidra-sweep-2026-10-29-b3-agent1.md`); that note had recorded the
addresses but the targets had never been given function objects, which is why they
were still in the b7 "no function object" list. The bodies confirm the roles: every
slot-2 body calls `Effect_SetMatrixParam`, every slot-8 body reads the vertex cursor
at `+0x20`.

### 2. `std::` stream layer (`0x140356790` / `0x140356810`)

| addr | name | slot | why |
|---|---|---|---|
| `0x140082ea0` | `FileBuf_Lock` | `basic_filebuf` slot 1 | `RCX=[this+0x80]; if (RCX) jmp [_lock_file]`. |
| `0x140082f10` | `FileBuf_Unlock` | slot 2 | `… jmp [_unlock_file]`. |
| `0x140085d90` | `FileBuf_PBackFail` | slot 4 | textbook `pbackfail`: `gptr>eback` and `*(gptr-1)==c` → bump `*(this+0x50)`, decrement `+0x38`, return 0. |
| `0x140086890` | `FileBuf_SetBuf` | slot 12 | builds the `setvbuf` mode (null buffer + non-zero size → 4 = `_IONBF`), calls `setvbuf`, sets `+0x7c=1`. |
| `0x140082bf8` | `Ofstream_DeletingDestructorThunk` | `basic_ofstream` `0x140356810` slot 0 | vtordisp adjustor: `this -= *(int*)(this-4)`, `JMP 0x140082c50` which destroys the `-0xa8` sub-object (`basic_ostream` dtor) and frees. |

This is the C++ stream layer used by the dialogue/save loaders (cf.
`docs/engine-hge.md`: `load_dialog` uses an `ifstream`), not game code.

### 3. `std::function<float(float)>` wrappers around the property setters

Four `_Func_impl_no_alloc<lambda…,float,float>` tables `0x140357cb0/ce8/d20/d58`; the
`_Do_call` of each is one of the property setters `Property_SetFloat148`,
`0x140092fc0` (field `+0x150`), `Property_SetFloat158`, `Property_SetFloat168`.

| addr | name | slot | why |
|---|---|---|---|
| `0x140092f90` | `FuncImpl_SetFloat148_CopyMove` | 0 = 1 | `[dst]=vt; dst+8=this+8; return dst` (ICF-folded `_Copy`/`_Move`). |
| `0x140092f70` | `FuncImpl_SetFloat158_CopyMove` | 0 = 1 | same, vtable `0x140357d20`. |
| `0x140092f50` | `FuncImpl_SetFloat168_CopyMove` | 0 = 1 | same, vtable `0x140357d58`. |
| `0x140092f30` | `FuncImpl_Field150_CopyMove` | 0 = 1 | same, vtable `0x140357ce8`. |
| `0x140092fc0` | `FuncImpl_Field150_DoCall` | 2 | `Property_SetFloat(*(this+8)+0x150, v)`. |
| `0x140093080` | `FuncImpl_GetTargetPointer` | 5 (all four) | `LEA RAX,[this+8]`. |
| `0x1400930c0` | `FuncImpl_SetFloat148_TargetType` | 3 | returns `&type_info 0x1403c3010`. |
| `0x140093090` | `FuncImpl_Field150_TargetType` | 3 | `&type_info 0x1403c2fd0`. |
| `0x1400930b0` | `FuncImpl_SetFloat158_TargetType` | 3 | `&type_info 0x1403c2f90`. |
| `0x1400930a0` | `FuncImpl_SetFloat168_TargetType` | 3 | `&type_info 0x1403c2f50`. |

Slot order observed: `_Copy`(0), `_Move`(1, ICF-folded with 0), `_Do_call`(2),
`_Target_type`(3), `_Delete_this`(4, the ICF'd `free`), `_Get_function_pointer`(5).

`Property_SetFloat148` (`0x140093050`) itself resolves the field object through
`*(this+8)+0x148`, i.e. the impl wraps a `(property-owner, field)` pair and the
`std::function` is the generic setter used by the shader/pipeline constant block.

### 4. GUI / serializer classes (`0x1400e7xxx–0x1400f5xxx`)

| addr | name | vtable / slot | why |
|---|---|---|---|
| `0x1400e7d80` | `Intel_ScalarDeletingDestructor` | `Intel` `0x14035dff8` slot 0 | `Intel_Destructor(); if (flag&1) free(this)`. |
| `0x1400e7e40` | `Launched_ScalarDeletingDestructor` | `Launched` `0x14035e808` slot 0 | `Launched_Destructor(); …`. |
| `0x1400e80d0` | `MapShip_ScalarDeletingDestructor` | `.?AVMapShip@Escadra@@` `0x14035e498` slot 0 | installs its own vtable, releases `+0x50` via vtable `+0x48`, frees the Links at `+0x78/+0x60/+0x48`, `ISerializable_Destructor`, then `free`. |
| `0x1400e8210` | `ListVectorsProperty_ScalarDeletingDestructor` | `listVectorsProperty` `0x14035df50` slot 0 | `Property_Destructor` + delete. |
| `0x1400e8250` | `VProperty_ScalarDeletingDestructor` | `vProperty` `0x14035df28` slot 0 | same. |
| `0x1400e8290` | `VectorVectorsProperty_ScalarDeletingDestructor` | `vectorVectorsProperty` `0x14035df78` slot 0 | same. |
| `0x1400f3a30` | `Escadra_DisplayNameOnUI` | `Escadra` `0x14035e4e0` slot 43 | grows the `std::string` at `+0xc8` with the literal **`ESCADRA_NAME_`** (`0x14035fd50`, 13 chars), builds a temp via `0x140015570`, calls `displayOnUI_` through the wrapper `0x1401ae060`. |
| `0x1400f3b20` | `Location_DisplayNameOnUI` | `Location` `0x14035e670` slot 43 | identical, literal **`LOCATION_NAME_`** (`0x140360150`, 14 chars). |
| `0x1400f5200` | `MapShipBody_GetAdjustedField90C` | `MapShipBody` `0x14035e1d0` slot 58 | `x=[this+0x90c]; p=[this+0xa50]; if(p) x -= (p->0x168 / 9000.0) * 0.3`. |
| `0x1400f5270` | `Node_GetField128` | shared virtual, same slot in `MapShipBody` (47), `Mark` (47), `Escadra`, `Location` | `return *(float*)(this+0x128)`. |
| `0x140073520` | `Body_Kill` (thunk) | `Creature` `0x140354c40` slot 9 | `JMP 0x140049ea0` = `Body_Kill`. |

## New / confirmed structure facts for agent 10 (`docs/structures.md`)

* **`Effect+0xc0..+0xff` is the 4x4 projection matrix** and `Effect+0xb8` is the
  `Property` object that owns it (`Property_SetFloat16` target). The virtual set is
  now complete and consistent: slot 16 = set raw block (`0x1400887f0`),
  slot 17 = `Effect_SetProjectionMatrix` builds scale/translate/ortho into `+0xc0`,
  slot 18 = getter (`0x140088410`, `IShader` provides the zero default).
* **`Property` layout** (reinforces `0x1400a0010`): `+0x8` = owner object,
  `+0x10` = "silent" byte (skip the change notification), `+0x18` = `float*` to the
  storage; the owner's change-notification virtual is `owner->vtable+0x28`.
* **`Texture`/`TextureSingle`/`RenderTarget`**: `Texture` declares three pure virtuals
  (slots 1–3, `JMP [__imp__purecall]`); `TextureSingle` and `RenderTarget` implement
  them as `(float)+0x20`, `(float)+0x24` and pointer identity. `Texture+0x18` and
  `+0x50` are the two refcounted D3D11 objects (released through vtable `+0x10`).
  Width vs height remains unprovable (b7 note) — `+0x20`/`+0x24` in that order is
  *likely* width/height but is not proven.
* **`Node`-family virtual returning `+0x128`** is installed in at least four
  unrelated tables (`Escadra`, `Location`, `MapShipBody`, `Mark`); for `Escadra` it is
  the documented side marker (`findings/battle-ally.md`).
* **Class-name literals**: `ESCADRA_NAME_` `0x14035fd50` (13 chars),
  `LOCATION_NAME_` `0x140360150` (14 chars) — used by the slot-43 "display my name on
  the UI" virtual of those two classes.
* `MapShip` (nested in `Escadra`) is a real class with its own vtable `0x14035e498`;
  its destructor releases a child at `+0x50` and three Links at `+0x48/+0x60/+0x78`.
* `Intel` (`0x14035dff8`) and `Launched` (`0x14035e808`) vtables are adjacent to
  `IntelPolygon` and `LastPlayerPosData`, i.e. the map-intel/`Location` family.

## Left unproven (created + plated, but the name deliberately describes only the field)

* `TextureSingle_GetField20` / `GetField24` — width/height assignment not provable.
* `MapShipBody_GetAdjustedField90C` — `+0x90c`, `+0xa50`, `+0xa50->0x168` unidentified;
  only the arithmetic (9000.0 and 0.3 constants) is proven.
* `Node_GetField128` — class-specific meaning varies per table (documented for
  `Escadra` only).
* `ShaderParamTextureNew_CommitValue` — `+0x20 → +0x28` copy proven, the meaning of
  the two fields is not.
* `FuncImpl_*` — MSVC `std::function` internals; slot roles are proven by body, the
  "which lambda" mapping is proven only through the `_Do_call` target.

## Cross-references for other agents

* `0x140049ea0` = **`Body_Kill`** (already in the parent's name table
  `b7a1_allnames2.tsv`); it had no function object and was created as a side effect of
  creating the `0x140073520` thunk. Its body uses `Body+0x3c4` (`m_logic`, 900 =
  `0x384`), `+0x9d0`, `+0x230` (the joint list), `Joint_Release` `0x140193970` and
  `Node_KillSelf` `0x1402805d0` — so `+0x230` is a joint list on Body, which agent 10
  may want for `structures.md`.
* `0x1400838e0` (still unnamed, agent 8's list) is the texture factory wrapper: it
  builds a `D3D11_TEXTURE2D_DESC` (`{w,h,1,1,0x37,1,0,0x40}`) then calls device
  vtable `+0x28`/`+0x50` and `New(0x40)`; the 0x40-byte wrapper is
  `{texture, view, copy-of-view}` (`*(o)=tex; *(o+8)=view; tex->vtable+0x50(o+0x10)`).
* The `TextureSingle`/`RenderTarget` slot-1/2 float getters are the targets of the HGE
  adapters `0x14016cd10` / `0x14016cd30` (HGE vtable `+0x320`/`+0x318`), which therefore
  return `(int)*(this+0x24)` and `(int)*(this+0x20)` in one order or the other — see the
  b7 note; nothing here resolves which is width.
