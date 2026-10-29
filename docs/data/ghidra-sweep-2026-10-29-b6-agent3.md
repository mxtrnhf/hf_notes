# Ghidra sweep, batch 6 agent 3 — `rep_*` in `0x140100000–0x1401FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `rep_*` function with entry point in `0x140100000–0x1401FFFFF`.
Start count: **498** `rep_*`. End: **449** `rep_*`.

| | count |
|---|---|
| `rep_*` in scope | 498 |
| **renamed + plated** | **49** |
| stale label (identity recorded, not renamed) | 448 |
| unreadable (body bytes could not be hashed) | 1 |
| functions created | 0 |

No `save_program`, no tags, no README/STATUS edits, no commits. Every rename
carries a doc plate (summary / `Algorithm:` / `Parameters:` / `Returns:`).
Audit TSV: `docs/data/rep-audit-2026-10-29-q2.tsv` (498 rows, one per function).

## Method

1. **Whole-image body hash.** SHA-1 of every function body (address-set bytes,
   including alignment padding inside the body) built a `hash -> functions` map.
   Result for this range: **0 of 498** `rep_*` bodies are byte-identical to any
   other function in the image, in-range or not. This independently confirms
   batch-5 agent 5: the `rep_*` prefix is a signature-DB artefact, **not** ICF
   folding. ("It is a replica, leave it" is unsafe.)
2. **Embedded target classification.** Parsed `rep_<hex>_` and resolved `<hex>`:
   * 456 fall *inside* an unrelated function (usually mid-instruction),
   * 13 are real function entries — and in every one of the 13 the entry has an
     unrelated name and size (e.g. `rep_1401218d0_GUI::GUI_2` at 0x14012a5b0 is
     a 112-byte Gauge constructor, while 0x1401218d0 is a 17-byte
     `vecBoolTooLong`),
   * 7 point at undefined bytes,
   * 22 names carry no address at all (`rep_wrap_0_*`, `rep__FileSearch_*`).
   No embedded name matched its body.
3. **Vtable scan.** Searched `.rdata` (`0x140351000–0x1403bc9ff`) for qwords
   pointing at in-range functions, walked each candidate back over function
   pointers / nulls to the table base, required a CompleteObjectLocator pointer
   at `base-8` and a `. ?A` TypeDescriptor string, then reported slot index and
   RTTI. **90 of the 498** are genuine vtable slots; 44 of those are among the
   49 renames. This is the strongest identity signal in the range.
4. **Callee / string / shape signatures.** For all 498: instruction count,
   call count, returns/`int3`, callee name set, referenced string literals,
   callers, and a normalised mnemonic+operand-shape hash to find clone families.
   207 functions reference string literals; 244 have neither a vtable slot nor a
   string reference.
5. **Targeted decompilation** (batches of ≤10) of every candidate rename and of
   each clone family representative. No bulk decompilation, no function over
   `0x2000` bytes.

**Trap worth recording:** the first vtable pass looked for "pointer to this
function with a function pointer on either side". That matches `.pdata`
`RUNTIME_FUNCTION` records (`0x148078000–0x14808c1ff`), which made 496 functions
look like vtable members. `.pdata` is not a vtable; only `.rdata` slots with a
COL/RTTI pointer before the table are. Anyone re-running this must exclude the
`0x1480xxxx` block (also noted in the blackboard for agent 1).

## Structural findings (useful beyond the renames)

### `ISerializable` 8-slot ABI (vtable 0x140368998 and every derived table)

| slot | +offset | meaning | usual target |
|---|---|---|---|
| 0 | 0x00 | scalar deleting destructor | per class |
| 1 | 0x08 | base destructor | 0x140280c50 / 0x140005e70 |
| 2 | 0x10 | `Serialize` | 0x140190820 |
| 3 | 0x18 | `Deserialize` | 0x14018fa40 |
| 4 | 0x20 | `SerializeHeader` | 0x1402810a0 / 0x140192950 |
| 5 | 0x28 | shared base helper | 0x1401922b0 |
| 6 | 0x30 | shared base helper | 0x1400055d0 |
| 7 | 0x38 | **per-class `AddProperty`** | per class |

Slot 7 is proved by five in-range bodies (Explosion, Launched, LastPlayerPosData,
Escadra::MapShip, FX): each allocates `Property` objects, binds them to member
addresses via `Property::Property` + vtable + `CopyString(fieldName)` +
`AddProperty(this, prop)`. This makes slot 7 a cheap way to inventary any
class's serialized field layout — see the rename table for five concrete field
maps (offsets are in the plates).

### Property vtable ABI (4 slots, e.g. `fProperty` 0x140352540)

| slot | +offset | meaning |
|---|---|---|
| 0 | 0x00 | scalar deleting destructor |
| 1 | 0x08 | **write** field to text stream: `name<sep>value\n`, skipped if value == default (`this+0x38`) |
| 2 | 0x10 | **read** field from text: parse argument (`atoi`/`atoll`/`atof`/`_atoi64`/`sscanf`) into `*(this+0x30)` |
| 3 | 0x18 | container-only extra virtual (Clear for `li/l/mii`, shared 0x140005e70 otherwise) |

