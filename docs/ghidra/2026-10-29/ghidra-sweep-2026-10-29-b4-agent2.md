# Unnamed-function sweep, 2026-10-29 — batch 4, agent 2

Range: `0x140340000–0x140350510` (the dense tail of the image).

Program `Highfleet.exe.unpacked.exe` v1.163. **567 unnamed `FUN_*`** were in
range, plus **110 `rep_*`** duplicates (left untouched, see below) and four
already-named oddities (`dtor$1` 0x14034a550, `zeroOutCertainData`
0x14034d6d0, `CFUN_1401228f0` 0x14034f080, `~_Fac_tidy_reg_t` 0x140350510).

Result: **53 renamed** (all plated), **514 deliberately left** and documented
here as compiler output.

The whole range is **compiler tail**, not game logic and **not Box2D**. Box2D
ends before it: no body in this range calls a `b2*` function, and no `b2`
vtable slot points into it. There is therefore no "remaining Box2D single" to
name here, contrary to what the assignment predicted.

## How the range was surveyed

1. `list_functions` once, then `batch_decompile` over all 567 `FUN_*` in
   batches of 10 (57 calls). Every body was normalised (names, addresses and
   type words stripped) and grouped by exact body text. Result: **118 distinct
   bodies**, i.e. 449 of the 567 functions are exact or near-exact copies.
2. Each distinct body was classified by call shape: `free(frame+n)`,
   `String_Tidy(frame+n)` under a construction-bit guard,
   `_eh_vector_destructor_iterator_`, `~basic_ios`, `deallocate+_CxxThrowException`,
   or — for the `void f(void)` bodies — the global the body destroys.
3. Every global destroyed by a `void f(void)` destructor was then matched
   against batch-4 agent 3's initialiser table
   (`ghidra-sweep-2026-10-29-b4-agent3.md`, "static initialisers"). Same
   address means the initialiser built that object, so the destructor takes the
   same name; that gave 10 exact names without any inference.
4. Names + plates applied in two `run_script_inline` passes (the script refuses
   already-named functions; all rows came back `OK`).

Every function in the range has exactly **one DATA xref, from the table block
`0x14808a000–0x14808bxxx`** (e.g. `0x140344030 <- 14808a6d8`,
`0x14034c1c0 <- 140001580`, which is inside `InitGlobal_SeriaLibraryLink`).
For the `_eh` funclets that block is the unwind / funclet registration table,
so **a funclet's owner can only be recovered by parsing that table**, not by
following calls.

## The two clusters

| span | count | what it is |
|---|---|---|
| `0x140340150–0x14034b390` | 437 | MSVC `_eh` / `/GS` cleanup + handler funclets (`(int, void* frame)` ABI) |
| `0x14034b780–0x140350500` | 130 | `atexit` static-object destructors of namespace-scope globals (`void f(void)`, operates on a fixed global) |

Between them sits CRT scaffolding at 0x14034b6b8
(`rep_14031fb7f___ArrayUnwind`) and 0x14034b75b
(`rep_wrap_0_..._seh_filter_exe`), already named — not touched.

### Cluster A — `_eh` funclets, `0x140340150–0x14034b390`, 437 functions

Grouped by identical body:

| pattern | count | body |
|---|---|---|
| member-string cleanup, guard bit | 250 | `if (*(u32*)(frame+guard) & bit) { clear bit; String_Tidy(frame+str); }` — five families: guard `+0x88`/str `+0x640` (170), guard `+0x70`/str `+0x8a0` (27), `+0x70`/`+0xcc0` (22), `+0x70`/`+0xf60` (16), `+0x88`/`+0xea0` (15). Also 4 copies of `+0x88`→`+0x388` (Link, not string) |
| free one field at `frame+0x38` | 106 | `free(*(void**)(frame+0x38));` |
| free one field, other offsets | 29 | `frame+0x30…0x1a0` (`0x70`, `0x78`, `0x88`, `0x118`, `0x1d8`, …) |
| ctor-failure array cleanup + rethrow | 35 | destroy/release the partial buffer, then `_CxxThrowException(0,0)` |
| `basic_ios` destructor cleanup | 10 | guard bit → `basic_ios::~basic_ios(frame+0xd0…0x150)` |
| `_eh_vector_destructor_iterator_` | 5 | string vectors (`0x28×0x12`, `0x20×0x10`, `0x20×1`), `vector<CHN*>`, `Link` (`0x18×4`) |
| vector-insert rollback + rethrow | 2 | two `memmove`s restore the tail, then `_CxxThrowException` |

