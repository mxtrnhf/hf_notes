# Part D — in-memory data tables and safe re-run of loaders (Highfleet 1.163)

Status: final. Written incrementally; the load-bearing claims were re-read at the end
("Checked twice"), and one of them was corrected there.
Program: `Highfleet.exe.unpacked.exe v1.163`, image base 0x140000000, read-only.
Tags: `[code]` = read in this session at the cited address (quote given); `[notes]` = repo note,
not checked here; `[guess]` = inference, with what would confirm it; `[game]` = behaviour seen in
an earlier game run and relayed from the notes (not re-verified here).

Scope given by TASK.md: **in-memory data tables** and **safe re-run of loaders** — i.e. what a
"re-read the game's own data files while it runs" feature would have to touch, and whether the
loader functions can be called a second time. Static analysis only; no game was run.

Budget: TASK.md overrides the generic DS_RULES budget ("no tool-call cap", ~500 lines report).
The *methodology* rules of DS_RULES are followed (verbatim formulas/lines, condition polarity,
honesty tags, "Checked twice").

---

## 0. Verdicts (summary)

| Idea | Verdict | One-line reason |
|---|---|---|
| **Mutate part stats in place** (OL.seria values, while running) | **feasible** | stats records are heap objects reached through a global pointer vector; consumers read them at use time (`Part_Tick` re-reads reload time/magazine/fuel/crew every tick); ship totals are cached and need `CalculateStats` §1.6 |
| **Re-run the OL.seria loader** (full table rebuild) | **feasible with caveats** | a load empties the vector first (`ISerializable::Deserialize` calls `VProperty::Clear`), then refills it in file order; live `Body`s hold *indices* (+0x188) resolved at load time, so file order must stay stable, a parse error leaves the table empty, and each reload leaks the old records (code 0x803 is not freed by `Clear`) |
| **Re-run parts.seria / body prototypes** | **feasible with caveats** | the engine itself re-reads it on every entry to the constructor/editor screen (`loadSeriaForLibraries_` `0x1400d09a0`) into a fresh `Node`; the campaign copy (`ALL_PARTS` `0x143a139f0`, loaded by `PreLoadLibraries_` `0x140233710` at `initGame`) is *not* re-read and its old tree is leaked on a repeat run |
| **Re-run the language pack** | **feasible** | `LoadDialogue` `0x1402253a0` starts by freeing the whole old string table (`0x140191b90` on `0x143a1c3a0`) and every lookup copies the string out |
| **Re-run `.res` resources / atlases** | **not feasible without engine surgery** | `Init_HGE` `0x1401ad080` creates the HGE instance, parses `Media/media.res`, loads all atlases in parallel and then caches font/atlas handles in ~28 globals; HGE rejects a name that is already defined |
| **Re-run a level seria (re-enter a level)** | **feasible with caveats** (already supported by the engine) | `APP::reload_sg` `0x140240b90` = `LoadSeriaFile(LevelSingleton, "Data/Levels/<x>")` + `Level::Load()`, triggered from the frame task `SomethingPreTask` `0x140286e40` via the `SeriaToLoad` queue; state loss is the caveat |
| **Hot-edit the *file* on disk and expect the game to read it** | **not feasible for the files already parsed at startup** | `OL.seria` is read once at startup and then written back at quit; the language pack is read once; `parts.seria` is re-read only when entering the editor/constructor (into a different global), not for the campaign; the only general re-read path is the level reload queue |
| **Mod JSON config re-read** | out of my part (ds4-modside) | but see §6: the *pattern* "parse JSON → write the affected fields of the existing record" is exactly what my findings support |

The single most important discovery for the user's goal: **the game writes `Libraries/OL.seria`
back out from memory when it exits** (`APP::exit_game` `0x140211e10` → `SerializeToFile`
`0x14024e3e0`, and the same in `BuildQuitMenu`). Any in-memory change to the stats table therefore
becomes a *permanent file change* at quit, whether the mod wants that or not. Design around it
(keep a pristine copy, restore before exit, or accept it and version the file).

---

## 1. The stats table (`Libraries/OL.seria`) — the main data table

### 1.1 Where it lives

| What | Address | Evidence |
|---|---|---|
| `StatListBase` (vector begin, `Stats**`) | `0x143a33bf0` | `[code]` `GetStats` `0x140281e00`: `MOV RDX,qword ptr [0x143a33bf0]` |
| `StatListMax` (vector end) | `0x143a33bf8` | `[code]` same, `MOV RCX,qword ptr [0x143a33bf8]` |
| vector capacity | `0x143a33c00` | `[code]` `FUN_14034ee20` `0x14034ee20`: `DAT_143a33c00 - StatListBase` in the free path |
| name → index map (MSVC `std::map` root) | `0x143a33c08` | `[code]` `GetPartIndex` `0x140281cc0` walks it, `compareEscadraString` on key at node+0x20, value at node+0x40 (int) |
| `ObjectsLibrary` singleton pointer | `0x143a1c428` | `[code]` ctor `0x140281538`: `MOV qword ptr [0x143a1c428],RDI`; also `ObjectsLibrarySingleton` symbol |
| record class code / size | `0x803` (2051) / `0x188` | `[code]` factory `DynNewSerializable` `0x1402024e0`: `param_1 == 0x803` → `New(0x188)` → `initStats2` `0x140281660` |
| number of records in the shipped file | **176** | `[file]` `grep -c '^m_stats=' ~/Downloads/OL.seria` = 176, same as `m_oid=`; each line is `m_stats=2051` followed by a `{ m_classname=Stats ... }` block (2051 is the class code, not a count — `formats.md` is wrong here) |
| path string | `0x14036ae10` = `"Libraries/OL.seria"` | `[code]` `search_strings` |

`GetStats(int partOID)` `[code]`, verbatim:

```
if (partOID != -1) {
  if ((ulonglong)(longlong)partOID < (ulonglong)(StatListMax - StatListBase >> 3)) {
    return *(void **)(StatListBase + (longlong)partOID * 8);
  }
}
return (void *)0x0;
```

Reading: `GetStats` is a **bounds-checked index into a pointer vector**; `-1` and out-of-range
give NULL (callers check for NULL, e.g. `Part_Tick`). The record fields are at the offsets in
`hf_notes/docs/structures.md` §"Stats record" (price +0x88, category +0xb0, load_amount +0x148,
load_time +0x14c, thrust +0xf8, ...).

### 1.2 How it is filled

`PrepareMainLoop` `0x1401ad5a0` `[code]`:

```
pOStack_2a188 = (ObjectsLibrary *)New(0x48);
if (pOStack_2a188 != (ObjectsLibrary *)0x0) { ObjectsLibrary::ObjectsLibrary(pOStack_2a188); }
LoadSeriaFile(ObjectsLibrarySingleton,"Libraries/OL.seria");
LoadPlaneLoadouts();
```

