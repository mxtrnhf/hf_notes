# Ship bodies: fixtures, centre of mass, tear-off and hull break-up (1.163)

Status: read in Ghidra 2026-10-21 [code]. Related: [box2d-physics-setup.md](box2d-physics-setup.md), [contact-damage-and-fire.md](contact-damage-and-fire.md), [simulator-research.md](simulator-research.md).

## Part A: fixtures and centre of mass

Tags: [code] read today; [guess] not verified. Functions: `Body::Reflect 0x14004b010`, `Body_CreateFixture 0x14004b530`, `Body_CreateB2Body 0x14004b330`, `Frame::Reflect 0x14011cbc0`, `Body::get_world_pos 0x140055af0` (vtable +0xe8), `FUN_14004a100` (vtable +0xf8), part removal `FUN_140024f70`, `Body_UpdateMassFromB2 0x140054b80`.

### (1) Which parts get a fixture on the Frame body  [code]
* `Frame::Reflect` (0x14011cbc0): needs a master (`+0x88`) and no b2 body yet; calls `Body_CreateB2Body` for the FRAME: b2 position = Frame `+0x128/+0x12c` x 0.05, angle = Frame `+0x138`, type dynamic (2) if Frame `+0x1d0` (density) > 0 else static (0), linearDamping = angularDamping = 0.05, allowSleep, gravityScale 1, bullet = `+0x1fc`. Then `Node::Reflect` calls `Body::Reflect` on each child.
* `Body::Reflect(part)`: does nothing unless the part has a mesh (`+0x1b8 != 0`). Needs a master; logs an error if the part already has a b2 body (`+0x178`) or a fixture (`+0x168`). Then:
  * master class code low 5 bits == 0x1f (a **Frame**): `Body_CreateFixture(part, frame)` -> fixture on the FRAME's b2 body.
  * master == `GlobalNode_` (a free part: debris, fragments, anything not under a Frame): the part gets its OWN b2 body (same parameters as above, dynamic if its density > 0) and `Body_CreateFixture(part, part)`.
  * any other master class: nothing is created.
* `Body_CreateFixture` itself adds only: frame has a b2 body (`+0x178`) and the mesh vertex count (`mesh+0x50`) != 0.
* **There is no condition on slot type, layer, m_state, hp, floor flags, `m_mdl_covered`, decoy or category** in Reflect/CreateFixture. Whether a part gets a fixture on the frame is decided by (mesh present) and (master is a Frame). Which parts hang under which Frame is decided by the ship builder (ship loader / `CreateFrameFragments`), not here: that is where the JOINTED slot types (146/162/266/282) end up as separate bodies, I did not read that builder [open].

