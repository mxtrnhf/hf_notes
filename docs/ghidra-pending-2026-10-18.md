# Ghidra annotations still to apply / save (2026-10-18 night)
The Ghidra MCP timed out on `save_program` and on later `set_plate_comment` calls. Applied (in the open program, unsaved): rename `FUN_14002ff60` -> `LaunchZenithAtOwnerTarget`, first versions of the plate comments of `LaunchZenithAtOwnerTarget`, `AiWeaponController`, `FireGuns`, `FireGun`, and the disassembly comments listed in changes-2026-10-18.md.
To correct (re-apply these plate texts, then save and check in with "Annotate 1.163: AI fire gates, Zenith launch, fire bytes"):
* `LaunchZenithAtOwnerTarget`: replace "~4.1 s free flight before self-destruct [data]" with "~4.1 s of free flight in the telemetry; a fixed self-destruct timer is a [guess]"; replace "hf_ai uses this to detect a launch" with "hf_ai DETECTS a launch from the player's side with the TARGET link (side < 0); the owner link (+0x4b0, confirmed side +1 on 18+ launches) is only logged".
* `AiWeaponController` item (7): "(checked only when the list at 0x147fc73d8 has > 1 entry; that it is the player-side/ally set is a [guess])".
* `FireGuns`: add "[data] CONFIRMED at runtime: an AI ship's +0xbbc written by a mod persists and fires group 0 (hf_ai v0.6.4: enemy f0 = 1 in 3% of rows, 34 episodes, 13 produced shells)".

## Full list to re-apply after a Ghidra restart (if the unsaved edits are lost)
Rename `FUN_14002ff60` -> `LaunchZenithAtOwnerTarget`. Then plate comments (use the CORRECTED wording above where noted) and these disassembly comments (set_disassembly_comment):
* `0x14007ba84`: AI RANGE GATE group 0: COMISS XMM8,XMM1 ; JA skip. XMM1 = creature +0x1838 (x2.0 if zoom>=4 / outside level bounds, else x1.0).
* `0x14007bd55`: AI RANGE GATE group 1 (same test, creature +0x183c).
* `0x14007f799`: CMP byte [creature+0xbbc],0: the player's LMB (group-0 fire byte); set -> FireGuns for every gun of group 0. The AI controller never sets it; hf_ai early fire writes it. hf_ai flare hook is at 0x14007f864 in this same function.
* `0x14007f7d9`: CMP byte [creature+0xbbd],0: the player's RMB (group-1 fire byte), same handling.
* `0x140065edb`: CALL LaunchZenithAtOwnerTarget (enemy Zenith launch over launch list +0x13d8); qol AI missile dump wraps this call (roll at 0x140065c6c, launch here).
* `0x14018a7c9`: CALL LaunchZenithAtOwnerTarget: the PLAYER launch path also uses it (player missiles carry target link +0x490/+0x498 and owner link +0x4a8/+0x4b0).
* `0x140354678`: 0.025 rad: AI gun angle tolerance (|gun +0x138 - aim angle|), PRIVATE constant (single xref 0x14007b959).
Plate comment content: the fire-gate text is in section 5 of `docs/findings/ai-tick-patch-sites.md` (per-gun order 1-8, addresses, constants); LaunchZenithAtOwnerTarget = see `docs/findings/ai-flares.md` and the wording above; FireGuns / FireGun = section 5 of the same page.
