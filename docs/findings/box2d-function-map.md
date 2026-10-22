# Box2D and flight-input function map: names applied in Ghidra, what was checked (ghidra-curator, 2026-10-22)

Tags: **[V]** decompile read by the curator after the rename, **[A]** proposed by a helper agent (Haiku), agreed by two agents or confirmed through a vtable read, but the body not read by the curator, **[open]**. The embedded engine is stock-shaped Box2D 2.3 (lengths x 0.05, see `Body_SyncFromB2`). Names follow the `b2Class_Method` pattern used by the existing `b2World_Step`, `b2Island_Solve`.

## World, island, memory
| Address | Name | Tag | Notes |
|---|---|---|---|
| 0x1403226f0 | `b2StackAllocator_Allocate` | V | stack 0x19000 bytes, entry count +0x19210, malloc fallback |
| 0x140322790 | `b2StackAllocator_Free` | V | was labelled `rep_1402f77a0...free` |
| 0x1403239b0 / 0x140323a60 | `b2Island_Construct` / `b2Island_Destruct` | V | 5 stack arrays (bodies, contacts, joints, positions 12 B, velocities 12 B) |
| 0x14031a910 | `b2World_DestroyBody` | V | destroys joint edges, contacts, fixtures, frees 0xb8 bytes |
| 0x14031ac00 | `b2World_DestroyJoint` | V | unlinks both bodies, wakes them (+0xac := 0, flag 2) |
| 0x14031a7e0 | `b2World_CreateJoint` | V | already named; only caller `Joint_CreateB2Joint` |

## Broadphase and tree
`b2DynamicTree_Balance` 0x140322a00, `_RemoveLeaf` 0x1403235d0, `_CreateProxy` 0x140322eb0 (fat AABB +-0.1), `_MoveProxy` 0x140323470 (fat margin 0.1, +2*displacement on the moving side), `_AllocateNode` 0x1403228d0 (was labelled `rep_1402f78e0...free`), **`b2DynamicTree_Query` 0x140320fd0** (stack of node ids, AABB overlap test, callback; its only caller is `b2BroadPhase_UpdatePairs`; was labelled `rep_1402f5fe0...free`) [V]. `b2DynamicTree_InsertLeaf` 0x140322fb0 [A: named by two agents, consistent with the checked tree functions, body not read]. `b2BroadPhase_BufferMove` 0x1403237d0, `_CreateProxy` 0x140323850, `_MoveProxy` 0x1403238c0 [V]. `b2BroadPhase_UpdatePairs` 0x140321240 [V] (12-byte pair records, sort + dedup, calls AddPair).
**There is no Box2D raycast or QueryAABB for game code**: the only tree query serves the broadphase pairs; `Weapon_FlakInterceptScan` and `Body_AreaDamageFromBlast` scan `somethingBodyArray_` directly.

## Contacts and narrowphase
`b2ContactManager_FindNewContacts` 0x140322210 (wrapper, calls UpdatePairs with itself as callback), `_AddPair` 0x140321d90 (dedup over the body contact list +0x88, filter at cm+0x68, `b2Body_ShouldCollide`, `b2Contact_Create`, wakes both bodies), `_Destroy` 0x140322100 [V]. `b2Contact_Create` 0x140325a70 (registry 0x148076a20, stride 0x18: create +0, destroy +8, primary flag +0x10; lazily filled; no chain-vs-chain entry) [V]. `b2Contact_DestroyDispatch` 0x140325c80 [V]. `b2Contact_Construct` 0x1403259b0 (friction = sqrt(fA*fB), restitution = max) [V]. Creators `b2CircleContact_Create` 0x1403309b0, `b2PolygonAndCircleContact_Create` 0x140330a80, `b2PolygonContact_Create` 0x140330b10 [V] (200-byte allocation, vtables 0x140378e40/e50/e60). Unnamed but known from the registry [A]: edge/circle 0x140330ba0, edge/polygon 0x140330c30, chain/circle 0x140330cf0, chain/polygon 0x140330e10, shared destroy 0x140330a10.
`b2CollideCircles` 0x140330f30, `b2CollidePolygonAndCircle` 0x140331050, `b2CollidePolygons` 0x140331450 (flip constants 0.98 / 0.001 as stock) [V]. `b2FindMaxSeparation` 0x140331f70, `b2FindIncidentEdge` 0x140331ca0, `b2ClipSegmentToLine` 0x140318830 [V by call signature; two helper agents had the last two swapped].
Solver: `b2ContactSolver_SolveVelocityConstraints` 0x1403292d0 (friction clamp, 1-point clamp, 2x2 block solve), `_WarmStart` 0x14032a2f0, `_StoreImpulses` 0x14032a260 [V]; `b2ContactSolver_SolvePositionConstraints` 0x140328470 (already named; Baumgarte 0.2, max correction 0.2, slop 0.005, early-out -0.015: stock) [A].
Bodies/fixtures: `b2Body_ShouldCollide` 0x14031a510, `b2Body_SynchronizeFixtures` 0x14031a550, `b2Fixture_Synchronize` 0x140320ea0, `b2Body_SetTransform` 0x14031a290 (also calls FindNewContacts, as stock 2.3 does; a helper agent called this a deviation, it is not) [V].

