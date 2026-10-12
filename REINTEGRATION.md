# Re-integration notes (for me; delete when done)

**Branch `review-1151-annotations` is local only.** Rules from the user: do NOT push, do NOT switch to `master`, keep every step as a commit, no edits to the 1.151 program (read-only).
After the review by logdot and his agent, this branch is merged/split into the normal docs. This file tracks what has to move where.

## Files on this branch that are not for the final tree
* `docs/review-1151.md`: working file with everything about the 1.151 annotation review. Split it using the `<!-- MOVE: ... -->` comments in it, then delete it.
* `docs/review-1151-groups.md`: (added during the review) one section per group of 1.151 functions I read; same rule.
* `REINTEGRATION.md`: this file.

## Commits on this branch that ARE final (cherry-pick or merge to master after review)
* `494e8b9` systems.md: map-launch queue details (nuclear warning gating, target types, dead-part skip).
* `docs/ai-flares.md` (+ the README row and the roadmap pointer, added together in one commit on this branch): **self-contained, can be cherry-picked to master on its own** without the rest of the review. Preserves the AI-flares finding in full.
* `docs/khiva-crash.md` and `docs/ai-tick-patch-sites.md` (+ their README rows and roadmap pointers, one commit): **self-contained, cherry-pickable on their own**. They preserve the Khiva-crash cause and the AI patch sites in full; the `review-1151-groups.md` copies (groups 16-18) are the working versions.
(If the review changes it, amend before merging.)

## Open flags to raise with logdot before anything moves
1. `structures.md` says `+0x858` is `m_weapon_ammo_amount`; `FireGun` (1.163 `0x140032e60`) decrements `+0x860`. Decide with a second code read or in-game test.
2. Ghidra's 1.163 `Body` struct is 0xa08 bytes, the object is 0xa40; offsets past ~0x2a8 are stale in Ghidra.
3. `.conflict` duplicate types in the 1.163 program (`Body.conflict`, `BodyVFTABLE.conflict`, `DLL<Body>.conflict`, ...).
4. The four air-group functions (`CreateMapAircraftGroup`, `UpdateMapAircraftGroup`, `ComputeMapAircraftWeaponStrength`, `ConfigureStrategicMissileForTacticalBattle`) have no 1.163 match.
5. `mdl_covered` / `mdl_turbine` names in 1.151 are swapped relative to what 1.163 `UpdateEngineCovered` writes.

## More flags for logdot (added during the groups pass)
6. `structures.md` "fleets +0x270/+0x278" is probably the MapCraft vector (Profile remap +0x48); fleets are the +0x1f8 list. Verify one writer/iterator of +0x270.
7. 1.163 has no function defined at 0x140117840 (UpdateMapAircraftGroup); same likely for other "unmatched" air-group functions. Needs a Ghidra edit (create function) after the review.
8. Real Body size: 1.151 = 0xa08, 1.163 = 0xa40 (+0x38); the 1.163 Ghidra struct is the 1.151 layout. Fleet field shifts (count +0x4e8->+0x4ec, range +0x4f0->+0x4f4, missile cooldown +0x508->+0x50c, aircraft cooldown +0x50c->+0x510).
9. TryLaunchAiAircraftGroup limit raised from 480.0 to 1200.0 in 1.163 (target +0x78); group size = all aircraft (coin-flip half if >10): roadmap item "AI launches everything".
10. Intercept probabilities (0.75 missiles, 0.66 aircraft) are the two constants in runMissileandAircraftIntercept_ (1.163 0x140111110); add the 75% roll to systems.md.

