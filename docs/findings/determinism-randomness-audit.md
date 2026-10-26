# Randomness / non-determinism audit of ship flight and engines (1.163)

Done 2026-10-23 for the simulator session. Method: Ghidra script over the direct-call graph from each root
(depth 1-4), flagging (a) calls through the HGE object (global 0x143a119e0): vtable +0x108 (Random_Int-like), +0x110 (Random_Float(min,max)),
+0x100; (b) CRT rand/srand, AssignRandomId, Perlin; (c) _Xtime_get_ticks / _time64 / GetTickCount-like calls. Indirect/vtable-only
callees are NOT followed, so a random call behind a virtual call is not seen (confidence note below).

## 1. RNG in flight/engine paths
No RNG at all (nothing flagged within the searched depth) in: Body_PreStepUpdate (0x14001d440, 38 fns searched), Body_SyncFromB2, Engine_ServoUpdate
(0x140053690), Joint_SetMotor, Part_HandleCommand, Player_SendThrustCommands' own code, CalculateStats (0x14007fcf0, 52 fns), Creature_BurnFuel (only a
_Xtime_get_ticks inside rep_1402a2f40_New = UI/log), PhysicTask, b2World_Step.
RNG found, with effect:
- Engine_ApplyThrustForce 0x140028360: HGE+0x110 at 0x140028882/0x140028914/0x140028938 = camera shake (FAST_SHAKE_X/Y) and flame light flicker. Visual only; the force F is computed before and has no random term.
  Its helper 0x140215430 (flame particle setup) also uses HGE randoms: visual.
- Body_BurnUpdate 0x140054850 (from Part_Tick 0x140054fb0): HGE+0x110 at 0x1400549ec (flame intensity value stored at +0x2f4, 0.5..1.5 range, visual/scale) and 0x140054ae6: a ~5% per call chance (threshold DAT_140354738) to remove one crew member (+0x804) of a burning part. That changes crew counts -> can change stats via crew.
  The burn damage and temperature rise themselves are deterministic (hp -= min(+0x334, k*dt), T += dt*Stats+0xc0).
