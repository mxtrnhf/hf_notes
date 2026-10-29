# Ghidra post-sweep Phase 1b — CRT EH glue / `__scrt` stragglers

Program `Highfleet.exe.unpacked.exe` **v1.163**, project `HighfleetServer`.
Scope: the three CRT EH glue thunks (`0x14034b6b8`, `0x14034b743`,
`0x14034b75b`), the seven `__scrt_*` outlines
(`0x14033503c/050/354/36c/388/394/39c`), and any remaining `FUN_*` padding /
compiler glue in `0x140335000–0x14034FFFF` that is **not** a row of
`funclet-ownership-2026-10-29.tsv` and **not** the Phase 1a funclets or
`0x140342380`.

**Result: 3 named + plated, 7 classified as compiler glue, 7 funclets handed
off to Phase 1a (not touched), 0 created.**
No `save_program`, no `create_function`, no tags, no README/STATUS edit, no
commit, no `startTransaction` opened by me (every write went through the
server's own per-call transaction).

| | count |
|---|---|
| named + plated | **3** |
| classified as compiler glue (left unnamed) | **7** |
| funclets documented + handed off (left unnamed) | **7** |

## Table

| address | current name | verdict | proposed / actual name | evidence |
|---|---|---|---|---|
| `0x14034b6b8` | `rep_14031fb7f___ArrayUnwind` | **renamed** | `` `eh_vector_destructor_iterator'_EhCleanup_0x60 `` | `.pdata` handler of C-scope `0x3341a7–0x3341d5` inside `eh_vector_destructor_iterator` `0x140334174`; guarded `__ArrayUnwind` over that function's argument homes |
| `0x14034b743` | `FUN_14034b743` | **renamed** | `CRT_AccessViolationFilter` | filter of C-scope `0x33435f–0x3343e9` in `__scrt_is_nonwritable_in_current_image`; returns `ep->ExceptionRecord->ExceptionCode == 0xC0000005` |
| `0x14034b75b` | `rep_wrap_0_API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL::_seh_filter_exe` | **renamed** | `CRT_SehFilterExeThunk` | filter of the `__try/__except` in `mainCRTStartup`; forwards `(code, ep)` to the imported `_seh_filter_exe`. No byte-identical twin in the image |
| `0x14033503c` | `FUN_14033503c` | glue | `compiler outline of CRT_InitializeProcess` | `MOV EAX,1; RET`; sole caller `0x140334bb9` uses it as the `_crt_argv_unexpanded_arguments` argument of `_configure_narrow_argv` |
| `0x140335050` | `FUN_140335050` | glue | `compiler outline of __scrt_fastfail` | `AND dword [0x1480771ec],0; RET` (ignores ECX); both callers are inside `__scrt_fastfail` (`0x140335086`, `0x14033518c`, `MOV ECX,3`) |
| `0x140335354` | `FUN_140335354` | glue | `compiler outline of CRT_InitializeProcess` | `MOV EAX,0x4000; RET`; `0x140334b80` feeds it to `_set_fmode` (`0x4000` = `_O_TEXT`) |
| `0x14033536c` | `FUN_14033536c` | glue | `compiler outline of CRT_InitializeStdioOptions` | whole body of `CRT_InitializeStdioOptions` `0x140334c28` (that function is only `CALL` + `return 0`); ORs `0x24` into `[0x140397200]` and `0x2` into `CRT_LocalStdioScanfOptions` |
| `0x140335388` | `FUN_140335388` | glue | `compiler outline of CRT_InitializeProcess` | `return *(int*)0x1403c2e68 == 0`; gates `__setusermatherr(0x140055f20)`. The cell is a `.rdata` flag equal to `1` with no code writer, so the branch is dead in this build |
| `0x140335394` | `FUN_140335394` | glue | `compiler outline of mainCRTStartup` (`__dyn_tls_init` callback slot) | `LEA RAX,[0x148077208]; RET`; caller `0x140334ceb` calls `(*cell)(0,2)` after `__scrt_is_nonwritable_in_current_image(cell)` — i.e. `__dyn_tls_init(NULL, DLL_PROCESS_ATTACH)` through the linker-provided slot |
| `0x14033539c` | `FUN_14033539c` | glue | `compiler outline of mainCRTStartup` (thread-local atexit callback slot) | `LEA RAX,[0x148077200]; RET`; caller `0x140334d17` passes `*cell` to `_register_thread_local_exe_atexit_callback` |
| `0x1403368e0` | `FUN_1403368e0` | hand-off | — | EH funclet (`.pdata` `0x3368e0–0x336908`, unwind `0x381e6c`), destroys `+0x70/+0x78/+0x20` via `0x1400099e0`; **no ownership-TSV row** |
| `0x140336c40` | `FUN_140336c40` | hand-off | — | EH funclet (`.pdata` `0x336c40–0x336c7b`), virtual dispose of `+0x60` via `[0x140351360]` flag 1 |
| `0x140336d90` | `FUN_140336d90` | hand-off | — | EH funclet (`.pdata` `0x336d90–0x336db8`), destroys `+0x50/+0x68/+0x58` via `0x140009990` |
| `0x140336dc0` | `FUN_140336dc0` | hand-off | — | EH funclet (`.pdata` `0x336dc0–0x336de8`), destroys `+0x60/+0x78/+0x68` via `0x1400099e0` |
| `0x140336e30` | `FUN_140336e30` | hand-off | — | EH funclet (`.pdata` `0x336e30–0x336e66`), `+0x80`→`0x1400199d0`, then `+0x38/+0x88` via `0x140023990` |
| `0x140336e70` | `FUN_140336e70` | hand-off | — | EH funclet (`.pdata` `0x336e70–0x336e98`), store through `+0x88`→`+0x98` only |
| `0x140336f50` | `FUN_140336f50` | hand-off | — | EH funclet (`.pdata` `0x336f50–0x336f80`), `+0x50`→`0x1400199d0`, then `+0x68/+0x58` via `0x140009990` |

Excluded by assignment: `0x140342380` (Phase 1a, aliased FuncInfo4) and the 40
open funclet rows of the ownership TSV. `0x1403377e0` is a TSV row, not mine.

## 1. The three CRT EH glue thunks (named)

The binary is MSVC **x64**, so "funclet" here means a `.pdata`
RUNTIME_FUNCTION whose unwind info is `0x1403822b8` (chained) or `0x381e6c`,
and whose address also appears in the *scope table* of a parent function's
`.xdata`. Each scope record is four RVAs `{begin, end, handler, jump}`:

* `jump != 0` → `handler` is a **filter** (called with `_EXCEPTION_POINTERS*`,
  returns an EXCEPTION_* disposition) and `jump` is the `__except` body.
* `jump == 0`  → `handler` is a `__finally`-style **termination handler**
  (called with `(ep, establisher frame)`).

All three scope tables are in `.rdata` and are located by the handler RVA
`0x003365ca` in the first dword (which Ghidra does not have a function object
for; it is the `__C_specific_handler`/`__CxxFrameHandler4` entry point).

### 1.1 `0x14034b6b8` → `` `eh_vector_destructor_iterator'_EhCleanup_0x60 ``

Old name `rep_14031fb7f___ArrayUnwind` is **provably wrong**: the replica
target `0x14031fb7f` lies inside the float/geometry routine `0x14031f890`, and
the real `__ArrayUnwind` in this image is `0x1403341e0`.

```
14034b6b8: PUSH RBP ; SUB RSP,0x20 ; MOV RBP,RDX
14034b6c1: CMP byte ptr [RBP+0x20],0 ; JNZ done        ; completion guard
14034b6c7: MOV R9,[RBP+0x78] ; MOV R8,[RBP+0x70]
14034b6cf: MOV RDX,[RBP+0x68] ; MOV RCX,[RBP+0x60]
14034b6d7: CALL 0x1403341e0                            ; __ArrayUnwind
```

Owner proof (not inference from shape):

* `.pdata` `0x14034b6b8–0x14034b6e4`, unwind `0x1403822b8`; the RVA
  `0x0034b6b8` appears in the scope table at `.rdata` `0x1403b9804` as
  `{begin 0x3341a7, end 0x3341d5, handler 0x34b6b8, jump 0}` — a `__finally`
  handler with no `__except` body.
* Both scope addresses lie inside `eh_vector_destructor_iterator`
  `0x140334174–0x1403341de`. The established frame is that function's RSP after
  the prologue (entry RSP − 0x58): `frame+0x60/+0x68/+0x70/+0x78` are exactly
  its argument homes `[RAX+8]/[RAX+0x10]/[RAX+0x18]/[RAX+0x20]` = (end pointer,
  element size, count, destructor), and `frame+0x20` is the byte initialised at
  `[RAX-0x38]` and set to 1 only after the destructor loop finishes. So the
  handler re-destroys the not-yet-destroyed prefix by unwinding backwards from
  `end` — which is `__ArrayUnwind`'s contract (its loop does `p -= size` before
  `dtor(p)`).