`ObjectsLibrary::ObjectsLibrary` `0x140281500` `[code]` makes one property:

```
CopyString(&pPVar1->propertyName,"m_stats",0x7);
pPVar1[1].propertyName.string.ptr = (char *)&StatListBase;   /* the vector */
*(undefined4 *)&pPVar1[1].vfTable = 5;                        /* type tag 5 (scalar props write 0) */
```

The `5` is a *type tag* [guess: the scalar "m_keycode" property in the Keybind class writes `0` at
the same offset, so 0 = scalar and 5 = dynamic vector; the deserializer that reads it is
`DeserializeDynamic`]. Either way the property points at the global vector, which is what matters
below.

So the whole table is **one serializable property of a singleton**, bound directly to the global
vector. `LoadSeriaFile(container, path)` `0x140225930` `[code]` is generic and tiny in effect:
open the file (`OpenFile_`), then `container->vfTable->Desearialzie(container, stream)`.

### 1.3 What a deserialization does — the vector is EMPTIED first, then refilled

`ISerializable::Deserialize` `0x14018fa40` starts with a pass over the object's property list
`[code]` (disassembly of the same function, `0x14018fa93..0x14018fab4`):

```
14018fa93: MOV  RAX, qword ptr [R15 + 0x30]     ; RAX = property-list sentinel
14018fa97: MOV  RBX, qword ptr [RAX]            ; first node
14018fa9a: CMP  RBX, RAX / JZ  ...
14018faa0: MOV  RCX, qword ptr [RBX + 0x10]     ; node->data = the Property object
14018faa4: MOV  RAX, qword ptr [RCX]            ; property->vfTable
14018faa7: CALL qword ptr [RAX + 0x18]          ; vtable slot +0x18
14018faaa: MOV  RAX, qword ptr [RBX] / ...loop
```

For the vector property of `ObjectsLibrary` (vtable `0x14035df28`, read twice:
`read_memory 0x14035df40` = `90 1e 19 40 01 ...`), slot `+0x18` is `0x140191e90`, whose body
`[code]` is:

```
140191eb0: MOV  RDX,[RAX+8]        ; end
140191eb4: MOV  RCX,[RDX-8]        ; last element
140191eb8: MOVZX EDX, byte ptr [RCX + 0x28]   ; element class code, low byte
140191ebc: AND  DL, 0x7
140191ebf: CMP  DL, 0x7
140191ec2: JNZ  0x140191ed2                   ; not 7 -> do NOT delete
140191ec4: MOV  RAX,[RCX] / MOV EDX,1 / CALL [RAX]   ; virtual dtor(this, 1)
140191ed2: ADD  qword ptr [RAX + 0x8], -0x8   ; end -= 8
140191edf: CMP  qword ptr [RAX], RCX / JNZ 0x140191eb0
```

So the sequence of a load is: **empty the vector (element-destruct only when `code & 7 == 7`),
then parse and push fresh elements**. Concretely for `m_stats`:
* `Stats` records have class code `0x803`; `0x803 & 7 = 3` ≠ 7, so the clear **unlinks them
  without deleting them** → 176 records x 0x188 = 68,992 bytes ≈ **67 KiB leaked per reload**
  (the records stay allocated and keep their content);
* a re-load therefore **replaces** the table rather than growing it — but a load that fails
  *after* the clear leaves the table **empty** (worst case, see risks);
* the elements are pushed by `DeserializeDynamic` `0x140190660` `[code]`:
  `lVar1 = _atoi64(ObjectCode); DynNewSerializable(lVar1); *pInsertPos = plVar2; pVec[1] += 8;`
  (or `vec_realloc_insert`) — one element per `m_stats=<code>` line, appended in file order;
* the name → index map is **not** cleared by this pass (it lives in separate globals), see 1.4.

Consequences for a runtime reload of `OL.seria`:
1. Same file, same order → the new records get the same indices (0..175 for the 176-record file) again, so
   every live part's `+0x188` still points at the same part; the table works, the cost is the leak.
2. File order changed / a part added in the middle → every index after the insertion point now
   designates a different part; live parts silently use wrong stats (see 1.5).
3. Parse failure (truncated/edited file) → table empty → `GetStats` returns NULL for every part;
   the accessors I read return 0 in that case (§1.6), so parts lose thrust/power/reload rather
   than crashing — broken, but silent.
4. The leaked old records mean a *cached* `Stats*` from before the reload stays readable (stale)
   instead of dangling — an accidental safety net, not something to rely on.

Using `VProperty::Clear` alone (without re-loading) is therefore "empty the table": every part
goes to NULL stats and the records are leaked. It is a teardown, not a usable edit operation.


### 1.4 The name → index map, and why order matters

`GetPartIndex(EscadraName* name)` `0x140281cc0` `[code]`: a plain `std::map` walk
(`compareEscadraString((node+0x20), name)`), returning `*(int*)(node+0x40)` or `-1`.

The map is filled by `FUN_140281fa0`, which is **vtable slot +0x30 of the ObjectsLibrary**
(vtable `0x140372fd8`: `+0x00` dtor `0x140281aa0`, `+0x10` Serialize, `+0x18` Deserialize,
`+0x30` `0x140281fa0`) `[code]` (`read_memory` of the vtable, plus `LEA RAX,[0x140372fd8]` in the
ctor). `ISerializable::Deserialize` calls it as the *last* step: `(*(code *)this->vfTable->calc_angle_cache_)(this);`.
`FUN_140281fa0` `[code]` walks `StatListBase..StatListMax`, takes the name from `record+0x48`
(an `EscadraName`, i.e. `m_oid`) and inserts `name -> i` **only if the name is not already in the
map** (`if (found) { ... }` → the insert branch is only taken when the key is absent; the found
branch does not rewrite the stored index).

So:
* map rebuild is *insert-missing only* — it cannot repair an index if the file order changed;
* it runs only after a *complete* successful parse (it is the tail of `Deserialize`); a parse
  error aborts before it, leaving the map untouched while the vector has already been emptied and
  possibly half refilled (§1.3) — i.e. the map then points into a table that no longer has those
  indices.

### 1.5 What live objects hold: an index, not a pointer

`Body::calc_angle_cache` `0x14004a1c0` (the post-deserialize hook of a part) `[code]`, verbatim:

```
**(code **)(*(longlong *)param_1 + 0x1f8))(param_1);
if (((*(longlong *)((longlong)param_1 + 0x28) == 0xf) &&     /* exactly a Body */
     (*(int *)((longlong)param_1 + 0x188) == -1)) &&          /* stats index unresolved */
     (*(longlong *)((longlong)param_1 + 0x1a0) != 0)) {       /* m_oid length != 0 */
  uVar1 = GetPartIndex((longlong)param_1 + 400);              /* +0x190 = m_oid string */
  *(undefined4 *)((longlong)param_1 + 0x188) = uVar1;
}
```

