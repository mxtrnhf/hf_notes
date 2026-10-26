# Aircraft AI out-of-bounds read: a stock crash at `0x140010a51` (1.163)

Status: **read in Ghidra 2026-10-20 [code]; the crash itself seen in play [game], session 1792493861 (hf_ally sim.17 megalog, `hf_ml/data/sim_runs7`)**. Full report: `hf_ml/out/ds2-plane-crash/REPORT.md`. **Proper bug report (details, intended logic, QA text, fix): [aircraft-logic-bug-report.md](aircraft-logic-bug-report.md).**

**Summary:** the aircraft AI object `AircraftLogic` is allocated with `New(0x1b0)` (432 bytes; sites `0x1400184ea`, `0x14002e99b`, and `DynNewSerializable`), but its state-6 handler (`0x1400109c0`, called from `aircraftStateHandler` `0x14000fbc0` at `0x14000fd6c`, Ghidra name `...atan2f`) tests `this+0x108`, `this+0x48` and then **`this+0x3c4 == 500`**, which are fields of a plane `Body` (logic id `500`), 0x214 bytes beyond the object. The constructor `0x14000adf0` sets state `+0x118 = 6`, so every new aircraft logic starts in this state. Normally the read returns neighbouring heap data (not 500) and the code takes the usual retarget path; when the object sits at the end of a mapped heap region the read faults: `Highfleet.exe+0x10A51`, access violation reading `this+0x3c4`.

* Stack in the crash: `0x140010a51` <- `aircraftStateHandler` <- `FUN_14000f7a0` <- `creatureLogic` plane case (`0x140038f7c`: `MOV RCX,[RSI+0xa20]; CALL 0x14000f7a0`) <- body update `FUN_140054b20` <- `SomethingGameTask`.
* The first condition probably meant the owner body `*(this+0x50)` (the second condition does test it correctly) [guess].
* **Candidate fix, not applied:** at `0x140010a51` bytes `41 81 BE C4 03 00 00 F4 01 00 00` -> `41 81 BE 48 00 00 00 F4 01 00 00` (compare the state int at `+0x48`, never 500, same path as the garbage in practice).
* Not caused by our mods (the megalog says no hf_ally hook was running); risk grows with many planes alive.
* Open: `DynNewSerializable` size, parse of the `.dmp`, whether garbage == 500 gives a second crash route.

## Update 2026-10-26 (ds3-crash report; bytes at `0x140010a51` re-read by the curator) [code]
* Fix confirmed: bytes at `0x140010a51` are `41 81 BE C4 03 00 00 F4 01 00 00` (`CMP dword [R14+0x3c4],500`); patch `C4 03` -> `48 00`. The read is 0x214 bytes past the 0x1b0-byte object. The normal path is byte-identical for every value except 500, and for 500 it does what the current code does when the foreign dword happens to be 500.
* The patch **does not repair the intended test**: the "mirror the owner's target" shortcut stays dead. A real repair would use the owner Body (`*(this+0x50)`) as the base, as the duplicate correct test at `0x140010a8c`-`0x140010ad7` does; that is far more than 2 bytes.
* Call chain re-read: `creatureLogic` plane case `0x140038f75` loads `[RSI+0xa20]`, `AircraftLogic_Tick` (`0x14000f7a0`, Ghidra name set earlier) -> `aircraftStateHandler` (`0x14000fbc0`, state at `+0x118`) -> state 6 = `AircraftLogic_State6_SelectTarget` (`0x1400109c0`, one caller `0x14000fd6c`). The constructor sets state 6, so every new object starts there.
