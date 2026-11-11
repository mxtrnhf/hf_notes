# Ghidra changes, 2026-11-11 (bulk port of v1.163 annotations into the v1.151 program)

Program: `Highfleet.exe.unpacked.exe v1.151` (project `HighfleetServer`),
image base `0x140000000` — **this pass changes the 1.151 program**, not
1.163. Source of every change below is the sibling program
`Highfleet.exe.unpacked.exe v1.163` (state as of 2026-11-11, after the
October sweeps and the 2026-11-05 friendly-fire pass). No code bytes were
changed; only function names, plate comments, signatures, and data types.

Full method, evidence and caveats: [port-163-to-151-report.md](port-163-to-151-report.md).
Raw data and scripts: [data/](data/) (`matched.tsv` is the complete
address pair table).

## Function names, plate comments, signatures

- **1,404 rename + plate ports** of 1.163-named functions onto their 1.151
  twins (`FUN_*`/`rep_*`/`CFUN_*` targets only; nothing already named was
  touched). Match tiers: 1,280 unique mnemonic-hash + instruction-count,
  64 distinctive-string-set, 60 anchored-callee propagation (two rounds).
  Result: 1.151 went from 961 to 2,366 named functions (20% -> 48%);
  `FUN_*` 1172 -> 566, `rep_*` 2776 -> 1977.
- **1,333 plate comments** copied verbatim (4 targets already had a plate;
  they kept it).
- **488 signatures** rebuilt: 94 onto functions whose committed parameters
  already matched storage-for-storage, plus 394 reconstructed with
  `DYNAMIC_STORAGE_FORMAL_PARAMS` on functions whose parameters were never
  committed (only for hash-tier pairs - identical instruction streams make
  the calling-convention placement safe). 31 non-hash pairs with custom
  1.163 signatures were left unnamed-sig on purpose (version-affected bodies
  may pass arguments differently).

## Data types

- **270 structures + 10 unions + 1 enum** (`b2ShapeType`) created verbatim
  from the 1.163 DTM (categories preserved, e.g. `_Box2D/`, `_Shader/`,
  `_Containers/`, `auto_structs/`), with field comments intact. Each carries
  a description: "Ported verbatim from Highfleet v1.163 program
  (2026-11-11). Offsets are 1.163 values; classes changed between 1.151 and
  1.163 may differ - see docs/porting-1151-1163.md".
- Dependency cycles (b2Body/b2Fixture/b2World, the HashMap family, the
  DLL/SentinelList family) were broken with empty shells first, fields
  second, so all 280 import candidates resolved.
- 5 structs initially came out short because a referenced class exists in
  1.151 only as a placeholder (`CReObject` in 1.151 is 1 byte vs 40 in
  1.163); `CSGlitch` got explicit tail padding, the other four rebuilt to
  their exact declared lengths.

## What was deliberately NOT ported

- 19 structures that exist under the same name in both programs but with
  different sizes (`Body` 2624 vs 2576, `Creature` 6736 vs 6443, `Profile`
  1512 vs 1380, `Escadra` 1560 vs 1536, `Ammo` 392 vs 360, `Panel`, `GUI`,
  `ObjectList`, vtables...). The 1.151 definitions are the ones modelled
  against 1.151 memory and were left untouched; the full size table with the
  delta analysis is in the report.
- Plate/sig of non-hash matched pairs where the twin is clearly
  version-affected (31 sigs, see above), and one propagation candidate
  rejected by spatial-delta consistency
  (`aircraftStateHandler` 163 `0x14000fbc0` -> candidate `0x1400d51d0`,
  +0xC5210 against a local expectation within ~0x1000; almost certainly a
  same-body false positive, the real 1.151 twin is not yet found).
- 6 hash-tier candidates dropped for duplicate name/target collisions, and
  164 named-1.163 functions whose 1.151 counterpart keeps logdot's own
  earlier name were not overwritten.

## Caveats

- Everything here is static cross-version matching. The mnemonic-hash tier
  is strong (identical instruction sequences), the string and propagation
  tiers are per-candidate evidential (see `matched.tsv` column `tier`/`ev`).
  No in-game validation was performed - no mod touches these annotations.
- Ported structure layouts are 1.163 values. For the version-changed classes
  (Body/Profile/Escadra/Ammo record/stats record weapon block) the zone
  tables in [porting-1151-1163.md](../../porting-1151-1163.md) still apply;
  treat ported `_Shader`/`b2*`/`_Containers`/auto_struct types as identical
  across versions only until a read of the 1.151 code confirms the field.
- The 1.151 scan for `aircraftStateHandler` (and other unmatched
  version-affected functions: `FireGun` twins already exist by name in 1.151)
  remains open; the propagation tier stalls below 3 anchored callees.

## Rounds 2 and 3 (same day, after the check-in)

Three further passes were applied and checked in after the first round:

- **Round 2 (147 pairs)**: 95 *group* tier — whole ICF-merged groups where the
  1.163 side is uniformly named and the 1.151 group is uniformly unnamed,
  ported member-for-member by sorted address (this also absorbed the 6
  "duplicate name" pairs the round-1 uniqueness rule had rejected, e.g. both
  `VectorStride48_InsertMove` instances); 23 *strings2* (>=60% string-set
  overlap + anchored-callee support + 25% score margin); 29 *prop2*
  (relaxed >=2 anchored callees). Includes `Body_AreaDamageFromBlast`
  `0x14002cdc0 -> 0x14002dca0` - exactly the porting guide's anchor pair.
- **Round 3 (96 pairs)**: repaired a format bug that had silently dropped the
  3,063 `port_work/M.json` anchor pairs from the anchor map (short vs
  16-digit address keys); with the full anchor set, 47+1 more
  callee-propagation matches and a new **caller-vote tier** (48): >=3 of the
  target's 1.163 callers map to 1.151 functions that call the same candidate,
  best unique with margin, spatial-delta consistent. Examples:
  `Effect_Add*Param` family, `Body_SetHealth`, `RbTree_DestroySubtree`.
- **Inline comments (1,378)**: all PLATE(68)/POST(1310) comments of 1.163
  sitting on instructions of identical-body pairs (tiers hash/group), ported
  by instruction index with the mnemonic sequence guaranteed equal by the
  tier. 80 target instructions already had a comment and kept it. PRE/EOL
  comments on non-identical pairs were deliberately not ported (index mapping
  is unsafe when the bodies differ).

Cumulative state after round 3 (live audit): 2,609 of 4,923 functions named
(53%), 1,723 functions carry plate comments, plus 1,378 inline comments.
Remaining rejects of interest: `aircraftStateHandler` (163 `0x14000fbc0`) -
the only content-supported candidate (`0x1400d51d0`) is spatially impossible
and no other candidate shares even one anchored callee; the true 1.151 twin
needs a decompile-level comparison. `Profile_GetActive`, `Vec2_WorldToScreen`,
`Trail_DrawLayer` and four more caller-vote candidates were rejected by
spatial delta with thin content evidence.
