# Mishaps

A running log of things that went wrong in funny, instructive or expensive ways. Newest first. Keep the entries short, true and blameless: what happened, why, and what we learned. No data here that belongs in a findings note; link to it instead.

## 2026-10-25: The bombers that capsized their own carrier (hf_ally rel.11 to rel.24)

**What happened.** Once bombs finally worked, the user's LA-29 planes were too eager. They were switched into the game's bomber routine the moment they were armed, so they started their bombing dive straight off the deck and hit the landing deck of the carrier they had just left. The carrier capsized.

**Why.** The first bomb fix (the one-byte patch at `0x14000cf16`) made every plane with a bomb list use the bomber routine from frame one, and the later rocket fix (planes put into mode 3 once they have a target) did the same with no waiting. Nothing gave the plane time to take off and clear the ship first. The game's own script keeps a plane idle until it is more than twice the carrier's radius away; the bomber routine has no such stage.

**The fix** (rel.25): the global patch is off by default (`plane_bombers` false). Bomb and rocket planes now fly the game's normal script first, and are switched to the bomber routine only after `plane_attack_delay` seconds (default 6) and only if they have a target.

**Lesson.** "Make the plane attack" also means "not yet". When you bypass a state machine's early states, you also bypass whatever those states were quietly doing, here clearing the carrier.

## 2026-10-24: The mod that queued five billion rockets (hf_ally rel.21)

**What happened.** The user asked for unlimited plane armaments in Shipworks test fights, so that every plane loadout could be picked without touching the real campaign stock. I (the ally-mod session) hooked the game's two profile stock calls, only while the test-fight flag is set: "how many do you own" (`0x14028c460`) answers 1000, and "remove N items" (`0x140293ad0`) does nothing.

The test run: the user picked bombs for an LA-29 in a test fight. The game clock froze at 25.62 s, the mod's own heartbeat kept ticking, and a minute or two later Steam said **"memory shortage"** and the game died. A second run died the same way.

**Why.** "Remove" is not a void function. It returns the amount it removed. The game's rocket auto-supply (`FUN_14000ceb0`, notes `carrier-plane-loadouts.md` section 10) reads that return value and pushes that many rockets onto the plane's rocket list. My "do nothing" hook was a hand-written trampoline:

```
mov rax, 0x147fc6fb6   ; the test-flag address, loaded to compare it
cmp byte [rax], 0
je  original
ret                    ; "do nothing"
```

It left the flag's *address* in `RAX`, which is the return register. So the game saw "removed 0x147fc6fb6 rockets" (about 5.4 billion) and happily started pushing five billion rockets onto one plane's list, one at a time, in a single frame. Hence the frozen clock and the memory exhaustion. The plane in question was supposed to be carrying bombs.

**The fix** (rel.22): the hook now returns the requested count (`mov eax, r8d; ret`), which is also what the real function would have answered for a stocked item.

**Lessons.**
* A function that "returns nothing" in the decompile may still have a meaningful return value. Check every caller, not just the signature, before turning a function into a no-op.
* A hook that uses a scratch register for its own comparison must restore it, or set the return register on every exit path.
* A frozen game clock plus a still-running mod heartbeat (`HB t=` lines in the megalog all showing one value) means the game thread is stuck inside the game, not that the mod crashed. The memory graph then tells you it is an unbounded loop.
* Related earlier reading: vanilla rocket supply and why a plane "only shoots 1 or 2 rockets" are in `findings/carrier-plane-loadouts.md` sections 10 to 12.

## 2026-10-24: We called the wrong flag "campaign" for most of an afternoon

**What happened.** The bomb loadout loaded correctly (bomb list 2 or 4, stock charged) but the planes never dropped a single bomb. The log line `campaign bytes 0/0` looked like proof that the test fight was not a campaign battle.

**Why.** `0x147fc6f80` and `0x147fc6f81` are hot-seat / multi-profile flags, not "campaign" (the real campaign flag is `0x147fc6fd0`). Bombs only work in the bomber variant of the plane code, which the game only enters when one of those hot-seat flags is set. In a normal single-player battle the bomb list is simply never read. The fix was a one-byte patch (`75` to `EB` at `0x14000cf16`). The first T-7 bombs dropped in a real campaign battle immediately after.

**Lesson.** A label in Ghidra or in our own notes is a guess until a caller proves it. Our first reading ("campaign byte") was written down as fact and sent us looking at the wrong thing for hours. See `carrier-plane-loadouts.md` section 11.

## 2026-10-24: Seventeen builds of one button

**What happened.** The "plane loadout" button for the carrier took about twenty builds to get right. Highlights, in order:
* It was invisible: a card link was read one field off, and the whole inventory lookup used the wrong map.
* It was drawn at full size over the card header, because the sprite chosen was a wide weapon picture, not a round icon.
* The LA-29 button was never clickable. Its element name was `PLANE_LOADOUT_10`, sixteen characters, and the game's inline name buffer holds fifteen. Buttons 1 to 9 worked; buttons 10 to 18 could not be found, clicked or hidden. The "stale" ghost button after a ship swap was the same bug.
* Swapping two carriers did not move the buttons, because the layout check only compared card x positions, and two carriers swapping leave the x positions identical.
* The label text started in the middle of the button (render alignment 2 is centred, not left).
* The label font was rough until it used the ammo picker's own font and a whole-pixel position.

**Lessons.** Names that look free in a GUI list may have a hidden length limit. Re-place triggers must include identity, not only geometry. When the game already draws something you want to imitate, find out how (here, the markup `{font=flash_large_shadow}{color=4293514025}` in notes section 15) instead of guessing.
