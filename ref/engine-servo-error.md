# Engine_ServoUpdate (0x140053690) swivel error formula

Decoded 2026-10-23 for the simulator session (stateless, no hysteresis).

    c = norm2pi(cmd)            // cmd = *(float*)(param_2+4)
    a = norm2pi(part+0x138)
    d = c - a                   // in (-2pi, 2pi)
    d = d - n*2pi,  n = sign(d) * (int)floorf(|d|/2pi + 0.5)   // nearest wrap, ~[-pi, pi]
    motor = d * (power * Stats+0x108 * power) (x0.25 if DAT_147fc6fd4)   // power = part+0x818
    Joint_SetMotor(joint, motor, part+0x1d8 / 100)   per joint in list part+0x230
    param_2+0x10 = d; param_2+0xc -= 1

- norm2pi: same pattern, n = sign*(int)floorf(|x|/2pi+0.5); x-=n*2pi; if x<0 x+=2pi  (float32, 2pi=6.2831855)
- No stored swing direction, no deadband, no stale sample, no epsilon. All state is cmd and part+0x138.
- For a true error of -3.148 this wrap gives +3.135 (same as plain wrap_pi). So the world-angle
  reading cannot explain the observed downward swing. Hypothesis: part+0x138 is NOT the world
  angle; if it is hull-relative (1.576 - 0.0745 = 1.50), error = -1.5708 - 1.50 = -3.07, which is
  inside [-pi,pi], is not wrapped, stays negative -> long way down. Matches the trace (1.48 -> 0.08).
  NOT yet verified: who writes part+0x138 (check writers).

## Follow-up: who writes part+0x138 / +0x13c (2026-10-23)
- Writer: Body_SyncFromB2 (0x140054bf0), virtual (vtable slot probably +0xf0; AddWorldAngle is +0xe0).
  Only runs if Body+0x208 != 0 and the body has its own b2Body (+0x178):
  +0x138 = *(float*)(b2+0x38) = b2 body angle, copied raw (float32, no narrowing, no reference-angle term,
  no joint-angle composition). +0x13c = b2+0x48 = ANGULAR VELOCITY (not an angle). cos/sin stored at +0x8fc..+0x908.
  So for a swivel engine (has joints at +0x230 -> own b2Body) +0x138 is the WORLD b2 angle.
- Bodies WITHOUT own b2Body (static engines on a Frame) keep a LOCAL mount angle in +0x138; world angle =
  Body_AddWorldAngle (0x140055ab0, slot +0xe0) summing +0x138 along the master chain (+0x88).
  Servo reads +0x138 directly, so a non-b2 engine would be compared in local frame. Swivel engines are b2.
- Servo is called from Part_HandleCommand (0x1400533f0) <- AiShipTick, AiShip_SteerController,
  AiWeaponController, Player_SendThrustCommands, UpdateShipsAndMapFrame, FUN_140079b20.
- NOT determined: frame ordering of the sync vs the servo call (which sync/step precedes which); so a one-tick
  stale angle (angle from before the step) is not ruled out. Not known if the logger 'ang' is b2+0x38 or +0x138
  (hook code is not in Ghidra; check the hook source). If both are the same float, they are identical bitwise.