Reading: a plain part's `+0x188` is `-1` after construction and is resolved **by name** at load
time; the value stored is the *index*, `-1` if the name is unknown. `Part_Tick` then uses it as
`GetStats((int)param_1[0x31])` (`+0x188` = 0x31 qwords) `[code]`.

The `-1` initial value is set by the part constructor `createNewBody` `0x140015690` `[code]`:
`1400156e3: MOV dword ptr [RSI + 0x188],0xffffffff` (RSI = the new Body). So the sequence for a
part that arrives from a file is: ctor sets -1 → `Deserialize` fills `m_oid` → post-hook
`calc_angle_cache` resolves the name to an index. A part cloned from a prototype (editor/DefinePart
path, §2.3) inherits the prototype's already-resolved index by the copy.

Therefore: after a table swap that preserves name→index, every existing part keeps working; after
a swap that changes the order, every part silently reads **another part's stats** (wrong damage,
wrong reload, wrong thrust) with no crash. That is the landmine of "just re-run the loader".

### 1.6 Consumers read the record at use time (this is what makes in-place edit hot)

`Part_Tick` `0x140054fb0` `[code]`, extract (each `GetStats` is a fresh call):

```
pvVar8 = GetStats((int)param_1[0x31]);
if ((pvVar8 != 0) && (*(float *)((longlong)pvVar8 + 0x14c) != 0.0)) { ...reload step... }
... *(float *)((longlong)pvVar8 + 0x14c) ...            /* load_time, float */
... (float)*(int *)((longlong)pvVar8 + 0x148) ...       /* load_amount, INT */
... *(float *)((longlong)pvVar8 + 0xd0) ...             /* fuel need */
... *(float *)((longlong)pvVar8 + 0xdc) ...             /* crew need */
uVar12 = *(uint *)((longlong)pvVar8 + 0xb0);            /* category (bit test) */
```

The small accessors show the same shape and are the ones a hot edit hits directly `[code]`:

```
GetThrust(body)        { s = GetStats(*(int*)(body+0x188)); if (!s) return 0; return *(undefined4*)(s+0xf8); }
GetPowerNeedStat(body) { s = GetStats(*(int*)(body+0x188)); if (!s) return 0; return *(undefined4*)(s+0xe0); }
GetMdlAt(body)         { s = GetStats(*(int*)(body+0x188)); if (!s) return 0; return *(undefined4*)(s+0x100); }
```

`FireGun`, `FireGuns`, `Engine_ApplyThrustForce`, `Body_BurnUpdate`, `Creature_AccumulatePartStats`
are all in the caller list of `GetStats` (`get_function_callers 0x140281e00`, 111 callers). I read
`Part_Tick` in full plus these three accessors; I did **not** audit all 111 for cached
pointers [honest scope]. Two things follow for a hot-edit:
* a changed float is picked up on the next tick for the fields read per tick;
* **field types must match the accessor**: `+0x148` is read as `int` (magazine size) and
  `+0x14c` as `float`; writing a float where an int is read (or vice versa) corrupts the value,
  it does not "just work".

Mutable fields are copied into the instance at spawn where they are *state*, not *stats*
(e.g. health `+0x2c8/+0x2cc`, rounds `+0x860`); those copies do **not** follow a stats edit for
parts already built — only newly built parts get the new base values [code for the copy
locations via `structures.md`; not re-derived here].

**One important exception to "hot"**: the *ship-level aggregates* are cached on the `Creature` and
are only recomputed by `CalculateStats` `0x14007fcf0`, which calls
`Creature_AccumulatePartStats` `0x140071380` (the only caller of that function) `[code]`:

```
pvVar10 = GetStats((int)param_2[1].field16_0x60);          /* the part's record */
... *(float *)(param_1 + 0x15cc) = (float)returnMass(param_2) + *(float *)(param_1 + 0x15cc);
... *(float *)(param_1 + 0x15e4) = (float)GetValue(param_2) + *(float *)(param_1 + 0x15e4);
... thrust into +0x1684/+0x1688, etc.
```

So a changed `m_thrust`/`m_mdl_at`/`m_density`/price shows up in per-part code immediately but in
the ship totals only after `CalculateStats` runs for that creature (it is called from
`BattleSpawner_SpawnShips`, `DrawBattleShipPanel`, the shipworks commit, `Creature_RecalcStatsPass`
`0x140287370`, …). A mod that edits stats should call it (or accept that totals update on the next
panel draw).

### 1.7 Teardown that does exist: the ObjectsLibrary destructor

`0x140281aa0` (ObjectsLibrary dtor, vtable `0x140372fd8+0x00`) `[code]`, verbatim core:

```
lVar2 = StatListBase;
if (StatListBase != StatListMax) {
  do {
    puVar1 = *(undefined8 **)(StatListMax + -8);
    if (puVar1 != (undefined8 *)0x0) { (**(code **)*puVar1)(puVar1,1); }   /* element dtor(1) */
    StatListMax = StatListMax + -8;
  } while (lVar2 != StatListMax);
}
... clears the map 0x143a33c08 (root re-linked to itself, count 0) ...
ObjectsLibrarySingleton = 0;
```

So a *correct* rebuild is: `dtor(singleton,1)` → `new ObjectsLibrary` (0x140281500, re-sets the
singleton) → `LoadSeriaFile(singleton, "Libraries/OL.seria")`. That is precisely the
construct/load/destroy cycle the engine itself uses (`PrepareMainLoop` builds it, the shutdown
block at the end of `PrepareMainLoop` destroys it, `exit_game` writes it out).

Caveats for calling that at runtime:
* every *record pointer* becomes dangling at the dtor; anything that cached `GetStats()` output
  across frames dies. I found no such cache in the code I read, but I cannot prove its absence
  for 111 call sites [guess → would need a full audit or a runtime test];
* the map is cleared, so a failed re-parse leaves `GetPartIndex` empty → all *new* bodies get
  index `-1` → `GetStats(-1)` = NULL → the accessors I read return 0 (thrust/power/angle) rather
  than crash, but a part with 0 thrust that still burns fuel, or a weapon with 0 magazine, is
  broken in a way that is hard to diagnose; treat a failed reload as fatal for the session.
* **you usually do not need it**: a plain `LoadSeriaFile` on the existing singleton already
  empties the vector first (§1.3) and leaks the records instead of freeing them. The dtor is the
  only path that *frees* them, i.e. use it when you reload many times, not for a one-off.

### 1.8 Who touches `Libraries/OL.seria` — the complete xref list

The string `"Libraries/OL.seria"` at `0x14036ae10` has exactly **four** references `[code]`
(`get_xrefs_to 0x14036ae10`), and the two directions are cleanly separated:

| Site | Function | Direction |
|---|---|---|
| `0x1401ad9c8` | `PrepareMainLoop` `0x1401ad5a0` | **read** (`LoadSeriaFile`, right after the ObjectsLibrary ctor) |
| `0x140211e2f` | `APP::exit_game` `0x140211e10` | **write** (`SerializeToFile(singleton, ...)`) |
| `0x1401ecb9a` | `BuildQuitMenu` (in `0x1401ecb10`) | **write** (`MOV RCX,[0x143a1c428]; CALL 0x14024e3e0`) |
| `0x140240eac` | `reload_sg` `0x140240b90`, failure branch | **write** (then `exit_game` logic) |

Reading: **(a)** the table is read exactly once per process, at startup; **(b)** it is written
out from memory on the normal quit path (the quit menu builds this too, not only a crash path);
**(c)** therefore an in-memory edit *will* be saved over the user's file at quit, and a file edit
made while the game runs *will* be overwritten at quit. Both halves of "edit the data file while
running" are dead ends; only the in-memory path exists.


---

## 2. `Libraries/parts.seria` — body prototypes / editor palette

### 2.1 Two globals, two loaders

`PreLoadLibraries_` `0x140233710` (called from `initGame` `0x1401a94d0`) `[code]`:

```
local_80 = (Node *)New(0x128); ... ALL_PARTS = pIVar5;                 /* 0x143a139f0 */
CopyString(...,"LIB_EDITOR",0xa);
bVar3 = LoadSeriaFile(ALL_PARTS,"Libraries/parts.seria");
if (!bVar3) { ... LogFatalError("ERR: Preload_libraries was unable to load LIB_EDITOR."); }
(*(code *)ALL_PARTS->vfTable[2].destructor_)(ALL_PARTS,0);   /* post-load pass */
AssignRandomId(ALL_PARTS,1);
(*(code *)ALL_PARTS->vfTable[2].field1_0x8)();
```

then the same pattern for `DAT_143a13a08` (`LIB_TOWN`, `Objects/Town`), `DAT_143a13a28`
(`LIB_GROUND`, `Objects/Land`), `DAT_143a13a40` (`LIB_ROCK`, `Objects/Rock`),
`DAT_143a13a50` (`LIB_DOCS`, `Objects/Docs`), `newNode_` (`LIB_SHIPS`, `Objects/Designs` +
`Ships`), finishing with the per-file ship loader `rep_1401a0a70_LoadSeriaFile` for each ship
file. Note `ALL_PARTS` is a **raw global**, assigned without freeing the previous value.

`loadSeriaForLibraries_` `0x1400d09a0` (called from the editor/shipworks entry
`FUN_1400beea0`, itself called from `SomethingWithLevelSerias` `0x1402ac970`) `[code]`:

```
this = (Node *)New(0x128);  node = (void *)Node::Node(this);
SetLink((Link *)&DAT_1403ef4f0,node);            /* 0x1403ef4f8 = the container pointer */
pcVar3 = "Libraries/parts.seria";
if (LOAD_CONSTRUCTOR_OR_EDITOR != '\0') { pcVar3 = "Libraries/constructor.seria"; }
bVar1 = LoadSeriaFile(PARTS_CONSTRUCTOR_SERIA,pcVar3);
if (bVar1) { ... CopyString(name); dtor(vtbl+0x10,0); AssignRandomId(...,1); ...+0x7a8 = 999; }
```

Reading: **this loader is run again on every entry to the editor/constructor screen** and builds
a *new* `Node` each time, re-pointing the smart-`Link` at `0x1403ef4f0`. So re-reading
`parts.seria` at runtime is *already exercised by the game* — the pattern is proven safe for
that screen. Two honest caveats:
* `SetLink` `0x140194de0` only re-points the `Link` (`RemoveNodeLink(old)` + `AddNodeLink(new)`);
  I saw no destructor call for the old node on this path → the previous library tree is leaked
  (its child `Body` prototypes included). Size: the shipped `parts.seria` has **162** Body
  prototypes (`[file]` `grep -c '^m_children=15' ~/Downloads/parts.seria` = 162), 162 x 0xa40 ≈
  415 KiB per entry;
* the campaign copy (`ALL_PARTS`) is a *different* global from the editor/constructor copy
  (`0x1403ef4f8`), so re-entering the editor does not refresh the campaign's prototypes.

### 2.2 What an edit of a prototype affects

Body prototype fields are read when a part is *instantiated* (the copy ctor `0x140015690` /
`createNewBody`, and `CopyObject` `0x1401bfd00`); a live part carries its own health, fuel, etc.
`[notes: structures.md "Body" table + formats.md "Copied into ships/saves when a part is placed,
so edits do not reach existing ships"]`. So editing `parts.seria` in memory changes **new**
parts only (new ships bought/built/spawned, editor placements), never existing ones. That is the
same limitation as editing the file, except no restart is needed.

### 2.3 The palette is a *derived* structure — it can simply be rebuilt

`DefineEditorParts` `0x1400d0ac0` `[code]`, head:

```
if (LOAD_CONSTRUCTOR_OR_EDITOR == '\0') {
  if (EditorLibraryHull != (longlong *)0x0) { (**(code **)(*EditorLibraryHull + 0x48))(); }  /* kill */
  pNVar1 = (Node *)New(0x128); pvVar2 = Node::Node(pNVar1);
  SetLink((Link *)&HULL_LINK,pvVar2);
  CopyString((longlong **)(EditorLibraryHull + 0x19),"EDITOR_LIBRARY_HULL",0x13);
  pvVar2 = DefinePart(ALL_PARTS,"MDL_DECK_01",EditorLibraryHull,1);
  ... ~200 more DefinePart(ALL_PARTS,"MDL_...",EditorLibraryHull,1) ...
```

and `DefinePart` `0x14021b190` `[code]` (this is also the third-party `DefinePartEx` entry point):

```
pvVar1 = (**(code **)(*(longlong *)allPartLibrary + 200))();   /* find by m_oid in the library */
if (pvVar1 != 0) {
  plVar2 = CopyObject(pvVar1);                                  /* clone the prototype */
  (**(code **)(*plVar2 + 0x80))(plVar2,0);                      /* relink_ */
  AssignRandomId(plVar2,1);
  (**(code **)(*plVar2 + 0x88))(plVar2);                        /* Load_ / init */
  *(int *)(plVar2 + 0xf5) = count;                              /* +0x7a8 = count */
  if (categoryLibrary != 0) { (**(code **)(*categoryLibrary + 0x50))(categoryLibrary,plVar2,0,0); }
}
```

Reading: the editor palette (`EditorLibraryHull` and the other category libraries) is **destroyed
and rebuilt from `ALL_PARTS` every time `DefineEditorParts` runs**, which the editor entry path
does on every entry (§2.1). `DefinePart` clones a prototype by name and inserts the clone into a
category library — this is the runtime-safe way to *add* parts (it is what the Shipworks palette
does via `DefinePartEx` `0x14021b190` / `CreateLibraryEx` `0x14027f200` per `setup.md`), and it
fails cleanly (returns NULL) for an unknown `m_oid`.

