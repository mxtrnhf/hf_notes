# Playing a sound from a mod

How a DLL mod makes the game play one of its own sounds (a radio line, an alarm, an effect). Confirmed in play with `hf_ally` v0.10.1 on Steam **1.163** (2026-10-17). All addresses are 1.163; the 1.151 addresses are **[not read]**. Tags: legend in [../README.md](../README.md).

## The recipe [game]
Call the game's own sound player, `playSFXSound_` at **`0x1402e30e0`** (Ghidra `playSFXSound_`; the probe calls it `playSFXSound?`). Its entry is `48 8b c4 48 89 58 08 48 89 68 10 48 89 70 18` (15 bytes): use it as the byte precheck. The argument layout below is copied from the stock radio's own call at `0x1402d6d32` (end of `PlayRadioSounds_`), so it is a call the game itself makes [code].

| Arg | Where (Win64) | Radio value | Meaning |
|---|---|---|---|
| 1 `kind` | RCX (int) | `0xb` | sound category; indexes the per-kind tables below [code] |
| 2 `name` | RDX (`char*`) | `"mission_danger_01"` | resource name from `<game dir>/Media/Snd/sound.res`, NUL-terminated; the game copies it [code] |
| 3 `node` | R8 | `*(0x147fc6f88)` (`GlobalNode_`) | the node the sound is linked to; the stock radio passes the global node. Read the pointer, do not pass the address [code] |
| 4 | XMM3 (f32) | `60.0` | base volume [code] |
| 5 | `[rsp+0x20]` (f32) | `1.0` | pitch, multiplied by `coreTimeWrap_` [code] |
| 6 `volume*` | `[rsp+0x28]` | pointer to a float, **must be 1.0** | see the pitfall below [code][game] |
| 7 | `[rsp+0x30]` (u64) | `0` | second multiplier pointer (volume is not touched; `+0x90` of the sound object); the stock radio passes 0 [code] |
| 8 | `[rsp+0x38]` (u8) | `0` | reaches the last argument of the HGE play call (vtable `+0x150`), probably loop [guess] |
| 9 | `[rsp+0x40]` (i32) | `0` | picks one of three option-volume multipliers (`DAT_1403c1250..1264`); which slider each is: [guess] |
| 10 | `[rsp+0x48]` (u8) | `0` | no effect seen in `FUN_1402e2da0` besides the `param_3 == 0` test [code] |
| 11, 13 | `[rsp+0x50]`, `[rsp+0x60]` (u8) | `0`, `1` | [not read] |
| 12 | `[rsp+0x58]` (f32) | `0.0` | pan [code] |

Returns an f32 in XMM0: **1.0 = queued, -1.0 = dropped** [code]. Rust (`hf_ally`, `src/lib.rs`, `play_radio`):

```rust
type PlaySfxFn = unsafe extern "C" fn(i32, *const u8, usize, f32, f32, *mut f32, u64, u8, i32, u8, u8, f32, u8) -> f32;
let node: usize = read(0x1_47fc_6f88);               // GlobalNode_ (null early in start-up: skip)
let play: PlaySfxFn = std::mem::transmute(0x1_402e_30e0usize);
play(0xb, b"mission_danger_01\0".as_ptr(), node, 60.0, 1.0, vol_ptr, 0, 0, 0, 0, 0, 0.0, 1);
```
It ran from `hf_ally`'s battle-manager hook (`0x1402cc260`, the game thread) [game]. Other threads: untested, do not.