- World_ThermalPass 0x140127810: its random calls all sit in FUN_1401c7270 (explosion/particle spawn: direction, spread, life, explosion sounds). Visual/sound. No random heat dose found in the thermal pass itself.
- creatureLogic 0x140033b90: ~45 random sites. Checked 14003b430 (random re-roll of the logic_f1 timer from logic_f2: timer between 2*f2.. for the weapon fire logic), 14003b64d (particle value), the rest sit in FireShell 0x1400300d0 (muzzle spread/ammo effects), FUN_14022ad00, FUN_14002d3b0, BulletImpact (0x140052a80). Stabiliser case NOT individually examined (decompile of creatureLogic fails/times out); no random call was seen in the code near the engine command sums.
- AI: AiRerollAmmoFlags 0x140079810 (random ammo-type flags +0xc74..0xc76 from probabilities), AiShipTick 0x140062f90 (0x140065c6c / 0x140065dea: random roll vs a threshold to decide a launch/fire gate, combined with a wall-clock toggle flag DAT_1403ef11c/118 using _Xtime_get_ticks, seconds-scale), AiWeaponController 0x14007a8d0 (0x14007abc1/0x14007adb2). These make weapon/missile decisions non-deterministic; they do not touch the steering/engine command code that I saw (AiShip_SteerController 0x14006cb30: only reaches Engine_ApplyThrustForce's visual randoms).
- Engine MISFIRE / flicker / tolerance of thrust: none found. F = GetThrust(stats +0xf8) * strength * g (x1.2 perk, x0.01 spool); no random factor.

## 2. Wind / seeds
Body_PreStepUpdate has no wind term (drag, gravity, +0x1ec attraction only), no random. Perlin_BuildTables (0x140283930) uses rand() four times and Perlin_Noise2D_Octaves (0x140283c30) calls srand: used by generateCityLandscape (level/map generation), not by flight. initGame calls std::random_shuffle (0x1401a3a60). Whether the CRT rand seed is fixed per battle: not checked (only matters for terrain/map generation).

## 3. Engine-side
See 1. Random only in: crew-loss while burning (5%/call), flame intensity (visual), camera shake/flicker, AI ammo/launch rolls.

## 4. Wall-clock / frame time
- !FrameFunc (0x1401a8970) computes time_related_global_ (0x1403c126c) = (1.0 / coreFrameRateFlt_ ) * timescale (0x1403c0dec), coreFrameRateFlt_ (0x1403c0de4) is the constant 50.0 (bytes 00 00 48 42), timescale default 1.0, written only by FUN_140240b90; time_related_global_ is forced to 0 when the pause flag (0x143a11909) is set.
  So the gameplay dt is 0.02*timescale, independent of the real frame time. b2World_Step is called with 1.0/coreFrameRateFlt_ = exactly 0.02 s and 10 iterations ("10" as the 3rd arg), once per PhysicTask.
- QueryPerformanceCounter is only used as profiling brackets (Something*Task start/end), _Xtime_get_ticks/_time64 are logging, save timestamps, AI wall-clock toggles (AiShipTick) and UI.
- Not verified: how often HGE calls FrameFunc when a frame is late (HGE fixed-FPS loop semantics). If FrameFunc is called once per 20 ms tick, the physics is fixed-step; a late frame would just run late, not with a different dt.
- Uninitialised memory reads: not audited.
- Body iteration order: PhysicTask iterates somethingBodyArray_ (insertion/creation order, rebuilt by BodyArray_RebuildFromGlobalNode); no hashing/pointer-keyed order seen in the physics loop. b2 uses its own body list (creation order).

## 5. Box2D
b2World_Step is stock-like, called once per frame with dt=0.02, no randomisation of body/contact order found. PhysicTask also puts bodies to sleep-like state (vtable +0x68) for slow bodies when the body count exceeds 500 (the "loopVarLessThan15000 - 500" loop): deterministic by array order but only matters on huge scenes. Sleeping/waking flags are stock Box2D (joint setters wake both bodies every call).

## Confidence
- No RNG in force/torque/servo/motor path: high (direct-call graph + the functions read end to end: servo, SyncFromB2, SetMotor, ApplyThrustForce, PreStepUpdate).
- Misses possible via virtual calls (Part_Tick -> virtual methods, creatureLogic -> virtual) that the scan does not follow, and the stabiliser case of creatureLogic was not read: medium.
- Fixed dt = 0.02: high for the gameplay code; medium for HGE's late-frame behaviour.

## LVL_WIND_FORCE (2026-10-23)
- String at 0x140375c18, referenced once: InitializeLevelProperties 0x1402da04f creates a 0x40-byte Property object (name copied to +0x8,
  default float copied to +0x38, pointer to the target global stored at +0x30). Target global = float at 0x1403c2b60 (static image value
  0x466a6000 = 15000.0, probably irrelevant because the level file value overwrites it on load).
- xrefs to 0x1403c2b60: the Property init (READ of the default + LEA), and one WRITE at 0x1402cbdfd (level-state reset, sets it to 0 together with
  0x1403c2b58, 0x1403c2b5c and flag 0x147fc6f82). NO other instruction reads the global by address: no reader in Body_PreStepUpdate, Engine_*, FireShell,
  particles, sound, AI.
- Conclusion: the value is written by the level loader through the property object and nothing in the code reads it. LVL_WIND_FORCE has no effect on
  ships, shells, missiles, flares, debris, particles, sound or AI. Value is constant after load (no time or random term), since nothing consumes it.
- Caveat: a reader that gets the value only through the Property object (generic property get by name/pointer +0x30) would not show in xrefs. I
  searched xrefs only; I did not enumerate property-object reads. Confidence high (~90%).

## Intra-frame order for the swivel servo (2026-10-23, for sim.44/45 fast-spin lag)
One !FrameFunc tick k (see also hull-stabiliser-engine-logic.md addenda 2/3):
1. SomethingPreTask 0x140286e40: BreakUpFrame, CollectDeadNodes, Creature_RecalcStatsPass (CalculateStats(c,0,0), zeroes thrust sums), then FUN_140194b10 (= Joint_EnsureB2Joint) for every joint in GlobalNode+0x110.
   FUN_140194b10 destroys + recreates the b2 joint ONLY if the linked node ids differ (joint+0xc0 != node2+0x90 or joint+0xa8 != node1+0x90); otherwise returns 1 and touches nothing. No reset/warm-start loss in steady flight. (Recreate would restore motor values from joint+0x10c/0x108.)
2. PhysicTask 0x140286380: (a) vtable+0x168 Body_PreStepUpdate (drag/gravity/ttl; no engine or servo, no angle writes); (b) snapshot loop (+0x158 = +0x13c etc.); (c) b2World_Step(0.02, 10): uses the motor speed/torque, the forces (Body_AddForceAtPoint) and the stabiliser dw set in frame k-1; (d) vtable+0x160 Body_SyncFromB2: +0x138 = b2 angle(k), +0x13c = b2 w(k).
3. InputTask 0x14018dbf0 -> Player_SendThrustCommands: ALL parts get cmd 100/0x65 first (Engine_ServoUpdate: reads +0x138 = post-step angle(k), writes motor speed/torque via Joint_SetMotor, wakes bodies), THEN a second loop over all parts with 0x66, then a third with 0x67 (Engine_ApplyThrustForce). So in one frame: every servo, then every thrust force.
4. AITask 0x140011180: AI ships' steering/engine calls (same functions).
5. GameTask 0x140127590: World_ThermalPass (thermal substeps, dose reset), then vtable+0xa8 loop: CreatureUpdate -> Part_UpdateDispatch -> Part_Tick (timers, fuel, burn) and creatureLogic. Stabiliser (case 200) -> Body_AddTorque(Frame): w += T*0.05^5*invI immediately on the Frame b2 body. Nothing re-syncs +0x13c or the children/joint; the Frame's b2 w already includes dw when step k+1 starts, children keep their own w. Order servo(k) < stabiliser(k) in the same frame; the servo uses angle only, so hull w is not involved (confirmed).
Samples: servo error and thrust direction g=cos(cmd - a) both use angle(k) after the sync of step k (same value; the servo does not move the angle, only sets the motor), the thrust direction uses Body_AddWorldAngle (chain sum of +0x138 along master +0x88: UNVERIFIED that a b2-bodied swivel has no Body-class master, otherwise it would double count the Frame angle).
Motor set in frame k acts during step k+1, thrust force set in frame k is applied in step k+1, stabiliser dw of frame k is applied before step k+1. So command, motor and force are all one tick behind angle(k); a log sampled at step ENTRY (before step k+1) shows angle(k) and Frame w(k)+dw; a log sampled AFTER the sync of step k+1 shows angle(k+1) (one tick later) with the motor of frame k already applied. If the hook for the EA row sits on one side and the hull/swivel rows on the other, a one-tick offset (=0.16 rad at 8 rad/s) between the rows arises; the logger hook addresses are not in Ghidra.
No smoothing / rate limit: Engine_ServoUpdate writes motor speed = d*gain, torque = mass/100, nothing else; Part_Tick (0x140054fb0) contains no swivel or angle code; Joint_SetMotor stores raw. Only the b2 stock limits (max rotation per step) apply.

## Swivel direction rule (2026-10-23, for the simulator: error near +-pi)
- Engine_ServoUpdate 0x140053690 is stateless: inputs are cmd (record+4), part+0x138, power +0x818, Stats+0x108, part+0x188/0x1d8/0x230. Record+0x10 is only WRITTEN (d), never read back; no hysteresis, deadband, previous direction, per-part sign/mirror flag, or |d|~pi special case. Banks differ only by command code (100 = bank 1, 0x65 = bank 2) chosen by the part's spasmcode list; Part_HandleCommand 0x1400533f0 passes the record to the servo unchanged (no hull-relative transform, no mirroring, no normalisation).
- Exact float32 sequence (each wrap: n = (int)floorf(|x|/6.2831855f + 0.5f), sign applied, x -= n*6.2831855f):
    c = wrap(cmd); if (c < 0) c += 2pi        // cmd to [0,2pi)
    a = wrap(angle); if (a < 0) a += 2pi      // +0x138 to [0,2pi); handles unwrapped b2 angles (float precision loss for large |angle|)
    d = c - a; d = wrap(d)                     // nearest-wrap, NOT atan2/fmod; ties at |d|=pi decided by float rounding of floorf(|d|/2pi+0.5)
  Because both operands are first mapped to [0,2pi) with float32 rounding, a plain wrap(cmd - a) differs near |d|=pi. Examples: cmd=3.13974, a=-0.00022 -> a'=6.2829655, d=-3.14322, |d|/2pi+0.5 = 1.0002 -> n=-1 -> d=+3.13996 (swings positive, matches the log). cmd=+pi (3.1415927), a=-8e-7 -> a'=6.2831845 (float), d=-3.1415918, |d|/2pi+0.5 = 0.99999997..: floor gives 0 unless the float sum rounds to 1.0 -> d stays about -pi (negative swing) in the first case, flips to +pi if rounded up. Port the float32 sequence exactly (including the 2pi value 6.2831855f and 0.5f adds) instead of double math.
- Command angle: vectorCalculateAngles_ 0x14000dda0(v): n = v/|v| if |v| != 0; returns atan2f(n.x*0 - n.y*(-1)?...) simplified: angle = atan2f(n.x, -n.y), range (-pi, pi], so that (sin a, -cos a) = n. (code: atan2f(y2*0 - x*-1, x*0 - y2*1) with x=f1, y2=f2.) Signed zero matters: for m=0, hull tilt exactly 0: v = m - h = (-sin(0), cos(0)) = (+0, 1) -> atan2f(+0, -1) = +pi (not -pi). With hull tilt a slightly negative, v.x = -sin a > 0 -> y arg positive -> cmd = pi - |a| (matches 3.13974 for a = -0.00185).
- Player_SendThrustCommands 0x1402a9300: h = (sin A, -cos A) with A = hull angle +0x138 of the creature's first body wrapped to [-pi,pi]. v1/v2 = m, m+h, m-h per key flags (see its header comment). If v is exactly (0,0) (both components == 0.0f, e.g. idle with no keys, or m = h) the angle is set to 0 without calling vectorCalculateAngles_. So idle -> cmd 0.
- Joint orientation: the motor speed is d*gain with no sign flip; b2 motor drives wB - wA = speed, so the swivel must be node 2 (B) of its Joint for the servo to be stable; every working ship shows it is. Not checked per joint.
- AI: AiShip_SteerController 0x14006cb30 / AiShipTick call the same Part_HandleCommand -> Engine_ServoUpdate (same rule); their command angles come from their own steering math (not examined here).
