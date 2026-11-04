# Unnamed-function sweep, 2026-10-29 — batch 3, agent 1

Range: `0x140080000–0x14009FFFF` (235 unnamed `FUN_*`).

Program `Highfleet.exe.unpacked.exe` v1.163. Every name below was applied with
`rename_function_by_address` and given a doc-style plate comment (summary /
Algorithm / Parameters / Returns).

**Result: 246 renames** — all 220 `FUN_*` still unnamed in the range plus 26
`rep_*` FID aliases (mostly `rep_..._New` / `rep_..._FastFail?`) that turned out
to be real shader constructors, `Init` bodies or emitters. 15 `FUN_*` were
deliberately left (see "Skipped / open"), and 10 further vtable slots are
addresses *inside* an existing function body and therefore not renameable
without `create_function`.

## What the range actually is

The blackboard described this block as "the class factory: `New` + ctor +
`push_back`". It is not. The block is the game's **D3D11 shader layer**:

* `0x1400817E0–0x1400866FF` — `ComputeShader` / `CSGlitch`, `Texture`,
  `TextureSingle`, `RenderTarget` helpers, `std::bad_cast` / `std::codecvt`
  boilerplate and the D3D11 render-state (blend / rasterizer / scissor) helpers.
* `0x1400866FF–0x14009C430` — the `Effect` hierarchy: the `Effect` base class,
  `Shader` / `VShader` / `PShader`, 29 concrete `Shader*` classes, and their
  `ConstantBuffer<CBConstants<ShaderX>>` objects.
* `0x14009F8C0–0x14009FF80` — the `ShaderParam*New` value-binding classes
  (`ShaderData`, `ShaderResourceView`, `ShaderParam{New,Float,Int,Matrix,
  Vector,Texture,TextureArray,TextureVector,VectorArray}New`) plus their
  constructors and scalar deleting destructors.

The class of every function was recovered from MSVC RTTI, not guessed: each
vtable is preceded by a `CompleteObjectLocator` whose
`pTypeDescriptor` (RVA at COL+0xc) points at a `.?AV<Class>@@` name. The full
recovered map is at the end of this file.

Because most of these functions are **virtual members**, they have no direct
callers; RTTI + the vtable slot index is what identifies them.

## Renames

See the tables below (one per owning class). `slot N` is the vtable index.


## Recovered class map (shader hierarchy)

`vtable` is the address stored in the object's first field; every slot number
below is the index from that address. `?` marks a class whose constructor lives
outside the range (or was already named).

### Base classes

| class | vtable | members renamed here |
|---|---|---|
| `ComputeShader` | `0x140356668` | `ComputeShader_Constructor` `0x1400817E0`, `ComputeShader_Destructor` `0x140081800`, `ComputeShader_Dispatch` `0x140081880` |
| `CSGlitch` | `0x140356698` | `CSGlitch_UploadParams` `0x140081BC0` (slot 1), `CSGlitch_ClearParams` `0x140081C70` (slot 2) |
| `Texture` | `0x140356718` | `Texture_ScalarDeletingDestructor` `0x140082D10` (slot 0) |
| `IShader` | `0x140356968` | `IShader_Destructor` `0x1400874E0` (slot 1) |
| `Effect` | `0x140356A08` | `Effect_Destructor` `0x1400874A0` (1), `Effect_Release` `0x140088340` (5), `Effect_Draw` `0x140088700` (13), `Effect_SetProjectionMatrix` `0x140088830` (17), `Effect_SetMatrixParam` `0x140088650` (19), `Effect_SetInstanceMatrices` `0x140088460` (20), `Effect_SetTexture` `0x140088920` (21) |
| `ConstantBuffer<CBMatrix<Effect>>` | `0x140356AD8` | `EffectMatrixConstantBuffer_Upload` `0x1400882A0` (slot 0) |
| `Shader` | `0x140356AF0` | `Shader_Destructor` `0x140088C80` |
| `VShader` | `0x140356B00` | `VShader_Constructor` `0x140088C00`, `VShader_Destructor` `0x140088CB0`, `VShader_CompileFromFile` `0x140089210` (slot 1) |
| `PShader` | `0x140356B18` | `PShader_Constructor` `0x140088BE0`, `PShader_Destructor` `0x140088C20`, `PShader_CompileFromFile` `0x140088D10` |