Consequence for hot reload of `parts.seria`: **you do not need to re-run the file loader to
refresh the palette.** Edit the prototype fields (or add prototypes), then run
`DefineEditorParts` (or re-enter the screen, which does) and every palette entry is a fresh clone
of the new prototype. The mod-injected entries must be re-added after that, because the rebuild
wipes them — which is the shape the Shipworks-style mods already have.

### 2.4 What a *ships* re-read would mean

`LoadSeriaFile` on a ship file (`rep_1401a0a70_LoadSeriaFile` `0x1401b08a0`) `[code]` always
builds a **fresh `Node`** (`this = New(0x128); container = Node::Node(this); LoadSeriaFile(container, path)`),
runs the post-load passes, and the *caller* adds that container to the ship library
(`PreLoadLibraries_` does `(*(code *)newNode_->vfTable[1].Serialize)(newNode_, container, 0, 0)`).
Nothing replaces an existing entry by name, so a second run adds **another copy** of the ship;
and a ship already in a save is a separate object anyway. Hot-reload of ship files would therefore
be "load an extra copy", not "update the design" — the useful path is to mutate the loaded
`Creature`/`Body` fields directly (new spawns only, same as §2.2).

---

## 3. The language pack (`Data/Dialogs/*.seria_enc`)

`LoadDialogue` `0x1402253a0` `[code]`, first instruction group:

```
LEA RCX,[0x143a1c3a0]
CALL 0x140191b90            /* clear + free the whole hash table */
... open "Data/Dialog/" + ("russian"|"english").seria_enc ...
... decrypt in place: pcVar5[i] ^= (byte)(iVar13>>0xf) ^ (byte)iVar13; iVar13 = iVar13 + 0x343fd;
    starting iVar13 = 0x269ec3  (2531011, step 214013 - matches formats.md)
... split on '#' and '\n', register each entry
```

Reading: (a) the cipher is exactly the documented MSVC `rand` LCG; (b) the container at
`0x143a1c3a0` is a hash table whose clear/free helper `0x140191b90` walks the buckets and frees
every node (`free(puVar1)` after freeing the key); (c) `LoadDialogue` **resets it first**, so
re-running it is a genuine replace, not an append — a cleaner reset than the OL.seria path of
§1.3, because here the old entries are actually freed.

Lookup `FUN_1401ae090` `[code]` = `bool getString(const char* key, std::string* out)`:
FNV-1a hash (`0xcbf29ce484222325`, prime `0x100000001b3`) of the key, walk the bucket list,
`memcmp`, then **copy** the value into the caller's `std::string`. So no caller keeps a pointer
into the table; clearing it cannot dangle a previously fetched string.

Risk: `LoadDialogue` reads `coreLanguage` and hard-codes the filename; re-running it while a
dialogue box is on screen changes strings mid-sentence (cosmetic). Re-running costs a full file
parse (the file is read whole into memory) — a few ms to tens of ms [guess], i.e. at most one
frame hitch, acceptable on a hotkey.

---

## 4. The ammo table (code-defined, not a file) — the counter-example

`DefineAmmos` `0x140256f10` `[code]`, first instructions:

```
MOV RDI,qword ptr [0x143a13be8]     /* AMMO_LIST_END */
MOV RBX,qword ptr [0x143a13be0]     /* AMMO_LIST_BEGIN */
CMP RBX,RDI / JZ ...
loop: MOV RCX,RBX; CALL 0x1401a5ad0; ADD RBX,0x188; ...   /* destroy each element */
MOV RBX,qword ptr [0x143a13be0]
MOV qword ptr [0x143a13be8],RBX       /* END = BEGIN  (size 0) */
... then push fresh 0x188-byte records (0x140289190 template, 0x140289080 copy,
    0x14019a380 vector grow) and fill them with strings/constants ...
```

Reading: `DefineAmmos` **is** restartable — it destroys the old elements, resets the size, and
rebuilds. Same order → same indices. It is called once from `PrepareMainLoop` after
`LoadDialogue`, so the ammo names it embeds (`CALL 0x1401ae090`, the string lookup) are taken
from the freshly loaded language table. Two consequences:
* it is the model to copy for any table you want to make re-loadable: *destroy → reset → rebuild*;
* because it is code, not data, a mod cannot change ammo stats by editing a file — only by
  patching code or by mutating the 0x188-byte records in memory (which is what the AA-missile
  work does at the data level).

The neighbouring `LoadPlaneLoadouts` `0x1401af830` (called right after `LoadSeriaFile(OL.seria)`
in `PrepareMainLoop`) `[code]` has the same shape but **no clear**: it calls `AddPlane(&PLANE_TLL,
...)` for `CRAFT_LA29` and `CRAFT_T7` (crafts at `0x143a13c50`, loadouts at `0x143a15a60`,
hard-coded, no data file). A second run would add two more craft entries and duplicate loadouts.
So: aircraft loadouts are code tables (nothing to hot-reload from disk), and the loader is *not*
idempotent — do not re-run it.


---

## 5. Resources (`.res`, atlases, fonts) — the negative case

`Init_HGE` `0x1401ad080` `[code]`:

```
HGE = CreateHGE(0x180);
... state, title, log file, screen mode ...
local_58 = New(0x78);
pvVar5 = MediaClassConstructor(local_58,"Media/media.res");   -> Media_res
cVar2 = (**(code **)(*HGE + 8))();                            /* resource init / parse */
ArrayLoadedByMedia_res = (**(code **)(*HGE + 0x2e8))();       /* find files under Media/Tex */
rep_wrap_0_VCOMP140_DLL___vcomp_fork(Media_res,3);            /* load atlases (parallel) */
LoadNameIntoMedia(Media_res,"myriad_15"); LoadNameIntoMedia(Media_res,"myriad_10");
DAT_143a13958 = ...; ... 28 globals copied out of the media object ...  /* cached handles */
```

Reading: the resource script is parsed once, the textures are loaded once, and ~28 *raw pointers
to resource objects* are cached in globals (`0x143a13958..0x143a13a58`). HGE rejects a resource
name that is already defined (`formats.md`, "already has been defined", the first definition
wins), so a naive second parse of `media.res` only produces error lines. To hot-swap art you
would need: delete/free the named `Texture`/`Animation` objects, re-parse the `.res`, reload the
atlas texture, and refresh all cached handles — that is engine surgery, not a loader re-run.
**Verdict: no.** Art changes need a restart.

Language/`Data/Dialogs` and `Libraries/*.seria` are the only data classes with a cheap hot path.

---

## 6. Levels and the engine's own "safe re-run" mechanism

