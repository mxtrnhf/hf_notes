# BUG REPORT: aircraft AI reads outside its own object (random crash `ACCESS_VIOLATION 0x140010A51`), Highfleet 1.163

Author: ghidra-miner session, 2026-10-20. Program: `Highfleet.exe.unpacked.exe` v1.163 (base `0x140000000`). Read-only analysis; NOTHING was renamed or patched in Ghidra or in the game.
Tags: **[V]** = verified by me in Ghidra bytes/decompile; **[log]** = from the crash logs of session 1792493861; **[guess]** = my inference, with what would confirm it.

## 0. One-paragraph summary
Each aircraft has a big **body** (position, health, type) and a small **AI brain** (432 bytes) that points at the body. The brain's state-6 routine (choose a target) starts with a test that reads three fields that exist only in a **body** (`+0x3c4` "type id = 500"), but it reads them from the **brain**. `+0x3c4` is 0x214 bytes past the end of the brain, so the game reads whatever happens to be in memory after it. Normally that is harmless leftover data and the game carries on; when the brain sits at the very end of a memory region the read falls off the edge and the game crashes. It is **one bug (wrong object read)** with two visible effects, see section 5.

## 1. Where it is (functions and addresses)
All addresses v1.163. "Ghidra name now" is what the program shows today; "Proposed name" is only a suggestion (the user renames by hand).

| Address | Ghidra name now | Proposed name | Role [V unless noted] |
|---|---|---|---|
| `0x1400109c0` (body `..0x140010ff0`) | `rep_1400107f0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` (wrong; the decompiler also prints it under the old 1.151 address `0x1400107f0`) | `AircraftLogic_State6_SelectTarget` | **the buggy function.** Called once, from `aircraftStateHandler` when the brain's state selector `+0x118` is 6 |
| `0x140010a51` | (inside the function above) | - | **the faulting instruction**, see section 2 |
| `0x14000fbc0` (`..0x14000fdcc`) | `aircraftStateHandler` | keep, or `AircraftLogic_RunState` | switch on `brain+0x118`: 0 `0x14000faa0`, 1 nothing, 2 pick the first `logic 10/1` ship, 3 `0x140010100`, 4 clear target, 5 `0x140010340`, 6 `0x1400109c0` (call at `0x14000fd6c`, bytes `E8 4F 0C 00 00`), else prints `CHECK ERROR ... AircraftLogic.cpp` line `0x8c7` |
| `0x14000f7a0` (`..0x14000fa24`) | `FUN_14000f7a0` | `AircraftLogic_Tick` | per-frame entry: checks `*(brain+0x50)` (owner body) is alive and logic id 500, then `aircraftStateHandler(brain)` and moves the sprite |
| `0x140038f7c` | inside `creatureLogic` (`0x140033b90`; Ghidra has no function body at this address) | add a comment: "plane case: call AircraftLogic_Tick" | the plane case: `MOV RCX,[RSI+0xa20]` (RSI = plane body) then `CALL 0x14000f7a0`; return address `0x140038f81` is frame 11 of the crash |
| `0x140006b40` | `AircraftLogic` | keep | the constructor; allocates nothing itself, calls the init below at `0x140006c7e` |
| `0x14000adf0` (`..0x14000ae8a`) | `rep_14000a560_CopyString` (wrong) | `AircraftLogic_InitDefaults` | writes the class name "AircraftLogic" (`0x1403525e8`), class code `+0x28 = 0x800000000003`, **`+0x118 = 6`** (initial state), `+0x1ac = 1`, zeroes `+0x64..+0xf8` |
| `0x1400184ea` | in `copyOverBody` (`0x140017e70`) | keep | `MOV ECX,0x1b0 ; CALL New` then `CALL 0x140006b40` (copy of a plane body: brain pointer stored at `body+0xa20`) |
| `0x14002e99b` | in `loadAmmoForAircraft??` (`0x14002e930`) | `SpawnAircraftBodyAndBrain?` [guess: it also creates the brain] | `MOV ECX,0x1b0 ; CALL New` then `CALL 0x140006b40`, result stored at `[body+0xa20]` |
| `0x140202d9f` | in `DynNewSerializable` | keep | same `ECX = 0x1b0`, `CALL 0x140006b40` at `0x140202db5` (the data-driven creation path) |

