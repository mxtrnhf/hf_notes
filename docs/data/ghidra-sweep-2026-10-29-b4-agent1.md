# Unnamed-function sweep, 2026-10-29 — batch 4 agent 1

Range: `0x140330000–0x14033FFFF` on `Highfleet.exe.unpacked.exe` v1.163
(project `HighfleetServer`). 479 function objects in range at the end of the
pass (477 before, +2 created). Every rename below was made with
`rename_function_by_address`-equivalent semantics (script `Function.setName`,
USER_DEFINED) plus a doc-style plate comment. `create_function` was used for
two vtable slots that had no function object (batch-4 exception).

Counts: **16 renamed, 2 created + plated, 323 still unnamed** — 306 C++ EH
cleanup funclets in `0x140336700–0x14033FFFF` and 17 CRT / import-thunk
leftovers, all recorded below. A third `create_function` target (0x1403198c0)
is outside the range and was left.

Stock reference used for the Box2D naming decisions: Box2D **2.3.1**
`Box2D/Box2D/Collision/b2CollideEdge.cpp`, `b2CollidePolygon.cpp`, and the
2.3.1 contact classes (`b2CircleContact`, `b2PolygonAndCircleContact`,
`b2PolygonContact`, `b2EdgeAndCircleContact`, `b2EdgeAndPolygonContact`,
`b2ChainAndCircleContact`, `b2ChainAndPolygonContact`). The embedded engine is
2.3.1-shaped (the edge/polygon path here is the `b2EPCollider` class, which
2.4 removed).

## Contact vtables and their Evaluate slots

Each contact vtable in this build is exactly two entries
`[0] = Evaluate, [1] = scalar deleting destructor`; the destructor is ICF
merged to `0x140325a40` for all seven classes. The factories
(`b2*Contact_Create`, see `box2d-function-map.md`) install these tables, and
`b2Contact_DestroyAllocated200` 0x140330a10 calls slot [1].

| vtable | class | Evaluate slot | new name |
|---|---|---|---|
| 0x140378e40 | circle/circle | 0x140330a50 | `b2CircleContact_Evaluate` |
| 0x140378e50 | polygon/circle | 0x140330ae0 | `b2PolygonAndCircleContact_Evaluate` |
| 0x140378e60 | polygon/polygon | 0x140330b70 | `b2PolygonContact_Evaluate` |
| 0x140378e70 | edge/circle | 0x140330c00 | `b2EdgeAndCircleContact_Evaluate` |
| 0x140378e80 | edge/polygon | 0x140330c90 | `b2EdgeAndPolygonContact_Evaluate` |
| 0x140378e90 | chain/circle | 0x140330d70 | already `b2ChainAndCircleContact_Update` |
| 0x140378ed8 | chain/polygon | 0x140330e90 | already `b2ChainAndPolygonContact_Update` |

Every one of the five new ones is a 44-byte forwarder: it reads
`fixtureA+0x18` / `fixtureB+0x18` (fixtures at contact `+0x60` / `+0x68`) and
calls the corresponding narrowphase:
`b2CollideCircles` 0x140330f30, `b2CollidePolygonAndCircle` 0x140331050,
`b2CollidePolygons` 0x140331450, `b2CollideEdgeAndCircle` 0x1403336e0,
`b2CollideEdgeAndPolygon` 0x140333a90.

**Correction / clarification for `box2d-function-map.md`:** the two chain slots
that batch 2 named `b2ChainAndCircleContact_Update` / `..._Polygon..._Update`
are the *Evaluate* virtual, not a separate `Update` method (this build has no
`b2Contact::Update`, as stock 2.3.1 has none either). The names are harmless,
but the role is `Evaluate`. Not renamed here (already named).

## Edge/polygon narrowphase (new names)