`APP::reload_sg` `0x140240b90` `[code]` (the level switcher):

```
reset a block of globals (target screen, zoom, shake, several maps/lists)
if (IsInEditor) loadShipworks_();
... if (LevelSingleton != 0) ...
bVar2 = LoadSeriaFile(LevelSingleton, "Data/Levels/" + param_1);
if (bVar2) { WriteToClientLog(...,"LEVEL reload successful with %s."); Level::Load(); ... }
else { ... log "ERR: reload_sg failed" ... APP::exit_game(); }
```

and its trigger, `SomethingPreTask` `0x140286e40` `[code]`:

```
piVar6 = &SeriaToLoad;  if (0xf < DAT_1403c13a8) piVar6 = SeriaToLoad;
if ((DAT_1403c13a0 == 4) && (*piVar6 == 0x74697865)) { /* "exit" */ CopyString(&SeriaToLoad,""); FUN_140211e10(); return; }
...
cVar5 = FUN_140240b90(piVar6);          /* the actual reload, on the game thread, top of frame */
CopyString((longlong *)&SeriaToLoad,"",0);
DAT_143a11903 = 0;  DAT_143a11908 = 0;
```

`SetLevelSeriaToLoad_` `0x14025afd0` `[code]` is the public "queue a load":

```
CopyString((longlong **)&SeriaToLoad,param_1,len);   /* 0x1403c13a0 */
DAT_143a11903 = param_2;  DAT_143a11908 = param_3;
... optional zoom save ...
if (name is "Map.seria" or "City_generated.seria") { build+show the loading GUI }
```

Reading, and this is the design lesson for the whole report: **the engine never calls a loader
from an arbitrary place.** It writes a *request* into a global string and a per-frame task
performs the load at the top of a frame, on the game thread, outside any other loader. A mod that
wants to re-run a loader while the game runs should use the same shape: a request flag consumed
by an existing per-frame hook (the mods already have several, e.g. the per-frame creature
registry rebuild at `0x14006bf60` and the battle manager `0x1402cc260` in `hooks.md`).

One other precedent that file loading mid-session is *not* firewalled: `ClickFunc` calls
`LoadSeriaFile` twice from GUI click handlers (`0x140135297`, `0x14013d875`) `[code]`; at
`0x140135289..0x14013529c` the sequence is `escadraStringToStr` → `LoadSeriaFile(container, path)`
→ `CALL qword ptr [RAX+0x80]` (the same "post-load virtual pass" the parts library loader uses).
I did not identify which menu item that is — it is the model of a "load this file into this
object now" action, i.e. the engine does load data on a click, just not the startup tables.

The level loader itself is a good target for a hot reload because the engine already does it —
but note what `reload_sg` **does not** do: it does not save the current battle, and it resets the
globals listed at its top; it is a *screen transition*, not a "refresh the data of the current
scene". Using it mid-battle loses the battle.

---

## 7. Behaviour matrix — what each loader does when run a second time

| Loader | Second run | Old data | Verdict |
|---|---|---|---|
| `LoadSeriaFile(ObjectsLibrarySingleton,"Libraries/OL.seria")` | **clears** the vector (leaks stats records), then refills | old records unlinked, leaked | workable, see §1.3 |
| ObjectsLibrary dtor + ctor + load | replace | freed (element dtors) | the clean rebuild |
| `loadSeriaForLibraries_` (parts.seria, editor) | new `Node`, `SetLink` re-point | old tree leaked (no dtor seen) | already used by the game |
| `PreLoadLibraries_` (parts.seria, campaign) | new `Node`, raw global overwritten | leaked (162 prototypes ≈ 415 KiB for parts.seria, more for the ship library) | feasible, leaks |
| `LoadDialogue` | **clear then rebuild** | freed | safe |
| `DefineAmmos` | **destroy, reset size, rebuild** | freed | safe |
| `LoadPlaneLoadouts` | appends 2 crafts + loadouts again | kept | do not re-run |
| `DefineEditorParts` (palette from `ALL_PARTS`) | **kills the category library and rebuilds it** | freed (vtbl+0x48 kill) | safe, wipes mod-added entries |
| `DefinePart` (clone one prototype into a library) | adds one more clone | n/a | safe, fails on unknown oid |
| `LoadSeriaFile(LevelSingleton, level)` + `Level::Load()` | replace (via `reload_sg`) | engine resets | supported |
| `Init_HGE` / `media.res` | new HGE instance, duplicate names rejected | not freed | no |
| `ISerializable_SerializeToFile` (exit) | writes the table back to disk | — | **side effect to design around** |

---

## 7.1 Address book of the tables (for a mod that wants to touch them)

| Table | Globals | Element | Notes |
|---|---|---|---|
| part stats (`OL.seria`) | `0x143a33bf0` begin, `0x143a33bf8` end, `0x143a33c00` cap; map root `0x143a33c08` | `Stats*`, record `0x188` bytes, code `0x803` | §1; index resolved by `m_oid` |
| `ObjectsLibrary` singleton | `0x143a1c428` | 0x48-byte object with the `m_stats` property | §1.2 |
| body prototypes / editor library | `ALL_PARTS` `0x143a139f0`; constructor copy `0x1403ef4f8` (held by Link `0x1403ef4f0`) | `Node`/`Body` tree, code `0x7`/`0xf` | §2 |
| ammo definitions | `AMMO_LIST_BEGIN` `0x143a13be0`, `AMMO_LIST_END` `0x143a13be8`, cap `0x143a13bf0` | 0x188-byte record | §4, rebuildable |
| plane crafts / loadouts | `0x143a13c50` / `0x143a15a60` (names from the Ghidra comment on `LoadPlaneLoadouts`) [guess] | craft node, loadout node 0xa0 | §4, do not re-run |
| dialogue strings | `0x143a1c3a0` (+ buckets at `0x143a1c3b8`, mask `0x143a1c3d0`) | unordered-map node, key at +0x20 | §3, replace-safe |
| font / atlas handles | 28 qwords `0x143a13958..0x143a13a58` | resource pointers | §5, no hot path |
| level loading queue | `SeriaToLoad` string `0x1403c13a0`; flags `0x143a11903`, `0x143a11908` | name string | §6, engine's own reload request |
| level object | `LevelSingleton` (symbol; address not read) | level `Node` | §6 |

---

## 7.2 Recommended shape for a hot-reload feature (from the above)

If I were to build "re-read my JSON and apply it while the game runs", the minimal safe design is:

1. **Never call a loader from your own thread.** Do the work either in a per-frame hook you
   already own (the mods have several), or in a hotkey handler that only sets a flag. The engine's
   own `SeriaToLoad` queue (§6) is the precedent.
