# AI interception targets: the threat list at creature `+0xca0` (1.163)

Status: **read from the decompilation; the filter built on it (hf_ally side patch `intercept_ignore_oids`) is not yet tested in play.** Tags: legend in `../../../README.md`. Addresses are 1.163.

## What it is [code]
* Each AI tick (`aiShipDriver` `0x1400739c0`, case "not a state-2/3 ship", `0x140073bb4`) empties the vector at creature `+0xca0` and refills it with **`0x1400625a0`** (Ghidra mislabels it `rep_1400601a0...free`; `param_2` is the vector, `param_3` a range limit, 0 = none). Entries are 0x20 bytes: kind (u32), count of missiles already on that body (u32 at +8), distance (f32 at +0xc), the body pointer (+0x10).
* `FUN_14006c0e0` returns the body of the first entry. The driver (`0x140073c7b`, `call 0x14006c100`, then `SetLink` on the Link at creature `+0xb10`) stores the chosen threat as the **missile target**, node at `+0xb18`. `AiWeaponController` (`0x14007a8d0`) loads it into R14 (`0x14007a9bd`) and aims the guns at it with a longer reach for category `0x8000000`/`0x4000`/`0x400` targets; the anti-air launchers (`FUN_14002e3a0`) and `AiShipTick` read the same list. So the guns (CIWS) and the interceptor launches share one candidate list.

## How candidates are chosen [code]
1. **Only when `DAT_147fc6fda` is set** (a battle flag from the arcade-flags group; the missile-vs-ship scene is the likely meaning [guess]): every active body in the global body array `0x143a33c90` for which `checkShipPartFlagActive(body, 0x8000000)` is true is added (kind 0). **There is no side or owner test.** The flag test is `GetStats(body +0x188) -> +0xb0 & 0x8000000`, called at `0x140062812`.
2. If the list is still empty: bodies attached to enemy-side creatures (kind 2) and bodies with logic id `+0x3c4 == 500` whose owner is not on this ship's side (kind 1). Not read in detail.
3. The list is then sorted (by `isCollinear` helper `0x1400598c0` or a plain sort).

## The Sprint report (Discord, 2026-10-19) [game + code]
A Sprint (AA missile) given `m_category` with bit `0x8000000` in `OL.seria` passes test 1 for every AI ship on both sides. A Sprint launched by the player is "something to intercept" for the player's allies, one launched by an enemy for the other enemies; being the nearest, it takes priority over the real strategic missile.

## The filter (hf_ally branch `side/ignore-intercept-oids`)
Call-site wrapper at `0x140062812`: runs the stock test, and if it says yes, asks `keep(body)`; a body whose `m_oid` (Body `+0x190`, MSVC `std::string`: inline up to 15 bytes, length `+0x1a0`, capacity `+0x1a8`) is in `intercept_ignore_oids` makes the test say no. It applies to every AI ship, enemy side included, and (because of the scene flag above) only where step 1 is in force. Step 2's other paths are not filtered; if a Sprint still draws fire in a test, look there first.