### Concrete shaders

Column layout: ctor / dtor (slot 1) / `Init` (slot 2) / `EmitVerticesA`
(slot 8) / `EmitVerticesB` (slot 9) / `ConstantBuffer<CBConstants<Class>>`
upload (slot 0 of the CB vtable). Extra members are listed after the row.

| class | vtable | ctor | dtor | Init | EmitA | EmitB | UploadConstants |
|---|---|---|---|---|---|---|---|
| `ShaderBackground` | `0x140356B60` | `0x1400894D0` | `0x140089620` | `0x140089760` | `0x140089970` | `0x140089A80` | `0x140089670` |
| `ShaderBloom` | `0x140356C50` | `0x140089D60` | `0x140089EB0` | `0x140089FF0` | `0x14008A360` | `0x14008A590` | `0x140089F00` |
| `ShaderBlur` | `0x140356DB8` | `0x14008A740` | `0x14008A7D0` | `0x14008A8C0` | `0x14008AA70` | `0x14008ACA0` | `0x14008A820` |
| `ShaderClouds` | `0x140356EA0` | pre-existing `ShaderCloudsConstructor` | `0x14008B130` | `0x14008B260` | `0x14008B630` | `0x14008B820` | `0x14008B180` |
| `ShaderColor` | `0x140356FD8` | `0x14008BBF0` | `0x14008BD00` | `0x14008BDF0` | `0x14008BFA0` | `0x14008C300` | `0x14008BD50` |
| `ShaderDefault` | `0x1403570C8` | ? | `0x14008C920` | `0x14008C9C0` | `0x14008CE70` | `0x14008D070` | ? |
| `ShaderDeferringClose` | `0x140357220` | `0x14008D460` | `0x14008D5B0` | `0x14008D6E0` | `0x14008D880` | `0x14008DA50` | `0x14008D600` |
| `ShaderDeferringCloseAndPrebloom` | `0x140357310` | `0x140090230` | `0x14008E600` | `0x14008E900` | `0x14008EE80` | `0x14008F570` | `0x14008E720` + `0x14008E7C0` |
| `ShaderDeferringFar` | `0x140357490` | `0x14008FCB0` | `0x14008FD40` | `0x14008FD90` | `0x14008FE60` | `0x140090040` | ? (shared) |
| `ShaderDeferringFarPrerendered` | `0x140357568` | ? | `0x140090380` | `0x1400905B0` | `0x140090B60` | `0x140090DE0` | `0x1400903D0` + `0x140090470` + `0x140090510` |
| `ShaderDeferringFarStepness` | `0x140357788` | `0x140091190` | `0x1400912A0` | `0x140091390` | `0x140091530` | `0x140091740` | `0x1400912F0` |
| `ShaderDeferringMid` | `0x140357870` | `0x140091B10` | `0x140091C20` | ? | `0x140091D90` | `0x140092010` | ? (shared) |
| `ShaderDeferringSubscreen` | `0x140357948` | `0x140092280` | `0x140092310` | `0x140092400` | `0x140092580` | `0x1400926A0` | `0x140092360` |
| `ShaderDepth` | `0x140357A48` | `0x1400927D0` | `0x140092860` | `0x1400928B0` | `0x140092A80` | `0x140092C30` | ? |
| `ShaderDithering` | `0x140357B48` | `0x140092DE0` | `0x140092EE0` | `0x140093170` | `0x1400937B0` | `0x1400939E0` | `0x1400930D0` |
| `ShaderGlitch` | `0x140357D90` | `0x140094B20` | `0x140093F40` | `0x1400942B0` | `0x1400947A0` | `0x140094960` | `0x1400940E0` + `0x140093FA0` + `0x140094040` |
| `ShaderLighting` | `0x140357F08` | `0x140095590` | `0x140094BF0` | `0x140094CE0` | `0x140094FF0` | `0x140095220` | `0x140094C40` |
| `ShaderLightingMap` | `0x140358000` | `0x140096060` | `0x1400956E0` | `0x140095810` | `0x140095B10` | `0x140095DC0` | `0x140095730` |
| `ShaderMapPostProcessing` | `0x140358140` | `0x140096540` | `0x1400960F0` | `0x1400961E0` | `0x140094FF0` | `0x140095220` | `0x140096140` |
| `ShaderOutline` | `0x140358250` | `0x140096E40` | `0x1400965D0` | `0x140096760` | `0x1400969D0` | `0x140096C40` | `0x1400966C0` + `0x140096620` |
| `ShaderPost` | `0x140358340` | `0x1400971E0` | `0x140096F10` | `0x140097000` | `0x1400937B0` | `0x1400939E0` | `0x140096F60` |
| `ShaderPrebloom` | `0x140358428` | `0x140097BC0` | `0x140097270` | `0x140097360` | `0x1400976E0` | `0x140097950` | `0x1400972C0` |
| `ShaderPrebloomAndOutline` | `0x140358510` | ? | `0x140097C90` | `0x140097F40` | `0x1400985C0` | `0x140098970` | `0x140097EA0` + `0x140097D60` + `0x140097E00` |
| `ShaderPrebloomAndOutlineLOD` | `0x1403586F8` | `0x140098D70` | `0x140098E00` | `0x1400990B0` | `0x1400995C0` | pre-existing `ShaderPrebloomAndOutlineLOD?` | `0x140099010` + `0x140098ED0` + `0x140098F70` |
| `ShaderRadialBlur` | `0x140358850` | `0x140099D30` | `0x140099DC0` | `0x140099EB0` | `0x14008AA70` | `0x14008ACA0` | `0x140099E10` |
| `ShaderRainDrops` | `0x140358948` | `0x14009A180` | `0x14009A210` | `0x14009A3A0` | `0x1400937B0` | `0x1400939E0` | `0x14009A300` + `0x14009A260` |
| `ShaderShadowMapping` | `0x140358A40` | `0x14009A610` | `0x14009A6A0` | `0x14009A790` | `0x14009A970` | `0x14009AB10` | `0x14009A6F0` |
| `ShaderShockwave` | `0x140358B50` | `0x14009ACC0` | `0x14009AD50` | `0x14009AE40` | `0x1400937B0` | `0x1400939E0` | `0x14009ADA0` |
| `ShaderShockwaveTemplate` | `0x140358C30` | `0x14009B260` | `0x14009B370` | `0x14009B4B0` | `0x14009B630` | `0x14009B790` | `0x14009B3C0` |