The "long run of identical 0x20-byte bodies at 0x140344000..0x140345000" from
the blackboard is exactly **25 funclets at `0x140344030–0x140344350`**, stride
0x20, bodies 0x1c–0x20 bytes, all `free(*(void**)(frame+0x70))` (three of them
`+0x78`). They are copies of the 106-member free-one-field family, which is
spread across the whole span — the run is only the densest part of it.

Named (10 representatives, all plated as such — the plate says how many
siblings share the body):

| addr | name | why this one |
|---|---|---|
| 0x140344030 | `EhCleanup_FreeField70` | anchor of the 25-entry run above |
| 0x140340150 | `EhCleanup_MemberString88` | anchor of the 170-entry family (largest in the image) |
| 0x140341ca0 | `EhCleanup_ArrayThenRethrow` | anchor of the 35-entry ctor-failure family |
| 0x140342490 | `EhCleanup_InsertRollback` | the 2-entry vector-insert rollback |
| 0x140342c60 | `EhCleanup_CHNPointerVector` | only `vector<CHN*>` cleanup |
| 0x140343860 | `EhCleanup_StringVector40x18` | 0x28×0x12 string vector |
| 0x140348140 | `EhCleanup_StringVector32x1` | 0x20×1 string at frame+0x2d68 (≈0x4600-byte frame) |
| 0x140346f80 | `EhCleanup_LinkVector24x4` | 0x18×4 `Link` vector |
| 0x140341b90 | `EhCleanup_IosDestructor` | `basic_ios` dtor family (10) |
| 0x140341960 | `EhCleanup_IosSetState` | the only *handler* (returns 0, sets failbit) |

Left unnamed: the other 427. They are byte-identical copies whose only
difference is the frame offset; naming each would add 427 names that carry no
information the family plate does not. The frame offsets above are enough to
match any of them.

### Cluster B — global static destructors, `0x14034b780–0x140350500`, 130 functions

All are `void f(void)` bodies that destroy a namespace-scope object, called
only from the `atexit` registration block in `0x140001000–0x140004400`. They
are the teardown counterpart of the `InitGlobal_*` initialisers named in wave 1
and batch 4 agent 3, so they follow the same scheme:
**`DtorGlobal_<object>`**. Where the initialiser table names the object, the
destructor reuses that name verbatim (10 cases); the rest are named from the
global symbol the body touches.

Named (43):