2. **Prefer field writes over file loads.** `idx = GetPartIndex(oid)` → `rec = GetStats(idx)` →
   write the fields the JSON names, with the exact type the accessor uses (`int` at +0x148,
   `float` at +0x14c, `double` at +0xc8). Per-part code picks it up on the next tick; then call
   `CalculateStats` on the affected creatures so the ship totals (thrust, mass, price) match
   (§1.6). Nothing is reallocated; indices cannot shift.
3. **Snapshot before the first write**, so "revert" is a table of old values, and so the exit dump
   (§1.8) can be neutralised by restoring before quit.
4. **File loads only for data that is not already in memory**: the language pack (§3, replace-safe)
   and a level re-entry (§6). For `OL.seria` a re-load is possible (§1.3) but only worth it if the
   *set* of parts changes; then keep file order and check the record count before/after.
5. **Never require a part-order change.** Append new parts at the end of `OL.seria`; that keeps
   every existing `+0x188` valid, and the post-load map pass adds the new name.
6. **For parts.seria**, edit the prototype and rebuild the palette (`DefineEditorParts`, §2.3);
   do not re-run the file loader for a field change.
7. **Treat a failed load as fatal for the session**: the table is cleared before parsing, so there
   is no old table to fall back to.

---

## 8. Risks, ranked

1. **Exit dump**: in-memory stat edits are persisted to `Libraries/OL.seria` on exit
   (`0x140211e10`, `0x1401ecba1`) → the user's file changes silently. Mitigation: keep a pristine
   copy, restore the original values before quit, or accept the dump as the intended behaviour.
2. **Index shift**: any part-order change in OL.seria re-points every live part's `+0x188`.
   Mitigation: append-only edits; or re-resolve `+0x188` for every live `Body` by `m_oid` after a
   reload (the same `GetPartIndex` call `calc_angle_cache` uses).
3. **Partial parse**: `LoadSeriaFile` clears the table *before* parsing and returns false on a
   bad file, leaving it empty. Mitigation: validate the file first ("dry" parse into a scratch
   `ObjectsLibrary`), or keep a saved copy of the record pointers.
4. **Thread**: all of the above assume the game thread and a point outside any loader
   (see §6). Calling `LoadSeriaFile` from a mod's own thread races the renderer/AI which read the
   same records every frame.
5. **Type mismatch on field writes** (`+0x148` int vs `+0x14c` float, `+0xb0` category bits,
   `+0xc8` double fuel capacity): a wrong-type write is silently wrong, not a crash.
5b. **Stale ship aggregates**: changing thrust/price/mass stats does not update a `Creature`'s
   cached totals until `CalculateStats` `0x14007fcf0` runs for it (§1.6); the visible symptom is
   "the panel still shows the old number".
6. **Leaks**: each OL.seria reload unlinks the stats records without freeing them
   (`Clear` skips code 0x803; ~67 KiB for the 176-record file), and each parts-library reload
   leaks the old prototype tree (~415 KiB for parts.seria, more for the ship library). Only
   matters if reloads are frequent.
7. **Editor vs campaign copies**: refreshing the palette does not refresh `ALL_PARTS`; and the
   smart-`Link` at `0x1403ef4f0` is shared with other code that may hold the library.

---

## 9. Proposed minimal experiments (do not run here)

All are mod-side, log-only, one hotkey, game thread only.

