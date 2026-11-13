# Group counts: how many convoys / strike groups / tactical groups spawn (1.163)

Program: `Highfleet.exe.unpacked.exe` v1.163, image base `0x140000000`.
Re-audited 2026-11-13 from the live Ghidra program (byte-level disassembly of the
loop sites; guard bytes read from memory). Not validated in game. Tags: [code].

Companion to [enemy-ship-pools.md](enemy-ship-pools.md). This note pins the exact
spawn-count sites so mods can adjust "how many groups exist in total" per
category (implemented in `hf_hee` v0.4.0 as the `count` field on `traders`,
`strikegroups`, `tactical_air`, `tactical_missile`).

## 1. Trade Convoys — count is a call argument (vanilla 30)

* The convoy spawn loop is `FUN_14028fec0(RCX = profile, EDX = count)`. Inside, the
  count lands in `EBP` and `[RSP+0x20]` (`0x14028ff03`/`0x14028ff05`); the loop tail
  is `INC R12D; CMP R12D, [RSP+0x20]; JL 0x140290050` (`0x140290150`-`0x140290158`),
  and `TEST EBP, EBP; JLE` (`0x140290029`) skips the loop entirely for `count <= 0`.
  Each iteration picks a random eligible city (up to 10 tries, `CMP EBX, 0xa`) and
  calls `spawnTradeConvoy?` (`0x140208660`) at `0x1402900c3`.
* **Sole caller** of `0x14028fec0` (xref check): `0x14028fd6b` in
  `restOfEventsPrologueAntIsaiah` (`0x14028de70`), preceded by
  `MOV EDX, 0x1e` at **`0x14028fd63`** (5 bytes `ba 1e 00 00 00`) — the vanilla
  **30 convoys** at campaign start. Resume point after the immediate:
  `0x14028fd68` (`MOV RCX, R13; CALL 0x14028fec0`).
* The quest convoy (`CROW50`, `0x1400a9617`) calls `spawnTradeConvoy?` directly and
  is not part of this count.
* **Hook:** detour the 5 bytes at `0x14028fd63` and re-emit `MOV EDX, imm32` with the
  adjusted count, then jump to `0x14028fd68`.

## 2. Strike Groups — three wave loops (vanilla 6 / up to 4 / 3)

`Endgame_BuildEscadra` (`0x1402077c0`) has exactly three code callers:
`0x14028fce9` (campaign), `0x140262481` (Khiva assault), `0x1402628ce` (outer
Nuclear War) — all inside `spawnEndgameShips?` (`0x140261a20`) except the first.

### 2.1 Campaign roaming Strike Groups — integer loop bound (vanilla 6)

In `restOfEventsPrologueAntIsaiah`:

* `XOR ESI, ESI` at `0x14028fb5d` initializes the counter; loop head `0x14028fb90`.
* Loop tail: `INC ESI` (`0x14028fd4b`), then **`CMP ESI, 0x6; JGE 0x14028fd5f`** at
  **`0x14028fd4d`** (5 bytes `83 fe 06 7d 0d`). Fall-through (`0x14028fd52`,
  `MOVSS XMM0, [0x1403c0e24]; JMP 0x14028fb90`) continues the loop; `JGE` exits to
  `0x14028fd5f` (which immediately starts the convoy spawn, `MOV EDX, 0x1e`).
* `ESI` is otherwise only read in the body (`MOVD XMM6, ESI` for the per-group
  budget ramp at `0x14028fc5f`), so replacing the immediate is safe.
* **Hook:** detour the 5 bytes at `0x14028fd4d`; trampoline emits
  `CMP ESI, imm32(new)` + `JGE` to `0x14028fd5f`, fall-through jumps to
  `0x14028fd52`.

#### 2.1a Why high counts stack on one city (and the sprinkle fix)

Each loop iteration picks the spawn city by scanning `Profile::locations`
(`[profile+0x210]`..`[profile+0x218]`, fetched at `0x14028fbb2`/`0x14028fbb9`) **in
vector order**, keeping a city only if dword `[loc+0x2e8] >= 2` (`0x14028fbd8`),
float `[loc+0x248] != 0.0` (`0x14028fbe1`), and — once a candidate exists — a
Y-spacing rule (`COMISS XMM6, |loc.y - XMM7|` at `0x14028fc06`, threshold relaxed
per iteration by `SUBSS XMM7, XMM0` at `0x14028fb95`). The scan result lands in
`RBX` (`MOV RBX, RAX` `0x14028fc1b`), scan exit is **`TEST RBX, RBX; JZ 0x14028fd4b`
at `0x14028fc27`** (9 bytes `48 85 db 0f 84 1b 01 00 00`). With vanilla's 6
iterations this yields ~6 different cities; with e.g. `*50` (300 iterations) the
same first-eligible city wins almost every time — observed in a real save:
295 of 300 role-5 escadras at city `ISA` (1428.7, -10930), only 6 distinct
positions total.

