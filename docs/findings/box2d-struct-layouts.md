# Box2D object layouts and the antenna/weld setup (v1.163), ghidra-miner, 2026-10-21

Companion to [box2d-physics-setup.md](box2d-physics-setup.md). Ghidra names added 2026-10-21: `b2Body_Ctor` 0x140319c50, `b2Fixture_Create` 0x140320b30, `b2Joint_Ctor` 0x140324750, `b2Joint_Create` 0x1403247c0, `b2WeldJoint_Ctor` 0x14031e2e0, `b2WeldJoint_InitVelocityConstraints` 0x14031e590, `b2WeldJoint_SolveVelocityConstraints` 0x14031f030, `b2RevoluteJoint_Ctor` 0x14031be80, `b2DistanceJoint_Ctor` 0x14031d470, `b2Body_ResetMassData` 0x140319f80, `b2ContactManager_Collide` 0x140321f60, `Hull_CreateAntennaChain` 0x1401c3bd0.


Layout is stock Box2D 2.3.x, MSVC x64. [V] = read from code in this session (constructor, solver or step code). [guess] = inferred from stock layout only.
All offsets are hex bytes.

## b2Body (size 0xB8, ctor 0x140319c50, alloc in b2World_CreateBody 0x14031a760)
| off | field | |
|---|---|---|
| 00 | type int (0 static, 1 kinematic, 2 dynamic) | [V] |
| 04 | flags ushort: 01 island, 02 awake, 04 autoSleep, 08 bullet, 10 fixedRotation, 20 active | [V] (ctor sets them from the def; Solve tests `&0x22==0x22`) |
| 08 | islandIndex int | [V] (Solve writes it) |
| 0C | xf.p (x,y) | [V] |
| 14 | xf.q (sin, cos) | [V] |
| 1C | sweep.localCenter (x,y) | [V] |
| 24 | sweep.c0 (x,y) | [V] |
| 2C | sweep.c (x,y) | [V] |
| 34 | sweep.a0 | [V] |
| 38 | sweep.a | [V] |
| 3C | sweep.alpha0 | [V] (ctor zeroes it; role from stock layout) |
| 40 | linearVelocity (x,y) | [V] |
| 48 | angularVelocity | [V] |
| 4C | force (x,y) | [V] (b2World_Step clears 4C..57 when the clear-forces flag is set) |
| 54 | torque | [V] |
| 58 | m_world ptr | [V] |
| 60 / 68 | prev / next in world body list | [V] |
| 70 | m_fixtureList head | [V] |
| 78 | m_fixtureCount int | [V] |
| 80 | m_jointList head (b2JointEdge*) | [V] |
| 88 | m_contactList head (b2ContactEdge*) | [V] |
| 90 | mass | [V] |
| 94 | invMass | [V] |
| 98 | I (rotational inertia about the centre of mass) | [V] |
| 9C | invI | [V] |
| A0 | linearDamping (0.05) | [V] |
| A4 | angularDamping (0.05) | [V] |
| A8 | gravityScale (1.0) | [V] |
| AC | sleepTime | [V] (ctor zeroes it) |
| B0 | userData = game `Body*` | [V] |

Reverse link: game `Body+0x178` is the b2Body pointer.

b2JointEdge (jointList): `{other body +0, joint +8, prev +0x10, next +0x18}` [V].
b2ContactEdge (contactList): `{other +0, contact +8, prev +0x10, next +0x18}` [V] (the island DFS reads them).

Mass reset is `FUN_140319f80`.
- It only runs real mass maths when `type > 1`, i.e. for dynamic bodies.
- A body whose mass sums to exactly 0 is forced to mass = 1, invMass = 1.
- Ctor default: dynamic gets mass = invMass = 1.0 before any fixture; static gets 0 and 0.
- `invI = 0` if I <= 0 or the fixedRotation flag is set.
- It also subtracts `m*|c|^2` from I (the parallel-axis term).

## b2Fixture (size 0x48, ctor 0x140320b30)
| off | field | |
|---|---|---|
| 00 | density | [V] |
| 08 | next | [V] |
| 10 | body | [V] |
| 18 | shape ptr | [V] |
| 20 | friction | [V] |
| 24 | restitution | [V] |
| 28 | proxies ptr (0x20 per proxy) | [V] |
| 30 | proxyCount | [V] |
| 34 | filter.categoryBits ushort | [V] |
| 36 | filter.maskBits ushort | [V] |
| 38 | filter.groupIndex short | [V] |
| 3A | isSensor byte | [V] |
| 40 | userData | [V] |