The naming mirrors the already-approved twin
`` `eh_vector_constructor_iterator'_EhCleanup_0x50 `` `0x14034b68c`, which has
the identical shape for the constructor iterator. Role is distinct from
`__ArrayUnwind` (that is the callee) — this is the parent-specific EH glue.

Plate:

```
__finally-style EH handler for the temporary array of `eh_vector_destructor_iterator`.

Algorithm:
    If the completion guard byte in the parent frame is clear, destroys the
    elements that the destructor loop has not reached by calling __ArrayUnwind
    with the parent's (end pointer, element size, element count, destructor)
    argument slots. The guard is set once the loop completes normally.

Parameters:
    param_1 - exception record (unused).
    param_2 - establisher frame of `eh_vector_destructor_iterator`.

Returns:
    None.
```

### 1.2 `0x14034b743` → `CRT_AccessViolationFilter`

```
14034b743: PUSH RBP ; MOV RBP,RDX
14034b748: MOV RAX,[RCX]                  ; ep->ExceptionRecord
14034b74b: XOR ECX,ECX
14034b74d: CMP dword ptr [RAX],0xc0000005 ; ExceptionCode == STATUS_ACCESS_VIOLATION
14034b753: SETZ CL ; MOV EAX,ECX ; POP RBP ; RET
```

Parent: scope table `.rdata` `0x1403b9844`
`{begin 0x33435f, end 0x3343e9, handler 0x34b743, jump 0x3343e9}`. Both
addresses lie in `__scrt_is_nonwritable_in_current_image` `0x140334358`, whose
body walks the PE section headers of a caller-supplied address — exactly the
code that needs an AV guard. `jump = 0x3343e9` is that function's
`XOR AL,AL` / epilogue path, i.e. `__except (...) { return 0; }`.

Distinct from the existing `_seh_filter_exe` `0x14033667e` (the import thunk):
this one implements the code test itself and does not call anything.

Plate:

```
Exception filter that accepts only STATUS_ACCESS_VIOLATION.