| addr | new name | notes |
|---|---|---|
| 0x1403336e0 | `b2CollideEdgeAndCircle` | stock 2.3.1 b2CollideEdgeAndCircle: circle into edge frame, vertex A / vertex B / interior regions, `hasVertex0`/`hasVertex3` adjacency rejects, one manifold point, pointCount at manifold+0x3c |
| 0x140333a90 | `b2CollideEdgeAndPolygon` | 86-byte wrapper: 0x100-byte `b2EPCollider` on the stack + `b2EPCollider_Collide` |
| 0x1403322d0 | `b2EPCollider_Collide` | 4700 bytes, stock 2.3.1 `b2EPCollider::Collide`. Fills the collider: m_polygonB vertices 0x00 / normals 0x40 / count 0x80, m_xf 0x84, m_centroidB 0x94, m_v0..v3 0x9c/0xa4/0xac/0xb4, m_normal0/1/2 0xbc/0xc4/0xcc, m_normal 0xd4, m_type1/2 0xdc/0xe0, m_lowerLimit 0xe4, m_upperLimit 0xec, m_radius 0xf4 = 0.02, m_front 0xf8. Calls ComputeEdgeSeparation, inlines ComputePolygonSeparation, 0.98/0.001 hysteresis, `b2ClipSegmentToLine` 0x140318830, at most 2 manifold points |
| 0x140333530 | `b2EPCollider_ComputeEdgeSeparation` | writes `b2EPAxis {type=e_edgeA, index=m_front?0:1, separation=min dot(m_normal, polygonB.v[i]-m_v1)}` |
| 0x1403319c0 | `b2PolygonEdgeSeparation` | per-edge separation of poly2 against one edge of poly1; used **four** times by `b2FindMaxSeparation` 0x140331f70 |

### `b2FindMaxSeparation` in this build is not stock

`0x140331f70` (already named `b2FindMaxSeparation` by batch 2, confirmed: its
only callers are the two calls in `b2CollidePolygons` 0x140331450 at
0x1403314ae / 0x1403314db) does **not** scan every edge of poly1 the way stock
2.3.1/2.4.1 do. It seeds the search at the poly1 edge whose normal is most
anti-parallel to the poly1→poly2 centre delta, then hill-climbs with
`b2PolygonEdgeSeparation` over the neighbouring edge indices. The result is the
same quantity (max separation + edge index), so the old name is still right,
but a reader comparing against the stock source should not expect the stock
loop. Worth a sentence in `box2d-function-map.md` if anyone revisits it.

## b2EdgeShape vtable (0x140378ea0)

Seven slots; `b2EdgeShape` type field = 1 and default radius 0.01, size 0x38
(confirmed by `Clone`). Slot [2] `GetChildCount` is a 6-byte
`mov eax,1; ret` at **0x1403198c0, which is outside this agent's range and has
no function object** — left for whoever owns `0x140319xxx` (do not assume it is
edge-specific: it is an ICF-merged `return 1` shared by every 1-child shape).
Slot [3] `TestPoint` pointed at a 3-byte `xor al,al; ret` with no function
object, and slot [6] `ComputeMass` had none either; both were created here.

| slot | addr | new name | notes |
|---|---|---|---|
| [0] dtor | 0x140330cc0 | `b2EdgeShape_DeletingDtor` | stores the b2Shape vtable 0x140352998 (= `b2Shape_ScalarDeletingDestructorB`) then frees 0x38 |
| [1] Clone | 0x140333b80 | `b2EdgeShape_Clone` | alloc 0x38, vtable 0x140378ea0, type 1, radius 0x3c23d70a (0.01), copies v1/v2/v0/v3 + hasVertex0/3 |
| [2] GetChildCount | 0x1403198c0 | *not created — out of range* | `mov eax,1; ret` |
| [3] TestPoint | 0x140333f90 | `b2EdgeShape_TestPoint` | **created** here; 3-byte `return false` stub, ICF-shared |
| [4] RayCast | 0x140333d50 | `b2EdgeShape_RayCast` | ray vs the radius-inflated segment; out+0 normal, out+4 fraction |
| [5] ComputeAABB | 0x140333c10 | `b2EdgeShape_ComputeAABB` | min/max of the two transformed vertices ± radius |
| [6] ComputeMass | 0x140333d10 | `b2EdgeShape_ComputeMass` | **created** here; mass 0, centre = midpoint, I 0 |