| addr | name | object destroyed |
|---|---|---|
| 0x14034b7c0 | `DtorGlobal_LevelListHead` | level list head DAT_1403c6320 (`InitGlobal_LevelListHead`) |
| 0x14034b870 | `DtorGlobal_SpriteUnset` | std::string `sprite_unset` |
| 0x14034baf0 | `DtorGlobal_NewPropertyTree` | std::map `newProperty_` (property registry) |
| 0x14034bb60 | `DtorGlobal_SharedObject` | refcounted singleton at DAT_1403ef0e0 (strong/weak counts, vtable[0]/[1]) |
| 0x14034c1c0 | `DtorGlobal_AmmoLink` | `Link` AMMO_LINK |
| 0x14034c1d0 | `DtorGlobal_ArmorLink` | ARMOR_LINK |
| 0x14034c1e0 | `DtorGlobal_CraftLink` | CRAFT_LINK |
| 0x14034c1f0 | `DtorGlobal_DefenceLink` | DEFENCE_LINK |
| 0x14034c200 | `DtorGlobal_EmergencyLink` | EMERGENCY_LINK |
| 0x14034c210 | `DtorGlobal_EngineLink` | ENGINE_LINK |
| 0x14034c220 | `DtorGlobal_ExpendableLink` | EXPENDABLE_LINK |
| 0x14034c230 | `DtorGlobal_FuelLink` | FUEL_LINK |
| 0x14034c240 | `DtorGlobal_GeneratorLink` | GENERATOR_LINK |
| 0x14034c250 | `DtorGlobal_GunLink` | GUN_LINK |
| 0x14034c260 | `DtorGlobal_HullLink` | HULL_LINK |
| 0x14034c270 | `DtorGlobal_LegLink` | LEG_LINK |
| 0x14034c280 | `DtorGlobal_QuarterLink` | QUARTER_LINK |
| 0x14034c290 | `DtorGlobal_SensorLink` | SENSOR_LINK |
| 0x14034c3c0 | `DtorGlobal_SurvivorStateA` | survivor-state map DAT_1403ef440 (`InitGlobal_SurvivorStateLinkA`) |
| 0x14034c430 | `DtorGlobal_SurvivorStateB` | second survivor-state map DAT_1403ef400 (`InitGlobal_SurvivorStateLinkB`) |
| 0x14034c810 | `DtorGlobal_TrailList` | trail list DAT_1439e5fc8 (`InitGlobal_TrailList`) |
| 0x14034cd40 | `DtorGlobal_BindingMapMode` | std::map `bindingMapmode` + DAT_1439ef1c0 |
| 0x14034cdb0 | `DtorGlobal_BindingOther` | std::map `bindingOther` + DAT_1439e9310 |
| 0x14034cff0 | `DtorGlobal_LinkVector240` | vector of 0xf0-byte `Link`, runs `Link_Destructor` |
| 0x14034d220 | `DtorGlobal_Pi2Cash` | float table `PI__2_Cash` |
| 0x14034d290 | `DtorGlobal_AtanCache` | float table `Atan_Cache` |
| 0x14034d510 | `DtorGlobal_SeriaToLoad` | std::string `SeriaToLoad` |
| 0x14034d8d0 | `DtorGlobal_LostShipList` | lost-ship list DAT_143a13c90 (`InitGlobal_LostShipLink`); nodes are `Captain` records at +0x18 |
| 0x14034daa0 | `DtorGlobal_GraphicsBufferA` | per-row float-pair buffer DAT_143a13ca0 (`InitGlobal_GraphicsBufferA`) |
| 0x14034dbb0 | `DtorGlobal_PlaneLoadouts` | std::map `PLANE_LOADOUTS` |
| 0x14034dc70 | `DtorGlobal_CaptainVector` | vector of 0x58-byte `Captain` slots |
| 0x14034de60 | `DtorGlobal_EscadraNameList` | 0x20-strided `ESCADRA_NAME_LIST` |
| 0x14034dee0 | `DtorGlobal_EscadraNameList2` | `ESCADRA_NAME_LIST_2` |
| 0x14034df60 | `DtorGlobal_CallsignList` | `CALLSIGN_LIST` |
| 0x14034dfe0 | `DtorGlobal_EscadraNameList3` | `ESCADRA_NAME_LIST_3` |
| 0x14034e380 | `DtorGlobal_AmmoList` | 0x188-byte `AMMO_LIST`, `Ammo_DestroyRecord` |
| 0x14034eaa0 | `DtorGlobal_GraphicsBufferB` | second float-pair buffer DAT_143a13ed8 (`InitGlobal_GraphicsBufferB`) |
| 0x14034ee20 | `DtorGlobal_StatList` | `StatListBase` (8-byte elements) |
| 0x14034ee90 | `DtorGlobal_PhysicTaskLink` | physic-task list DAT_143a33c48 (`InitGlobal_PhysicTaskLink`) |
| 0x14034ef60 | `DtorGlobal_CreatureDllAiVector` | `creatureDLL_AI_StdVec_` |
| 0x14034f540 | `DtorGlobal_BattleStarList` | battle-star list DAT_147fc7500 (`InitGlobal_BattleStarList`) |
| 0x14034f710 | `DtorGlobal_AiTargetLink` | AI target map DAT_147fc7550 (`InitGlobal_AiTargetLink`) |
| 0x14034fd50 | `DtorGlobal_ChnVectorPool` | 100-entry `vector<CHN*>` pool DAT_14801dd00 (`InitGlobal_ChnVectorPool`) |