Algorithm:
    Reads the exception record from the exception-pointers argument and compares
    its exception code with 0xC0000005. Returns EXCEPTION_EXECUTE_HANDLER for an
    access violation and EXCEPTION_CONTINUE_SEARCH otherwise. Used as the
    __except filter of the image-section lookup in
    __scrt_is_nonwritable_in_current_image, whose handler returns 0.

Parameters:
    param_1 - _EXCEPTION_POINTERS* supplied by the unwinder.

Returns:
    1 for STATUS_ACCESS_VIOLATION, 0 for any other code.
```

### 1.3 `0x14034b75b` → `CRT_SehFilterExeThunk`

```
14034b75b: PUSH RBP ; SUB RSP,0x20 ; MOV RBP,RDX
14034b764: MOV RAX,[RCX]        ; ep->ExceptionRecord
14034b767: MOV RDX,RCX          ; arg2 = ep
14034b76a: MOV ECX,[RAX]        ; arg1 = exception code
14034b76c: CALL 0x14033667e     ; _seh_filter_exe (import thunk, JMP [0x140351840])
14034b771: NOP ; ADD RSP,0x20 ; POP RBP ; RET
```

Parent: scope table `.rdata` `0x1403b98c4`, `{count 2}`:
`{0x334c78, 0x334d7c, 0x34b75b, 0x334d7c}` and
`{0x334dab, 0x334dbd, 0x34b75b, 0x334d7c}`. Both ranges are inside
`mainCRTStartup` `0x140334c54` (the vcruntime `__scrt_common_main_seh`), and
the jump target `0x334d7c` is its epilogue (`MOV EAX,EBX; JMP 0x140334d95`).
So this is the compiler-emitted filter for
`__except (_seh_filter_exe(GetExceptionCode(), GetExceptionInformation()))`
around the whole startup body — the codegen is the canonical one:

```
mov rax,[rcx] ; mov rdx,rcx ; mov ecx,[rax] ; call _seh_filter_exe
```

**Twin check (required by the task):** the exact byte string
`40 55 48 83 EC 20 48 8B EA 48 8B 01 48 8B D1 8B 08 E8` occurs **once** in the
whole image (only `0x14034b75b`), and the related AV-filter pattern
`40 55 48 8B EA 48 8B 01 33 C9 81 38 05 00 00 C0 0F 94 C1 8B C1 5D C3` occurs
only at `0x14034b743`; the `__ArrayUnwind` guard pattern occurs only at
`0x14034b68c` and `0x14034b6b8`. There is therefore **no byte-identical twin**
to record, and the old `rep_wrap_0_…::_seh_filter_exe` label (which claims this
*is* `_seh_filter_exe`) was replaced by one that says what it does.

Plate:

```
Startup SEH filter that forwards the exception to _seh_filter_exe.

