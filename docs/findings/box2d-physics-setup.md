# How the game sets up Box2D: shapes, mass, filtering, damping, gravity (v1.163) - ghidra-miner, 2026-10-20

**See also (2026-10-21):** field offsets of the Box2D objects, the weld joint's 6.0 linear mass scale and the antenna chain: [box2d-struct-layouts.md](box2d-struct-layouts.md).
[V] = read by me in Ghidra today (decompile/disassembly). [file] = checked against the data files. [guess] = inference.

## 0. The engine
Box2D 2.3-era (RTTI b2PolygonShape, b2ContactListener/b2CListener, b2ContactFilter(b2CFilter), b2DestructionListener(b2DListener); joint defs incl. wheel/rope). World object `SuperBig` (0x143a119f0), created in PrepareMainLoop 0x1401ada0d..: `b2World(gravity)` with `New(0x19380)`, constructor `SuperBigConstructor` 0x14031a610. Three small listener objects are installed: b2CListener vtable 0x140369270 (BeginContact/EndContact empty; PreSolve 0x140284730; PostSolve 0x140284340), b2CFilter vtable 0x1403692a0 (ShouldCollide 0x1402858c0), b2DListener vtable 0x1403692b8. World flags word 0x1000101 = warm starting on, continuous physics on, sub-stepping off; allowSleep = true [V].
Stepped once per frame in SomethingPhysicTask: `Step(SuperBig, 1.0/coreFrameRateFlt_, 10)` (wrapper 0x1402f0ca0).

## 1. Gravity [V]
gravity = (0, 0.05 x 9.82) in Box2D units (9.82 = float 0x411D1EB8 at 0x14035480c; 0.05 = float at 0x1403c0e10), +y is down, so **9.82 in game units**. Every body has gravityScale 1.0. Game units = Box2D value / 0.05 for lengths (20 game units per Box2D metre).