Left unnamed: the other **87**. Their globals have no symbol — only a
`DAT_<addr>` or a `PTR_LinkVFTABLE_<addr>` label — and no initialiser table
entry, so a name would have to embed the address
(`DtorGlobal_String_1403c13b0`), which adds nothing over the function address
already shown. They are fully characterised here by the shape of the
destruction and the global touched:

```
string  (guard 0xf<size, free via CONCAT71, reset capacity 0xf):
    bf60 ca60 cb60 cc60 d320 d430 d4a0 d800 d9a0 e150 e730 f8a0   (12)
vec8    (ptr/size/cap at +0/+8/+0x10, 8-byte elements):
    b8e0 b950 b9c0 bbb0 c610 c890 eef0 f010 f1e0 fbd0 fcc0 350480   (12)
vec12   (element count / 0xc):
    cad0 cbd0 cf60 fe50                                             (4)
vec16   (element count / 0x10):  bc90 350260                        (2)
vec4    (element count / 4):     350030                              (1)
vec32   (free range via rep_140055d80, 0x20 stride):
    c130 d650 e4f0 e570 e5f0                                        (5)
list    (singly linked, 2-word nodes, free(head) last):
    e0f0 e680 eab0 f3f0 f460 f4d0                                   (6)
        e0f0/f3f0/f460/f4d0/eab0 also freeLinkMemory_ the node payload
tree    (RbTree_DestroySubtree + free header):  cea0                (1)
link    (freeLinkMemory_ on one/two globals):
    b850 c4a0 c4c0 c500 ce20 ce30 ce60 ce70 ce80 ce90
    de50 e2c0 e320 e460 e470 e480 e490 fd30 fd40                    (19)
object  (single object dtor reached through a tail-call thunk, no size info):
    b780 c2a0 c2b0 c4e0 c4f0 c580 c590 c870 c880 cf20 d940 d950
    d960 d970 d980 e280 e450 e6e0 efe0 f9a0 f9b0 fbc0 fe40
    3504f0 350500                                                   (25)
    special cases inside this group:
      b780/cf20  call a helper with (hdr,hdr,hdr->[8]) then free - tree-shaped
                 (b780's global 1403c6330 sits next to the level list head
                 1403c6320 and is probably its twin, but that is inference)
      c4e0/c4f0/c580/c590  single-object dtor through the Escadra thunk
      3504f0/500 `PTR_PTR_1403c2e10/18 = &PTR_FUN_140369200/18` - these are not
                 destructors at all, they *assign* a function-table pointer to
                 a global; role not recoverable, left unnamed on purpose
```

Notable in cluster B: the destructor of `AMMO_LINK` is registered by
`InitGlobal_SeriaLibraryLink`, i.e. one initialiser registers the destructors
of every static in its translation unit, so the init→dtor link is a TU link,
not an object link. That is why the mapping above was done by *global address*,
not by caller.

## `rep_*` in range (110, untouched)

They keep the `rep_` prefix because each already carries the name of its
target. Sample: `rep_14031b820_VCRUNTIME140.DLL::_CxxThrowException`,
`rep_140320710_..._invalid_parameter_noinfo_noreturn`,
`rep_140322ac0_..._invalid_parameter_noinfo_noreturn`,
`rep_14031fb7f___ArrayUnwind`, `rep_wrap_0_..._memmove`. Renaming them would
duplicate existing names, which the blackboard forbids.

## Deliberately left — summary

| what | count | reason |
|---|---|---|
| `_eh` funclet copies without a named representative | 427 | compiler output, byte-identical within family, only the frame offset differs |
| anonymous global static destructors | 87 | object has no symbol and no initialiser-table entry; an address-encoded name adds nothing over the function address |
| `rep_*` duplicates | 110 | already named after their target |
| `dtor$1`, `zeroOutCertainData`, `CFUN_1401228f0`, `~_Fac_tidy_reg_t` | 4 | already named, not mine to touch |

Ownership of the 437 funclets is still unknown and is the only real open
question in this range: it needs the `0x14808a000` unwind table parsed, not a
decompiler pass.
