# Unnamed-function sweep, 2026-10-29 — agent 3

Ranges: `0x140070000–0x14011FFFF` (engine / render / audio / resources, map and
fleet data) and `0x140300000–0x140350510` (physics glue + embedded Box2D).

Program `Highfleet.exe.unpacked.exe` v1.163. Every entry was renamed with
`rename_function_by_address` and given a doc-style plate comment. Names follow
the conventions in `ghidra-changes-2026-10-29.md`: `b2<Class>_<Method>` for the
embedded Box2D, `<Subsystem>_<Verb><Object>` for game code, and `String_` /
`Vector` / `Array_` prefixes for the std/CRT-shaped helpers.

## Renames — Box2D (`0x140300000–0x140350510`)

| addr | new name | description |
|---|---|---|
| 0x14031bf90 | `b2RevoluteJoint_Dump` | writes the revolute joint as a `b2RevoluteJointDef` snippet |
| 0x14031c200 | `b2RevoluteJoint_GetJointAngle` | bodyB.a - bodyA.a - referenceAngle |
| 0x14031d520 | `b2DistanceJoint_Dump` | writes the distance joint as a `b2DistanceJointDef` snippet |
| 0x14031e390 | `b2WeldJoint_Dump` | writes the weld joint as a `b2WeldJointDef` snippet |

## Renames — engine (`0x140070000–0x14011FFFF`)

| addr | new name | description |
|---|---|---|

## Skipped / open

(none yet)

## Renames — Box2D, continued (distance / TOI / joints / fixture / broadphase)

| addr | new name | description |
|---|---|---|
| 0x14031f4e0 | `b2Simplex_GetMetric` | simplex metric: length for 2 vertices, 2*area for 3 |
| 0x14031f560 | `b2Simplex_ReadCache` | rebuilds a simplex from a cache and rejects a stale cache |
| 0x14031f7c0 | `b2DistanceProxy_Set` | proxy from shape + child index (circle/edge/polygon/chain) |
| 0x14031f890 | `b2Simplex_Solve` | GJK Voronoi-region solve, reduces the simplex to 1-3 vertices |
| 0x140320b00 | `b2Fixture_Construct` | zeroes a fixture, default filter category 1 / mask 0xffff |
| 0x140320c10 | `b2Fixture_CreateProxies` | one broad-phase proxy per shape child |
| 0x140321560 | `b2SortSwap3Pairs` | sorts three 12-byte pair records with a comparator |
| 0x140321620 | `b2SortPairs` | three-way quicksort over the broad-phase pair buffer |
| 0x140323750 | `b2BroadPhase_Construct` | zeroes the broad phase, allocates move and pair buffers |
| 0x140324a20 | `b2PulleyJoint_Ctor` | pulley joint constructor, constant = lengthA + ratio*lengthB |
| 0x140324af0 | `b2PulleyJoint_Dump` | writes a `b2PulleyJointDef` snippet |
| 0x1403252d0 | `b2PulleyJoint_SolvePositionConstraints` | pulley position solver |
| 0x140325750 | `b2PulleyJoint_SolveVelocityConstraints` | pulley velocity solver |
| 0x140325f10 | `b2SeparationFunction_Evaluate` | separation at a given interpolation time |
| 0x1403262f0 | `b2SeparationFunction_FindMinSeparation` | min-separation support pair |
| 0x140326a10 | `b2SeparationFunction_Initialize` | builds/ normalises the TOI separation axis |
| 0x140326880 | `b2DistanceProxy_GetSupport` | vertex index with max dot product |
| 0x140326fe0 | `b2Vec2_Normalize` | normalise in place, return old length |
| 0x140327030 | `b2TimeOfImpact` | conservative-advancement TOI for one swept pair |
| 0x14032a8f0 | `b2WheelJoint_Ctor` | wheel joint constructor |
| 0x14032a9d0 | `b2WheelJoint_Dump` | writes a `b2WheelJointDef` snippet |
| 0x14032ac60 | `b2WheelJoint_InitVelocityConstraints` | wheel joint frames and mass terms |
| 0x14032b350 | `b2WheelJoint_SolvePositionConstraints` | wheel joint position solver |
| 0x14032ba60 | `b2MouseJoint_Ctor` | mouse joint constructor |
| 0x14032bf60 | `b2MouseJoint_SolveVelocityConstraints` | mouse joint velocity solver |

## Renames — Box2D, contacts and shapes

| addr | new name | description |
|---|---|---|
| 0x140318e80 | `b2PolygonShape_ComputeCentroid` | area-weighted polygon centroid |
| 0x140319180 | `b2PolygonShape_ComputeMass` | mass, centre and inertia for a density |
| 0x1403198d0 | `b2PolygonShape_RayCast` | ray vs convex polygon, clipping fractions |
| 0x140319e80 | `b2Body_DestroyFixture` | unlink fixture, destroy its contacts, free proxies, reset mass |
| 0x140330a10 | `b2Contact_DestroyAllocated200` | shared contact destructor + 200-byte free |
| 0x140330ba0 | `b2EdgeAndCircleContact_Create` | edge/circle contact factory |
| 0x140330c30 | `b2EdgeAndPolygonContact_Create` | edge/polygon contact factory |
| 0x140330cf0 | `b2ChainAndCircleContact_Create` | chain/circle contact factory |
| 0x140330e10 | `b2ChainAndPolygonContact_Create` | chain/polygon contact factory |

## Renames — Box2D, remaining joint solvers

