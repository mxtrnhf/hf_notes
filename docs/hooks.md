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
| `0x14011521f`, `0x140115240`, `0x14011529c` (refuel rate `MULSS`) | operand repoint | highfleet-refuel |
| `0x1400ea980` (add-fuel routine), only with `log_calls=1` | logging detour | highfleet-refuel |
| `0x140080699` (a `call powf`), cave `0x140073330` | call-site patch | highfleet-speed |
| editor held-part pointer `0x1403c0d88` (read), `m_floor` writes | polling | highfleet-elevation |
| `0x140032f22` (gun blocking) and others | detours | highfleet-qol (logdot) |

New feature wanting a site inside an owned function's first 14 bytes: patch a constant instead, or coordinate with the owner.