Created with `create_function`, then named and plated:
`b2EdgeShape_ComputeMass` 0x140333d10 (54 bytes),
`b2EdgeShape_TestPoint` 0x140333f90 (3 bytes).
A third `create_function` was attempted for 0x1403198c0 and deliberately not
done (range).

## Misc / CRT (one rename)

| addr | new name | notes |
|---|---|---|
| 0x140334e50 | `StdBadAlloc_Ctor` | sets message pointer to the literal "bad allocation" (len 0) and the std::exception vtable 0x1403522b8; feeds `badAllocationException` 0x140334e70 |

## Skipped and recorded (do not re-file these as "missed")

### 1. C++ EH cleanup funclets — the bulk of the range

`0x140336730–0x14033FFB0` (plus 0x140336b00/0x140336b20) is **306** unnamed
function objects, every one a compiler-generated `/EH` destructor/unwind
cleanup helper of the shape

```
void f(void* unused1, Frame* frame)        // 29-93 bytes
{
    if ((frame->flags_at_X & MASK) != 0) { frame->flags_at_X &= ~MASK;
                                           String_Tidy(&frame->obj + OFF); }   // or
    free(frame->ptr_at_OFF);                                                    // or
    DeleteArrayNN(frame->ptr_at_OFF); _CxxThrowException(0,0);                  // or
    DestroyRangeNN(...); deallocate(...); _CxxThrowException(0,0);
}
```

They are distinguished only by the destroyed member's byte offset into the
enclosing frame object and by the destroying callee, so the owning class is not
recoverable from the body; naming ~300 of them individually would be noise.
Grouped inventory (count, first, last → destroying callee, first member offset
seen in the body):

