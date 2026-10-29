# Unnamed-function sweep — batch 5 agent 1

Range: `0x140330000–0x140336FFF` on `Highfleet.exe.unpacked.exe` v1.163
(project `HighfleetServer`). 191 function objects in range at the start of the pass
(no new ones from batch 4's count except the two batch-4 creations).

Counts: **1 renamed, 5 created + plated, 34 names still `FUN_*`/`rep_*`.** Of those 34,
18 are `/EH` cleanup funclets or their `rep_*` aliases in `0x140336730–0x140336f80`
(catalogued below), 9 are `__scrt_*` outline stubs used only by the `_set_app_type`
worker, 7 are `rep_*`/runtime replicas, and `FUN_140334e00` is the unnamed `sincos`
helper. Three further funclet `.pdata` regions have no function object at all.

The range is the tail of the real Box2D contact/edge/shape code (it starts at
`b2RopeJoint_SolvePositionConstraints` and ends at `b2CollideEdgeAndPolygon`), then the
CRT/exception-handler block, then the `/EH` funclet run from `0x140336730` onward.
Every Box2D function object in the range was already named and correct; this pass
verified them and concentrated on the CRT tail.

## Vtable slot check

Data-scan of every 8-aligned qword in `.rdata` / `.data`
(`0x140350000–0x1403C6400`) for pointers into the range:

* All b2 contact `Evaluate` slots and the b2EdgeShape vtable slots point at function
  objects (batch 4's work). Vtables involved: `0x140378e40–0x140378e90` (seven
  contacts), `0x140378ea0` (`b2EdgeShape`).
* The only pointers into the range without a function object are the import-thunk
  island (`0x1403365ac` = `memmove` thunk, plus `0x14033404c/52/5e/70/76/7c/82/88/8e`,
  which are the std::streambuf import thunks `xsgetn`, `showmanyc`, `_Lock`, `_Unlock`,
  `imbue`, `setbuf`, `sync`, `uflow`), the CFG dispatch thunk `0x140336710`, and the
  four CRT objects below. None is a class vtable slot; nothing was created from
  "vtable-looking" evidence alone.
* `0x140336710` = `JMP qword ptr [0x1403519c8]` i.e. the CFG dispatch stub
  (`[0x1403519c8]` → `_guard_dispatch_icall` 0x1403366f0). It appears twice at
  `0x1403519d0/d8` because those are the load-config `GuardCFDispatchFunctionPointer`
  fields, **not** vtable slots. Not created.
* `0x1403519e8` (a C++ initialiser entry) points at `0x140334c38` — see "left
  unnamed" below. `.pdata`-only references were treated as exception metadata, not as
  vtable evidence (confirms @agent6's blackboard note).
* Hand-off still open: `0x1403198c0` (`b2EdgeShape` vtable slot [2] GetChildCount,
  `mov eax,1; ret`) still has **no function object** and is out of this range. Proposed
  name in batch 4: `b2Shape_GetChildCountOne` (ICF-shared by all 1-child shapes).

## Box2D functions verified in range (no renames needed)

| addr | name | verification |
|---|---|---|
| 0x140330460 | `b2RopeJoint_SolvePositionConstraints` | recomputes both world anchors, clamps separation to `maxLength` at joint+0x94, applies the cached mass, returns residual test. Uses `FUN_140334e00` (below) to get the sin/cos of each body angle instead of calling `sinf`/`cosf`. |
| 0x140330780 | `b2RopeJoint_SolveVelocityConstraints` | C = length − maxLength at +0x94/+0x90, predictive bias `inv_dt*C` when slack, accumulated impulse clamp, applies to both bodies. |
| 0x140330cc0 | `b2EdgeShape_DeletingDtor` | writes `b2Shape` vtable 0x140352998, frees 0x38 if flag bit 0. |
| 0x140330cf0 / 0x140330e10 | `b2ChainAndCircleContact_Create` / `b2ChainAndPolygonContact_Create` | alloc 200, `b2Contact_Construct`, install chain contact vtable. |
| 0x140330d70 / 0x140330e90 | `b2ChainAndCircleContact_Update` / `b2ChainAndPolygonContact_Update` | build a temporary `b2EdgeShape` (vtable `b2EdgeShape_DeletingDtor_140378ea0`, type 1, radius 0.01) via `b2ChainShape_GetChildEdge` at the cached child index (contact+0x70), then `b2CollideEdgeAndCircle` / `b2CollideEdgeAndPolygon`. These are the **Evaluate** virtual (vtable 0x140378e90 / 0x140378ed8), as batch 4 agent 1 flagged; names left as they were (already named). |
| 0x140333af0 | `b2ChainShape_GetChildEdge` | confirmed; chain layout vertices +0x10, count +0x18, prevVertex +0x1c, nextVertex +0x24, hasPrev +0x2c, hasNext +0x2d. |
| 0x140333a90 | `b2CollideEdgeAndPolygon` | 0x100-byte `b2EPCollider` on the stack, `b2EPCollider_Collide`; stock 2.3.1. |

The b2 contact `Evaluate` forwarders, the `b2Collide*` narrowphases and the
`b2EPCollider` helpers keep batch 3/4 names; no body contradicted them.

## Created (5)

All five were posted to the blackboard `Open questions` as `@agent1 -> creation`
before `createFunction`; each has a `.pdata` `RUNTIME_FUNCTION` entry and no function
object. Plates were set with summary / Algorithm / Parameters / Returns.

| addr | name | why it is code | size |
|---|---|---|---|
| 0x140334494 | `__GSHandlerCheck` | vcruntime GS+SEH handler: `__GSHandlerCheckCommon(pExcept,pRN,pContext,pDC)` then returns 1 (`ExceptionContinueSearch`). `.pdata` only, no vtable (reached through the GS cookie handler chain). | 29 |
| 0x140334510 | `__GSHandlerCheck_EH4` | `__GSHandlerCheckCommon`, then tests `pDC->ScopeTable[1] & 0x66`, and if set tail-calls the import `__CxxFrameHandler4` (0x140336594); otherwise returns 1. This is the `/EH` GS variant linked from VCRUNTIME140_1. | 127 |
| 0x14033524c | `__scrt_unhandled_exception_filter` | address taken by `LEA RCX,[0x14033524c]` in 0x14033523c. Body: code 0xE06D7363 && `ExceptionInformation[0]==4` && magic in {0x19930520,0x19930521,0x19930522} → stores the record in `__current_exception` (0x1403365d0) and `__current_exception_context` (0x1403365d6), then `terminate()`; else returns 0. Stock MSVC `__scrt_unhandled_exception_filter`. | 91 |
| 0x14033469c | `__crt_thread_safe_statics_cleanup` | the `atexit` target registered by 0x1403345cc (that function creates critical section `0x148076c28` with spin 4000, resolves `SleepConditionVariableCS`/`WakeAllConditionVariable`, falls back to `CreateEventW` into `0x148076c20`, then `__scrt_initialize_onexit_tables(0)` + `atexit(this)`). Body deletes exactly that critical section and closes that event. | 40 |
| 0x140335d60 | `__sse41_sinf4` | SSE4.1 4-lane sin kernel (`BLENDVPS`, `PINSRD`), shares `__common_ssin_cout_rare` 0x1403364e0 with `__sse2_sinf4` 0x140335420, and is the branch taken by the scalar `sinf` entry 0x140334de0 when `__isa_available` (`0x1403c2e50`) `>= 2` (SSE4.1). Name is the descriptive family name; the original libm symbol string is not in the program. | 1905 |

`__sse41_sinf4` is only reachable through the dispatcher at 0x140334de0
(`cmp __isa_available,2; jge 0x140335d60; jmp __sse2_sinf4`); the dispatch happens at
runtime, so it has no static code xref — the `.pdata` entry plus the branch is the
proof.

## Renamed (1)

| addr | old | new | reason |
|---|---|---|---|
| 0x14033523c | `rep_14030a29c_KERNEL32.DLL::SetUnhandledExceptionFilter` | `__scrt_set_unhandled_exception_filter` | §4 provably-wrong `rep_`: the embedded target `0x14030a29c` is **mid-instruction inside another function**, and the 14-byte body is not an import thunk. It is `LEA RCX,[__scrt_unhandled_exception_filter]; JMP qword ptr [SetUnhandledExceptionFilter IAT]`, i.e. the CRT helper that installs the filter. |

## Runtime/CRT inventory of the range (context for the names above)

The b2 code ends at `0x140333f90`; `0x140333f93–0x1403366ff` is the import-thunk
island (already named by waves 1–4, not touched). Around it:

| addr | name | note |
|---|---|---|
| 0x140334008 | `_Facet_Register` | already named. |
| 0x140334094 / 0x140334104 / 0x140334174 / 0x1403341e0 | `New`, `eh_vector_constructor_iterator`, `eh_vector_destructor_iterator`, `__ArrayUnwind` | already named. |
| 0x140334244…0x14033447a | `__scrt_*` / `_onexit` / `atexit` | batch 4 names, confirmed. |
| 0x1403344b4 | `__GSHandlerCheckCommon` | called by both GS handlers created here. |
| 0x1403345cc | `InitializeCriticalSectionAndSpinCount` (existing name) | **misleading existing name**: the 208-byte body is the UCRT thread-safe-statics initialiser (crit section + dynamic `SleepConditionVariableCS`/`WakeAllConditionVariable` + `CreateEventW` fallback + `__scrt_initialize_onexit_tables` + `atexit(__crt_thread_safe_statics_cleanup)`). Not renamed (rule: only `FUN_*`/`rep_*`), but the name should be re-pointed at `__crt_initialize_thread_safe_statics` if the parent allows. |
| 0x1403346f4 / 0x140334754 / 0x1403347bc / 0x140334800 | `_Init_thread_footer/header/notify/wait` | already named; confirms the thread-safe-statics block. |
| 0x140334880–0x140334b6d | `_alloca_probe`, `__raise_securityfailure`, `__report_gsfailure`, `__report_rangecheckfailure`, `__report_securityfailure`, `capture_current_context`, `capture_previous_context` | already named. |
| 0x140334b70 | `rep_…_set_app_type` | body is the CRT `_set_app_type` worker; leaves as-is. It calls 0x14033503c (returns 1 → `_configure_narrow_argv`), 0x140335354 (returns `_O_TEXT` 0x4000 → `_set_fmode`), 0x140335388 (`DAT_1403c2e68==0`), 0x1403353e0 (atexit callback), 0x14033536c. |
| 0x1403353e0 | unnamed (atexit callback) | iterates a function-pointer array `0x140381bc0…0x140381bc0` (start == end in this build) calling each through `_guard_dispatch_icall`. Effectively a no-op in 1.163; no function object, left unnamed. |
| 0x140335420 | `__sse2_sinf4@@16` | the SSE2 branch of `sinf`. |
| 0x140334de0 | `rep_…___sse2_sinf4@@16` | actually the **scalar `sinf` entry**: `cmp __isa_available,2; jge __sse41_sinf4; jmp __sse2_sinf4`. Already named via the libm symbol; not renamed (would need `sinf`, but the current name is a real libm symbol for the merged target). |
| 0x140334e00 | `FUN_140334e00` (left unnamed) | scalar **sincos** helper: `|x| < 2^-13` → returns packed `{x, 1 − x²/2}`; otherwise packs `{x, |x|+π/2}` and tail-jumps into the sin kernel, so lane 0 = `sinf(x)`, lane 1 = `cosf(x)`. Used by `b2RopeJoint_SolvePositionConstraints` (twice) to build the two body rotations. This is the `sincosf`-style helper batch 4 flagged as "not b2Rot::Set" — it is AMD-libm-style, not b2. Left unnamed because no symbol string survives. Name if desired: `__sincosf`. |
| 0x140334e43 | `rep_wrap_0_rep_…_sse2_sinf4@@16` | scalar `cosf` entry: `SHUFPS; ADDPS {0,π/2,0,π/2}; JMP` the same kernel → `sin(x+π/2)`. Left as-is. |
| 0x140334e50 / 0x140334e70 | `StdBadAlloc_Ctor`, `badAllocationException` | batch 4. |
| 0x140334e98 | `__isa_available_init` | sets `__isa_available` (`0x1403c2e50`), which is the global the sin/cos dispatcher tests. |
| 0x14033503c / 0x140335050 / 0x140335354 / 0x14033536c / 0x140335388 / 0x140335394 / 0x14033539c | `FUN_*` (left unnamed) | 6–27-byte `__scrt_*` outline stubs used only by the `_set_app_type` worker: `mov eax,1; ret`; zero `DAT_1480771ec`; `mov eax,0x4000; ret` (`_O_TEXT` default fmode); set flag bits in two scrt globals; `(DAT_1403c2e68==0)`; return `&DAT_148077208`; return `&DAT_148077200`. Names not provable → recorded, not named. |

## Left unnamed on purpose

### 1. `/EH` cleanup funclets `0x140336730–0x140336f80`

Same shape as batch 4's census: `(void*, Frame*)`, destroy a member of the enclosing
frame, then usually `_CxxThrowException(0,0)`; no class recoverable from the body.
Catalogue by destroying callee + frame offset (all offsets into the frame, hex):

| addr | destroying callee(s) | frame off | object |
|---|---|---|---|
| 0x140336730 | `Link_DestroyRange` + `deallocate` | a0/a8, 30; 40/38/b8 | link/vector pair |
| 0x140336850 | `DeleteArray32` | 60/20/68 | array |
| 0x140336880 | `deallocate` | 60/78/68 | array |
| 0x1403368b0 | `DeleteArray32` | 50/68/58 | array |
| 0x1403368e0 | `DeleteArray16` | 70/20/78 | array |
| 0x140336b00 | `free` | 48 | pointer |
| 0x140336b20 | `free` | 48 | pointer (clone of b00) |
| 0x140336c40 | `basic_ios<char>::setstate(4,true)` | 60 | iostream state |
| 0x140336c80 (`rep_…_CxxThrowException`) | `Array_DestroyRange24` + `deallocate` | 70/88/28; 70/80/78 | array |
| 0x140336cc0 *(no function object)* | `deallocate` | 80/88 (+30) | array |
| 0x140336cf0 *(no function object)* | `DeleteArrayStride16` | 70/78/20 | array |
| 0x140336d20 (`rep_…_CxxThrowException`) | `EhCleanup_InvalidParameterWrapper` + `DeleteArray56` | d0/40/50; d0/58/48 | array pair |
| 0x140336d60 *(no function object)* | `deallocate` | 60/68/78 | array |
| 0x140336d90 | `deallocate` | 50/68/58 | array |
| 0x140336dc0 | `DeleteArray16` | 60/78/68 | array |
| 0x140336df0 (`rep_…_CxxThrowException`) | `EhCleanup_FreeWrapper` + `DeleteArray32` | 70/78/20; 70/28/88 | array pair |
| 0x140336e30 | `EhCleanup_IdentityWrapper` + `deallocate` | 80; 38/88 | array |
| 0x140336e70 | store `frame+0x88` → `*frame+0x98`, throw | 88/98 | pointer store |
| 0x140336ea0 (`rep_…_CxxThrowException`) | 2× `memmove` + store | 80/88/38/98/28 | vector insert/erase |
| 0x140336f00 (`rep_…_CxxThrowException`) | `memmove` + store | 80/38/98/88/28 | vector insert/erase |
| 0x140336f50 | `EhCleanup_IdentityWrapper` + `deallocate` | 50; 68/58 | array |

The three without function objects (0x140336cc0, 0x140336cf0, 0x140336d60) were **not**
created: §3 forbids creating compiler `_eh` funclets. They have `.pdata` entries but no
callers other than the unwinder.

The `rep_*_CxxThrowException` names inside this block are ICF aliases: the embedded
target is the throw thunk, the body is the cleanup funclet. Left as-is (§4: funclets are
noise, and the callee table above is the useful record).

### 2. Runtime objects that stay unnamed

* `0x140334c38` — 24 bytes, first entry of the C initialiser table at `0x1403519e8`:
  `sub rsp,0x28; call __scrt_set_unhandled_exception_filter; call <return-0>;
  mov ecx,eax; add rsp,0x28; jmp _set_new_mode`. So it installs the unhandled-exception
  filter and calls `_set_new_mode(0)` at startup. `.pdata` entry, no other xrefs. The
  exact UCRT symbol is not provable (there is no `__scrt_*` source function with that
  pair in the version I can check), so it is left unnamed rather than guessed.
* `0x1403346c4` — 48 bytes: `EnterCriticalSection(&0x148076c28); *arg = 0;
  LeaveCriticalSection; JMP _Init_thread_notify`. Semantics match vcruntime's
  `_Init_thread_abort`, but it has **no code xref at all** (only `.pdata`), so it is
  either dead or reached indirectly; left unnamed.
* `0x1403340d8` — scalar deleting destructor that stores `PTR_FUN_140378f08` and frees
  0x18 bytes. Batch 4 left it unnamed; the "vtable" at `0x140378f08` is a single
  function pointer followed by a UTF-16 string (`api-ms-win-c…`), so it is an entry in
  a name→pointer table, not a real vtable. Class not provable; skip.
* `0x140334e00` — sincos helper (see inventory): semantics proven, symbol name not.
  Left unnamed; naming proposal `__sincosf` on the blackboard.

## Post-pass verification

All five created function objects have the expected contiguous bodies and no overlap
with their neighbours:

| addr | name | body |
|---|---|---|
| 0x140334494 | `__GSHandlerCheck` | 0x140334494–0x1403344b0 |
| 0x140334510 | `__GSHandlerCheck_EH4` | 0x140334510–0x14033458e |
| 0x14033469c | `__crt_thread_safe_statics_cleanup` | 0x14033469c–0x1403346c3 |
| 0x14033524c | `__scrt_unhandled_exception_filter` | 0x14033524c–0x1403352a5 |
| 0x140335d60 | `__sse41_sinf4` | 0x140335d60–0x1403364d0 |

`InitializeCriticalSectionAndSpinCount` still ends at 0x14033469b and
`__GSHandlerCheckCommon` at 0x14033450e, so neither was truncated by the creations.
`__scrt_set_unhandled_exception_filter` is 0x14033523c–0x140335249.

Final state of the range: 196 function objects (191 + 5 created), 1 renamed, 34 names
still `FUN_*`/`rep_*`: 18 `/EH` funclet/runtime objects in `0x140336730–0x140336f80`,
9 CRT/`__scrt_*` stubs in `0x140334000–0x140335400` and 7 `rep_*`/runtime replicas
(including the `sincos` helper `FUN_140334e00`). The 3 funclet `.pdata` regions with no
function object are additional to that 34.

## Hand-off / open questions

1. `0x1403198c0` (`b2EdgeShape` slot [2], `mov eax,1; ret`) still has no function
   object; out of range for me. `b2Shape_GetChildCountOne` remains the proposal.
2. `0x1403345cc` is named `InitializeCriticalSectionAndSpinCount` but is the UCRT
   thread-safe-statics initialiser; re-pointing it to
   `__crt_initialize_thread_safe_statics` needs a non-`FUN_*` rename waiver.
3. `0x140334de0` / `0x140334e43` / `0x140334e00` are the scalar `sinf` / `cosf` / sincos
   entry trio around the AMD-libm kernels; `__sse41_sinf4` (new) is the SSE4.1 branch.
   If anyone revisits libm naming, this is the cluster.
4. Existing-name caveats (not touched): the two chain contact `_Update` names are the
   `Evaluate` slot (batch 4 already flagged); `b2FindMaxSeparation` 0x140331f70 is the
   locally optimised centre-seed/hill-climb variant, not the stock full scan.