| addr | new name | description |
|---|---|---|
| 0x14032dcb0 | `b2GearJoint_Dump` | writes a `b2GearJointDef` snippet |
| 0x14032de80 | `b2GearJoint_InitVelocityConstraints` | gear joint frames and mass term |
| 0x14032e790 | `b2GearJoint_SolvePositionConstraints` | gear equation position solver |
| 0x14032f060 | `b2GearJoint_SolveVelocityConstraints` | gear equation velocity solver |
| 0x14032f4b0 | `b2FrictionJoint_Dump` | writes a `b2FrictionJointDef` snippet |
| 0x14032f5c0 | `b2FrictionJoint_InitVelocityConstraints` | friction joint frames and mass terms |
| 0x14032fa60 | `b2FrictionJoint_SolveVelocityConstraints` | friction impulse clamped to force/torque * dt |
| 0x14032ff70 | `b2RopeJoint_InitVelocityConstraints` | rope joint frames and mass term |
| 0x140330780 | `b2RopeJoint_SolveVelocityConstraints` | rope impulse, non-positive clamp, predictive bias |
| 0x140330460 | `b2RopeJoint_SolvePositionConstraints` | distance limited to maxLength |

## Renames — Box2D, contact updates and joint base destructor copies

| addr | new name | description |
|---|---|---|
| 0x140330d70 | `b2ChainAndCircleContact_Update` | chain child edge -> circle narrowphase |
| 0x140330e90 | `b2ChainAndPolygonContact_Update` | chain child edge -> polygon narrowphase |
| 0x14031bf20 | `b2Joint_DeletingDtor` | base-joint deleting destructor, copy 1 |
| 0x14031bf50 | `b2Joint_DeletingDtorCopy2` | base-joint deleting destructor, copy 2 (shared by wheel/friction vtables) |
| 0x140324ac0 | `b2Joint_DeletingDtorCopy3` | base-joint deleting destructor, copy 3 (pulley vtable) |

## Renames — engine (`0x140070000–0x14011FFFF`)

| addr | new name | description |
|---|---|---|
| 0x1400733f0 | `Creature_IsPlayerCreature` | creature pointer matches one of the profile's player slots |
| 0x1400734e0 | `Creature_HasTitanName` | std::string at +0xa90 equals "Titan" |
| 0x140315fc0 | `Vector_Resize40` | resize a vector of 0x28-byte elements |

## Skipped / open

Everything below was looked at and deliberately **not** named.

### Box2D
* **`0x140321930`** - sift-down over 12-byte records with a comparator (a
  `std::_Adjust_heap`-shaped helper for `b2Pair`); its only caller is a
  `memmove` wrapper, so the owning container is not clear.
* **`0x140319da0`** - empty stub (`return;`) called from `b2World_DestroyBody`
  and the world destructor; cannot tell which listener slot it stands in for.
* **`0x140318b20`** - 4.2 KB geometry routine over a vertex array; not read to
  the end, no anchor in the notes.
* **`0x140330cc0`** - deleting destructor whose vtable (0x140352998) is in the
  game area, not one of the contact vtables; class unknown.
* Functions that are **vtable slots but not defined in Ghidra** (no
  `FUN_` symbol exists, so nothing to rename): `0x14032b6c0`
  (`b2WheelJoint_SolveVelocityConstraints`), `0x14032dde0`/`0x14032de30`/
  `0x14032de60` (gear dtor/GetAnchorA/GetAnchorB), `0x140324c70`/`0x140324cc0`/
  `0x140324d10`/`0x140324d40` (pulley virtuals), `0x14032abe0`-area wheel
  Get* methods, `0x14032bb60`/`0x14032bb70`/`0x14032bbc0`/`0x14032bbe0`
  (mouse joint virtuals), `0x14032bf50` (friction SolvePos). The parent may want
  to `create_function` at those addresses in a later pass; the plate text for
  the ones I did not create is in this note's reasoning only, so I did not
  invent names for them.

### Engine
* **Factory block `0x140086000–0x14009B000`** - not touched at all, per the
  brief: the derived class of each `FUN_14009f9xx`/`FUN_14009faxx` constructor
  cannot be recovered from the three-line `New`/ctor/`push_back` wrapper.
* **`0x1400f3860`, `0x1400f48c0`, `0x1400f4a20`** (`Escadra.cpp`) - three
  lazy HGE-texture creators: each fills a per-index texture at +0x268/+0x278
  (0x100x0x80) or +0x248/+0x258 (0x100x0x100) and then creates an object with
  `CreateHGE`. Which Escadra visual each slot is (card? icon? silhouette?) is
  not readable from the code, so they are left unnamed.
* **`0x140073450`, `0x1400734a0`, `0x140070620`, `0x1400702a0`** - small
  Creature accessors (name==Titan-or-flag, Zenith list size > 5, fuel fraction
  times a coefficient, sum of four floats at +0x15e8..+0x15f4). The arithmetic
  is clear but the semantic name is not, so they are left for an agent with
  `structures.md` at hand.
* **`0x1400743c0`, `0x140077840`** - serialisable-property registration
  (`addProperty("massXP", ...)`, `addProperty("design", ...)`); the owning
  class (Body vs Part) is ambiguous.
* **`0x1403169c0`, `0x140316a50`, `0x140316ba0`, `0x140316d00`,
  `0x140309d70`, `0x140110340`** - engine/render settings and per-frame
  update helpers driven by `graphicsQuality` / HGE calls. Identifiable only as
  a group; the individual names would be guesses.
* The remaining ~1,750 unnamed functions in `0x140070000–0x14011FFFF` are
  either the factory block, per-class serialisation boilerplate
  (`Property::Property`, `ISerializable::ISerializable` copies), or
  Creature/Escadra logic that needs the structure notes; not attempted.