| n | first | last | callee | member off |
|---|---|---|---|---|
| 24 | 0x140337e80 | 0x14033cc30 | String_Tidy | 20 |
| 4 | 0x140338c30 | 0x14033e150 | String_Tidy | 30 |
| 2 | 0x140338df0 | 0x140338e20 | String_Tidy | 38 |
| 2 | 0x14033ddf0 | 0x14033de20 | String_Tidy | 60 |
| 1 | 0x140338ab0 | — | String_Tidy | 64 |
| 7 | 0x1403375d0 | 0x14033c480 | String_Tidy | 68 |
| 1 | 0x140338a70 | — | String_Tidy | 6c |
| 2 | 0x14033e060 | 0x14033e090 | String_Tidy | 70 |
| 28 | 0x14033b9c0 | 0x14033bfd0 | String_Tidy | 74 |
| 21 | 0x140338b40 | 0x14033f960 | String_Tidy | 80 |
| 1 | 0x14033ff80 | — | String_Tidy | 88 |
| 1 | 0x14033dfd0 | — | String_Tidy | 90 |
| 6 | 0x14033a290 | 0x14033b250 | String_Tidy | 98 |
| 1 | 0x14033dda0 | — | String_Tidy | 9c |
| 6 | 0x14033c010 | 0x14033c120 | String_Tidy | c8 |
| 5 | 0x140337420 | 0x14033d8e0 | free | 20 |
| 19 | 0x1403374a0 | 0x14033d620 | free | 30 |
| 7 | 0x1403377a0 | 0x14033d640 | free | 38 |
| 8 | 0x140339260 | 0x14033e4b0 | free | 40 |
| 4 | 0x140336b00 | 0x140337ad0 | free | 48 |
| 2 | 0x140337400 | 0x140337af0 | free | 50 |
| 4 | 0x140338ce0 | 0x14033ec50 | free | 58 |
| 17 | 0x140337440 | 0x14033c7b0 | free | 60 |
| 5 | 0x1403376e0 | 0x14033df90 | free | 68 |
| 5 | 0x1403374c0 | 0x14033f6a0 | free | 70 |
| 2 | 0x1403376c0 | 0x14033feb0 | free | 78 |
| 1 | 0x1403375a0 | — | free | 80 |
| 3 | 0x14033d500 | 0x14033e4e0 | free | 88 |
| 2 | 0x140337810 | 0x1403378f0 | free | 90 |
| 2 | 0x140337b50 | 0x14033e000 | free | 98 |
| 1 | 0x1403372d0 | — | free | a0 |
| 3 | 0x14033c600 | 0x14033dbd0 | free | a8 |
| 1 | 0x14033db70 | — | free | c0 |
| 1 | 0x140337a10 | — | free | c8 |
| 1 | 0x14033c6c0 | — | free | d8 |
| 3 | 0x140338a10 | 0x14033e510 | free | e0 |
| 5 | 0x14033f840 | 0x14033fe70 | free | 11f0 |
| 1 | 0x140337950 | — | free | 138 |
| 1 | 0x14033d800 | — | free | 148 |
| 1 | 0x14033c850 | — | free | 198 |
| 1 | 0x1403379e0 | — | free | 1d0 |
| 1 | 0x14033cb80 | — | free | 1e8 |
| 1 | 0x14033a810 | — | free | 218 |
| 1 | 0x14033abd0 | — | free | 2d0 |
| 1 | 0x140337fa0 | — | free | 300 |
| 1 | 0x14033ad20 | — | free | 318 |
| 1 | 0x14033ad50 | — | free | 320 |
| 1 | 0x14033ad80 | — | free | 328 |
| 1 | 0x14033adc0 | — | free | 330 |
| 1 | 0x14033ae10 | — | free | 340 |
| 1 | 0x14033aea0 | — | free | 378 |
| 1 | 0x14033aef0 | — | free | 388 |
| 1 | 0x14033af20 | — | free | 390 |
| 1 | 0x14033aff0 | — | free | 3c0 |
| 1 | 0x14033b020 | — | free | 3c8 |
| 1 | 0x14033b140 | — | free | 410 |
| 1 | 0x14033b070 | — | free | 458 |
| 13 | 0x140336e30 | 0x14033e310 | deallocate + _CxxThrowException | 10 |
| 4 | 0x140336880 | 0x14033cd50 | deallocate + _CxxThrowException | 10 |
| 2 | 0x140336e70 | 0x14033cdc0 | _CxxThrowException only | 10 |
| 5 | 0x140336ea0 | 0x14033cdf0 | memmove + _CxxThrowException | 10 |
| 4 | 0x140336850 | 0x14033cce0 | DeleteArray32 + throw | 10 |
| 2 | 0x1403368e0 | 0x140336dc0 | DeleteArray16 + throw | 10 |
| 2 | 0x140336d20 | 0x1403380c0 | DeleteArray56 + throw | 10 |
| 1 | 0x140336df0 | — | DeleteArray32 + FUN_1400199b0 + throw | 10 |
| 1 | 0x140339700 | — | DeleteArray56 + FUN_1400199d0 + throw | 10 |
| 1 | 0x140336730 | — | Link_DestroyRange + deallocate + throw | 10 |
| 1 | 0x140336c80 | — | Array_DestroyRange24 + deallocate + throw | 10 |
| 1 | 0x140338110 | — | Array_DestroyRange48 + deallocate + throw | 10 |
| 1 | 0x14033e350 | — | Array_DestroyRange24 + FUN_1400199d0 + throw | 10 |
| 2 | 0x14033e240 | 0x14033e2c0 | Array_FreeStride24 + deallocate + throw | 10 |
| 1 | 0x14033e650 | — | Array_DestroyRange88 + Array_FreeStride88 + throw | 10 |
| 1 | 0x140339a20 | — | StringPairVector_DestroyRange + free + throw | 10 |
| 1 | 0x14033cea0 | — | FUN_1400199d0 + FUN_1400e85a0 + deallocate + throw | 10 |
| 1 | 0x14033e600 | — | FUN_14015c1c0 + deallocate + throw | 10 |
| 1 | 0x1403393e0 / 0x1403394e0 / 0x140339550 / 0x140339750 / 0x140339800 / 0x1403398b0 | — | FUN_1400199d0 + throw + a per-body `free` copy | 10 |
| 1 | 0x14033f2a0 | — | `eh_vector_destructor_iterator` | e0 |
| 9 | 0x140337ba0 … 0x1403378c0 | — | freeLinkMemory? (Link cleanup) | 74-90 |
| 4 | 0x14033dea0 / 0x14033deb0 / 0x14033df00 / 0x14033df30 | — | freeLinkMemory? | 158 |
| 1 | 0x14033dab0 | — | freeLinkMemory? | 128 |
| 1 | 0x14033dd30 | — | freeLinkMemory? | 170 |
| 2 | 0x14033c700 / 0x14033c730 | — | freeLinkMemory? | 1d8 |
| 2 | 0x14033e0c0 / 0x14033e0f0 | — | freeLinkMemory? | 24 |
| 1 | 0x14033de50 | — | freeLinkMemory? | 68 |
| 2 | 0x14033b3e0 / 0x14033b5a0 | — | freeLinkMemory? | 74 |
| 1 | 0x14033f6f0 | — | freeLinkMemory? | 80 |
| 3 | 0x14033fee0 / 0x14033ff20 / 0x14033ffb0 | — | freeLinkMemory? | 88 |
| 1 | 0x1403378c0 | — | freeLinkMemory? | 90 |
| 1 | 0x140337ef0 | — | freeLinkMemory? | b8 |
| 2 | 0x14033f9b0 / 0x14033fa30 | — | FUN_14005e560 | 80 |
| 1 | 0x14033f9f0 | — | FUN_14005e6b0 | 80 |
| 1 | 0x140336c40 | — | basic_ios::setstate wrapper | 10 |
| 1 | 0x140339100 | — | `~basic_ios<char>` | 40 |

