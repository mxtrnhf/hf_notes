# Ghidra sweep 2026-10-30 — Phase 2 agent C (red-black-tree families)

Program: `Highfleet.exe.unpacked.exe v1.163` (project `HighfleetServer`).
Source of scope: [data/unnamed-classification-2026-10-30.tsv](../data/unnamed-classification-2026-10-30.tsv),
families `container_rbtree_node_stride0x40` (5), `container_rbtree_node_stride0x28_candidate` (5),
`container_rbtree_node_stride0x30_candidate` (3), `container_rbtree_node_stride0x48` (2),
`container_rbtree_node_stride0x68` (1), `container_sort_helper_stride0x18_candidate` (2) — 18 rows.
No `save_program`, no commit, no README/STATUS edit. No `create_function` was needed.

**Result: 12 renamed + plated, 6 skipped (recorded below), 0 left to a later phase by accident.**

## Node layout — proven from the field stores

Every renamed body allocates its node with `New(size)` and then writes the same
seven fields, so the `std::_Tree` node header is identical across all of them:

| offset | field | store observed |
|---:|---|---|
| `+0x00` | `_Left` | `*node = header` (sentinel until linked) |
| `+0x08` | `_Right` | `node[1] = header` |
| `+0x10` | `_Parent` | `node[2] = header` |
| `+0x18` | `_Color` | low byte of `*(u16*)(node+3) = 0x0000` — red, not nil |
| `+0x19` | `_Isnil` | high byte of the same word — 0 for a real node |
| `+0x20` | `_Myval` | key, then value |

The sentinel/header itself is allocated with `New(node_size)` and initialised to
`all-three-links-self`, `*(u16*)(hdr+0x18) = 0x101` (black, nil) — seen verbatim in
`RbTreeStride72_InsertRange` and in the `0x28`/`0x30` node trees. The `+0x19` isnil
byte is also the loop guard (`CMP byte ptr [RAX + 0x19],R14B` in `RbTreeStride64_ConstructNode`),
and `RbTree_Insert` is `0x1400076d0` in every case.

Element stride = node size − 0x20. All twelve bodies are the same algorithm
(MSVC `_Tree::_Emplace_hint` / `_Insert_node` inlined): lower-bound walk on the key,
early return with `inserted = 0` when the key compares equal, otherwise
`New(node_size)` → move/copy key+value → link init → `RbTree_Insert`, with the tree's
`max_size` guard (`0x3ff…ff`, `0x666…66`, `0x555…55`, `0x38e…8e`, `0x276…76`) throwing
"list too long".

Naming follows the existing decimal stride convention (`VectorStride24`,
`VectorStride56`, `RbTree_InsertNode56` = 0x38): `RbTreeStride64` is a 0x40-byte node.

## Renamed (12)

| address | size | name | node | key → value |
|---|---:|---|---:|---|
| `0x1400069a0` | 316 | `RbTreeStride64_ConstructNode` | 0x40 | int key `+0x20` → three qwords `+0x28/+0x30/+0x38` |
| `0x1401a25b0` | 314 | `RbTreeStride64_ConstructNodeAlt` | 0x40 | int key `+0x20` → three qwords from `param_4` |
| `0x1401a2bd0` | 322 | `RbTreeStride64_ConstructNodeEscadraKey` | 0x40 | `EscadraName` `+0x20` (moved), `compareEscadraString` |
| `0x1401a2d20` | 303 | `RbTreeStride64_ConstructNodeEscadraKeyAlt` | 0x40 | `EscadraName` `+0x20` (`CopyEscadraName` deep copy) |
| `0x1400a15d0` | 252 | `RbTreeStride40_ConstructNode` | 0x28 | qword key `+0x20`, no value |
| `0x1401881a0` | 352 | `RbTreeStride40_ReassignKey` | 0x28 | int key `+0x1c` → int value `+0x20` |
| `0x140185a20` | 424 | `RbTreeStride40_ReassignKeyGuarded` | 0x28 | int key `+0x1c` → int value `+0x20` |
| `0x1401a6430` | 245 | `RbTreeStride48_ConstructNode` | 0x30 | qword key `+0x20` → qword `+0x28` (returns `&value`) |
| `0x1400e34c0` | 333 | `RbTreeStride72_ConstructNode` | 0x48 | `EscadraName` `+0x20` → int `+0x40` |
| `0x14012a330` | 333 | `RbTreeStride72_InsertRange` | 0x48 | header + range insert of 0x28-byte records |
| `0x14009c470` | 633 | `RbTreeStride104_ConstructNode` | 0x68 | `EscadraName` pair `+0x20/+0x40` → ptr `+0x60` |
| `0x14009c270` | 440 | `RbTreeStride104_EmplaceShader` | 0x68 | same key pair → `VShader*` `+0x60` |

Two names deliberately leave the four-suffix palette:

* `RbTreeStride72_InsertRange` (`0x14012a330`) is not a single-node helper: it
  allocates the header sentinel and then loops `RbTree_FindIntKey` + `New(0x48)` over
  a vector of 0x28-byte records — the `std::map(first,last)` constructor.
* `RbTreeStride40_ReassignKey` / `…Guarded` (`0x1401881a0`, `0x140185a20`) are inlined
  *operations on* a member map at `this+0x48` (header), not `_Tree` members: they walk
  the tree setting `value = -1` where `value == old`, lower-bound the new key, insert a
  node if absent, then store the mapping. Naming them `_ConstructNode` would hide the
  retarget pass; the stride and the node layout are still proved from the body.

