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
| `0x14011521f`, `0x140115240`, `0x14011529c` (refuel rate `MULSS`) | operand repoint | highfleet-refuel; **also** highfleet-qol fork branch `refuel-rate` (patchy `patch_call`, `ReturnType::Xmm0`, replaces the 8-byte `MULSS` with a hook that returns `dt * base * mult`). Never install both |
| `0x1400ea980` (add-fuel routine), only with `log_calls=1` | logging detour | highfleet-refuel |
| `0x140080699` (a `call powf`), cave `0x140073330` | call-site patch | highfleet-speed; **also** highfleet-qol fork branch `refuel-rate` (patchy `patch_call` over the 5-byte call, no cave). Never install both |
| editor held-part pointer `0x1403c0d88` (read), `m_floor` writes | polling | highfleet-elevation |
| `0x140032f22` (gun blocking) and others | detours | highfleet-qol (logdot) |
| `0x140303fb4` (`E8 C7 03 DD FF`, the call to the label pass `0x1400d4380` inside the editor renderer; wrap = original call, then ours) | trampoline | **highfleet-qol fork, branch `elevation`** (native hint, commit 95d09cd); **also** hf_probe (debug only: HUD, sprite test) and hf_draw_test (debug only, never ship). Never install more than one of them. |
| `0x14007f864` (`cmp byte [rsi+0xbc0],0` in the per-creature update `0x14007eb50`, 7 bytes, stack aligned; hook calls the flare release `0x14002eed0` for AI ships) | trampoline | **highfleet-qol fork, branch `ai-flares`** ([findings/ai-flares.md](findings/ai-flares.md)) |
| `0x140064a8d` (`movss [r14+0xbf0],xmm9` in the AI tick `0x140062f90`: the desired waypoint store; xmm9/xmm10 = waypoint, xmm12/xmm14 = ship position; 9 bytes, resume `0x140064a96`, also a jump target from `0x1400648a7`) | trampoline | **highfleet-qol fork, branch `ai-flares`** (evasion) |
| `0x140065744` (12 bytes: `mov rdi,rbx` + 9-byte nop before the engine-command loop of the AI tick `0x140062f90`; resume `0x140065750`) | trampoline | **highfleet-qol fork, branch `ai-flares`** (panic boost) |
| `0x140052af2` (1.151 `0x140050372`; `MOVAPS XMM1,XMM10` in `BulletImpact__`, the "penetrative > 0 means ttl 1.0" override) | 4-byte NOP (`enable_unblocked_ttl`) | highfleet-qol (logdot) [code, `src/ttl.rs`] |
| `0x140036bb5` (`MOV RBX,RAX; MOV RCX,RSI`, 6 bytes `48 8b d8 48 8b ce` in `creatureLogic`, right after `CALL 0x14021b070`; null-check trampoline, resume `0x140036bbb`, null exit `0x140036ca2`; 1.163 only) | trampoline (`enable_flare_crash_fix`) | highfleet-qol (logdot) [code, `src/flare_crash.rs`]; [findings/flare-crash-hunt.md](findings/flare-crash-hunt.md) |

### hf_probe hooks (debug only, log-only, never ship)
Besides the `0x140303fb4` wrapper above, `hf_probe` ([mods/probe.md](mods/probe.md), [runs/probe-run-1.md](runs/probe-run-1.md), [runs/ui-events-and-screens.md](runs/ui-events-and-screens.md)) installs log-only entry hooks that no mod should also patch:

| Site | What |
|---|---|
| `0x14012f120` (`ClickFunc`) | `CLICK`: accepted GUI clicks |
| `0x1401ae090` (localised string lookup) | `TEXT`: string keys a screen asks for |
| `0x1402e30e0` (`playSFXSound?`), `0x140225930` (`LoadSeriaFile`) | `SOUND`, `LOAD` |
| explosion code: routine 1.163 `0x140029b60` (1.151 `0x140028520`) and its damage calls | `BLAST` / `DMG`, the only hooks that run on 1.151 ([findings/explosion-damage-1151-vs-1163.md](findings/explosion-damage-1151-vs-1163.md)) |

### Candidate sites, not owned and not applied (findings only; each needs a version guard)
| Site | What | Note |
|---|---|---|
| `0x14007b021`, disp32 at `0x14007b025` | close-range cutoff margin (`30.0` operand) | operand repoint; [findings/ai-tick-patch-sites.md](findings/ai-tick-patch-sites.md) |
| `0x1400631a6`, `0x1400631ec`, `0x14006320d`, `0x1400631fe`, `0x140064723` | AI stand-off knobs (`0.35`, `1000`, `660`, `600`) | operand repoints; same note |
| `0x140262226` (84 bytes) | unguarded list-head writes (Khiva crash) | entry-style detour; [findings/khiva-crash.md](findings/khiva-crash.md) |
| `0x1400efa2a`, `0x1400ef9fb` | AI aircraft launch group size | [findings/ai-aircraft-launch.md](findings/ai-aircraft-launch.md) |
| `FUN_140032fb0` entry (`0x140032fb0`) | bomblet lifetime (sixth argument) | [findings/cluster-bomblet-ttl.md](findings/cluster-bomblet-ttl.md) |
| `0x14002e3a0` (also owned above by multicharge) | AI launch limits per target (1 per second, 10/2/1 in flight) | coordinate with the owner |

Rule for sites that another mod may already have patched (for example `0x140303fb4` with `hf_draw_test` or `hf_probe` installed): pre-check the expected bytes (the 5 bytes of the original `E8 rel32`) before preparing the patch and skip the feature on a mismatch. With patchy a failed prepare makes `install_permanently` fail and `init` return false, which would take every QoL feature down with it.

New feature wanting a site inside an owned function's first 14 bytes: patch a constant instead, or coordinate with the owner.