11. Stats record: 1.163 inserts `sectors_shift` (0x12c) and `cluster` (0x16c); confirmed by strings `m_mdl_sectors_shift`, `m_missile_explosive_cluster` (only in 1.163). Notes' `+0xd4 tank capacity` is probably `crew capacity`; tank capacity is the double at `+0xc8`.
12. `GetPartPrice` returns 0 after `Profile.endWar` and for category bit 6; `endWar` is set by `spawnEndgameShips_` (1.151 0x14023fa80; 1.163 counterpart `FUN_140261a20`, found, group 18).
13. 1.163 adds Skirmish/PVP modes, SDL2 controllers, captains, KAZ ammo; removes the 1.151 debug overlay strings. `formats.md` level list is incomplete for 1.163.
14. Ammo table lives in code (`DefineAmmos`), not in `OL.seria`; `caliber` there is a projectile logic id; all cannon shells have 1 HP (`BulletImpact__` argument); `index 54` (300mm) has no `FireShell` case in 1.151.
15. Ghidra type library: `ShipPart` and `HGEVFTABLE` exist only in 1.151; 1.163 `Body`/`Escadra`/`Creature` structs are stale.
16. Names to fix in Ghidra (after review): the 1.151 AI weapon controller at 0x140076300 is named `rep_140076300_...::atan2f` (propagated); its 1.163 twin `FUN_14007a8d0` is unnamed. `creatureLogic` is the projectile/missile/aircraft behaviour dispatcher (keyed by the ammo `caliber` logic id), not the ship AI, so the name misleads. Creature flag names `damageCounter_` (1.151) and `linkDLL` (1.163) at the 700-range cap are wrong.
17. `Ammo` struct: 1.151 is 0x168, 1.163 is 0x188 (adds `shell_enemy` string and float `ttl` at +0x16c). 1.163 `ttl` makes shell lifetime per ammo type (100mm 4 s, 130mm 7 s, 180mm 30 s). My earlier note that the 1.151 stride was 0x188 was wrong (fixed in group 12/13/15).
18. Latent bug in both versions: the AI controller looks up `ITEM_AMMO_230MM*`, the table has `ITEM_AMMO_203MM` (group 16). Harmless in vanilla; logdot may know if it is intended.
19. Names to fix: `0x1400739c0` is labelled `shipKill?` but is the per-ship AI tick caller of `FUN_140062f90`; `0x140071120` is labelled `...::sqrtf` but computes the ship bounding radius (writer of Creature +0x1850); `0x14007ffaa` sits in `CalculateStats`.
20. Likely cause of the Khiva crash (group 18): four unguarded `first_node->payload->+0x19c = 2` writes at 1.163 0x140262226 (1.151 0x140240266). Earlier group 7 text claimed they were guarded; corrected. Also: 1.163 `Profile` struct is the stale 1.151 layout (+0x58 from `endRace`). Please confirm one empty-quadrant case by reading the list code or reproducing on a throwaway save before anything is merged to master.
21. `FUN_140261a20` and the `SCR_MAP` handler region around 0x1402b8a00-0x1402b8b30 have no function defined / are unnamed; same Ghidra-gap family as flag 7.
22. `+0xd4`: group 19 now supports crew capacity (and `Body +0x804` = crew present) from the ship stats aggregation in 1.163; this resolves flag 11's open part in logdot's favour. Roadmap 'combined sensors' item is NOT confirmed by the code read (sensors combine by max; only jammers sum).

## Pending moves (update as I go)
| From | To | Status |
|---|---|---|
| review-1151.md "What was compared", "Method" | setup.md | not moved |
| review-1151.md "1.151 names that confirm ..." | systems.md / structures.md / engine-hge.md as "(1.151 name: X)" tags | not moved |
| review-1151.md "CreateMapAircraftGroup settles ..." | structures.md class table + systems.md | not moved |
| review-1151.md "Body remap" anchors | structures.md new subsection "Version differences" | not moved |
| review-1151.md "How automatable ...", "Body remap" | roadmap.md Ghidra side / structures.md | not moved |
| review-1151-groups.md Profile remap | structures.md world singleton line (after flag 6) | not moved |
| review-1151-groups.md groups 1-15 | systems.md / structures.md / formats.md / engine-hge.md / content.md / roadmap.md / open-questions.md per the MOVE comments in each group | not moved |
| review-1151-groups.md group 15 (ammo ttl and value changes) | roadmap.md version scope (damage changes) + systems.md Ammo + structures.md Ammo size | not moved |
| review-1151-groups.md group 16 (tactical AI controller) | systems.md Tactical AI + roadmap.md AI items + structures.md Creature | not moved |
| review-1151-groups.md group 17 (AI tick, patch site) | hooks.md Ownership row + roadmap.md AI items + systems.md Tactical AI + structures.md Creature | not moved |
| review-1151-groups.md group 18 (endgame, Khiva crash cause) | roadmap.md Khiva bug + systems.md End game + hooks.md + open-questions.md | not moved; wait for logdot's confirmation |
| review-1151-groups.md group 19 (sensor combine rules, +0xd4) | structures.md Stats + Body, roadmap.md sensors/crew items, systems.md | not moved |
| review-1151-groups.md group 20 (flares, crash hunt, partial) | roadmap.md flare bug + systems.md + structures.md Body logic ids | not moved |
| review-1151-groups.md group 21 (AI flares: cause and mod design) | roadmap.md AI flares item + hooks.md + systems.md + structures.md Creature | not moved |
