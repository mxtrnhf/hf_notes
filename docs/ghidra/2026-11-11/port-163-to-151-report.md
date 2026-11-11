# Porting 1.163 annotations into the 1.151 program — method and evidence

Run of 2026-11-11, programs `/Highfleet.exe.unpacked.exe v1.163` (source) and
`/Highfleet.exe.unpacked.exe v1.151` (target) in project `HighfleetServer`,
via the Ghidra MCP bridge (`run_script_inline`). This is the reverse of the
2026-10 `port_work/` effort, which had ported logdot's 1.151 names *into* the
1.163 program; all prior pairing knowledge (port_work `M.json`, 3,063 pairs)
was reused as anchors here.

## 1. Inventories (live, 2026-11-11)

Per function: address, name, name source, body size, instruction count,
SHA-1 (first 12 bytes) of the mnemonic sequence, callees, referenced
strings, thunk flag, plate length, signature parts, rep origin. Per program
DTM: every structure/union/enum with full component fields, comments and
descriptions. Raw dumps: `data/funcs_163.tsv.gz`, `data/funcs_151.tsv.gz`,
`data/dtypes_163.tsv.gz`, `data/types_151.tsv.gz`
(pre-assert cf. `data/coverage.py` for the before numbers).

| | v1.163 | v1.151 (before) | v1.151 (after) |
|---|---|---|---|
| functions | 5,432 | 4,923 | 4,923 |
| named | 4,663 (86%) | 961 (20%) | 2,366 (48%) |
| `FUN_*` | 55 | 1,172 | 566 |
| `rep_*` | 713 | 2,776 | 1,977 |
| plate comments | 4,061 | 154 | 1,490 |
| structures (+unions) | 416 (+10) | 251 (+14) | 521 (+14) |
| enums | 5 | 447 | 448 |

## 2. Matching pipeline (data/match3.py, output data/matched.tsv)

Targets: the 3,980 1.163 functions with names absent from the 1.151 name
set, whose 1.151 twin was still `FUN_*`/`rep_*`/`CFUN_*`.

1. **hash tier (1,280) — unique mnemonic-hash + instruction count on both
   sides, >=12 instructions.** Identical instruction streams modulo
   addresses; strongest evidence, and the only tier used for
   signature reconstruction.
2. **strings tier (64)** — the 1.163 function references a set of string
   constants that in 1.151 occurs in exactly one still-unnamed function,
   superset match, instruction count within max(4, 15%), e.g.
   `Body_BuildPartStatsText` (23 strings).
3. **propagation (60+1, two rounds)** — at least 3 callees already paired
   (anchors: port_work `M.json`, same-name pairs, tiers 1-2), >=75% of the
   anchored callee set present in the candidate, callee hit count unique
   with margin, strings not disjoint, size ratio 0.7-1.4. Example:
   `AircraftLogic_Mode3_Bomber` 163 `0x14000bd50` -> 151 `0x14000b730`,
   7/7 anchored callees.

Uniqueness both ways (one 163 name -> one 151 address, one 151 address ->
one name) is enforced globally per tier.

### Spatial-delta consistency (rejects gross outliers)

"Neighbours move together": between versions the address delta drifts
gradually per region (from about +0x700 at `0x140032xxx` to -0x22b40 at
`0x14029xxxx`). For tiers 2-3 the expected delta is interpolated linearly
between the two bracketing hash-tier pairs (<=1 MB away) and the candidate
is rejected if it deviates by >0x40,000. This rejected exactly one
candidate: `aircraftStateHandler` (163 `0x14000fbc0` -> `0x1400d51d0`,
+0xC5210 vs local expectation ~ +0xC20); its 5/5 anchored callees made it
look good, so without this filter it would have been ported wrongly.

Other deliberate losses: 6 hash-tier candidates dropped for duplicate
name or target collisions; 164 logdot-named 1.151 twins were never targets
because their name already exists in 1.151.

## 3. Function application (scripts in data/, applied in one transaction)

Per pair: rename to the 1.163 name (only if the target was still unnamed);
copy the plate verbatim (only if the target had none — 4 targets kept
their own plate); rebuild the signature:

