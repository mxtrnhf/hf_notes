# Re-integration notes (for me; delete when done)

**Branch `review-1151-annotations` is local only.** Rules from the user: do NOT push, do NOT switch to `master`, keep every step as a commit, no edits to the 1.151 program (read-only).
After the review by logdot and his agent, this branch is merged/split into the normal docs. This file tracks what has to move where.

## Files on this branch that are not for the final tree
* `docs/review-1151.md`: working file with everything about the 1.151 annotation review. Split it using the `<!-- MOVE: ... -->` comments in it, then delete it.
* `docs/review-1151-groups.md`: (added during the review) one section per group of 1.151 functions I read; same rule.
* `REINTEGRATION.md`: this file.

## Commits on this branch that ARE final (cherry-pick or merge to master after review)
* `494e8b9` systems.md: map-launch queue details (nuclear warning gating, target types, dead-part skip).
(If the review changes it, amend before merging.)

## Open flags to raise with logdot before anything moves
1. `structures.md` says `+0x858` is `m_weapon_ammo_amount`; `FireGun` (1.163 `0x140032e60`) decrements `+0x860`. Decide with a second code read or in-game test.
2. Ghidra's 1.163 `Body` struct is 0xa08 bytes, the object is 0xa40; offsets past ~0x2a8 are stale in Ghidra.
3. `.conflict` duplicate types in the 1.163 program (`Body.conflict`, `BodyVFTABLE.conflict`, `DLL<Body>.conflict`, ...).
4. The four air-group functions (`CreateMapAircraftGroup`, `UpdateMapAircraftGroup`, `ComputeMapAircraftWeaponStrength`, `ConfigureStrategicMissileForTacticalBattle`) have no 1.163 match.
5. `mdl_covered` / `mdl_turbine` names in 1.151 are swapped relative to what 1.163 `UpdateEngineCovered` writes.

## Pending moves (update as I go)
| From | To | Status |
|---|---|---|
| review-1151.md "What was compared", "Method" | setup.md | not moved |
| review-1151.md "1.151 names that confirm ..." | systems.md / structures.md / engine-hge.md as "(1.151 name: X)" tags | not moved |
| review-1151.md "CreateMapAircraftGroup settles ..." | structures.md class table + systems.md | not moved |
| review-1151.md "Body remap" anchors | structures.md new subsection "Version differences" | not moved |
| review-1151.md "How automatable ..." | roadmap.md Ghidra side | not moved |