## b2Joint base (ctor `FUN_140324750`, allocated per type by `FUN_1403247c0`)
| off | field | |
|---|---|---|
| 00 | vtable | [V] |
| 08 | type | [V] |
| 10 / 18 | prev / next in world joint list | [V] |
| 20 | edgeA `{other, joint, prev, next}` | [V] |
| 40 | edgeB | [V] |
| 60 / 68 | bodyA / bodyB | [V] |
| 70 | index | [V] (ctor zeroes the dword at 0x70) |
| 74 | islandFlag byte | [V] |
| 75 | collideConnected byte | [V] |
| 78 | userData = game `Joint*` | [V] |

Joint sizes: 1 revolute 0x120, 2 prismatic 0x140, 3 distance 0xF0, 4 pulley 0x100, 5 mouse 0xE8, 6 gear 0x160, 7 wheel 0x120, 8 weld 0x110, 9 friction 0xF0, 10 rope 0xE8.

### b2WeldJoint (type 8, ctor 0x14031e2e0). THIS BUILD DIFFERS FROM STOCK
| off | field | |
|---|---|---|
| 80 | frequencyHz | [V] (from def+0x3c; the game sets it to 0, so the weld is rigid) |
| 84 | dampingRatio | [V] (from def+0x40; the game sets 10.0; unused while freq is 0) |
| 88 | bias | [V] (zeroed; used by the soft branch) |
| 8C | **linear mass scale** (game sets 6.0) | [V] (from def+0x44) |
| 90 | localAnchorA (x,y) | [V] |
| 98 | localAnchorB (x,y) | [V] |
| A0 | referenceAngle | [V] |
| A4 | gamma | [V] |
| A8 / AC / B0 | impulse Vec3 (x, y, z) | [V] |
| B4 / B8 | indexA / indexB | [V] |
| BC / C4 | rA / rB (Vec2) | [V] |
| CC / D4 | localCenterA / localCenterB | [V] |
| DC / E0 | invMassA / invMassB **(already multiplied by the +0x8C scale)** | [V] |
| E4 / E8 | invIA / invIB (not scaled) | [V] |
| EC..10F | Mat33 mass matrix | [V] |

**"freq 10 / damping 6" is wrong for the weld.**
- `frequencyHz = 0`, so the rigid 3x3 branch is used.
- `+0x84 = 10` is a dead damping value.
- `+0x8C = 6.0` multiplies both bodies' invMass, in the linear terms only.
- `FUN_14031e590` is InitVelocityConstraints and `FUN_14031f030` is SolveVelocityConstraints.
- Both use the scaled `invMass` (`+0xDC/+0xE0`) for the linear velocity update and the unscaled `invI`.
- That is inconsistent with a real rigid body: the linear and angular impulse parts no longer match, so angular momentum is not conserved across the joint. This is an inference from the code, not measured. The sim should reproduce it exactly.

### b2RevoluteJoint (type 1, ctor 0x14031be80): all [V]
| off | field |
|---|---|
| 80 / 88 | localAnchorA / localAnchorB |
| 90 | impulse Vec3 (x, y, z at 90 / 94 / 98) |
| 9C | motorImpulse |
| A0 | enableMotor byte |
| A4 | maxMotorTorque |
| A8 | motorSpeed |
| AC | enableLimit byte |
| B0 | referenceAngle |
| B4 / B8 | lowerAngle / upperAngle |

### b2DistanceJoint (type 3, ctor 0x14031d470): all [V]
| off | field |
|---|---|
| 80 | frequencyHz (game sets 10.0) |
| 84 | dampingRatio (game sets 10.0) |
| 88 | bias |
| 8C / 94 | localAnchorA / localAnchorB |
| 9C | gamma |
| A0 | impulse |
| A4 | length |

Joint kind to type, from Joint_CreateB2Joint 0x140193a10: kind 0 = distance (type 3), kind 1 = revolute (type 1), kind 2 = weld (type 8), kind 3 = rope (type 10, `maxLength` in the def at +0x38 = length x 0.05). Rope ctor not read.
Distance length is the anchor distance x 0.05 (the 0.05 scale also applies to all the anchors).

