# Making a GUI element the game's own way (and catching its click)

Steam 1.163, image base `0x140000000`. A second route next to the seam drawing of [README.md](README.md) section 3: instead of painting text or a sprite from a render seam, create a real `GUI` object the game draws, hit-tests and clicks itself. Proven in `hf_ally` v0.6 to v0.8 (the per-ship ALLY buttons on the pre-combat screen). Tags as in [../../README.md](../../README.md): **[game]** seen in play, **[code]** read in Ghidra, **[guess]** inferred.

## The recipe [code, read from the PRECOMBAT_OK block of `0x1402d7620`; works in play [game]]
```
mem  = New(0xe70)                          ; 0x140334094, RCX = size of a GUI object
gui  = GUI_2(mem, 0)                       ; 0x14012a910 (constructor)
gui->vtable[+0x2c0](gui, name, f2, f3, w, h, s1..s5, f1)   ; a 12-argument INITIALIZER, not a name setter:
        ;   name (C string), f2/f3 = the f32 globals at 0x148075ce8 / 0x148075cec (set at run time),
        ;   w/h = (i32 at 0x143a158fc / 0x143a13e5c) * f32 at 0x140354698, five default strings at
        ;   0x140352962 (""), 0x140353b70, 0x140353b60, 0x140353b50 ("gui_std_click"), 0x140353628 ("flash_large_shad.."),
        ;   and 1.0 (f32 at 0x1403524d8). It leaves the size fields +0x218/+0x21c at w x h (274 x 154).
root = *(0x147fc6f88)                      ; the global node every GUI is a child of
root->vtable[+0x50](root, gui, 0, 0)       ; add
SetBackground_(gui, 0, "sprite", -1.0f, 0u8, -1i32)   ; 0x14001be50; the float is the f32 at 0x1403524ec
gui->vtable[+0x88](gui)                    ; refresh
0x14015cc30(gui)                           ; clears the strings at +0xab8 / +0xad8 / +0xaf8 / +0xb18 and +0xb78
setXposYpos(gui, &[x, y])                  ; 0x1400520b0, writes the Vec2 at +0x128 (and updates the physics body)
```
Rust types in `hf_ally/src/lib.rs` (`GuiInitFn`, `SetBgFn`, ...): the x64 argument positions are what matter (floats in XMM2 and XMM3 for arguments 3 and 4, the rest on the stack).

## Facts about the objects [game unless tagged]
* **The element list** `GUI_ELEMENTS`: a `std::list`, head pointer at `0x143a13ac8`, count at `0x143a13ad0`; node +0 next, +0x10 the GUI object; sorted by name. `FindGuiElement(char*)` (`0x1401a9170`) returns the first **active** (`+0x48 != 0`) element with that name. Name = C string at `+0xa40`, class string at `+8`, active flag `+0x48` (2 = shown), position f32 pair `+0x128`, size `+0x218` / `+0x21c`, value field `+0xc00`, linked ship / object `+0xbc0`.
* **Coordinates**: GUI units are the virtual 1920 x 1080 frame with the **origin at the centre and y pointing down**: the pre-combat OK button is at (21, 421), the bottom centre. Children (the ammo selector, the ship numbers) report positions that look **relative to their parent card** [guess; the parent-less `PRECOMBAT_A` and `MES_APP` report absolute ones].
* **The game never frees an element you add**: the screen's own rebuild frees only the objects in its own lists. Our element stayed on screen in combat. Hide it by writing `0` to `+0x48` (the state the game itself uses for unused elements, shown as `(off)` in dumps) and set it back to `2` to reuse it; `FindGuiElement` skips inactive ones, so keep your own pointer and check the name string before reuse. A destroy-by-name helper probably exists (`0x1401a9420`, called with `"AMMO_SELECT"`), [guess from its label and one call].
* **Size = hit box**: set `+0x218` / `+0x21c` yourself to the icon size after creating it (the initializer leaves 274 x 154, which makes neighbouring buttons overlap). Hit testing is done by the game; a click on the element reaches `ClickFunc`. These fields are **only the hit box**: the sprite is drawn at its own size [game: `precombat_capital` (`Static2.res`) set on a 64 x 64 element covered the whole pre-combat screen with a paper texture, hiding ships and numbers, v0.11.4 2026-10-17]. Check what a sprite looks like before using it as an icon; the `order_*` sprites are the proven icon-sized ones.
* **Sprites**: any `Animation` name works, for example `order_unset`, `order_support`, `order_support_on`, `order_bombing(_on)` (in `Media/Tex/Midground2.res`), `precombat_button` (`Static3.res`), `precombat_button_on` (`Static5.res`). Swap with `SetBackground_` then call the refresh (`vtable +0x88`), otherwise the icon may not redraw.
* **One click arrives twice** (the same element, the same button, within a few ms) [observed; press and release is a guess]: debounce, for example one action per 350 ms.

