# `creatureLogic` id 120: two-stage air-braked warhead (`FireShell` case 70)

Status: **[V]** verified from static disassembly and decompilation in Ghidra 1.163 on 2026-11-01 (image base `0x140000000`).

Question: What does `logic 120` (`body+0x3c4 == 120`) do, and is it tied to planes?

Answer: **No — `logic 120` is not plane code.** It is a two-stage **air-braked cluster mine / delayed warhead** state machine inside `creatureLogic` (`0x140033c5a..0x140033ce5`), spawned only by `FireShell` (`0x1400300d0`) under `case 70` (`0x46`, at `0x1400322b0..0x140032760`), an unused/cut ammo index not assigned to any vanilla ammo in `LoadAmmo`.

---

## 1. Where `logic 120` is spawned (`FireShell` `0x1400300d0`, `case 0x46`)

A full-binary byte-pattern search for `MOV dword ptr [reg + 0x3c4], 0x78` (`c4 03 00 00 78 00 00 00`) has exactly **one** hit in 1.163: `0x140032650` inside `FireShell` (`case 0x46` = `ammo->index == 70`).

When `FireShell` runs `case 0x46` (`0x1400322b0..0x140032760`):
1. It rotates the firing direction by `-0.3 rad` and loops **6 times** (`lVar26 = 6`), stepping the direction by `+0.1 rad` each iteration (`0.6 rad` / `34.4 deg` fan).
2. For each of the 6 projectiles, it allocates a `Body` (`New(0xa40)`), calls `CreateShell_(body, x, y, 2.0, 2.0, 1000.0, 3)`, attaches a `"shrap"` sprite, and initializes:

| Offset | Field | Value written | Address | Meaning |
|---|---|---|---|---|
| `+0x1fc` | `bullet` | `1` | `0x1400323af` | Continuous collision (CCD) enabled |
| `+0xf4` / `+0xf8` | `desowningTimer` / `Time` | `3.0f` | `0x1400323c4` | 3.0 s owner-collision grace |
| `+0x1f0` | `layer` | `7` | `0x1400323ea` | Projectile/aircraft collision layer mask |
| `+0x2c0` | `ttl` | `30.0f` (`0x41f00000`) | `0x140032609` | 30-second lifetime |
| `+0x2b8` | `collisions` | `1` | `0x140032613` | Collision flag |
| `+0x2c8` / `+0x2cc` | `health` / `healthMax` | `10.0f` (`0x41200000`) | `0x14003261d` | 10 HP |
| `+0x2dc` | `explosivePower` | `0.0f` | `0x140032631` | **Unarmed at launch** |
| `+0x2e4` | `explosiveType` | `2` | `0x14003263b` | Explosive type 2 |
| `+0x1c0` | `meta` | `0x85` | `0x140032645` | Body metadata flags |
| `+0x3c4` | `logic` | **`120` (`0x78`)** | `0x140032650` | `creatureLogic` id 120 |
| `+0x3c8` | `logicActive` | `1` | `0x14003265a` | Runs `creatureLogic` each tick |
| `+0x3cc` | `state` (`m_logic_i1`) | `0` (from ctor) | — | Starts in stage 0 |
| `+0x3d0` | `logicF1` (`m_logic_f1`) | **`1.2f`** (`0x3f99999a`) | `0x140032661` | Stage-0 countdown timer (s) |
| `+0x3d4` | `logicF2` (`m_logic_f2`) | **`20.0f`** (`0x41a00000`) | `0x14003266b` | Linear drag (`+0x1dc`) applied after stage 0 |
| `+0x3d8` | `logicF3` (`m_logic_f3`) | **`500.0f`** (`0x43fa0000`) | `0x140032675` | Explosive power (`+0x2dc`) armed after stage 1 |

3. It sets the initial velocity to `sourceBody->velocity` and applies a linear impulse (`vtable+0x190`) of `Random_Float(100.0, 200.0) * 250.0 * body->mass` along the fan direction.

---

## 2. What `creatureLogic` id 120 (`0x140033c5a`) does each tick

In `creatureLogic` (`0x140033b90`), `body+0x3c4 == 120` maps via byte table `0x140045170[119] = 2` to jump table entry `0x14004512c[2] = 0x140033c5a`.

### Disassembly (`0x140033c5a..0x140033ce5`)