## b2World (World `SuperBig` at 0x143a119f0)
| off | field | |
|---|---|---|
| 19298 | flags: bit0 new fixtures, bit1 locked, bit2 clear forces | [V] |
| 192A0 | contactManager (broadphase first) | [V] |
| 192F8 | contactManager.contactList head | [V] (cm+0x58; Collide at 0x140321f60 walks it) |
| 19300 | contactCount int | [V] (cm+0x60; passed to the island as contact capacity) |
| 19308 | contactFilter ptr | [V] |
| 19310 | contactListener ptr | [V] |
| 19320 | bodyList head | [V] |
| 19328 | jointList head | [V] |
| 19330 | bodyCount | [V] |
| 19334 | jointCount | [V] |
| 19338 | gravity (x,y) | [V] (passed to b2Island_Solve) |
| 19340 | allowSleep byte | [V] |
| 19358 | inv_dt0 | [V] |
| 1935C | warmStarting byte | [V] |
| 1935D | continuousPhysics byte | [V] |
| 1935E | subStepping | [guess] (the slot between continuous and stepComplete) |
| 1935F | stepComplete byte | [V] |

## b2Contact (stock 2.3 layout, confirmed by b2ContactSolver_Construct 0x140327900 and Collide)
| off | field | |
|---|---|---|
| 08 | flags: 01 island, 02 touching, 04 enabled, 08 filter flag | [V] |
| 10 / 18 | prev / next | [V] |
| 20 | nodeA | [V] |
| 40 | nodeB | [V] |
| 60 / 68 | fixtureA / fixtureB | [V] |
| 70 / 74 | indexA / indexB | [V] |
| 78 | manifold.points[0..1], stride 0x14: localPoint (8), normalImpulse (+8), tangentImpulse (+C), id (+10) | [V] |
| A0 | manifold.localNormal | [V] |
| A8 | manifold.localPoint | [V] |
| B0 | manifold.type | [V] |
| B4 | manifold.pointCount | [V] |
| B8 / BC | toiCount / toi | [guess] |
| C0 | friction | [V] |
| C4 | restitution | [V] |

## How the antenna chains are built (`Hull_CreateAntennaChain` @ 0x1401c3bd0, string ANTENNA_PART at 0x1403706c8)
Not `Body::Reflect`; it is a separate builder called for the hull.
1. It first skips the whole thing if the hull already has a child of id 0x38E.
2. Loop of 4:
   - Allocate a game `Body` (0xA40 bytes), construct it, name it ANTENNA_PART and set its id to 0x38E.
   - Call `CreateShell_(body, x, y - 3.5 x n, 1.0, 1.0, density = 1e-06, vertices = -1)`.
   - That makes a 4-vertex diamond fixture (radius 0.707) with **density 1e-06, not 0** [V].
   - `Body+0x1D0` is the density; Body_CreateB2Body makes the b2Body dynamic (type 2) when it is > 0, so every antenna link is a **dynamic body with tiny density** [V].
3. Each link gets its own game `Body` and its own b2Body, and its own fixture. They are not part of the hull's body.
4. A `Joint` (0x118 bytes) is built per link with the previous body (the hull for the first link) as one side, via `rep_1401850e0_MakeGlobal_(joint, prev, body, 0,0,0,0, 2)`. The last argument 2 is the joint kind [guess; not checked in MakeGlobal_]. Kind 2 = weld (type 8): rigid, with the 6.0 linear mass scale, collideConnected false.
5. The mass of a link is density x area x unit scale, so tiny but not zero, and the "mass == 0 forces mass 1" rule does **not** apply to them. The inertia is smaller still, so invI can be huge. The size is [guess]: the value from `Body_GetFixtureDensity` x 0.05 is not confirmed, and my rough estimate is about 1e-10. Please log the real invMass/invI.
6. Conflict with the earlier note that ids 63-87 are density 0 / mass 0: the code says density 1e-06 and dynamic. The logger probably printed a rounded or scaled mass. A raw `invMass` / `invI` read (+0x94, +0x9C) settles it.

## Prediction for the logger (inference, not measured)
A rigid weld whose linear terms are scaled by 6 while `invI` is not, joined to a dynamic body with a huge `invI`, should make a badly conditioned system and inject angular momentum into the hull. That is consistent with the sawtooth.