## 2. Which Bodies get a b2Body, and the body definition [V]
`Body::Reflect` 0x14004b010 / `Body::createB2Body` 0x14004b330 (identical code):
* A b2Body is created for a body whose master is the world root (GlobalNode_), and for each hull **Frame** (class 0x1f). All other parts of a ship are fixtures of the Frame's b2Body.
* b2BodyDef: **type = dynamic (2) if Body+0x1d0 (m_density) > 0, else static (0)**; position = 0.05 x (Body+0x128, +0x12c); angle = Body+0x138; velocity 0; **linearDamping = 0.05, angularDamping = 0.05** (0x3d4ccccd); allowSleep = true, awake = true, fixedRotation = false; **bullet = Body+0x1fc (byte)** (continuous collision for flagged bodies, e.g. shells); active = true; gravityScale 1.0. userData of the b2Body (+0xb0) = the game Body; the game Body keeps the b2Body at +0x178.
* **Drag (corrected 2026-10-20 after the Opus audit):** Box2D damping gives v' = v / (1 + dt x 0.05), i.e. a = -0.05 v per second, linear in v (the audit's C1 = 0.041-0.055 for Lightning matches it). It cannot make the speed-dependent part (the audit's C2 about 5e-4 per u/s: a = -(C1 + C2 |v|) v). The game DOES have a quadratic air-drag force in code: at `0x14001d921` (no Ghidra function) for a body whose `Body+0x1dc` (save key `m_drag_lin`) is non-zero it applies, through the body's vtable `+0x178` (apply force), the force `-v_hat x 0.5 x 1.29 x m_drag_lin x |v|^2` (1.29 = float at `0x140354764`) [V]. But `m_drag_lin` appears only in level objects (City.seria, Objects/Land/*, Objects/Town/*), in no ship design or part, so ship hulls have 0 there and this force does not act on them [file: grep over the game folder]. The ships' speed-dependent term must therefore come from elsewhere, most likely the engine force law (thrust falloff; the audit says drag and falloff are degenerate per ship) [guess]. The world gravity IS read: 9.82 game units (section 1), which closes audit item (c)14.
* **CORRECTION 2026-10-21 [code]: hulls DO have a hardcoded quadratic air drag.** The Frame (class 0x1f) branch of `Body_PreStepUpdate` (`0x14001d440`, Body vtable `+0x168`, run for every live body before each `b2World_Step`) applies `F = -v_hat x A x min(W,H) x |v|^2 x 1.29 x 0.5` with `v` = Frame `+0x130/+0x134`, `W,H` = Frame bbox `+0x218/+0x21c`, `A = |H(-sin th n.x + cos th n.y)| + |W(cos th n.x + sin th n.y)|` (silhouette across the velocity, `th` = Frame `+0x138`, `n` = v_hat rotated -90 degrees), through `Body_AddForceAtPoint` at the Frame point `+0x210/+0x214`, so it also makes a torque about the COM that depends on the hull angle relative to the velocity. This is the speed-dependent term the audit found (a = -C2 |v| v); the statement above that hulls have no drag is wrong for Frames (it holds for the `m_drag_lin` branch only).

## 3. Part shape -> fixture (`Body::createFixture` 0x14004b530, called with this = part, owner = Frame/free body) [V]
* Source vertices: the part's Mesh (Body+0x1b8, vertex count at mesh+0x50, float pairs at mesh+0x48), **at most 8 vertices** (count clamped to 8 = b2_maxPolygonVertices). Loop goes from the LAST vertex to the first (order reversed, irrelevant because b2PolygonShape::Set builds the convex hull itself).
* Each vertex is converted part-local -> world (part vtable +0xe8) -> owner-local (owner vtable +0xf8) when the part is not the owner, then multiplied by **0.05**.
* Shape: b2PolygonShape::Set(points, n) (0x140319aa0), **radius 0.01** (0x3c23d70a), one polygon, **one fixture per part Body** (sprites are only for drawing).
* b2FixtureDef: **friction = Body+0x1d4** (default 0.6, set in setCertainBodyFloatVals; no per-part value in the files I looked at), **restitution = 0.001**, **density = 0.05 x min(Body+0x218, Body+0x21c) x Body+0x1d0**, isSensor = false (none are sensors), filter: categoryBits = 1, maskBits = 0xFFFF, groupIndex = 0, userData = the part Body (fixture+0x40). The b2Fixture is kept at part+0x168.
* **Body+0x218 / +0x21c = width / height of the mesh bounding box, +0x210 / +0x214 = its centre** (computed by the routine at 0x140054780 from the vertices) [V].

## 4. Mass and inertia [V + file]
* Box2D computes mass from the fixture: m_b2 = density x polygon area (Box2D units). With the scale factors this equals, in game units, **mass = min(width, height) x m_density x polygon_area** (0.05 x 0.05^2 = 0.05^3 and the game divides by 0.05^3). So the shape is treated as a plate of thickness min(w,h).
* **Check on the data:** MDL_ENGINE_01 in parts.seria: mesh vertices (7.00642,-7.10641) (7.00641,5.60644) (4.88572,8.4) (-5.07143,8.4) (-7.10642,5.60644) (-7.10641,-7.10642): width 14.11283, height 15.50644, shoelace area 213.03 -> min(w,h) x density 100 x area = **300,654 vs m_mass = 300653** in the file [file]. So m_mass in the .seria is this product (precomputed by the editor); the simulator's 0.8-23 ratio disappears if the min(w,h) factor is included.
* The game does NOT call SetMassData: inertia is Box2D's own (sum of polygon inertias of all fixtures of the Frame body, about the centre of mass, with Box2D's m_I). After each createFixture, `FUN_140054b80(owner)` copies back **Body+0x1d8 (mass) = b2Body.m_mass (+0x90) / 0.05^3** [V]. The AI's `FUN_140048440` (hull inertia about the body origin) = (m x |localCenter|^2 + I) / 0.05^5 with b2Body +0x1c/+0x20 localCenter, +0x90 mass, +0x98 I [V]: the parallel-axis term adds Box2D's centre-of-mass offset back.

## 5. Collision filtering (b2CFilter::ShouldCollide 0x1402858c0) [V, summary; the function has ~25 rules]
All fixtures use category 1 / mask 0xFFFF / group 0, so Box2D's own filter never blocks anything; **everything is decided in this callback** on the two game Bodies (fixture userData):
1. no collision when `fileRead_` is false, or when `(A+0x1f0 & B+0x1f0) == 0` (a 32-bit collision-layer mask on the Body);
2. parent/child and same-owner pieces: A is B's master (+0xb8) or vice versa, or `A+0xc0 == B+0xc0` (same group/ship id), or the ownership grandparent rule: no collision;
3. two root ship bodies (creatures) never collide; a creature whose phase `+0x190 == 6`, or whose phase is 0 and the other is flagged (0x4000000 / 0x400), does not collide;
4. projectiles (`+0x1c0 & 0xd == 0xd`): two projectiles collide only 50% of the time (random), a projectile never collides with logic-id 3 bodies, same-owner/side shells and missiles do not collide with their own side or launcher; planes of the same side (FUN_140220120) do not collide;
5. launch grace: a body with `+0x3c0 > 0` (launch timer/logic activity) ignores bodies of certain categories while the timer is below 0.9 (nuke 0x8000000) / 0.8 (missiles, planes);
6. both bodies of class 0x10 (`+0x1c8 == 0x10`) do not collide; same-owner explosive bodies with the 0x228 flag etc.
Use this list as the source of truth for 'who collides with whom'; the exact flag meanings (e.g. `+0x1c0` bits) are only partly decoded.
The PreSolve callback 0x140284730 additionally detonates explosive projectiles on first contact (calls the blast routine FUN_14002cdc0 with the body's explosive); PostSolve 0x140284340 records the contact result used for contact damage (see contact-damage-and-fire.md).

## 6. What I did not find
* A SetLinearDamping/SetAngularDamping call after creation (none found, so Box2D's own drag is 0.05/s); where the hull's |v|-dependent term comes from is open (see section 2).
* How many velocity/position iterations Box2D really runs (the `10` is passed to a wrapper).
* The meaning of every bit of `+0x1c0` / `+0x1f0` / `+0x1c8` used by the filter.