`this+0x08` is the `std::string` property name, `+0x30` points at the bound
member, `+0x38` holds the default. Container properties store a pointer to an
intrusive `Link` ring at `+0x30`; their read methods insert nodes and throw
`std::_Xlength_error("list too long")` at the per-container sentinel
(0x0aaa… for 24-bit nodes, 0x0666… for 40-byte nodes). The 7 renamed
`*_ReadField`/`*_WriteField` pairs reduce the "unknown accessor" families
(`hf_notes/docs/structures.md` audit item) to the concrete list above.

### Text-serialization separator
`DAT_140352a14` is the separator written between property name and value; the
name string itself is `s__140352a10`. Both appear in every `*_WriteField` body.

## Renames (49)

### Property serialization (24)

| addr | new name |
|---|---|
| 0x14018ffb0 | `iProperty_ReadField` |
| 0x140190ae0 | `fProperty_WriteField` |
| 0x14018ff40 | `fProperty_ReadField` |
| 0x140190c40 | `liProperty_WriteField` |
| 0x140190000 | `liProperty_ReadField` |
| 0x14018ff80 | `i64Property_ReadField` |
| 0x1401909e0 | `bProperty_WriteField` |
| 0x140190a70 | `dProperty_WriteField` |
| 0x14018ff10 | `dProperty_ReadField` |
| 0x1401905a0 | `sProperty_ReadField` |
| 0x1401910b0 | `oProperty_WriteField` |
| 0x140190530 | `oProperty_ReadField` |
| 0x140190930 | `ListLinksProperty_WriteField` |
| 0x14018fe20 | `ListLinksProperty_ReadField` |
| 0x140190790 | `viProperty_ReadField` |
| 0x140190090 | `listVectorsProperty_ReadField` |
| 0x140190710 | `vectorVectorsProperty_ReadField` |
| 0x140191240 | `uiProperty_WriteField` |
| 0x140190630 | `uiProperty_ReadField` |
| 0x140190ea0 | `msfProperty_WriteField` |
| 0x140190170 | `msfProperty_ReadField` |
| 0x140190fa0 | `mssProperty_WriteField` |
| 0x140190340 | `mssProperty_ReadField` |
| 0x1401907e0 | `vsProperty_ReadField` |

### Property container clears (3)

| addr | new name |
|---|---|
| 0x140191d80 | `liProperty_Clear` |
| 0x140191d00 | `lProperty_Clear` |
| 0x140191df0 | `miiProperty_Clear` |

### Per-class `AddProperty` slot 7 (5)

| addr | new name | fields registered (offset) |
|---|---|---|
| 0x140100c30 | `Explosion_AddProperty` | m_life/m_power/m_emmision/m_radius/m_explosive, isNuclear, isShipDamaged |
| 0x140101a20 | `LastPlayerPosData_AddProperty` | escadraId, lastPosition.x/.y, lastPositionTime |
| 0x140101bd0 | `Launched_AddProperty` | m_count, m_range, m_radar_range/cone, m_jammed, m_target_pos, m_target.id, m_aimer.id, m_search_state, m_homming_type, m_velocity_max, m_acceleration_time, m_agility, m_health, m_oid, originalTarget.id, m_slow_target |
| 0x140103830 | `MapShipEscadra_AddProperty` | pBody.id, pEscadra.id, pCreature.id, index, wing, curs, prevCurs |
| 0x140124e20 | `FX_AddProperty` | m_library |

### Scalar deleting destructors, proved by RTTI + slot 0 (13)

| addr | new name |
|---|---|
| 0x14011f510 | `FXPS_ScalarDeletingDestructor` |
| 0x14012caa0 | `GuiBinding_ScalarDeletingDestructor` |
| 0x14012cb90 | `GuiMapSky_ScalarDeletingDestructor` |
| 0x14012cbd0 | `List_ScalarDeletingDestructor` |
| 0x14012cc50 | `ObjectList_ScalarDeletingDestructor` |
| 0x14012cd30 | `Panel_ScalarDeletingDestructor` |
| 0x14012cde0 | `Replica_ScalarDeletingDestructor` |
| 0x14012ce30 | `Slider_ScalarDeletingDestructor` |
| 0x14012cee0 | `uiProperty_ScalarDeletingDestructor` |
| 0x140185e20 | `KeyBinding_ScalarDeletingDestructor` |
| 0x14018f980 | `ISerializable_ScalarDeletingDestructor` |
| 0x140194e50 | `SLink_ScalarDeletingDestructor` |
| 0x1401a8380 | `Item_ScalarDeletingDestructor` |

### Other proved identities (3)

| addr | new name | evidence |
|---|---|---|
| 0x14012a5b0 | `Gauge_Constructor` | installs Gauge vtable 0x140361238, name string `"Gauge"`, initialises gauge floats (1.0 / 0.4 / 1.0), calls virtual +0x38. |
| 0x1401952c0 | `LOG_Singleton_ScalarDeletingDestructor` | slot 0 of `Singleton<LOG>` 0x140368ed8; clears 0x1439ef248 and runs `ISerializable_Destructor`. |
| 0x140195350 | `LOG_ScalarDeletingDestructor` | slot 0 of `LOG` 0x140368f20; flushes/closes both log streams (`"Errorlog finished."`, `"Clientlog finished."`), then base dtor. |