**The brain is allocated with `New(0x1b0)` = 432 bytes at all three creation sites [V].**

Crash call chain (return addresses from the megalog, session 1792493861, game t=82.64 s) [log]: `0x140010a51` <- `0x14000fd71` (`aircraftStateHandler`) <- `0x14000f834` (`AircraftLogic_Tick`) <- `0x140038f81` (`creatureLogic` plane case) <- `0x140054b5f` (`FUN_140054b20`, per-body update) <- `0x140127a05` <- `0x1401275dc` (`SomethingGameTask`) <- `0x1401a8ed1` <- `0x14017e26a` ... Registers at the fault: `R14 = RDI = 0x13c8fe40` (= the brain, `this`), `RBX = RAX = 0x13c8ff90` (= `this + 0x150`, the target link), fault address `0x13c90204` = `this + 0x3c4`, an unmapped page [log].

## 2. The faulting code, raw bytes [V]
```
140010a40  49 83 BE 08 01 00 00 00   CMP qword ptr [R14+0x108], 0     ; R14 = this (the brain)
140010a48  74 42                     JZ  0x140010a8c                  ; zero -> skip to "choose a target"
140010a4a  41 83 7E 48 00            CMP dword ptr [R14+0x48], 0
140010a4f  74 3B                     JZ  0x140010a8c
140010a51  41 81 BE C4 03 00 00 F4 01 00 00   CMP dword ptr [R14+0x3c4], 0x1F4   ; <-- FAULT. 0x1F4 = 500 = "plane" type id
140010a5c  75 2E                     JNZ 0x140010a8c                  ; not 500 -> "choose a target"
140010a5e  49 8B 96 20 0A 00 00      MOV RDX, qword ptr [R14+0xa20]   ; (second out-of-bounds read, only reached if the 500 test passes)
140010a65  48 85 D2                  TEST RDX, RDX
140010a68  74 22                     JZ  0x140010a8c
140010a6a  8B 82 90 01 00 00         MOV EAX, dword ptr [RDX+0x190]   ; state of another brain (in bounds there)
140010a70  83 E8 06 / 83 F8 01 / 76 14   SUB EAX,6 ; CMP EAX,1 ; JBE 0x140010a8c    ; state 6 or 7 -> "choose a target"
140010a78  48 81 C2 50 01 00 00      ADD RDX, 0x150                   ; other brain's target link
...        ReassignLinkNode(this+0x150, RDX)                          ; "copy the other plane's target"
```
In decompile form (Ghidra, cleaned): `if (this[+0x108]==0 || this[+0x48]==0 || this[+0x3c4] != 500 || (x = this[+0xa20]) == 0 || (x[+400] - 6) < 2) { choose own target } else { ReassignLinkNode(&this[+0x150], &x[+0x150]); }`.

