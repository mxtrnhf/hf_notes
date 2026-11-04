# Ghidra unnamed-function sweep, 2026-10-29 — agent 1

Range: `0x140005000`–`0x14001ffff` (aircraft, projectiles/explosions, link/vector/ship
helpers, alloc/container helpers). Program `Highfleet.exe.unpacked.exe` v1.163,
project `HighfleetServer`. Every entry below was read from the decompiler and/or
its call sites. Plate comments were added in the same pass.

## Renames

| addr | new name | description |
|---|---|---|
| 0x140005160 | `Exception_CopyConstructA` | copy-constructs a `std::exception`-derived object (vtable variant A) |
| 0x1400051a0 | `Exception_CopyConstructB` | same for the second vtable variant |
| 0x140005620 | `ThrowBadArrayLengthException` | raises `std::bad_array_new_length` (was already plated) |
| 0x140005640 | `Link_CopyRange` | copy-constructs a range of `Link` into raw storage |
| 0x140006b00 | `RbTree_CreateHeader` | allocates and self-links an empty red-black-tree header |
| 0x140007d00 | `AllocateArrayOf8Byte` | `operator new[]` for 8-byte elements (was already plated) |
| 0x14000a360 | `Aircraft_CollectActiveCraft` | collects non-parked aircraft from the scene tree into a vector |
| 0x14000c750 | `AircraftLogic_Mode5_Egress` | mode-5 (egress) per-frame behaviour and state transitions |
| 0x140011130 | `AITask_ScalarDeletingDestructor` | scalar deleting destructor of the `AITask` singleton |
| 0x140011570 | `String_ConcatStringCStr` | `string + const char*` |
| 0x140011710 | `String_ConcatCStrString` | `const char* + string` |
| 0x140011e20 | `Vector16_InsertReallocate` | grow a 16-byte-element vector and insert one element |
| 0x140012e20 | `RbTree_DestroySubtree` | recursive subtree free (right first) |
| 0x140012e80 | `RbTree_DestroySubtreeB` | identical body, second node-type instantiation |
| 0x140012ee0 | `Snap_LowerBoundKey` | `lower_bound` on the snap map's float-pair key |
| 0x140012f90 | `Sort3MedianFloat16` | median-of-three ordering for 16-byte records keyed at +8 |
| 0x140013ec0 | `Sort16_PartitionFloat` | introsort partition step for 16-byte records |
| 0x140014ea0 | `VectorString56_MoveRange` | move-construct a range of 0x38-byte string records |
| 0x140014f30 | `Vector24_PushBackZero` | append a zeroed 0x18-byte element |
| 0x140014f60 | `Vector16_PushBack` | append a 16-byte element |
| 0x140014f90 | `VectorString56_PushBack` | append a 0x38-byte record that starts with a string |
| 0x140015170 | `RbTree_InsertLinkByFloatPair` | insert a `Link` into the map keyed by two floats |
| 0x140015300 | `Sort16_Introsort` | sort 16-byte records by their float key |
| 0x140015320 | `Array_TransformBytes` | map a byte range through a callable |
| 0x140016ea0 | `Physics_MakeContactRecord` | build the fixed contact record used by the physics callback |
| 0x140017180 | `RbTree_ClearFreeHeader` | clear all nodes and free the tree header |
| 0x140017c30 | `List_FreeAllNodes28` | free the singly linked list rooted at object+0x28 |
| 0x1400189c0 | `Snap_KeyLess` | epsilon comparison of two snap keys |
| 0x140018c40 | `b2Body_ApplyLinearImpulse` | Box2D `b2Body::ApplyLinearImpulse` |
| 0x140019500 | `b2Body_SetAwake` | Box2D `b2Body::SetAwake` |
| 0x140019a20 | `Vector24_MoveRange` | move-construct a range of 0x18-byte elements |
| 0x14001c0d0 | `Body_ApplyAcceleration` | turns an acceleration into a mass-scaled force |
| 0x14001c2e0 | `String_Data` | `std::string::data()` (SSO-aware) |
| 0x14001c890 | `Cluster_SpawnRocketBomblets` | cluster-rocket bomblet spawner (kind 190, TTL from arg 6) |

## Skipped / open

| addr | why |
|---|---|
| 0x14000ad80 | 10-byte predicate returning `*(int*)(+0x190) != 0`; called from `Projectile_DetonateOnImpulse` on the `MDL_FIGHTER_01` target. `+0x190` is the aircraft state on an AircraftLogic but `m_oid` data on a Body, so the receiver type is ambiguous. |
| 0x140017d10 | virtual thunk: loads `*(*(*obj)+4)+0x48+*obj` and calls slot +0x10. No callers, only vtable data; cannot name without the class. |
| 0x140018ba0, 0x140018bd0 | two identical scalar deleting destructors (vtable `0x140352998`), compiler-generated duplicates. |
| 0x140019310, 0x140019380 | paired virtual methods referenced from five vtables (set/clear +0x13c, call slots +0x290/+0x280/+0x298, reset the frame counter); looks like a start/stop pair on a common app-state base, but the base class is not identified. |
| 0x140019990, 0x1400199b0 | argument-shuffling thunks forwarding to `_invalid_parameter_noinfo_noreturn` / `free`; compiler allocator boilerplate. |
| 0x1400199d0 | 3-byte `return param_1` — no-op deleter. |
| `rep_*` functions in range | already carry real (if stale) names from the 1.151 pass, e.g. `rep_140004e70_GetStats`, `rep_1400094a0_Get_Profile?`, `rep_14001a530_LoadParticle?`. Left untouched per ground rule 2. |

## Notes for the next agent

* `AircraftLogic_Update` (0x14000b370) dispatches on `logic+0x118` (mode) to the
  handlers; **mode 5 is 0x14000c750** (now `AircraftLogic_Mode5_Egress`), mode 4 is
  an inline leave path.
* `0x14001c890` (now `Cluster_SpawnRocketBomblets`) is the "different spawner" from
  `findings/cluster-bomblet-ttl.md` (TTL = arg6 * rand(0.5,1.0)).
* `0x140018c40` / `0x140019500` are the game-side copies of Box2D
  `ApplyLinearImpulse` / `SetAwake` — the `b2Body` layout from
  `findings/box2d-struct-layouts.md` matches exactly.
* Names `NewArray8` and `ThrowBadArrayNewLength` from the parent's first-pass note
  were **rejected by the rename tool** (token-subset collision with `New`); they
  are now `AllocateArrayOf8Byte` / `ThrowBadArrayLengthException`.