## The pitfall: the volume pointer (the reason v0.10.0 was silent) [game]
Argument 6 is stored in the sound object (`+0x88`). The per-frame updater (`0x1402e5000`, mislabeled `...sqrtf` in Ghidra) calls `FUN_1402e2da0` for every live sound, which ends with `volume *= *param_6` [code]. The stock radio stores the call's return value (1.0) in that float right after the call. v0.10.0 passed a float holding 0.0: the call returned 1.0 (`-> 1` in the log), `client.log` had no error, and nothing was audible. v0.10.1 initialises the float to 1.0: audible [game]. Rules:
* The pointer is **kept** for the life of the sound: never a stack local (use-after-return). `hf_ally` uses a ring of 8 statics, all `1.0f`.
* Both `playSFXSound_` and `FUN_1402e2da0` null-check it (`if (p != 0)`), so **NULL should also work and is the simpler choice** [code]; untried in game.
* Debug rule: a logged `-> 1` with no audio points at volume (this pointer, argument 4, the game's volume sliders), not at the name lookup.

## Names and failures
* `sound.res` has 449 `Sound <name> { filename=Media\Snd\...wav  resgroup=3 }` blocks [file]. Radio lines live in `Media/Snd/RADIO/`; the `_eng` blocks (`mission_danger_01_eng` -> `RADIO_ENG/`) are the English set. How the game chooses the language set is **[not read]**; `hf_ally` passes the plain (Russian) names, and the stock radio does too.
* A name that is not in `sound.res`: returns -1.0 and writes `ERR: SX::play failed to get effect = <name>` to `client.log` (seen for `radio_landing_start_02`) [game: [runs/ui-events-and-screens.md](runs/ui-events-and-screens.md)].
* Other -1.0 causes [code]: the `DEBUG_SOUND` flag is off, the kind's channel limit (`DAT_1403c2cc0[kind]`) is reached, HGE fails to start the channel. Per-kind tables: channel limit `DAT_1403c2cc0`, falloff radius `DAT_1403c2c88`, replace mode `DAT_147fc7668`; their values are **[not read]**.
* `hf_probe` (`hook_sounds`) detours this entry; a mod with a 15-byte precheck (`hf_ally`) then turns its sounds off. The hook list is in [hooks.md](hooks.md).

## The stock radio, for reuse [code]
* `PlayRadioSounds_` (`0x1402d5910`, `(int* code, float* out)`): a 35-case table from a code to a radio line (`0` death, `1` evac, `3` stall, `0x10..0x14` lost energy/generator/leg/missile/engine, `0x15..0x19` craft launch/lost, `0x1b` kill, `0x1d..0x21` go0..go4 ...), then the call above with `*out = result`. Only its caller list is odd (one bogus Ghidra caller); it is reached through a function pointer or jump table.
* `PlayRadioSound_` (`0x1401b1fb0`, `(base, rand?, bound, sep)`) builds `base` + separator + zero-padded number; the random pick calls an HGE vtable function whose arguments the decompiler dropped, so "random in 1..bound" is a [guess]. Mods that want a specific file just call `playSFXSound_` with the exact name.
* Map code uses the same player: `mission_end`, `radio_kill_06` on `MAPMODE_RADIO_HANDSET` ([systems.md](systems.md)).

## What `hf_ally` plays (v0.10.1/v0.10.2, config `ally_sounds`, default on)
| Event | Sound | Evidence |
|---|---|---|
| ally deployed into the battle | `mission_start_01..03`, random | log `ALLY sound (ally joins)`, all three variants, audible [game] |
| F8 retreat order given (at least one ally ordered) | `mission_danger_01` | log `ALLY sound (retreat key)`, audible [game] |
| ally destroyed | `radio_stall_01` or `radio_lost_energy_01`, one at random | v0.10.1 (trigger: state 6/7 in the roster) **did not fire** when an ally died [game]: a destroyed ship is not flagged 6/7, it leaves the roster with state still 1. v0.10.2 triggers on leaving the roster unless the last state was 2 (retreating) or 6/7, the ally was extracted, or no enemy was left; **untested** |

## Open
* The language choice (`_eng`), the kind tables, arguments 7-11 and 13, other threads, NULL for argument 6.
* Roadmap item "audio cue when aircraft intercept" ([roadmap.md](roadmap.md)) now has its play recipe: `radio_kill_06` through this call.