### Reserve note
`ListLinksProperty_DeleteAllElements` (0x140191c70) is slot 3 of
`ListLinksProperty`; its body frees every element (calling the element's
deleting destructor when `(byte[+0x28] & 7) == 7`) then unlinks and frees the
nodes. Behavioural name, not a library-virtual name — flagged as such in the
TSV identity column.

## Stale labels left in range (448)

The audit TSV records for every one: old label, SHA-1, where the embedded target
really lands, and the best partial identity available. Summary of what the 448
are:

* **46 are vtable slots** whose class and slot index are now known, but whose
  virtual role is not proved. These are the cheapest remaining wins because the
  class is already pinned by RTTI; only the body read is missing:
  * `Frame` slots 0/12/18/68 — 0x14011bd40, 0x14011cc60, 0x14011cbc0, 0x14011cdb0.
    The 12/18/68 bodies emit `"ERR: Frame::breaking_remove_fail"`,
    `"ERR: Frame::reflect_failed (...)"`, `"ERR: Frame::remove_failed, with ..."`
    through `WriteToClientLog` — i.e. Frame error-path reporting helpers. They
    were left because the exact slot contract (which Frame operation each reports)
    is not established.
  * `Gui` slots 37/71/91/101/102/105 — 0x14012dad0, 0x140166420, 0x1401636d0,
    0x14012ebe0, 0x14012ec60, 0x14012db80.
  * `Gauge` 7/71 (0x140165a30, 0x140166260), `Slider` 7/71 (0x140165cb0,
    0x140167cc0), `Panel` 17/71/88, `ObjectList` 108/110/111, `Replica`
    17/109/110, `Joint` 7/8 (0x140194040, 0x140194080), `SLink` 7
    (0x140194f70 — writes the class name `"SLink"` and a class-id word; looks
    like a registration/defaults virtual, not provable), `AADefence` 7,
    `AircraftLogic` 5, `MapShipBody` 85, `Mark`/`Missile`/`Explosion` slot 44.
  * `HGE_Impl` 6 (0x14017db90) and 98 (0x14016cd50). 98 is the
    `Texture_Load` identified by batch-5 agent 8 via `D3D11CreateTextureFromMemory`
    and is in my range; I did not rename it because the slot is HGE's own
    interface and the user's rule is body proof — the body is a one-line
    `D3D11` path, so this one is a strong candidate for the parent to accept
    from agent 8's evidence rather than re-derive.
  * `URAnimation`/`URFont`/`URParticle`/`URSprite`/`URStringTable` slots 1/2
    (7 functions, 0x1401789a0–0x1401793c0). Three-slot media vtables; slot 2 is
    a ~95-byte release/free body, slot 1 a per-class setup body.
* **~164 reference string literals but no vtable slot.** Many are clearly part
  of one subsystem (e.g. the `s_m_*`/`s_is*` property-name blocks used by the
  `AddProperty` family above, the `"CRAFT_UNREADY_LIST"`/`"LOADOUT_LIST"` editor
  keys at 0x14011ae30, the `Gauge`/`List`/`GuiBinding` widget constructors at
  0x14012a5b0–0x14012b000). Without a class name or a proved call contract they
  stay stale rather than getting a guessing name.
* **Clone families** found by shape hash, none renameable on shape alone:
  three 570-byte `MakeGlobal?` bodies at 0x1402432f0/0x140243770/0x1402439b0
  (outside this range, same family), two 177-byte `_invalid_parameter_noinfo`
  bodies at 0x14011ef50 and 0x1401af030, two 137-byte array-free bodies at
  0x1401a5390/0x1401a5420. Their shape matches named siblings but the *type*
  they operate on differs, which is exactly the case where a name would be a
  guess.

### The one unreadable body
`0x1401a4da0` (183 B, `rep_1401964b0_..._free`): the body covers an address
range whose bytes the memory model will not return (uninitialised/overlapping
data between functions), so SHA-1 could not be computed. Its callers are the
`std::basic_ios` destructor replicas 0x1401987c0/0x140198880, so it is
ios-teardown-adjacent, but it is recorded unreadable, not renamed.

## Hand-off notes for the documentation agent

* `structures.md` can now state the `ISerializable` 8-slot and `Property`
  4-slot layouts above; the `Property` slot-1/2 direction (write/read) is proved
  by 23 bodies, not inferred from names.
* The field maps in the five `*_AddProperty` plates are the authoritative
  member offsets for Explosion (0x248–0x261), Launched (0x248–0x2b8, 0x2e8),
  LastPlayerPosData (0x58–0x68), Escadra::MapShip (0x58–0x9c) and FX.
* The `rep_*` caveat should say: 498 in this range, 0 byte-identical bodies,
  456/498 embedded targets land mid-function, and the only reliable `rep_*`
  structure is the vtable-slot + RTTI path. Also add the `.pdata` false-positive
  warning (0x148078000–0x14808c1ff).
