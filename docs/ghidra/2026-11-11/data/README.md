Raw inputs and outputs of the 2026-11-11 bulk 1.163 -> 1.151 annotation port.
Preserved byte-for-byte. TSV formats are documented in the column headers.

- `funcs_163.tsv.gz`, `funcs_151.tsv.gz`: function inventories dumped from the live programs (matched dumps of the same day).
- `dtypes_163.tsv.gz`, `types_151.tsv.gz`: data-type inventories (163 detailed with fields/comments; 151 shallow, dump taken before the port).
- `matched.tsv`: the complete 1,404 pair table (addr163 addr151 tier ev) that drove the apply.
- `portfuncs.tsv`: per-pair name/return/params/plate text dumped from 1.163; the input of `PortFuncsApply.java`.
- `toimport.tsv`: the 281 data types (270 structs, 10 unions, 1 enum) imported into the 1.151 DTM; input of the (inline) type importer.
- `match3.py`, `mkimport.py`, `mkjtsv.py`, `coverage.py`, `match3.out`: the host-side matching pipeline and its final output.
- `PortFuncsApply.java`: final executed apply script (renames, plates, signatures).

The inventory dump script, the type importer and the function dump script ran
inline via the MCP bridge (`run_script_inline`); PortFuncsApply.java is the
only one kept verbatim, the others are recoverable from this change log's
description and the dump formats above.

Round 4 additions (mod-function port, see `../mod-port-2026-11-11.md`):

- `modaddr_163_151.tsv`: the deliverable - every mod-referenced 1.163 function
  mapped to its 1.151 counterpart, with status/evidence columns
  (renamed-round1/2/2026-11-11, named, equivalent-diff-name, no-twin,
  site-holder).
- `modsites.py`, `modfns.py`, `modsites_full.txt.gz`: address extraction from
  hf_ally/hf_ai sources and resolution to containing 1.163 functions.
- `candmod.py`, `gen_cands.py`, `cand151_addrs.txt`, `candmod.json.gz`:
  candidate generation (interpolated spatial delta + instruction-count bands).
- `mn163.tsv.gz`, `mn163c.tsv`, `mn151.tsv.gz`: per-instruction mnemonic
  sequence dumps for the 34 port targets (1.163) and 1,371 candidates (1.151).
- `score1.py`: first screening by string-set and mapped-callee overlap.
- `mnscore.py`, `mn_scored.json.gz`: 8-gram fingerprint ranking + LCS
  confirmation of the top 3 candidates per target.
- `verify.py`, `verify2.py`: targeted verification of the specific pairing
  hypotheses (level-seria family, radio, GUI New, displayShipworks).

Round 5 additions (no-twin re-audit + field/global mapping, see the change log):

- `fields_163_151.tsv`: creature field-offset migrations (1.163 off ->
  1.151 off, with status/evidence) and the data-global mapping (labeled vs
  unresolved).
- `matched4.tsv`: the six pairs accepted in the round-5 content re-audit
  (five renames + aircraftStateHandler equivalence).
- `r3_recover.py`: sandboxed re-run of round3.py used to recover the full
  P3/C3-DELTA-REJ reject lists (writes only inside r3sandbox/).
- `notwin_check.py`, `notwin_refine.py`: the reject re-audit itself -
  LCS against the rejected candidate plus a containment scan over ALL 4923
  1.151 functions (`mn_all151.tsv.gz`) for the inlining pattern.
- `ins_squad163.tsv`/`ins_prec151.tsv` + `align_squad.py`/`align_squad2.py`:
  the buildSquadPrecombatScreen-inlined-into-mainPrecombatScreen revision.
- `ins163all.tsv`/`ins151all.tsv` (.gz): full instruction listings (index,
  address, mnemonic, operand text) for the 18 anchor pairs; input of
  `mine_offsets.py`/`mine_pass2.py`, which produced `mined_map.json` and
  `globals_map.json` (raw votes).
- `choose_ctx.py`: targeted neighborhood pull used to resolve the waypoint
  and retimer fields.