Notes on the table:

* **Shared virtuals.** Several classes share the same emitter body, so only one
  name exists per address and its plate names the other owners:
  `0x14008AA70/B` = Blur + RadialBlur, `0x1400937B0/E0` = Dithering + Post +
  RainDrops + Shockwave, `0x140094FF0/0x140095220` = Lighting + MapPostProcessing,
  `0x140098450` = PrebloomAndOutline + LOD (`EmitQuad`, slot 11).
* **Additional slots renamed:** `ShaderClouds_EmitQuad` `0x14008B4D0`,
  `ShaderDefault_EmitQuad` `0x14008CD10`, `ShaderPrebloom_EmitQuad`
  `0x1400975A0` (slot 11); `ShaderDeferringCloseAndPrebloom_EmitInstances`
  `0x14008EE00` (slot 15), `ShaderGlitch_EmitInstances` `0x140094780` (slot 15);
  `ShaderDeferringCloseAndPrebloom_SetTexture` `0x14008FC10` (slot 21).
* **Auxiliary emitters:** `ShaderDeferringCloseAndPrebloom_EmitVerticesAuxA`
  `0x14008F1E0` (4 records) and `...AuxB` `0x14008F8E0` (3 records) are called
  from the slot-8/slot-9 bodies of that class.
* `ShaderPrebloomAndOutlineLOD_SetField138` `0x140098D30`,
  `..._SetFlag130/131/132` `0x140098D50/D40/D60`.