(Group boundaries above are the size+callee signature; the same funclet shape
repeats at many offsets, so this is a shape census, not a class list.)

### 2. CRT / scrt leftovers (not Box2D, not game logic)

Left unnamed on purpose; all are MSVC 14.x boilerplate that wave 3 already
covered or that names no class:

* 0x1403340d8 — scalar deleting destructor of a small std class, vtable
  0x140378f08 (also written by 0x140018bd0-style bodies); class not provable.
* 0x140334e00 — the SSE2 `sin`/`cos` table helper already flagged in
  `box2d-function-map.md` ("not b2Rot::Set"); 2^-13 table fraction, tail-calls
  `__sse2_sinf4`.
* 0x14033503c, 0x140335050 (zeroes `_DAT_1480771ec`), 0x140335354,
  0x14033536c (sets flag bits in two scrt globals), 0x140335388, 0x140335394,
  0x14033539c — 6-27 byte `__scrt_*` accessors/initialisers.
* 0x140336c40 / 0x140339100 — `basic_ios<char>` setstate / destructor
  funclets (already listed in the funclet table above).

### 3. Import-thunk island inside the range

`0x140333F93–0x1403365FF` (and the tail at 0x140336594–0x1403366FF) is a run of
6-byte `jmp qword ptr [rip+disp]` import thunks whose symbols are the
`D3D11CreateDeviceAndSwapChain`, `SDL_*`, `_Xlength_error`, `memmove`, … names
already in the program. They are **not** functions and were not touched.

**One address to remember:** `0x1403365AC` is one of these thunks (no function
object) yet it appears as a slot in ~25 data tables in `0x140356xxx–0x140378xxx`
(pure-virtual-shaped vtables). Do not read those tables as evidence of a class
method; they are unresolved import thunks.

## Open questions / hand-off

1. `0x1403198C0` (`b2EdgeShape` vtable slot [2] GetChildCount, 6 bytes
   `mov eax,1; ret`) needs `create_function` + a name, but it is **outside
   0x140330000–0x14033FFFF**. Proposed: `b2Shape_GetChildCountOne` (it is
   ICF-shared by every single-child shape, not edge-specific). Whoever owns
   `0x140319xxx` should take it.
2. `b2FindMaxSeparation` 0x140331f70 is a locally optimised variant (centre
   seed + hill climb via 0x1403319c0), not the stock full scan. If the parent
   wants a "this build differs from stock 2.3.1" section, this belongs in it.
3. Batch 2's `_Update` names for the two chain contact vtable slots are really
   the `Evaluate` virtual. Left as-is; flagging for the function map only.
