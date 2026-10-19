# Hooking and patch ownership

## Techniques (all our DLLs)
* **Function-entry detour:** a 14-byte `FF 25 00000000 <abs64>` jump over `len` stolen bytes (14..20, ending on an instruction boundary, position independent);
  a trampoline in a `VirtualAlloc` RWX page runs the stolen bytes and jumps back. The expected bytes are compared before patching (version guard):
  on any other build the mod does nothing and says why in its log.
* **Data patch:** change a constant inside an instruction (e.g. the 4-byte float immediate of `mov dword [rdi+0x50c], 300.0f`).
* **Operand repoint:** change the disp32 of `MULSS xmm0,[rip+disp]` to a private float (needs memory within +-2 GB of the code: allocate just above the image).
* **Call-site patch + code cave** (speed mod): redirect one `call` through a stub in `0xCC` padding.
* Do not change a shared constant (pooled `100.0f`, `200.0f`... are used by hundreds of places): patch the instruction, not the constant.

## Ownership (so mods never patch the same bytes)
The modloader loads mods in an unspecified order, and a second detour at an already hooked entry fails the first's version check. One owner per site:

| Site | Kind | Owner |
|---|---|---|
| `0x14002e590`, `0x14002e3a0` (combat launch), `0x1400eced0` (map launch) | entry detours | highfleet-multicharge |
| `0x14025afd0` (level loader) | entry detour | highfleet-salvo |
| `0x1400ed59e` (300.0 launch-cooldown immediate) | data patch | highfleet-salvo |
| `0x14011521f`, `0x140115240`, `0x14011529c` (refuel rate `MULSS`) | operand repoint | highfleet-refuel; **also** highfleet-qol (PR #19, merged) (patchy `patch_call`, `ReturnType::Xmm0`, replaces the 8-byte `MULSS` with a hook that returns `dt * base * mult`). Never install both |
| `0x1400ea980` (add-fuel routine), only with `log_calls=1` | logging detour | highfleet-refuel |
| `0x140080699` (a `call powf`), cave `0x140073330` | call-site patch | highfleet-speed; **also** highfleet-qol (PR #19, merged) (patchy `patch_call` over the 5-byte call, no cave). Never install both |
| editor held-part pointer `0x1403c0d88` (read), `m_floor` writes | polling | highfleet-elevation |
| `0x140032f22` (gun blocking) and others | detours | highfleet-qol (logdot) |
| `0x140303fb4` (`E8 C7 03 DD FF`, the call to the label pass `0x1400d4380` inside the editor renderer; wrap = original call, then ours) | trampoline | **highfleet-qol fork, branch `elevation`** (native hint, commit 95d09cd); **also** hf_probe (debug only: HUD, sprite test) and hf_draw_test (debug only, never ship). Never install more than one of them. |
| `0x14007f864` (`cmp byte [rsi+0xbc0],0` in the per-creature update `0x14007eb50`, 7 bytes, stack aligned; hook calls the flare release `0x14002eed0` for AI ships) | trampoline | **highfleet-qol fork, branch `ai-flares`** ([findings/ai/ai-flares.md](findings/ai/ai-flares.md)) |
| `0x140064a8d` (`movss [r14+0xbf0],xmm9` in the AI tick `0x140062f90`: the desired waypoint store; xmm9/xmm10 = waypoint, xmm12/xmm14 = ship position; 9 bytes, resume `0x140064a96`, also a jump target from `0x1400648a7`) | trampoline | **highfleet-qol fork, branch `ai-flares`** (evasion); also **`hf_ai`** v0.1.0 (log-only waypoint hook with a `decide()` plug-in point, standalone, **not installed yet**): never install both. With `hf_ai` first, qol finds a jump there, skips its steering hook and, because the boost hook needs it, the panic boost too; qol's flare hook at `0x14007f864` still installs ([findings/ai/ai-hf-ai-design.md](findings/ai/ai-hf-ai-design.md)) |
| `0x140065744` (12 bytes: `mov rdi,rbx` + 9-byte nop before the engine-command loop of the AI tick `0x140062f90`; resume `0x140065750`) | trampoline | **highfleet-qol fork, branch `ai-flares`** (panic boost) |
| `0x140052af2` (1.151 `0x140050372`; `MOVAPS XMM1,XMM10` in `BulletImpact__`, the "penetrative > 0 means ttl 1.0" override) | 4-byte NOP (`enable_unblocked_ttl`) | highfleet-qol (logdot) [code, `src/ttl.rs`] |
| `0x140036bb5` (`MOV RBX,RAX; MOV RCX,RSI`, 6 bytes `48 8b d8 48 8b ce` in `creatureLogic`, right after `CALL 0x14021b070`; null-check trampoline, resume `0x140036bbb`, null exit `0x140036ca2`; 1.163 only) | trampoline (`enable_flare_crash_fix`) | highfleet-qol (logdot) [code, `src/flare_crash.rs`]; [findings/flare-crash-hunt.md](findings/flare-crash-hunt.md) |
| `0x14006bf60` (per-frame creature registry rebuild, 10 stolen bytes `48 89 5c 24 08 57 48 83 ec 40`, entry hook) | log-only entry hook, runs every frame, only with `log_creatures` | **hf_ally** ([findings/battle-ally.md](findings/battle-ally.md)) |
| `0x1402cc260` (per-frame arcade battle manager, 11 stolen bytes `48 8b c4 57 48 81 ec a0 00 00 00`, entry hook) | entry hook: ally deploy via `0x1402d6e90`, `SetControlled` `0x1402a7e30`, `SetLink` `0x140194de0`, probe; v0.4 adds retreat (calls `0x14020ef30`) and ship swap | **hf_ally** ([findings/battle-ally.md](findings/battle-ally.md)) |
| `0x140062812` (the `call checkShipPartFlagActive(body, 0x8000000)` in the AI threat-list builder `0x1400625a0`, 5-byte call-site wrapper) | drops bodies whose `m_oid` is in `intercept_ignore_oids` | **hf_ally side branch** `side/ignore-intercept-oids` ([findings/ai/ai-intercept-targets.md](findings/ai/ai-intercept-targets.md)) |
| `0x1402672c0` (ship-from-template spawner, 10 stolen bytes `48 89 5c 24 10 48 89 74 24 18`, entry hook; logs the caller's return address and re-arms the ally per battle) | entry hook, otherwise passes through | **hf_ally** (same note) |
| `0x1402d88bb` (`E8 90 CF F9 FF`, the dispatcher call at the end of `buildPrecombatScreen` `0x1402d7620`) | log-only trampoline (`log_precombat`); **never fires**: that builder is not used in campaign or test fights | **hf_ally** ([rendering/precombat-screen.md](rendering/precombat-screen.md)) |
| `0x1402d752a` (`E8 21 E3 F9 FF`, B1) and `0x1402d75f2` (`E8 59 E2 F9 FF`, B2): the two dispatcher calls in `buildSquadPrecombatScreen` `0x1402d73a0`, the live pre-combat screen | trampolines (`preserved_call` hook, then the original call): B1 logs, **B2 creates the ALLY buttons** | **hf_ally** ([rendering/gui-elements.md](rendering/gui-elements.md)) |
| `0x14012f120` (`ClickFunc` entry, 26 stolen bytes `40 55 53 56 57 41 54 41 55 41 56 41 57 48 8d ac 24 f8 d3 ff ff b8 08 2d 00 00`) | **swallow-style entry trampoline**: calls a hook with the four arguments and returns early when it answers yes (safe: the caller ignores the return value) | **hf_ally** (`ally_toggle`, `gui_inspect`). **Collides with hf_probe `hook_clicks`**, which hooks the same entry (log only): run one of them, hf_ally checks the bytes and installs nothing when they differ ([rendering/gui-elements.md](rendering/gui-elements.md)) |
| `0x14026f880` (`ammoSelectButtonPress?`, 10 stolen bytes `48 89 5c 24 08 48 89 74 24 10`) | log-only entry hook (`gui_inspect`) | **hf_ally** ([rendering/precombat-screen.md](rendering/precombat-screen.md)) |
| `0x140073b93` (`E8 A8 4F 00 00`) and `0x140073c73` (`E8 C8 4E 00 00`): the two `mov rcx,rbx; call 0x140078b40` (AI target choice) in the per-ship AI driver `0x1400739c0` | **call-site wrappers** (`push rcx; sub rsp,0x28; call original; add rsp,0x28; pop rcx;` then a hook with the ship in RCX): `spare_prizes` re-targets prize ships for allies | **hf_ally** ([findings/battle-ally.md](findings/battle-ally.md)) |

Note on the QoL `ai_flares` rows above: the `allies` option (2026-10-16) changes only the "is this an AI ship" test inside our hook functions (side > 0 and AI flag `+0xbd4` set), not the patch sites.

### hf_probe hooks (debug only, log-only, never ship)
Besides the `0x140303fb4` wrapper above, `hf_probe` ([mods/probe.md](mods/probe.md), [runs/probe-run-1.md](runs/probe-run-1.md), [runs/ui-events-and-screens.md](rendering/ui-events-and-screens.md)) installs log-only entry hooks that no mod should also patch:

| Site | What |
|---|---|
| `0x14012f120` (`ClickFunc`) | `CLICK`: accepted GUI clicks |
| `0x1401ae090` (localised string lookup) | `TEXT`: string keys a screen asks for |
| `0x1402e30e0` (`playSFXSound?`), `0x140225930` (`LoadSeriaFile`) | `SOUND`, `LOAD` |
| explosion code: routine 1.163 `0x140029b60` (1.151 `0x140028520`) and its damage calls | `BLAST` / `DMG`, the only hooks that run on 1.151 ([findings/explosion-damage-1151-vs-1163.md](findings/explosion-damage-1151-vs-1163.md)) |

### Candidate sites, not owned and not applied (findings only; each needs a version guard)
| Site | What | Note |
|---|---|---|
| `0x14007b021`, disp32 at `0x14007b025` | close-range cutoff margin (`30.0` operand) | operand repoint; [findings/ai/ai-tick-patch-sites.md](findings/ai/ai-tick-patch-sites.md) |
| `0x1400631a6`, `0x1400631ec`, `0x14006320d`, `0x1400631fe`, `0x140064723` | AI stand-off knobs (`0.35`, `1000`, `660`, `600`) | operand repoints; same note |
| `0x140262226` (84 bytes) | unguarded list-head writes (Khiva crash) | entry-style detour; [findings/end-game.md](findings/end-game.md#the-khiva-end-game-crash-unguarded-list-writes-1163-probable-cause) |
| `0x1400efa2a`, `0x1400ef9fb` | AI aircraft launch group size | [findings/ai/ai-aircraft-launch.md](findings/ai/ai-aircraft-launch.md) |
| `FUN_140032fb0` entry (`0x140032fb0`) | bomblet lifetime (sixth argument) | [findings/cluster-bomblet-ttl.md](findings/cluster-bomblet-ttl.md) |
| `0x14002e3a0` (also owned above by multicharge) | AI launch limits per target (1 per second, 10/2/1 in flight) | coordinate with the owner |

Rule for sites that another mod may already have patched (for example `0x140303fb4` with `hf_draw_test` or `hf_probe` installed): pre-check the expected bytes (the 5 bytes of the original `E8 rel32`) before preparing the patch and skip the feature on a mismatch. With patchy a failed prepare makes `install_permanently` fail and `init` return false, which would take every QoL feature down with it.

New feature wanting a site inside an owned function's first 14 bytes: patch a constant instead, or coordinate with the owner.

* **`playSFXSound_` `0x1402e30e0`** (sound player, 15-byte entry `48 8b c4 48 89 58 08 ...`): detoured by `hf_probe` (`hook_sounds`); *called* (not hooked) by `hf_ally` v0.10+ behind a 15-byte precheck, so with the probe's sound hook loaded the ally sounds switch off. Call recipe: [sound.md](sound.md).
* **`SomethingInputTask` `0x14018dbf0`** (per-frame, game thread, entry `48 8b c4 48 89 58 08 48 89 70 10`): `hf_voice` (padded trampoline: `sub rsp,8` / call / `add rsp,8` / stolen bytes). Also read by the editor held-part code. `hf_ally` v0.11.4+ hooks it too (same padded trampoline, 11-byte precheck) for the pre-combat card-layout check, and it also ticks on the pre-combat screen [game: `ALLY precombat tick: first call from hook 0` in every v0.11.4 to v0.11.8 log]. Whichever mod loads first owns it, the other skips on the precheck: with `hf_voice` loaded, `hf_ally`'s buttons do not follow the shuffled cards. `hf_ally`'s second tick source, the battle-manager hook, never fired on the pre-combat screen [game: no `from hook 1` line in any v0.11.4+ log], so it is no fallback.
* **Layer-flush call sites B22 `0x140309327`, B23 `0x140309408`, B24 `0x140309897`** (`E8 rel32` to `checkD3DEngineStatus?` `0x140083b50`, the battle-branch renderer `0x1403050a0`): `hf_ally` v0.11.6+ wraps all three (`draw_marker_b22/b23/b24`; only the one chosen by `marker_seam` draws, default 24; v0.11.5 wrapped B24 only) to draw the pre-combat slot-1 label. These are the same sites `hf_probe`'s seam test (`seam_battle`) wraps: whichever installs second finds changed bytes and skips. Recipe and pitfalls: [rendering/README.md](rendering/README.md), [rendering/precombat-screen.md](rendering/precombat-screen.md).

**hf_ai v0.2.0 (2026-10-18, local, not yet in game):** owns `0x140064a8d` always (log-only unless a tactic acts) and `0x14007f864` + `0x140065744` when its `ai_flares.enabled` is true (the ported qol `ai_flares`); exactly one of qol `ai_flares` and hf_ai `ai_flares` may be enabled, because each mod byte-checks the site and the second loader skips with a log line. It also reads (never patches) `0x140036bb5` to warn if the flare-crash fix is off; qol `enable_flare_crash_fix` must stay on.