**E1 — prove in-place stats mutation is hot (30 min).** In a throwaway mod:
on a hotkey, `idx = GetPartIndex("MDL_CANNON_130")` (`0x140281cc0`, careful: its arg is an
`EscadraName*`, i.e. an MSVC `std::string`; build one with the game's `CopyString`), then
`stats = GetStats(idx)` (`0x140281e00`), log `*(float*)(stats+0x14c)` and `*(int*)(stats+0x148)`,
multiply the float by 2 and log again. Expect: the gun's reload visibly doubles on the next shot,
no crash, and — **before exiting** — restore the original value (or expect `OL.seria` to change on
exit and diff the file afterwards to see the dump). Variant: change `+0xf8` (thrust) and watch
whether the battle panel's thrust number only changes after `CalculateStats` (`0x14007fcf0`) runs
for that creature — that measures the aggregate caching of §1.6. This one experiment proves the
whole "hot-edit data tables" idea and measures the exit-dump side effect.

**E2 — prove the re-load of OL.seria (1 h).** Two variants, in this order:
(a) *cheap*: on a hotkey call `LoadSeriaFile(*(void**)0x143a1c428, "Libraries/OL.seria")`
(`0x140225930`; the container is the ObjectsLibrary singleton at `0x143a1c428`) and log
`(StatListMax - StatListBase)>>3` before and after (`0x143a33bf0/0x143a33bf8`). Expect 176 → 176
(clear-then-refill of §1.3; 176 is the record count of the `~/Downloads/OL.seria` copy, see §1.1)
and a working game; this is the whole "re-read the game's data file" feature in one call;
(b) *clean*: `(*(code**)singleton)(singleton,1)` (dtor `0x140281aa0`), then
`newlib = New(0x48); ObjectsLibrary::ObjectsLibrary(newlib)` (`0x140281500`), then the same load.
Compare the count and check that a newly spawned ship still gets resolved stats (`+0x188 != -1`).
If both work, ship (a) and only use (b) when reloads are frequent (the leak).


**E3 — prove the file must not be edited while running (5 min).** Change a value in
`Libraries/OL.seria` with the game running and observe (log-only) that nothing changes; then
quit and restart and observe the change. Confirms "no periodic re-read" and gives the baseline.

**E4 — level reload via the queue (30 min).** From a hotkey call `SetLevelSeriaToLoad_`
(`0x14025afd0`) with the current level name and let `SomethingPreTask` do the work; verify the
game reloads the scene, and note what is lost (battle state). This validates the "request, do not
call" pattern for any future hot reload.

**E5 — dialogue reload (if wanted).** Call `LoadDialogue` (`0x1402253a0`) from a hotkey after
editing the language file on disk; look for a changed string on the next screen build. Low risk,
high visibility.

**E6 — palette refresh from edited prototypes (30 min).** In memory, change one field of a Body
prototype found under `ALL_PARTS` (`0x143a139f0`; walk the library's children, match `m_oid` at
`+0x190`, e.g. `MDL_ARMOR2X1_01`, and write health max `+0x2cc` — a field that can legitimately be
absent from the file because defaults are omitted), log the value, then call `DefineEditorParts`
`0x1400d0ac0` and read the clone the palette got: `DefinePart` copies the prototype, so the new
entry should carry the new value at the same offset. This proves the "edit prototype → rebuild
derived structure" pattern without touching the file loader at all — the cheapest useful
hot-reload for parts.seria.


---

## 10. Not determined / open

* Whether any of the 111 `GetStats` callers cache the returned pointer across frames. I read
  `Part_Tick` and three small accessors (`GetThrust`, `GetPowerNeedStat`, `GetMdlAt`); all four
  call `GetStats` at use time. A cheap check for the rest: search the disassembly for
  `MOV [reg+disp], rax` right after a `GetStats` call and follow one; or test E1 with a longer
  delay and see whether anything reads stale data.
* The record count in the *installed* game folder. I read the copy at `~/Downloads/OL.seria`
  (42,900 bytes; notes call it the 1.163 copy): **176** `m_stats` records. `formats.md` says
  "2051 records" — that is the **class code** at the start of each record
  (`m_stats=2051` is `m_stats=<class code>`, not a count), so the notes are wrong on this number;
  the record count is the number of `m_stats=` lines.
* Whether `RemoveNodeLink` (`SetLink` path) ever frees a node when `linkCount` reaches 0. The
  loader does not call a destructor explicitly, so the "old tree leaked" line in the matrix is a
  guess about the *freeing*, not about the re-pointing (which is code).
* Whether the exit dump is unconditional (I read `APP::exit_game` `0x140211e10` and the
  `reload_sg` failure branch, both call `SerializeToFile`; the normal window-close path was not
  traced to `exit_game`).
* `.res` hot reload: whether HGE exposes a "remove named resource" call (`Resource_RemoveAllPacks`
  `0x140174bd0` exists but removes *packs*, not named resources; not read).
* Ghidra's `Stats`/`ObjectsLibrary` struct types were not used; all offsets are raw
  displacements from the cited instructions (the structs are stale per `setup.md`).

---

## Checked twice

Per DS_RULES, the three claims that carry the verdicts were re-opened and re-read at the cited
addresses at the end of the session.

**C1 — "a re-run of `LoadSeriaFile` on the ObjectsLibrary replaces the table" (the load-bearing
claim).** First reading (§1.3 draft) said the deserializer only appends, so a re-load would
duplicate the table. **That first reading was wrong** and is corrected in the report. Second and
third reads:
* `0x14018fa93..0x14018faa7`: the first pass over the object's property list takes
  `property->vfTable` and calls `slot +0x18`;
* `read_memory 0x14035df40` (twice) = `90 1e 19 40 01 00 00 00` → `0x140191e90`;
* `0x140191eb0..0x140191ee2`: that function takes the last vector element, tests
  `(byte[el+0x28] & 7) == 7`, deletes it only then, decrements `end` and loops while
  `begin != end` → the vector is emptied before the parse, and `Stats` (code 0x803, `&7 = 3`) are
  unlinked but not freed.
Result: claim holds in the corrected form ("clear, then refill, leak the records"). The initial
version would have told the user to avoid a re-load that is in fact the right call — the
correction matters for the verdict, and risk 1 and 3 were rewritten accordingly.

**C2 — "a live part stores the stats *index*, resolved by name at load time".**
Re-read `calc_angle_cache` disassembly `0x14004a227..0x14004a24d`:
`CMP qword ptr [RBX+0x28],0xf / JNZ` (only plain Body), `CMP dword ptr [RBX+0x188],-0x1 / JNZ`
(only unresolved), `CMP qword ptr [RBX+0x1a0],0x0 / JZ` (only with a non-empty `m_oid`),
`LEA RCX,[RBX+0x190] / CALL 0x140281cc0 / MOV dword ptr [RBX+0x188],EAX`. All three conditions
are `AND`ed and each skip goes to the same exit, so the polarity is "all three true → resolve".
The `-1` initial value was re-read at `0x1400156e3` (`MOV dword ptr [RSI+0x188],0xffffffff`).
Result: holds. The base object is the `Body` itself (RBX), not a Frame or a Creature — the
`0x28 == 0xf` test excludes those. The same index-based pattern was then confirmed in three
independent accessors (`GetThrust` `0x1400487e0`, `GetPowerNeedStat` `0x1400487b0`, `GetMdlAt`
`0x140048720`: all are `GetStats(*(int*)(body+0x188))` plus a field read, with a NULL guard).

**C3 — "the game writes `Libraries/OL.seria` from memory at exit".**
Re-read `0x140211e28..0x140211e36`: `MOV RCX,[0x143a1c428]` (the ObjectsLibrary singleton) ;
`LEA RDX,[0x14036ae10]` (the OL.seria string) ; `CALL 0x14024e3e0` (`SerializeToFile`, which opens
the path with mode 2 = out and calls `obj->Serialize`, disassembled at `0x14024e3e0`). The quit
menu path was re-read at `0x1401ecba1` with the same three instructions. Result: holds, and the
xref list in §1.8 shows the read side is a single site (`0x1401ad9c8`).

Additional checks done for the same rules:
* **Arithmetic**: `+0x188 = 0x31 qwords` (0x31 x 8 = 0x188) — the `GetStats((int)param_1[0x31])`
  argument in `Part_Tick`; `+0x190 = 400 decimal` (the `LEA RCX,[RBX+0x190]` argument);
  index bound `(StatListMax - StatListBase) >> 3` (`-` before `>>`); `176 x 0x188 = 68,992`.
* **The file format was cross-checked against the real file** (`~/Downloads/OL.seria`): 176 lines
  of `m_stats=2051`, each followed by a `{ m_classname=Stats ... }` block, which confirms that the
  number after `=` is the element's class code (written from element+0x28 by
  `VProperty::Serialize_` `0x1401912a0`) and that `2051` in `formats.md` is not a count.
* **No invented constants**: every address and field offset used in a claim was read from an
  instruction or from `read_memory` in this session. Numbers taken from the notes are marked
  `[notes]` (Body class size 0xa40, the third-party entry points `DefinePartEx`/`CreateLibraryEx`,
  the `m_health` offsets) or were cross-checked against the shipped files (record counts).
* **No dropped `sqrt`/`abs`/`clamp`**: the report contains no gameplay formula; the only
  float-bearing claim (`+0x14c` float vs `+0x148` int in `Part_Tick`) is quoted with its cast.
* **Not found / not verified** is listed in §10 instead of being guessed.

## Operation ledger (formulas actually used)

| Expression | Source | Reading |
|---|---|---|
| `count = (StatListMax - StatListBase) >> 3` | `0x140281e0c..0x140281e19` `[code]` | number of `Stats*` entries |
| `valid ⇔ 0 <= i < count`, else NULL | `0x140281e1d..0x140281e27` `[code]` | `CMP RAX,RCX; JNC fail` → fail when `i >= count` |
| `+0x188 = 0x31 * 8` | `Part_Tick` `[code]` | stats index word |
| `size = 176 x 0x188 = 68,992` | records x class size (real file) | leak per reload |
| `LCG: seed 0x269ec3 (2531011), step 0x343fd (214013), byte ^= (b>>15)^b` | `LoadDialogue` `[code]` | matches `formats.md` |
| `FNV-1a: h = (h ^ byte) * 0x100000001b3`, `h0 = 0xcbf29ce484222325` | `getString` `[code]` | dialogue key hash |

