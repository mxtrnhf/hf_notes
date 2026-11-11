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