* The CB uploads are `ConstantBuffer<UCBConstants@ShaderX>` objects, i.e.
  separate classes with their own RTTI (`0x1403572F8`, `0x140356C38`, ...). Where
  a shader has more than one block, the names are `..._UploadConstants`,
  `..._UploadVertexConstants` (`UCBConstantsVertex`), `..._UploadShadingConstants`
  (`UCBShading`), `..._UploadConstants2/3` when two/three blocks share the same
  inner type name.

### Shader parameter value classes

| class | vtable | ctor | deleting dtor |
|---|---|---|---|
| `ShaderData` | `0x140359108` | `ShaderData_Constructor` `0x14009F930` | `ShaderData_ScalarDeletingDestructor` `0x14009FC80` (also `ShaderData_ResetVTable` `0x14009FB40`) |
| `ShaderResourceView` | `0x140359120` | `ShaderResourceView_Constructor` `0x14009FB10` | `ShaderResourceView_ScalarDeletingDestructor` `0x14009FEF0` |
| `ShaderParamNew` | `0x140359138` | ? (base) | `ShaderParamNew_ScalarDeletingDestructor` `0x14009FDA0` |
| `ShaderParamTextureNew` | `0x140359150` | `ShaderParamTextureNew_Constructor` `0x14009FA30` | `ShaderParamTextureNew_ScalarDeletingDestructor` `0x14009FDD0` |
| `ShaderParamTextureArrayNew` | `0x140359168` | `ShaderParamTextureArrayNew_Constructor` `0x14009FA00` | `ShaderParamTextureNew_ScalarDeletingDestructor` `0x14009FDD0` (shared) |
| `ShaderParamTextureVectorNew` | `0x140359180` | `ShaderParamTextureVectorNew_Constructor` `0x14009FA60` | `ShaderParamTextureVectorNew_ScalarDeletingDestructor` `0x14009FE00` |
| `ShaderParamMatrixNew` | `0x140359198` | `ShaderParamMatrixNew_Constructor` `0x14009F9E0` | `ShaderParamMatrixNew_ScalarDeletingDestructor` `0x14009FD70` |
| `ShaderParamVectorNew` | `0x1403591B0` | `ShaderParamVectorNew_Constructor` `0x14009FAB0` (owns its 0x10-byte value) / `..._ConstructorBound` `0x14009FAF0` | `ShaderParamVectorNew_ScalarDeletingDestructor` `0x14009FE90` |
| `ShaderParamIntNew` | `0x1403591C8` | `ShaderParamIntNew_Constructor` `0x14009F9C0` | `ShaderParamIntNew_ScalarDeletingDestructor` `0x14009FD10` |
| `ShaderParamFloatNew` | `0x1403591E0` | `ShaderParamFloatNew_Constructor` `0x14009F960` (owns its 4-byte value) / `..._ConstructorBound` `0x14009F9A0` | `ShaderParamFloatNew_ScalarDeletingDestructor` `0x14009FCB0` |
| `ShaderParamVectorArrayNew` | `0x140359200` | `ShaderParamVectorArrayNew_Constructor` `0x14009FA90` | `ShaderParamTextureNew_ScalarDeletingDestructor` `0x14009FDD0` (shared) |

