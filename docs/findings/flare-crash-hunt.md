# Flares and the proximity-fuse crash hunt (1.163, partial: the crash site was NOT found)

Status: **partial; read from the decompilation, nothing run in game.** Tags: legend in `../../README.md`.
Why AI ships never use flares (a different question, solved): [ai-flares.md](ai-flares.md).

Roadmap item: "a proximity-fused missile colliding with flares crashes the game". What the read established, and what it did not:

* **How a flare is released:** the player-input update `FUN_14007eb50` (called with `FireGuns`, `FUN_14002f480` and the "flare" sound string at `0x14007f904`) loops over the ship's launcher lists and calls **`FUN_14002eed0` (the flare release)** for the list at `+0x1408..+0x1410`
  when the flag `+0xbc0` is set (the flag at `+0xbbd` drives `FireGuns`, `+0xbbe` drives `FUN_14002e7d0`). `FUN_14002eed0` refuses unless the launcher has its cooldown at `+0x848` at zero, is armed (`+0x80c`, `+0x818` non-zero) and has count `>= 1` (`+0x860`, which is the ammo counter,
  the `+0x860` of the weapon area), then decrements the count, sets the launcher cooldown from `FUN_1400490a0` (rate in 60ths), and spawns one `Body` (`New(0xa40)`).
* **The flare body [code]:** `timeToLive` (`+0x2c0`) 5.0 s, **`logic` (`+0x3c4`) = `0x44c` (1100)**, layer/state (`+0x1f0`) 0, sprite id (`+0x8d8`) 5, drag (`+0x1dc`) `0x3a378034` (about 0.0007, the same as AP shells), velocity along the launcher direction x 400 with a random angle +-0.2 rad,
  three particle effects (`smoke_FIRE`, `rocket_glow`, `fire_LRE`). It is **not** built from a stats record: `explosive` (`+0x2dc`) and `isArmorPiercing` are left at their defaults, and `isLogicActive` (`+0x3c8`) is not set. Its stats index (`+0x188`) is whatever `Body::Body(…, 0)` leaves.
* **What `FUN_14002f480` is:** the close-in point-defence burst of the "strides" sprites (`strides`, `strides_fire`), not a flare function: it picks an incoming projectile within 60/120 units and angle < 45 degrees, subtracts 1 from the launcher's count (`+0x860`) and calls the target's `+0x200` (damage) with the target's
  own explosive power. It excludes targets whose stats `+0xb0` is `0x4000` (tactical missile) / `0x8000000` (strategic) / `0x200000` (bomb), and it **does null-check `GetStats`** before reading `+0xb0`. This confirms the earlier "KAZ burst" label.
* **The destroy handler `FUN_140023ac0`** (called from `FUN_14006aab0`) reads stats `+0x180` (`fuze_type`) 1 and 2 on a body being destroyed, again after `GetStats(...) != 0`. It is the "ammo explosion / bomb explosion / leg / engine lost" message and effect handler, not the proximity trigger.
* **Not found:** the proximity-fuse trigger for missiles (a missile exploding when within range of another body). It is almost certainly inside `creatureLogic` (the huge per-body dispatcher, never decompiled successfully), likely the branch for the missile's logic id with the fuze type; the only `logic == 0xa0` compare outside
  `creatureLogic` is a tracer/render check in `handleAmmoInBattle?` (`0x14004c262`). So **no candidate dereference of a flare body was identified**, and I do not have a basis to say which pointer is wrong.
* **A hypothesis worth testing first [guess]:** the flare body has no valid stats index and `isLogicActive` unset, while a proximity-fused missile reads the target's `GetStats(...)` result (or the target's owner link at `+0x2e8`/`+0x480`, which `BulletImpact__` sets for shells but the flare path does not set). A missing null check on either would crash exactly when a missile's
  proximity test selects a flare. The existing code elsewhere is careful about `GetStats == 0`, so the crash, if this is it, is at a site that is not.

**How to get the crash address without reading `creatureLogic`:** a crash handler (roadmap tooling item 3, "Crash capture") that logs the faulting RVA, then fire a proximity missile at a flare once. That turns this into one address to open in Ghidra. Reading `creatureLogic` in chunks via disassembly is the static alternative.

## Live-test recipe
Run a crash handler or a debugger, fire a proximity-fused missile at a released flare once, and read the faulting address; open that address in Ghidra. The first suspects are reads of `GetStats` results and of the owner link `+0x2e8`/`+0x480` on the flare body.
