# `creatureLogic` (0x140033b90) dispatch: logic id (+0x3c4) to code block (v1.163), ghidra-miner, 2026-10-21

Tag **[V]** (jump and byte tables read from the image). `creatureLogic` is vtable `+0x1e8` of a body; `Part_UpdateDispatch` `0x140054b20` calls it every tick after `Part_Tick` when `+0x3c8` (m_logic_active) is non-zero. Dispatch: `id = [body+0x3c4]`; `id > 400` jumps to `0x140038d27`; `id == 400` to `0x140038767`; otherwise `idx = byte[0x140045170 + (id - 1)]` (ids 1..210, others fall to idx 16) and the target is `0x140000000 + dword[0x14004512c + 4 * idx]`.

| logic id | block | what it does |
|---|---|---|
| 1, 3, 4 | `0x140036024` | missile / rocket logic (ejection `0x140035e3b..`, fuze block `0x140036780`, see flares-and-missiles.md) |
| 2 | `0x14003798d` | not read |
| 10 | `0x140037fb7` | not read |
| 100 | `0x140033d47` | **plain cannon shell**: arming (`+0x3d0 = 20/|v|`, then `+0x38c = 25 * mass`), no spin, align to velocity; see shell-detonation-paths.md |
| 110 | `0x140033ce8` | timed fuse: state 0 `+0x3d0 = +0x3d4`; state 1 `Body_DieExplode` when the timer is spent |
| 120 | `0x140033c5a` | delayed warhead: state 0 `+0x3d0 = +0x3d4`-style delay, then `+0x38c = 10000.0`, `+0x2dc = +0x3d8`, logic id := 0 |
| 130 | `0x1400348be` | not read |
| 132 | `0x140034b78` | not read |
| 135 | `0x140035553` | missile arming: state 0 `+0x3d0 = 0.05`, state 1 when spent `+0x38c = 25 * mass` |
| 137 | `0x1400355c5` | not read |
| 140 | `0x14003447b` | not read |
| 150 | `0x140033e0b` | not read |
| 160 | `0x14003409f` | not read |
| 190 | `0x1400342a1` | not read |
| 200 | `0x140035652` | **hull stabiliser** (hull-stabiliser-engine-logic.md, hull-stabiliser-coupling.md) |
| 210 | `0x1400357d6` | not read |
| 400 | `0x140038767` | rotor / helicopter-style motor (commands 400) |
| all other ids | `0x14004501f` | nothing |