## 3. Which object each offset really belongs to [V unless noted]
| Offset | Used as | Really a field of | In bounds of the 0x1b0 brain? |
|---|---|---|---|
| `+0x50` | owner plane **body** pointer (`FUN_14000f7a0`, this function's second block) | brain | yes |
| `+0x118` | state selector, 6 after construction | brain | yes |
| `+0x128`, `+0x138` | two fields tested for "non-zero" (also in the state-5 handler `0x140010340`); that they mean "has weapon/payload" is a [guess] | brain | yes |
| `+0x150` (`+0x158` node) | current target link (`SetLink`, `ReassignLinkNode`) | brain | yes |
| `+0x190` (= `+400`) | second state ("phase") | brain | yes |
| `+0xc8` | side id, passed to `FUN_140220120` (friend check) | brain | yes |
| `+0x48` | alive flag/state (0 = dead) | both (Node base class) | yes, harmless |
| `+0x108` | child-list pointer | both (Node base class) [guess: same layout in both] | yes, harmless |
| **`+0x3c4`** | **logic id, 500 = plane** | **plane body only** | **NO: 0x214 bytes past the end -> out-of-bounds read** |
| **`+0xa20`** | **pointer to the body's brain** | **plane body only** | **NO: out-of-bounds, reached only if the 500 test passes** |
The same function's second block reads the owner correctly: `owner = *(this+0x50)`, then `owner+0x48`, `owner+0x3c4 == 500`, `owner+0xa20`, `*(owner.brain+400)`. So the author knew the body/brain split; the first block simply uses `this` where a body pointer was needed.

## 4. What the code is trying to do (intended logic)
**What the function does overall [V]:** "re-pick the attack target of this aircraft". Clear the target (`SetLink(this+0x150, 0)`), then if it has no usable target and still has payload (`+0x128`/`+0x138`) it scans ALL ships (`DAT_143faa5d8`), keeps hostile (`FUN_140220120` false), alive, not evac pods, not prize ships (`+0xc19`), scores each by `distance^2 / (1 - (angle/pi)^3)` where angle = between the plane's velocity and the direction to the ship (prefers ships ahead), counts how many aircraft already attack each ship (a map built by `0x14000a030`), and picks the ship with the **fewest attackers** (ties: lowest score). If the target changed it sets the phase `+0x190` to 3 (attack) or 7 and logs `STATE_ATTACK`. So the "usual path" = **load-balanced target choice: aircraft spread over enemy ships.**

**What the first test is for [guess]:** the else-branch copies another brain's target (`ReassignLinkNode(this.link, other.link)`) when `other` is a live plane whose phase is not 6/7. That reads as **"follow the target of another plane (a leader/wingman) if it is already engaged; otherwise choose your own"**.
Evidence: (a) [V] the else-branch is exactly "copy someone else's target link"; (b) [V] the test asks "alive, has children, logic 500, has a brain, brain phase not 6/7", all questions about *another plane body*. **It cannot be the owner:** the owner's brain is `this` (the owner's `+0xa20` points back to this brain, see `creatureLogic`), so the else-branch would copy the brain's own target onto itself (no effect), and its conditions (owner alive, plane, brain phase not 6/7) are a subset of what the "choose a target" block requires anyway, which would make the retarget block unreachable [V logic from the two decompiled blocks].
**Which pointer should be followed [unknown]:** a brain field that points at the leader/wing body. I could not identify it. Candidates are pointer fields in the brain's first `0x150` bytes near the owner pointer (`+0x58`/`+0x60`) or the two `+0x128/+0x138` fields; confirming needs where the aircraft group is built (`0x14000a030`, `FUN_14000f7a0` neighbours) [guess].
**What would happen if it worked [guess]:** the aircraft of a group would adopt the leader's target (focus fire) instead of all load-balancing independently. **What happens today [V reading]:** the test practically never selects the else-branch, so every plane always runs the independent load-balanced choice; the leader-follow feature is dead code. Gameplay effect is small: planes still spread over targets.

## 5. One bug or two? (the user's question)
**One bug: the first test reads body fields from the brain.** Provable consequences:
* **(A) the intended check never works.** The test reads `this+0x3c4` from memory that is not part of the brain. For it to be 500 by accident the leftover must be exactly `0x1F4` (about one in 4 billion for a random int), so the code almost always takes the "choose own target" branch [V reading; the probability is an estimate].
* **(B) rarely the read crashes.** The same instruction reads past the end of a 432-byte block. If that block lies within 0x214 bytes of the end of a mapped heap region the read touches an unmapped page: access violation. That happened once in the logs (`this = 0x13c8fe40`, read at `0x13c90204`) [log].
* **(C) a third, rarer effect of the same defect:** if the leftover happened to be exactly 500 and the next two reads passed, the else-branch would dereference garbage (`[this+0xa20]` is also out of bounds) and copy through a garbage pointer: crash or memory corruption [V code path; never observed].
(A), (B) and (C) are three outcomes of the **same wrong read**, not separate defects. **I cannot prove from the code that the in-bounds reads `+0x108` / `+0x48` are meaningless** (they exist on both objects); they are harmless either way. I also cannot rule out other places in the game with the same brain/body confusion; I found none in `aircraftStateHandler`, `AircraftLogic_Tick` or the state-5 handler (`0x140010340`), which all use `*(this+0x50)` correctly [V for these three].