### (2) Vertex transform part-local -> Frame-local  [code]
For up to 8 vertices (`n = min(mesh vertex count, 8)`: the FIRST 8 in mesh order are used, nothing is dropped by hull selection; more than 8 vertices are truncated):
1. `p = part.vtable+0xe8(p)` = `Body::get_world_pos`: `p = R(part) * p + part.position(+0x128,+0x12c)`, then the same call on the master, up the chain while the parent's class code low nibble is 0xf (parts, Frames and the creature all qualify).
2. `p = frame.vtable+0xf8(p)` (`FUN_14004a100`): world -> frame-local: apply the parent's inverse first, then `p -= frame.position`, then rotate by the inverse (transpose) of the Frame's matrix.
3. The transforms of the Frame and everything above it cancel exactly, so the result is: composition of the transforms of the part and every master BETWEEN the part and the Frame (mounted parts on hull modules compose with the module's rotation and position), expressed in the Frame's own axes, with the Frame's position as origin.
4. `R` is the 2x2 matrix stored at body `+0x8fc..+0x908` (4 floats: m0 `+0x8fc`, m1 `+0x900`, m2 `+0x904`, m3 `+0x908`). I did NOT find its setter (probably cos/sin of the body angle `+0x138`, but `+0x138` is the angle in the game's `-atan2(dx,dy)` convention); if they ever disagree the geometry follows the MATRIX, not `+0x138`.
5. The `m_center` (`+0x210/+0x214`) is NOT used by Reflect or CreateFixture: vertices come straight from the mesh vertex list at `mesh+0x48`. Mirroring/scale is already baked in the mesh vertices (`FUN_14004eab0`).
6. Each vertex is multiplied by 0.05 and the polygon is built with `b2PolygonShape::Set` (0x140319aa0): the standard 2.3 `Set` computes the convex hull of the points (and welds near-duplicates), so concave meshes become their convex hull; polygon radius 0.01 (`0x3c23d70a`).
7. Position of the Frame body's origin = the Frame's `+0x128/+0x12c`; Box2D itself computes `localCenter` (the COM) from the fixtures; the game never calls SetMassData, never moves the body origin to the COM.

### (3) Fixtures re-created or shifted later  [code]
* Part removal `FUN_140024f70`: if the part has a fixture (`+0x168`), `FUN_140319e80` (= `b2Body::DestroyFixture`) runs; if its master is a Frame, `Body_UpdateMassFromB2` follows. Box2D recomputes mass, COM and inertia of that body at once (2.3 `DestroyFixture` calls ResetMassData). So **mass, COM and inertia change live as parts die or are torn off**.
* After a break-up `CreateFrameFragments` builds new Frames; their parts get new fixtures through `Reflect` on the new Frame body, and the old Frame is recomputed (vtable +0x1f8).
* No `SetTransform`/origin re-centering found in these paths.

### (4) Child position composition  [code]
`+0x128/+0x12c` are local to the master (`+0x88`) in the master's own rotated axes: world = R_master * p + pos_master, recursively (see (2)).

### (5) Density and skin  [V + guess]
* Fixture density = `0.05 * Body_GetFixtureDensity(part)` = `0.05 * min(part +0x218, part +0x21c) * part +0x1d0` where `+0x218/+0x21c` are the mesh bounding-box WIDTH and HEIGHT (`+0x210/+0x214` its centre). Friction `+0x1d4`, restitution 0.001, filter category 1 / mask 0xffff.
* The polygon radius (0.01) does not enter `ComputeMass` in standard Box2D 2.3 (it uses the vertices only) [guess: the game's Box2D is stock 2.3; the project ships `Box2D-2.3.2.tar.gz` in `hf_ml`].

### What I would check next (cheap, decisive)
Mass matching to 1e-5 but COM/inertia off points at geometry. Candidates, in order: (a) meshes with MORE than 8 vertices: the game keeps only the first 8 (then hulls them); (b) concave meshes: hull vs your raw polygon; (c) the rotation matrix `+0x8fc` vs the angle (mounted parts); (d) parts you give a fixture that the game does not (no mesh) or that live under a non-Frame master. A one-shot probe dump of the Frame b2 body's fixture list (vertex count and the first fixture's vertices) for ONE small ship would settle (a)-(c).

## Part B: tear-off and break-up

Tags: [code] read today; details approximate where marked. Decompile of `BreakUpFrame 0x14011d3e0`, `CreateFrameFragments 0x14011c1a0`, `Body_TearOffFromFrame 0x140286100`, plus the two call sites.

### Tear-off of ONE part (impulse path)  [code]
`Body_TearOffFromFrame(part)` (called by `Physics_ProcessContactRecord` when impulse I > 4e6, 8e6 in `DAT_147fc6fd4` mode): detaches the part from its master Frame (vtable `+0x68`), re-adds it to `GlobalNode_` as a free body (vtable `+0x50`; it gets its own b2 body) and sets its velocity to the frame's rigid-body velocity at the part:
`w = Frame +0x158` (angular velocity), `f = part radius(+0x20c) / frame radius(+0x20c)`, `v = (1-f) * Frame(+0x150,+0x154) + f * Frame(+0x130,+0x134)` (the frame's previous and current velocity, blended by size), then `vx = v.x - w*(y_part - y_frame)`, `vy = v.y + w*(x_part - x_frame)` with positions read from the b2 bodies (`b2Body +0x2c/+0x30` / 0.05); part angular velocity = `w`. The frame's own linear and angular velocity are set again to the same `w` and the same formula applied to the frame. Skipped when the part has `+0x228` set and its `+0x498` link points at a class `0x80000000007` object (a special case, probably a loot/attached object). No damage call, no log line.

### Break-up of the hull into pieces  [code, flow; counts of conditions approximate]
* Driver: `SomethingPreTask` (0x140286f90..0x140286fb4) loops over a node list each frame; for every node of class `0x1f` (Frame) it calls `BreakUpFrame(frame, 0)`. A second call `BreakUpFrame(frame, 1)` at `0x1400e6fd1` (a different, error-logging routine; not the battle loop).
* `BreakUpFrame` does work only if the Frame's link-entry vector (`+0xa40..+0xa48`, 0x18-byte entries; filled when a part dies or a joint breaks) is non-empty AND Frame state `+0x48 != 0`.
* It **flood-fills the connected part groups**: start from each entry part whose master is this frame and whose mark `+0x220` is 0; neighbours are the parts reached through each part's slot vector `+0x350` where the slot is enabled (`slot +0xb8 & 1`) and (`slot +0xb8 bit 1` is clear OR `slot +0x80 & 0x40`), using the slot's far part `slot+0x58`. Each group is counted by number of parts.
* With `param_2 == 0` (battle): **the largest group stays in the old Frame** (strictly bigger replaces: on a tie the first found wins); every OTHER group is passed to `CreateFrameFragments`. With `param_2 != 0`: the group that contains a part with flag `0x40` (checkShipPartFlagActive(part,0x40), i.e. the bridge category) stays, and all other groups are killed (vtable `+0x48`) instead of becoming fragments.
* `CreateFrameFragments`: a one-part group becomes a free body (`+0x68` detach, `+0x50` add to `GlobalNode_`); a larger group becomes a NEW Frame (class `0x1f`, name "Frame", `New(0xa58)`) holding those parts and added to `GlobalNode_`. If the old Frame is left with fewer than 2 children its last child is also freed and the old Frame is killed. Mass/inertia of the old and new Frames are recomputed (vtable `+0x1f8`).
* **Fragment velocity** (rigid rotation about the old frame's centre): `v_new = v_frame + w * perp(r)` with `r` = (fragment b2 position - old centre) / 0.05, i.e. `vx = v.x - r.y*w`, `vy = v.y + r.x*w`, angular velocity = the frame's `w`. `v_frame`, `w` come from `FUN_1400486a0` / `FUN_140048030` (frame velocity and angular velocity). No explosion impulse, no energy loss.
* So: a ship breaks in two when the rigid connections between its parts (non-joint slots, enabled) are cut by part deaths; the bigger half (by PART COUNT, not mass) keeps the original Frame (and so the creature link). Joint slots (swivel mounts) do not hold a group together unless flagged `0x40`. Whether a fragment that loses the bridge/engines still counts as the ship: the creature keeps following the OLD Frame (the largest group), and `ShipStatusCheck` then evaluates what is left on it.

### Not done
* The exact meaning of slot flags `+0xb8` bit 0/1 and `+0x80 & 0x40` (enabled / is-joint / rigid-joint?).
* What fills the link-entry vector `+0xa40` (part death hook).
* Whether fragments keep a creature link (they do not look like creatures; they are Frames with parts, so they are debris).