Algorithm:
    Unpacks the exception-pointers argument into (ExceptionCode,
    ExceptionPointers) and calls the CRT's _seh_filter_exe with them. Used as
    the __except filter of mainCRTStartup's __try around the whole
    initialise/initterm/Main/exit sequence; the handler body is empty.

Parameters:
    param_1 - _EXCEPTION_POINTERS* supplied by the unwinder.

Returns:
    _seh_filter_exe's disposition.
```

## 2. The seven `__scrt_*` outlines (classified, left unnamed)

Re-read from ASM plus the call site in this pass (callers and globals re-checked
against the live program). None is a distinct API: each is either a constant
return, a two-instruction body that is the entire body of its only caller, or a
one-instruction address getter. Naming them would duplicate the caller's plate,
and no canonical MSVC symbol is provable for the two getters, so they stay
`FUN_*` with the behaviour recorded here (§8.1 of the playbook: catalog, don't
rename clones).

* **`0x14033503c`** — `MOV EAX,1; RET`. Sole caller `CRT_InitializeProcess`
  `0x140334bb9`: `_configure_narrow_argv(1)`. The `1` is
  `_crt_argv_unexpanded_arguments`. Constant-argument outline.
* **`0x140335050`** — `AND dword [0x1480771ec],0; RET`, ignores its register
  argument. Callers `0x140335086` and `0x14033518c`, both inside
  `__scrt_fastfail`, both `MOV ECX,3` first; `0x1480771ec` is the fastfail
  state cell (BSS, no other writer). Outlined "clear the fastfail state"
  tail of the fail path.
* **`0x140335354`** — `MOV EAX,0x4000; RET`. Sole code caller
  `CRT_InitializeProcess` `0x140334b80`: `_set_fmode(_O_TEXT)`. Also present as
  a pointer at `.rdata` `0x1480889f0`. Constant-argument outline.
* **`0x14033536c`** — the entire body of `CRT_InitializeStdioOptions`
  `0x140334c28`, which is just `SUB RSP,0x28; CALL 0x14033536c; XOR EAX,EAX;
  RET`. It ORs `0x24` into `[0x140397200]` (via getter `0x140011000`) and `0x2`
  into `CRT_LocalStdioScanfOptions` `0x14011bbc0`. Outlined initialiser body.
* **`0x140335388`** — `return *(int*)0x1403c2e68 == 0`; sole caller
  `CRT_InitializeProcess` `0x140334bce`, gating
  `__setusermatherr(0x140055f20)`. The cell reads 1 in the image and has no code
  writer, so the branch is dead — a link-config flag, not an API.
* **`0x140335394`** — `LEA RAX,[0x148077208]; RET`. Caller `mainCRTStartup`
  `0x140334ceb`: `cell = get(); if (*cell && __scrt_is_nonwritable_in_current_image(cell))
  (*cell)(0,2);` — i.e. it is the address of the linker-provided
  `__dyn_tls_init` callback slot, invoked as `__dyn_tls_init(NULL,
  DLL_PROCESS_ATTACH)`. The slot is BSS; there is no symbol to borrow. This is
  the first pass with the *semantics* of the two cells proven (batch 10 agent 8
  only had "adjacent 8-byte cells"), but the value is still a one-instruction
  address load whose only consumer is the startup plate.
* **`0x14033539c`** — `LEA RAX,[0x148077200]; RET`. Caller `mainCRTStartup`
  `0x140334d17`: `cell = get(); if (*cell && …) _register_thread_local_exe_atexit_callback(*cell);`
  — the thread-local atexit callback slot.

No `__scrt_common_main_seh` / `_initterm` / `_configure_narrow_argv` /
`_set_fmode` *function* is left unnamed in the range: `mainCRTStartup`
(`__scrt_common_main_seh`) is already named and plated, and
`_configure_narrow_argv` `0x14033665a`, `_initterm` `0x140336696`,
`_initterm_e` `0x14033669c`, `_set_fmode` `0x1403366ae` are import thunks with
symbol names. Nothing in the seven is a distinct-control-flow variant of them.

Inventory check for the rest of `0x140335000–0x14034FFFF`: the live `FUN_*` /
`rep_*` set in that range is exactly the 7 outlines + the 3 thunks + the 7
unowned funclets of §3 + `0x140342380` (Phase 1a) + `0x1403377e0` (an
ownership-TSV row). Every other unnamed object there is a TSV funclet row and
therefore Phase 1a's. There is no padding function object in the range.

## 3. Seven unowned EH funclets — documented, handed off (not touched)

`0x1403368e0`, `0x140336c40`, `0x140336d90`, `0x140336dc0`, `0x140336e30`,
`0x140336e70`, `0x140336f50` each has its own `.pdata` RUNTIME_FUNCTION (all
with unwind `0x381e6c`) but **no row in
`funclet-ownership-2026-10-29.tsv`**, so they are neither Phase 1a's TSV work
nor in either of my two explicit scope lists. Their bodies match batch-10 agent
8's table exactly (re-read this pass):

```
MOV [RSP+0x10],RDX ; PUSH RBP ; SUB RSP,0x20 ; MOV RBP,RDX
<destroy frame member(s)> ; XOR EDX,EDX ; XOR ECX,ECX ; CALL 0x14033658e
```

with the destroyed members `+0x70/+0x78/+0x20` (→`0x1400099e0`),
`+0x60` virtual dispose via `[0x140351360]` flag 1, `+0x50/+0x68/+0x58`
(→`0x140009990`), `+0x60/+0x78/+0x68` (→`0x1400099e0`),
`+0x80`→`0x1400199d0` then `+0x38/+0x88` (→`0x140023990`), `+0x88`→`+0x98`
store only, and `+0x50`→`0x1400199d0` then `+0x68/+0x58` (→`0x140009990`).
Their funclet-table RVAs live in the compressed FuncInfo4 blobs at
`.rdata` `0x1403829ab` (8e0), `0x140382d09` (c40), `0x140386048` (d90),
`0x140386004` (dc0), `0x1403861dd` (e30), `0x140386225` (e70),
`0x1403862d4` (f50); those blobs also reference the parent scopes, so the
owner walk is mechanical but is Phase 1a's method. Left unnamed rather than
inventing an `<Owner>_EhCleanup_<member>` name with no owner proof.

Hand-off request posted on the blackboard.

## 4. Method / session notes

* Every identity above was fixed with three independent reads: the function
  body (`disassemble_function`), the `.pdata` RUNTIME_FUNCTION entry, and the
  parent's `.xdata` scope table found by searching the image for the funclet's
  4-byte RVA. The parent is the function whose body contains the scope's
  `begin` address; the handler kind follows from `jump == 0`.
* Plates are the four-line doc style (summary / `Algorithm:` / `Parameters:` /
  `Returns:`); the old names are recorded here, not in the plates.
* Writes: `rename_function_by_address` + `set_plate_comment`, per call, no
  explicit transaction. No `save_program` (the parent saves).
* The Ghidra MCP bridge process exited once during Phase 0's spot-check and
  restarted the GUI. I reopened the project program; it came back at the same
  5,702 functions and the same names (spot-checked `0x140316d00`,
  `0x1401993c0`, `0x1403425c0`), so nothing of mine or of the saved baseline
  was lost. I recorded this on the blackboard for the other Phase 1 agents.
* `0x14031fb7f` (the target of the old `rep_` label on `0x14034b6b8`) is inside
  the unnamed float/geometry routine `0x14031f890` — worth knowing if anyone
  later audits the `rep_*` labels in `0x14031F000–0x140320000`.