* **Sprinkle hook:** detour the 9 bytes at `0x14028fc27`; trampoline calls a helper
  returning a **uniformly random eligible city** (same `+0x2e8 >= 2` /
  `+0x248 != 0` filters, `HGE::RandInt(0, eligible-1)` over the vector), then
  `MOV RBX, RAX; TEST RBX, RBX; JZ` — continue `0x14028fc30`, skip `0x14028fd4b`.
  `RBX` is the spawn position (`LEA R8, [RBX+0x150]` `0x14028fccf`) and the
  escadra's linked city (`0x14028fd0b`), so both move together. Implemented as
  `strikegroups.sprinkle` in `hf_hee` v0.5.0, **default-on since v0.5.1**
  (`"sprinkle": false` restores vanilla).

  **[game] Confirmed in a real save** (`Saves/Profile_1/profile.seria`, Steam
  1.163, 2026-11-13, `"count": "*50"` on `traders` + `strikegroups`, hf_hee
  v0.4.0): exactly 1500 role-1 convoys (30×50) and 300 role-5 SGs (6×50);
  without sprinkle 295/300 SGs at city `ISA`, convoys spread over 853 distinct
  positions. v0.5.1 sprinkle validated in game (SGs spread across cities).

### 2.2 Endgame Khiva assault wave — vector walk (vanilla up to 4)

In `spawnEndgameShips?` (`0x140261a20`):

* The four quadrant lists each get their first city marked state `2`
  (`0x140262226`-`0x140262279`, the known unguarded writes), then those cities are
  collected into a vector (`begin` at `[RBP+0x28]`, `end` at `RSI`).
* Spawn loop: entry check **`CMP RBX, RSI; JZ 0x14026333f`** at **`0x1402623de`**
  (9 bytes `48 3b de 0f 84 58 0f 00 00`; `RBX = [RBP+0x28]` = begin); body starts
  `0x1402623e7` and spawns at `0x140262481` (`role` overwritten to `6` at
  `0x1402624ce`); per-iteration tail `ADD RDI, 8; CMP RDI, RSI; JNZ 0x140262403`
  (`0x1402625d1`-`0x1402625d8`).
* `RSI` is read nowhere else in the body except the tail compare, and is reloaded
  after the loop on every path (`0x1402625f3`); `RAX` is dead at the entry check
  (reloaded at `0x140262429` in the body, `0x140263357` on the exit path). No `RSI`
  read on the `0x14026333f` exit path within 200 instructions.
* **Hook:** detour the 9 bytes at `0x1402623de`; trampoline emits
  `LEA RAX, [RBX + 8*count]; CMP RAX, RSI; CMOVG RAX, RSI; MOV RSI, RAX` (clamp the
  walk end to `min(end, begin + 8*count)`), then re-emits `CMP RBX, RSI` +
  `JZ 0x14026333f`, continuing at `0x1402623e7`. `count == 0` makes the entry `JZ`
  fire (zero spawns); otherwise the wave spawns `min(count, vector_len)` groups.

### 2.3 Endgame outer Nuclear War wave — integer loop bound (vanilla 3)

In `spawnEndgameShips?`:

* 100-try city search loop head at `0x1402626e0`; each found city spawns an SG at
  `0x1402628ce`; the spawned counter `[RBP-0x60]` is incremented at `0x1402629ab`
  (`INC EAX` into `EAX`).
* Loop tail: **`CMP EAX, 0x3; JL 0x1402626e0`** at **`0x1402629b1`** (9 bytes
  `83 f8 03 0f 8c 26 fd ff ff`). `JL` continues the search at `0x1402626e0`;
  fall-through exits at `0x1402629ba`.
* **Hook:** detour the 9 bytes at `0x1402629b1`; trampoline emits
  `CMP EAX, imm32(new)` + `JL` to `0x1402626e0`, fall-through jumps to `0x1402629ba`.

## 3. Tactical Air / Missile Groups — per-city chance, not an integer count

Tactical groups are appended onto pool-0 garrison fleets by the `chanceA` /
`chanceB` post-roll branches of `somethingSpawnShips` (`0x140203b80`), so the
number of tactical groups in total is driven by those per-city probabilities
(vanilla `0.15` normal / `0.20` hard, `0` within 5000 of `"UR"` on normal — the
near-UR zeroing happens in `Prologue_SpawnEventEscadra` `0x1402038e0`, which
forwards them as `XMM3` / `[RSP+0x28]`).

* Callers of `somethingSpawnShips` with non-zero chances: only the four
  `Prologue_SpawnEventEscadra` sites in `restOfEventsPrologueAntIsaiah`
  (`0x14028e9f6`, `0x14028ecc8`, `0x14028efe3`, `0x14028f477`, all pool `0`).
  Mercenary pools (`0x1402a8342` pool `2`, `0x140262bda` pool `4`) pass `0.0`.
* **Hook:** no new site needed — adjust `chanceA`/`chanceB` inside the existing
  `somethingSpawnShips` entry detour, gated on `poolId == 0`, so merc pools keep
  their vanilla `0.0`. Scaling the chance is what scales the total number of
  tactical groups (`0` disables the type, `>= 1` gives every city one).

## 4. Guard bytes (read from memory 2026-11-13)

| Site | RVA | Bytes | Stolen | Meaning |
|---|---|---|---|---|
| Trader convoy count | `0x14028fd63` | `ba 1e 00 00 00` | 5 | `MOV EDX, 0x1e` |
| Campaign SG bound | `0x14028fd4d` | `83 fe 06 7d 0d` | 5 | `CMP ESI, 6; JGE` |
| Khiva wave entry | `0x1402623de` | `48 3b de 0f 84 58 0f 00 00` | 9 | `CMP RBX, RSI; JZ` |
| Outer wave bound | `0x1402629b1` | `83 f8 03 0f 8c 26 fd ff ff` | 9 | `CMP EAX, 3; JL` |
| Campaign SG city pick (sprinkle) | `0x14028fc27` | `48 85 db 0f 84 1b 01 00 00` | 9 | `TEST RBX, RBX; JZ` after the location scan |