## Frame ordering and command latency (2026-10-23)
!FrameFunc (0x1401a8970) at 0x1401a8eb8..ec2 calls in this order: FUN_140286e40, SomethingPhysicTask (0x140286380),
SomethingInputTask (0x14018dbf0), then 0x140011180 ...
SomethingPhysicTask: (a) vtable +0x168 Body_PreStepUpdate (0x14001d440: drag/gravity forces, ttl; no servo, no angle
writes), (b) snapshot loop: +0x158 = +0x13c (prev ang vel), +0x148..+0x154 = prev pos/vel, (c) b2World_Step(dt=1/coreFrameRate, 10 iters),
(d) vtable +0x160 = Body_SyncFromB2 (slot confirmed by vtable delta: AddWorldAngle at 140354d20 (+0xe0), SyncFromB2 at 140354da0 = +0xe0+0x80 = +0x160;
+0x168 at 140354da8 = PreStepUpdate), (e) contacts.
=> +0x138 is updated AFTER the step in the Physic task; the input task (Player_SendThrustCommands -> Part_HandleCommand ->
Engine_ServoUpdate) runs right after, in the same frame. Servo sees the POST-step b2 angle of THIS frame (no stale sample).
Joint_SetMotor values are consumed in the NEXT frame's b2World_Step (motor set after step N, used in step N+1).
Player_SendThrustCommands (0x1402a9300): h comes from the creature's first body (traverseLinkedListCreature_(creature)) +0x138,
post-step this frame, wrapped to [-pi,pi] with the same floor wrap; NO extrapolation with w. cmd 100/0x65 are sent
synchronously (direct Part_HandleCommand calls, no record queue, no one-frame delay) every tick; 0x66/0x67 follow.
Command angle = vectorCalculateAngles_(m +- h) (h = (sin a, -cos a)); servo error = wrap(cmd - a) as above.
Total command->effect latency: 0 ticks to compute, +1 tick until the motor acts (step N+1). Nothing in this path depends on spin rate.
Lag at hull w=-4.7: hull moves 0.094 rad during the one-step motor delay; also motor max force = part+0x1d8/100 and gain is
power^2 * Stats+0x108 (finite), so a finite torque limit may bite at high spin. If the log (EA 'ang') is sampled
before the Sync or in the next frame vs the command from the previous one, you get an extra w*dt = 0.094 apparent lag.

## Joint_SetMotor / revolute motor decode (2026-10-23)
- Joint_SetMotor (0x1401949d0)(joint, speed, torque): joint+0x10c = speed, +0x108 = torque, +0x104 = (torque != 0).
  If b2 joint (+0xc8) exists and kind (+0xd0) == 1 (revolute): EnableMotor(torque != 0), SetMotorSpeed(speed),
  SetMaxMotorTorque(torque). Values raw: NO clamp, NO scale (no 0.05^n), NO sign flip, NO master/slave reversal. Called EVERY servo
  tick (every frame, once per engine per command); each setter wakes both bodies (flag |= 2, sleep time 0).
- Engine_ServoUpdate passes speed = d*(power*Stats+0x108*power) and torque = part+0x1d8/100 (m_mass / 100, raw).
  Other Joint_SetMotor callers: creatureLogic (4 sites, logic-driven joints, not checked for swivels), cmd-200 handler 0x140051060 (name/decomp stale).
- b2RevoluteJoint_Solve/Init are stock Box2D 2.3: motor impulse clamped to +-(dt*maxMotorTorque), Cdot = wB - wA - motorSpeed
  (A = Joint node 1 (+0x70), B = node 2 (+0x88)). Motor skipped if invI sum==0 (fixed rotation). Warm start: stock.
- Joint_CreateB2Joint (0x140193a10): revolute def: localAnchors explicit, collideConnected 0, enableLimit +0xf4, referenceAngle +0xf8,
  limits +0xfc/+0x100, enableMotor +0x104, maxTorque +0x108, motorSpeed +0x10c. Joint is recreated only if Joint+0xc8 == 0.
- Engine_ApplyThrustForce (0x140028360): thrust force F*(sin a, -cos a) applied to the ENGINE body with Body_AddForceAtPoint
  (vtable +0x170) at the part centre (+0x210/+0x214, "centerX/centerY"), a = chain-summed world angle. Any offset
  between that point and the engine b2 COM / revolute anchor gives a torque on the engine body that the motor
  (cap = mass/100 N*m) must resist. NOT checked: GetThrust scale, the +0x210 offset values, the engine b2 mass/inertia.
  Plausible cause of a held 0.12 rad error: thrust torque (and drag torque) vs the mass/100 cap. ENGINE_04 m_mass not found
  in Ghidra/notes (it's per-part data from OL.seria / design file, part+0x1d8).
- Body angular damping: Body_PreStepUpdate applies none for non-Frame bodies besides linear drag (+0x1dc) and +0x1e4/+0x1ec terms;
  m_drag_ang (+0x1e0) not found used there. b2Body_Ctor copies angular damping from def (param_2[8]?) -- b2BodyDef value not traced.