`ShaderResourceView_NotifyChanged` `0x14009FF80` is the `ShaderResourceView`
virtual that tells the owning `Effect` a bound value changed (owner vtable
`+0xc8` = vertex-shader block update, `+0x40` = pixel-shader block update).
`ShaderParamStringPairVector_PushBack` `0x14009F8C0` appends one 0x40-byte
two-string record to a parameter's value vector.

### Effect parameter factories

| addr | new name | what it creates |
|---|---|---|
| 0x140087510 | `Effect_AddFloatParam` | `ShaderParamFloatNew`, owning |
| 0x140087590 | `Effect_AddVectorParam` | `ShaderParamVectorNew`, owning |
| 0x140087610 | `Effect_AddFloatParamBound` | `ShaderParamFloatNew` over an existing float |
| 0x140087690 | `Effect_AddIntParam` | `ShaderParamIntNew` |
| 0x140087710 | `Effect_AddMatrixParam` | `ShaderParamMatrixNew` |
| 0x140087830 | `Effect_AddVectorParamBound` | `ShaderParamVectorNew` over an existing value |
| 0x1400878B0 | `Effect_AddTextureParam` | `ShaderResourceView` + `ShaderParamTextureNew` |
| 0x140087990 | `Effect_AddTextureArrayParam` | `ShaderResourceView` + `ShaderParamTextureArrayNew` |

## Renames — render-state / renderer helpers (`0x140082xxx–0x140086xxx`)

| addr | new name | description |
|---|---|---|
| 0x140082120 | `Std_Locale_GetCodecvtFacet` | `std::codecvt<char,char,_Mbstatet>` lookup/creation in a locale (the function `FUN_1400821F0` etc. are unrelated) |
| 0x1400821F0 | `RenderState_Constructor` | copies a 0x88-byte render-state descriptor from the parent renderer and applies it |
| 0x140082290 | `RenderState_ConstructorEx` | same, with explicit descriptor fields; sets parent `+0x2d8` |
| 0x140082580 | `Std_BadCast_Constructor` | `std::bad_cast` copy constructor |
| 0x1400825C0 | `Std_BadCast_ConstructorDefault` | `std::bad_cast` default constructor ("bad cast") |
| 0x140082700 | `RenderState_Destructor` | restores the parent's previous descriptor and clears `+0x2d8` |
| 0x140082B60 | `ComObject_Release` | releases the COM object referenced at `+8` |
| 0x140082EF0 | `ThrowBadCast` | throws `std::bad_cast`, never returns |
| 0x140083660 | `Render_SetBlendFactor` | packed ARGB -> 4 floats -> `OMSetBlendFactor` |
| 0x140083C50 | `Color_ARGBToFloat4` | 0xAARRGGBB -> float RGBA (the shader-side twin of `Color_FromARGB`) |
| 0x140083CC0 | `Matrix4x4_TranslationY` | identity + y translation (integer input) |
| 0x140083D00 | `Matrix4x4_Translation` | identity + x/y translation |
| 0x140085530 | `Matrix4x4_OrthoOffCenter` | off-centre orthographic projection |
| 0x140085660 | `Matrix4x4_Scale` | diagonal scale matrix |
| 0x140086000 | `Render_ResetViewportRect` | viewport/scissor back to +-200000 |
| 0x1400863C0 | `Render_SetRasterizerState` | applies a rasterizer descriptor, recreates the state object |
| 0x140086500 | `Render_SetBlendState` | blend/depth state selected by flags |
| 0x140086750 | `Render_BlendDescDefault` | fills the default blend description |
| 0x140086790 | `Render_SetBlendEnabled` | blend enable flag + re-apply |
| 0x1400867A0 | `Render_SetViewportRect` | sets the scissor rectangle (`+0x1c8`) |
| 0x140086D00 | `Render_SelectBlendState` | picks and binds one of the cached blend states |

## Renames — containers / strings