- *matched-storage* (94): target already had committed parameters with the
  same storages; the 1.163 typed parameters were applied onto them.
- *dynamic-storage* (394, hash tier only): target parameters were
  uncommitted (`<UNASSIGNED>`) — reconstructed with ordinal
  `ParameterImpl` + `DYNAMIC_STORAGE_FORMAL_PARAMS`, which places types by
  the 1.151 calling convention. Safe because the bodies are identical.
- *skipped* (31): non-hash (version-affected) pairs with custom 1.163
  signatures — a 1.149/1.151 mismatch in register layout would silently
  mislabel parameters, so only the name and plate were ported.

Audit after apply: all 1,404 targets present and correctly named
(`nameMismatch=0`), plates present on 1,336 of them.

## 4. Data types (data/toimport.tsv, decision in data/mkimport.py)

- **Ported 270 structures + 10 unions + `b2ShapeType`**: exactly the types
  that exist in 1.163 only (by leaf name). Built shell-first to resolve the
  dependency cycles (b2Body<->b2Fixture<->b2World, HashMap family,
  DLL/SentinelList family), fields second, categories and field comments
  preserved, provenance description appended (see change log).
- **NOT ported — same name, different size.** The 1.151-strong definition
  is local truth. Size deltas found (1.163 vs 1.151 DTM bytes):

| struct | 1.163 | 1.151 | delta |
|---|---|---|---|
| `Body` | 2624 (0xa40) | 2576 | +48 |
| `BodyVFTABLE`/`CreatureVFTABLE`/`ISerializable` | 704/704/72 | 696/696/65 | vtable slot shift |
| `Creature` | 6736 | 6443 | +293 |
| `GUI` | 3696 | 3640 | +56 |
| `GUIVFTABLE` | 856 | 848 | +8 |
| `Panel` | 3736 | 3680 | +56 |
| `ObjectList` | 3864 | 3808 | +56 |
| `Profile` | 1512 | 1380 | +132 |
| `Escadra` | 1560 | 1536 | +24 |
| `Ammo` | 392 | 360 | +32 |
| `Mark` | 584 | 616 | -32 (1.151 bigger) |
| `astruct` | 392 | 737 | type/local placeholder mismatch |
| `CReObject` | 40 | 1 | 1.151 placeholder |
| `HGE_Impl` | 1 | 3464 | 1.163 placeholder |
| `basic_ios<DOS/pdb variants>` | 1..81 | 24..37 | junk entries, ignored |

These extend the version-difference table in
[porting-1151-1163.md](../../porting-1151-1163.md): `GUI`/`Panel`/`ObjectList`
all gain 0x38 in 1.163 — consistent with the known vtable-slot growth
(damage slot 0x208 -> 0x210 = two 64-bit slots) — while `Mark` is the only
class found *smaller* in 1.163.

Rebuild guarantee check: every ported struct matched its declared 1.163
length, except 5 initially-short ones (5-byte `CReObject` tail family):
`CSGlitch` received explicit tail padding, the other four rebuilt cleanly
once their referenced types existed.

## 5. Caveats for future users of the 1.151 program

- Ported plates describe 1.163 behaviour. For the version-affected families
  (ammo weapon block, stats record, Profile vectors, map-speed formula,
  FireGun arc) the plate text can be subtly wrong for 1.151; the anchor
  table in porting-1151-1163.md section 4 remains the curated reference.
- `TWR`-based map speed has no 1.151 twin for `powf` callers; aircraft
  AI close-range weapon cutoff is 1.163-only — the renamed 1.151 twins of
  those paths (`Aircraft_...`, `runMissileandAircraftIntercept_`) inherit
  plates written from 1.163 code.
- Remaining gap: 566 `FUN_*` (many are 1.163-only features — skirmish,
  harpoon, KAZ — which have no 1.151 twin) and version-affected functions
  without string anchors or 3 anchored callees. The next natural pass is a
  decompiler-similarity matcher on the 31-skip pairs and the propagation
  rejects.
- Nothing here was validated in game; the annotations are inert until a mod
  or analysis reads them.