## Joints (the vtable trio called by `b2Island_Solve` at slots +0x30 / +0x38 / +0x40)
`b2Joint_Create` 0x1403247c0 switches on the definition type: 1 revolute (0x120 bytes), 2 and 6 and others unknown, 3 distance (0xf0), 8 weld (0x110). Vtables read from memory [V]: revolute 0x1403785e8 -> Init 0x14031c250, SolveVel 0x14031ced0, SolvePos 0x14031c960; distance 0x140378838 -> 0x14031d730, 0x14031e0b0, 0x14031dd50; weld 0x1403788f8 -> 0x14031e590, 0x14031f030, 0x14031eb20. Names are `b2RevoluteJoint_*`, `b2DistanceJoint_*`, `b2WeldJoint_*` (`InitVelocityConstraints`, `SolveVelocityConstraints`, `SolvePositionConstraints`). The weld position solver (0.005 linear, 0.0349 rad angular slop) and the distance joint (0.2 correction clamp, 2*pi soft constraint) were read and match stock 2.3 [V]; the revolute position constants (angularSlop 0.0349, maxAngularCorrection 0.1396) are from the helper [A]. `0x14031eb20` had no function in Ghidra; it was created (1281 bytes). Unknown joint types (2: 0x14032c160, 6: 0x14032d910, 4/5/7/9/10 through 0x1402f9760) were not read.
Game wrapper `Joint` object: +0xc8 b2 joint, +0xd0 kind (0 distance, 1 revolute, 2 weld, 3 rope-like), +0x104/+0x108/+0x10c motor enable/torque/speed. `Joint_CreateB2Joint` 0x140193a10, `Joint_DestroyB2Joint` 0x140193110 [V], `Joint_EnsureB2Joint` 0x140194b10 (recreates the b2 joint when the body pointers changed) [A], `Joint_SetMotor` 0x1401949d0.

## Units and constants
`Body_SyncFromB2` divides b2 position and linear velocity by 0.05 (angle and angular velocity unscaled). `b2Island_Solve` constants [A, read from memory by the helper]: max translation squared 4.0 (so 2.0 b2 units per step = 40 game units), max rotation pi/2, time to sleep 0.5, linear sleep tolerance 0.01 (b2) and angular 2 degrees: all stock 2.3, in b2 units. The tree margin 0.1 is in b2 units. So the 0.05 scale is applied only at the game/b2 boundary. Step: 1/50 s, 10 velocity and 10 position iterations (from the existing `b2Island_Solve` comment).

## Flight input and creature access
`Input_GetMoveVector` 0x1401888e0 (first record with key +0xe4 == player and a non-zero vector at +0x10; stride 0xf0), `Input_RebuildMoveVector` 0x14018d6c0 (flags +0xde y-1, +0xe0 y+1, +0xdf x-1, +0xe1 x+1), `Profile_GetPlayerCreature` 0x1402924b0 (Profile+0x50 + idx*0x18, idx < 4) [V]. `Input_KeyDown` 0x1401896a0 (key 0x1006 Shift writes creature +0xba8 = 2.0) and `Input_KeyUp` 0x14018a530 (0x1006 writes 1.0; 0x1016 calls `Creature_UseExtinguisher`) [A for the other keys; the Shift and 0x1016 behaviour is in player-thrust-keys-and-engine-heat.md].

## Corrections to earlier helper claims (so they are not re-imported)
* 0x1402f8ac0 is `displayShortage` (HUD text), not a b2Island report. 0x140334e00 is an MSVC sin/cos helper, not `b2Rot::Set`. Nothing was renamed to either.
* Labels `rep_...HEAP-L1...::free` inside Box2D code are often the allocator, the tree allocator or `BufferMove`: trust addresses and logic, not callee labels.

## Open
* Unverified static readings of flight code by a helper, not confirmed and not acted upon: `Player_SendThrustCommands` may `return` instead of `continue` for an idle player (would skip players 1 to 3; multiplayer only); Shift release writes 1.0 only when `doRecoil_global == 0`; `CalculateStats` computes `+0x1624 = +0x1638 / +0x1648` without a visible zero guard; part activation tiers by cost in `CalculateStats` (Stats+0xf0, +0xec, budget from +0x165c); `+0x181c` meaning.
* b2Body setters/getters (SetAwake, SetLinearVelocity, damping) and the tail of the joint types are unmapped. Insertion order of the global body list (see player-thrust-keys-and-engine-heat.md section 10) is still open.