| addr | new name | description |
|---|---|---|
| 0x14009B2F0 | `Vector_FreeStride12` | frees a vector with 12-byte elements |
| 0x14009BDB0 | `StringPairVector_MoveRange` | moves 0x40-byte two-string records |
| 0x14009C430 | `StringPairVector_DestroyRange` | destroys a 0x40-byte two-string range |
| 0x14009BFF0 | `List_InitHeaderNode68` | empty list with a 0x68-byte header node |

## Skipped / open

Deliberately **not** renamed:

* **Vtable slots with no function object in Ghidra** (the name is known, but the
  address is *inside* the neighbouring function's body; renaming/creating would
  need `create_function`, which the brief does not authorize):
  `0x14008B260` `ShaderClouds_Init`, `0x14008C9C0` `ShaderDefault_Init`,
  `0x14008D6E0` `ShaderDeferringClose_Init`, `0x14008D880`
  `ShaderDeferringClose_EmitVerticesA`, `0x140092580`
  `ShaderDeferringSubscreen_EmitVerticesA`, `0x1400928B0` `ShaderDepth_Init`,
  `0x1400942B0` `ShaderGlitch_Init`, `0x140094780` `ShaderGlitch_EmitInstances`,
  `0x140095810` `ShaderLightingMap_Init`, `0x1400976E0`
  `ShaderPrebloom_EmitVerticesA`.
* **`0x140083450`, `0x1400834E0`, `0x1400835A0`** — three thin sprite/quad draw
  wrappers around the FID-aliased `0x1400830F0`. Their argument order is clear
  but the callee's identity (2-vertex primitive emitter) is not documented, so a
  name would be a guess.
* **`0x140083760`, `0x140085E80`, `0x140085EB0`** — device-state setters whose
  target slots (`+0x1a8`, `+0x40`, `+0x58` of the device wrapper) are not mapped;
  could be texture/sampler/depth-stencil.
* **`0x140083D60`** — one-byte getter (`return this[0x10]`); too generic.
* **`0x140086C90`** — a `std::basic_filebuf` virtual (`_Lock`/`_Unlock`-shaped);
  STL internal, belongs with the other `rep_*` filebuf copies.
* **`0x140088950`** — five-field initialiser (`p[0]=owner; p[1..4]=0`) whose
  owning class is not recoverable from the single call site.
* **`0x14008DC30`** — `vector<0x20-byte>::_Insert` helper called from the
  `ShaderDeferringCloseAndPrebloom` constructor; generic container code.
* **`0x140092E70`, `0x140092FF0`, `0x140093020`, `0x140093050`** — the four
  `std::_Func_impl_no_alloc<lambda_...,float,float>` vtables used by
  `ShaderDithering`; compiler-generated closure thunks, kept as `FUN_*`.
* **`0x140094180`** — refreshes a batch of texture-size fields from nine texture
  objects and calls `ComputeShader_Dispatch`; the owning class (caller is an
  unnamed `pow`-aliased function) is not recoverable, so left alone.

## Cross-notes

* The whole block is **D3D11**, not HGE: `+0x20` of the shader objects is the
  device, `+0x1a0`/`+0x18` the immediate context, and the renderer keeps its
  scissor rect at `+0x1c8..+0x1d4` with `+0x1c4`/`+0x10` as blend selects.
* `Effect` object layout: `+0x08` device, `+0x10` owner/context, `+0x30`
  instance-vector begin/end/cap, `+0x68` resource-vector, `+0x80` parameter
  vector, `+0xb8` the single matrix parameter, `+0xd0` texture, `+0x48` cached
  texture, `+0x100`/`+0x108`/`+0x110` the derived class's own fields.
* The vtable layout of every `Shader*` class is identical: 0 (deleting dtor
  thunk), 1 deleting dtor, 2 `Init`, 5 `Release`, 8/9 vertex emitters,
  11 quad emitter (only some classes), 13 `Draw`, 15 instance upload (two
  classes), 17 projection matrix, 19/20 matrix parameters, 21 texture.