```
140033c5a: CMP   byte ptr [0x143a11909], R14B       ; skip if paused (R14 = 0)
140033c61: JNZ   0x14004501f
140033c67: MOV   ECX, dword ptr [RSI + 0x3cc]       ; ECX = state
140033c6d: TEST  ECX, ECX
140033c6f: JZ    0x140033cb0                        ; state == 0 -> Stage 0
140033c71: CMP   ECX, 0x1
140033c74: JNZ   0x14004501f                        ; state != 1 -> exit

; --- Stage 1 (state == 1): arm warhead after 1.0 s ---
140033c7a: MOVSS XMM1, dword ptr [RSI + 0x3d0]      ; timer logicF1
140033c82: XORPS XMM0, XMM0
140033c85: COMISS XMM0, XMM1
140033c88: JBE   0x14003fbf6                        ; if timer >= 0: timer -= dt and return
140033c8e: MOV   dword ptr [RSI + 0x38c], 0x461c4000 ; contact threshold +0x38c = 10000.0f
140033c98: MOV   EAX, dword ptr [RSI + 0x3d8]       ; EAX = logicF3 (+0x3d8 = 500.0f)
140033c9e: MOV   dword ptr [RSI + 0x2dc], EAX       ; explosivePower (+0x2dc) = logicF3
140033ca4: MOV   dword ptr [RSI + 0x3c4], R14D      ; logic (+0x3c4) = 0 (finished)
140033cab: JMP   0x14004501f

; --- Stage 0 (state == 0): deploy air brake after logicF1 (1.2 s) ---
140033cb0: MOVSS XMM1, dword ptr [RSI + 0x3d0]      ; timer logicF1
140033cb8: XORPS XMM0, XMM0
140033cbb: COMISS XMM0, XMM1
140033cbe: JBE   0x14003fbf6                        ; if timer >= 0: timer -= dt and return
140033cc4: MOV   EAX, dword ptr [RSI + 0x3d4]       ; EAX = logicF2 (+0x3d4 = 20.0f)
140033cca: MOV   dword ptr [RSI + 0x1dc], EAX       ; dragLinear (+0x1dc) = logicF2
140033cd0: MOV   dword ptr [RSI + 0x3d0], 0x3f800000 ; timer logicF1 (+0x3d0) = 1.0f
140033cda: LEA   EAX, [RCX + 0x1]
140033cdd: MOV   dword ptr [RSI + 0x3cc], EAX       ; state (+0x3cc) = 1
140033ce3: JMP   0x14004501f
```

### Summary of the two-stage timeline
1. **Launch (`t = 0.0 s`):** Fired unarmed (`explosivePower = 0`, `dragLinear = -1.0`/none, `state = 0`, `logicF1 = 1.2 s`).
2. **Air-brake deployment (`t = 1.2 s`, transition `state 0 -> 1`):**
   - `body->dragLinear` (`+0x1dc`) is set to `logicF2` (`20.0f`), activating quadratic air drag (`F = -0.5 * 1.29 * 20.0 * |v|^2 * v_hat` in `Body_PreStepUpdate` `0x14001d921`) so the sub-munition rapidly decelerates in mid-air.
   - `logicF1` (`+0x3d0`) is reset to `1.0 s`.
3. **Warhead arming (`t = 2.2 s`, transition `state 1 -> logic 0`):**
   - Contact detonation threshold `body+0x38c` is set to `10000.0f`.
   - `body->explosivePower` (`+0x2dc`) is set to `logicF3` (`500.0f`).
   - `body->logic` (`+0x3c4`) is cleared to `0` so the state machine stops running; the sub-munition remains a live `500`-explosive floating/falling contact mine until its `30.0 s` TTL expires.

---

## 3. Why `logic 120` is NOT tied to planes (and the `+0x120` offset lookalike)

1. **Plane bodies and weapons use different logic IDs:**
   - **Aircraft body (`CRAFT_LA29`, `CRAFT_T7`):** `body+0x3c4 = 500` (`0x1f4`)
   - **Dropped aircraft bombs (`MDL_BOMB_01` spawned by `0x140265b70` from `AircraftLogic_UpdateAttackRun` `0x140009a80`):** `body+0x3c4 = 100` (`0x64`, plain contact-arming shell/bomb logic)
   - **Aircraft unguided rockets (`ITEM_NAR122`, `ITEM_NAR340`):** `body+0x3c4 = 130` (`0x82`)
   - **Aircraft K-13 AA missiles (`MDL_MISSILE_03` spawned by `AircraftLogic_LaunchAAMissile` `0x14000f5b0`):** `body+0x3c4 = 4`
   - **Aircraft 37 mm gun shells (`ITEM_GUN37`):** `body+0x3c4 = 100` (`0x64`)

2. **The `AircraftLogic + 0x120` offset lookalike:**
   - In `AircraftLogic`, **hex offset `+0x120`** is the `std::list` head for class-2 **bombs** (count at `+0x128`), populated by `Aircraft_AddAmmoToList120` (`0x140007aa0`), alongside `+0x130` (`Aircraft_AddAmmoToList130`, rockets) and `+0x140` (`Aircraft_AddAmmoToList140`, K-13).
   - The `120` in `Aircraft_AddAmmoToList120` / `logic+0x120` is a struct byte offset (`0x120`), not `creatureLogic` ID `120` (`0x78`).

3. **Can a modded plane use `logic 120`?**
   - Yes, indirectly: plane guns (class 4) and plane rockets (class 3) both fire through `FireShell` (`0x1400300d0`). If a mod sets a custom plane ammo record's `index` (`ammo+0x28`) to `70` (`0x46`), firing it from a plane will spawn the 6-pellet `logic 120` air-braked mine spread.