## Catching the click: an entry hook on `ClickFunc` that can swallow it
`ClickFunc` `0x14012f120` (arguments RCX ctx, RDX gui, R8D button, R9D id; the element name is at `gui+0xa40`). Its caller `GUI::_HandleClick` `0x14012d050` **ignores the return value** (it returns 1 itself), so skipping the original is safe. Trampoline used by `hf_ally` (26 stolen bytes `40 55 53 56 57 41 54 41 55 41 56 41 57 48 8d ac 24 f8 d3 ff ff b8 08 2d 00 00`, all position independent):
```
51 52 41 50 41 51            push rcx, rdx, r8, r9
48 83 EC 28                  sub rsp, 0x28          ; shadow space + alignment
48 B8 <hook imm64>  FF D0    mov rax, hook ; call rax    ; bool hook(ctx, gui, button, id)
48 83 C4 28                  add rsp, 0x28
84 C0                        test al, al
41 59 41 58 5A 59            pop r9, r8, rdx, rcx   ; pops do not change the flags
75 <len(stolen)+14>          jnz handled
<26 stolen bytes>            ; the original path
FF 25 00 00 00 00 <addr imm64>   jmp [rip+0] to entry+26
C3                           handled: ret
```
The site is also hooked (log only) by `hf_probe` `hook_clicks`; only one of the two can own it ([../hooks.md](../hooks.md)). `hf_ally` checks the 26 bytes and installs nothing when they differ.

## Where to place things on the pre-combat screen
Dump data and screen structure: [precombat-screen.md](precombat-screen.md), raw dump: [../data/gui-dump-precombat-ammo-2026-10-16.txt](../data/gui-dump-precombat-ammo-2026-10-16.txt). Pitfalls met, in order: positions of the number labels are not usable at build time (use the cards); the screen is rebuilt on every ship swap (add again); the ammo selector sits in the card's column about 200 above the card centre (keep clear of it).

## Layering: the GUI pass is not a seam [game + code]
GUI elements (our ALLY buttons, the game's own cards, the roller covers) are drawn by the game's GUI pass in the order of the element list; they have **no render seam** of their own. Text drawn from a render seam (B22 to B24, [README.md](README.md) section 4) lands on top of **all** of them [game: the v0.11.5 "PLAYER" label showed over the sliding covers]. To keep seam text off a cover, read the cover's own GUI element instead: the pre-combat covers are `ROLL_DESK` (1155 x 843), `ROLL_TABLET`, `ROLL_TASK`, `ROLL_ALARM`, created in `secondaryPrecombatButtons` (`ROLL_ALARM` string ref `0x1401fcecc`, `ROLL_DESK` `0x1401fd835`) [code]. In the GUI dump of 2026-10-16 `ROLL_DESK` is at (-248, -20) while it covers the screen and at (-248, -1020) once slid away [game, [dump](../data/gui-dump-precombat-ammo-2026-10-16.txt)]. `hf_ally` v0.11.8 hides its label while `ROLL_DESK` y is above -900 [guess for the threshold; no `ALLY roller cover` log lines had been seen when this was written]. `ROLL_DESK` is also referenced twice inside a function Ghidra labels `rep_140223e80_...memcmp` (`0x140242e60`, refs `0x14024304e` and `0x14024307c`): probably the cover animation, unread [guess].

**Do not confuse them with the landing frame.** `buildLandingFrame` (`0x1401dd500`, was `handleRadiationCounts?`) builds `LANDING_FRAME` (backgrounds `window_01`, `geiger_01`, `geiger_02`, `servo_01`), its child `LANDING_RADIATION` (`geiger_arrow_01`) and its child `LANDING_DOOR` (`door_01`, `door_02`; string refs `0x1401dd975` / `0x1401dd996`). It is a one-shot (guard: the link at `0x143a13bc8` empty), called from two places in undefined scene code (`0x1402be259`, `0x1402c083e`) which set the GUI-init floats `0x148075ce8` / `0x148075cec` first [code]. It is the landing HUD, **not** the pre-combat covers: `hf_ally` v0.11.7 gated its label on `LANDING_DOOR` being active and that never matched (no `ALLY doors` log line in the whole test session) [game]. Whether the name was wrong: it builds the radiation gauge but counts nothing, so "half right"; `LANDING_RADIATION` is also referenced from `setupPropsSecondaryMapModes` (`0x140147782`, unread).