## 6. Plain-language explanation (for a QA tester)
**The two-objects picture.** Think of every aircraft as two cards in a filing cabinet: a thick **body card** (where it is, how healthy it is, "type: 500 = aeroplane" written on line 964) and a thin **brain card** (432 lines: who it is chasing, what state it is in; it also has a note saying which body card it belongs to). The routine that picks a target is supposed to look at a body card, but the programmer gave it the brain card by mistake. It asks the thin card "what does line 964 say?". The thin card has only 432 lines, so the game just reads the next 532 lines of the cabinet, which belong to some other card.
**Why it usually works.** Whatever is stored there is never exactly the number 500, so the routine answers "not a special case" and carries on with the normal target choice. The answer is wrong in theory, right in practice.
**Why it crashes only sometimes.** If the thin card happens to be the very last card in a drawer, line 964 is *beyond the end of the drawer*; there is nothing to read and Windows kills the program. Where each brain card lands depends on the game's memory at that moment, so every newly created aircraft is a small roll of the dice, and it is the same card every time it is read (the dice are rolled when the aircraft is created, not on every frame).
**How a developer makes this mistake.** The check was probably copied from code that already had the body in hand (where `+0x3c4` is correct), then pasted into a function that holds the brain. C++ does not check that a read stays inside an object, so the program compiles, runs, and passes every normal test.
**How to reproduce it more often.** Launch lots of aircraft (carrier-type ships, repeated launches): each new aircraft is another dice roll. In our logs 42 aircraft in one battle did not crash, 20 launched in another did, so expect maybe one crash in many battles. A deterministic way (developer/QA with the game under a Windows debugger) is to enable full page heap for `HighFleet.exe` (`gflags /p /enable HighFleet.exe /full`): then every allocation ends at a page boundary and the very first aircraft read faults; under Wine/Proton the equivalent is not known to me [guess].
**QA-style summary.** *Steps:* start a tactical battle against ships that launch many aircraft (e.g. carriers / multiple A/C launchers), let several waves launch and fly. *Expected:* the battle continues normally. *Actual:* occasionally (rarely, random) the game closes to desktop without a message; the game's `error.log` lists `ACCESS_VIOLATION address 40010A51`. *Frequency:* low, not tied to a player action. *Workaround:* none.

## 7. Severity and impact
* **Severity:** crash to desktop (major), **low and random frequency**, no save corruption known. Not caused by any mod (the mod loader's crash reporter says "hf_ally hook running: none (the game's own code)") [log].
* **Impact:** loses an unsaved battle; the risk grows with the number of aircraft created. The same defect could in principle (garbage exactly 500) corrupt memory instead of crashing; never observed.
* **Gameplay side effect:** the "follow the other plane's target" branch is permanently dead; effect on play is probably tiny (planes still choose load-balanced targets).

## 8. Candidate fix (NOT APPLIED; needs the user's OK and a mod/patch to carry it)
Change **2 bytes** at `0x140010a53`-`0x140010a54`: `C4 03` -> `48 00`, so the instruction at `0x140010a51` becomes
`41 81 BE 48 00 00 00 F4 01 00 00` = `CMP dword ptr [R14+0x48], 0x1F4` (compare the brain's own alive/state int, which is never 500).
* **Side effects / equivalence:** the test becomes constantly "not 500", so `JNZ` always jumps to `0x140010a8c` = "choose own target", **which is exactly what the game does in practice today** (garbage not 500). It removes the out-of-bounds read (and the unreachable `[this+0xa20]` read). It does **not** restore the intended leader-follow behaviour.
* **Rare case garbage == 500:** the original would enter the else-branch with garbage pointers (crash or corruption); the patched code always takes the safe "choose own target" path. So the patch is strictly safer and behaves identically in every case that works today.
* A faithful repair (follow the correct pointer) needs the leader pointer identified first (section 4) and a longer patch.
* The patch needs a version guard (the bytes at `0x140010a51` must match section 2 before writing), as for our other patch sites.

## 9. Open points
* Which brain field points at the leader/wing plane, and whether leader-follow was ever used (needs a read of the aircraft group setup).
* Whether state `+0x118` stays 6 for the brain's whole life (what changes it) and how often the state-6 routine really runs per plane; this decides the number of reads but not the crash risk, which is per allocation.
* The memory dump `hf_ally_crash_1792493950.dmp` was not parsed (what the leftover bytes looked like).