Plate comments were set on all twelve, in the house style (title, summary,
`Algorithm:`, `Parameters:`, `Returns:`), one template per family with the member
stride and the exact `+offset` of key and value filled in.

## Skipped (6) — body disproves the classifier

| address | size | TSV family | why |
|---|---:|---|---|
| `0x1400560c0` | 584 | `…stride0x28_candidate` | node 0x28 confirmed (key `+0x1c`), but the same body also allocates a `0x38` list node, bumps the global `DAT_1403ef0e8` property id and fills a 0x20-byte `EscadraName` result — it is a global property/rect registration routine. Element type not provable; needs the `newProperty_` structures. |
| `0x140192050` | 505 | `…stride0x28_candidate` | node 0x28 is inserted into `std::map<int,int>` given in `in_R9`, but only after `displayHyperlinks_` parses a `key=value` string and after a vector-of-string teardown. The map op is a side effect of a hyperlink handler; no stable owner. |
| `0x140288590` | 686 | `…stride0x30_candidate` | node 0x30 confirmed (`key = *(obj+0x78)` → obj), but the body builds a temporary 0x30-node map from a `std::vector<T*>`, calls a virtual on matches, then `TreeNode_DestroyRecursive` + `free` the tree and both vectors. Full batch-dispatch routine, not a node helper. |
| `0x1402c8fd0` | 597 | `…stride0x30_candidate` | node 0x30 is inserted inside a scan over a missile/part vector that evaluates flag words (`+0x28`, `+0x2e0`, `+0x300…0x33c`) and sets `+0x33c = 4`. Domain logic; needs the missile/part field map. |
| `0x140221be0` | 653 | `…sort_helper_stride0x18_candidate` | **not a sort helper.** Allocates 0x18 list nodes `{prev,next,payload}` (+0x10 payload ptr) while walking a tree at `param_1+0x20`, sorts that list with `Sort_MedianOfNByStats`, then dispatches each element through vtable `+0x50`. The 0x18 "stride" is the `std::list` node, not an element. |
| `0x140224480` | 1481 | `…sort_helper_stride0x18_candidate` | **not a sort helper.** Same 0x18 list node; gathers a 20×30 lattice from `DAT_143a15b00` (row 0xdc, cell 0x2c), merge-sorts it ascending on `payload[0]` (`Sort_PartitionByFloat`, `<`), then fills three `VectorStride16` outputs. The comparator is *inlined* here, so there is no callable `SortStride24_Less` to name; the routine itself needs the lattice/light structures. |

Both `sort_helper` rows therefore carry a zero-length rename for this phase. The comparator
classifier is right about the ordering (ascending, `<`, float at element `+0`) but wrong about
the object: there is no standalone predicate in either body.

## Classifier corrections

1. **`0x14009c270` is a 0x68-byte node, not 0x40.** The `New(0x40)` that produced the
   `stride0x40` row allocates the `VShader` *value object* (`VShader_Constructor`); the
   tree node is `New(0x68)` with the same key/value shape as `0x14009c470`. It was moved
   into the `RbTreeStride104` family.
2. **`0x1401a2bd0` / `0x1401a2d20` / `0x1400e34c0` keys are `EscadraName`, not raw
   bytes** — `compareEscadraString` / `CopyEscadraName` and the 0x20-byte
   `{ptr, length, capacity}` triple at `+0x20` prove it.
3. **`0x1401a6430` is `map<uint64,uint64>::operator[]`** — it returns `node+0x28`
   unconditionally, including on the found path (no `pair<iter,bool>` out parameter).
4. The `stride0x30_candidate` label is right for both members that do allocate a node
   (`0x140288590`, `0x1402c8fd0`); only `0x1401a6430` is a pure helper.

## Tool notes

* `tools.ghidra.*` was absent again; everything went through
  `/tmp/opencode/hf_ghidra_sweep/call.py` (UDS) and a thin `p2c/api.py` wrapper.
* `decompile_function` and `get_function_by_address` take `address` as a **query**
  param, so `call.py GET <endpoint> '{"address":"0x…"}'` works while `POST` returns
  `{"error":"Address or function name is required"}`. `rename_function_by_address` /
  `set_plate_comment` take body params (`function_address` / `address`).
* `rename_function_by_address` answers HTTP 200 with
  `{"status":"success","message":"Success: Renamed …","warnings":[…]}`. The warnings are
  style lint only (they demand PascalCase and a verb prefix and therefore fire on every
  `RbTree_*`/`VectorStride*` name in this project); they are not failures. A rename
  checker must look at `status`, not at a substring match on "error" — the old
  `rep_…_tooLongError` names make a naive substring test report a false failure.
* One `run_script_inline` pass (81 instructions of `0x1400069a0`, hard `n < 130` cap) was
  used to confirm the node stores at the assembly level; every other proof is decompiler
  output. No unbounded loop was run and no script was left on the event thread.

## Counts for the blackboard

`sweep-2026-10-30-p2c: 18 rows in scope → 12 renamed + plated, 6 skipped (2 of them
proved to be non-sort domain routines). Layout header (+0/+8/+0x10/+0x18/+0x19) and value
at +0x20 proved in all 12. No save, no commit.`
