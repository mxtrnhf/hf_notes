# Ghidra sweep, batch 10 agent 9 — quality / highest-value stale bodies

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: `0x1402e3580` (sound-name normaliser), `0x1403182a0` (post-spawn guard),
the two `_CxxThrowException` funclets owned by `0x140013160`, any `rep_*` /
`FUN_*` not covered by agents 1–8, plus a wrong/misleading-name audit of names
added in batches 1–9.

| | count |
|---|---|
| renamed + plated (in scope) | **4** |
| created | 0 |
| skipped / left stale | 0 in scope (23 sampled names + agent 2's 3 flagged names checked, all correct) |
| wrong-name corrections applied | **1** (`Sound_IsFinished` → `Sound_IsPlaying`, posted 15:55, applied after the cycle) |
| extra `rep_*`/`FUN_*` outside agents 1–8 | 0 (none exist: every live `rep_*`/`FUN_*` entry is inside 0x140000000–0x14034b75b, i.e. one of the assigned slices) |

No `save_program`, tags, README/STATUS edits, commits, or `create_function`.
No transaction was opened (all writes are tool-level, one function at a time).
The 12-function audit sample is listed at the end.

## Renames (4, all plated)

| addr | old label | new name | proof |
|---|---|---|---|
| `0x1402e3580` | `rep_1402b7eb0_deallocateString?` | `Sound_ResolveVariantName` | copies the input std::string, erases its last 3 chars (the caller's `_NN` suffix), matches the collapsed name against a 32-entry hard-coded sound ladder and calls `HGE_RandInt(1,N)` (HGE vtable +0x108 = `0x140174320`) where N is that sound's variant count; a compiler switch then loads the chosen variant string into RBX (`0x1403766f0 "war_attack_01"` … `0x140377008 "girlhit_03"`) and returns it. Only caller `pageSpecialEffect_` `0x140164180` does `playSFXSound_(1, Sound_ResolveVariantName(&name), GlobalNode_)`, and `playSFXSound_` `0x1402e30e0` takes that value as its `const char *soundChooser_` (`Media_GetOrCreateResource3(Media_res, soundChooser_, 0)`). |
| `0x1403182a0` | `rep_1402ed2b0_MSVCP140.DLL::_Xtime_get_ticks` | `TimerToken_Update` | record `0x1403c2d78` = `{int windowMs; int startMs; void *token}`; if `token != 0` and `elapsedMs - startMs <= windowMs` it returns non-zero (keep the current token), otherwise it stores the candidate token+start and returns 0. Sibling `TimerToken_IsValid` `0x1402f4150` is the read-only query over the same record; `VideoTask_RenderBattleScene` `0x140309a93` carries an inlined copy of the identical test. Callers: `BattleSpawner_SpawnShips` `0x1402d1a60`, `Battle_DeployFromReserve` `0x1402d22e0`, `0x1402d2d00` (all discard the result). |
| `0x140336ea0` | `rep_14030bf70_VCRUNTIME140.DLL::_CxxThrowException` | `Vector4_InsertRange_EhCleanup_0x98` | EH funclet of `0x140013160` (`std::vector<4-byte>::_Insert_range`: element scaling `>>2`/`*4`, max_size `0x3fffffffffffffff`, only caller `copyOverBody` `0x140017e70` at +0x4f0/+0x508). FuncInfo4 `0x1403861b0`, funclet list `0x1403861e4` (+0x34), owner UNWIND_INFO `0x140386194`; body restores `_Mylast` (`this+8`, via frame+0x98) from frame+0x28 after two memmoves, then rethrows. |
| `0x140336f00` | `rep_14030bfd0_VCRUNTIME140.DLL::_CxxThrowException` | `Vector4_InsertRange_EhCleanup_0x98_2` | second funclet of the same owner (same FuncInfo4, list entry `0x1403861eb`, +0x3b); single-memmove short variant, same member/restore, rethrows. |

## Structural findings

* **Sound variants are file-name templates, not just labels.** The ladder in
  `Sound_ResolveVariantName` gives the exact variant count per sound and the
  exact on-disk names/variant addresses (documented in full in the plate). The
  counts are: bladaway 2, fire 3, ricochet 3, war_attack 8, war_engage 8,
  war_oh 3, war_ah 5, war_ha 5, haha 10, war_hey 1, worm_attack 3, worm_oh 3,
  saw_attack 3, saw_oh 3, bee_attack 3, bee_oh 3, sophit_attack 3, sophit_oh 3,
  robot_oh 6, krank_attack 5, krank_engage 5, krank_oh 5, krank_ah 5,
  crowd_medium_win 5, voice_alert 5, voice_fame 5, ice_break 3, fury_hit 3,
  met_armor_break 3, wod_armor_break 2, manhit 6, girlhit 3.
  `worm_attack_01` is the only variant string stored outside the main block
  (`0x140370c20`); "bladaway" is the only base checked before the suffix strip.
* **HGE vtable confirmed slot-by-slot** for the audio/RNG range: +0x100
  `HGE_RandSeed` 0x140174350, +0x108 `HGE_RandInt` 0x140174320, +0x110
  `HGE_RandFloat` 0x1401742d0, +0x150 `Effect_Play` 0x14017c630, +0x1e0
  `Sound_ChannelStop`, +0x220 `Sound_ChannelIsPlaying` 0x14017c110.
* **`0x140013160`** is a `std::vector<T>::_Insert_range` replica for a 4-byte
  element type (the `_Change_array` demangled string in the old label is just a
  nearby assert string). Its two funclets are now named after the family
  (`Vector4_InsertRange_*`) because the owner itself sits in agent 3's slice and
  has no class identity beyond the element size.

## Wrong-name audit of batches 1–9

One provable inversion found and corrected (posted to the blackboard at 15:55,
applied after the cycle):

* `0x1402e4910` `Sound_IsFinished` → **`Sound_IsPlaying`**. The body returns 1
  only when `[this+0x2c]` (BASS channel) is non-zero AND HGE +0x220 returns
  true; +0x220 is `Sound_ChannelIsPlaying`, which returns 1 for
  `BASS_ChannelIsActive == BASS_ACTIVE_PLAYING`. The single caller
  `Sound_CommitChannelPosition` `0x1402e5000` pushes the channel position when
  the value is 1 — correct for a *playing* channel — but its plate had already
  copied the inverted wording ("0 when the sound is still playing"). Both caller
  plates (`Sound_CommitChannelPosition`, `Sound_UpdateActiveChannels`) were
  corrected in the same pass (plate only, no rename of the callers).

Everything else sampled is correct; no stylistic renames requested. The sample
(full bodies read, name/plate vs body):

Agent 2 also flagged its three new tutorial/radio owners for agent-9 review. All
three accepted, no rename proposal:

* `EscadraName_WrapText` `0x140237e30` - splits on spaces, keeps
  `ceil(words*ratio)` words, maps `@.,;:=-` separators to `_`/space. The body is
  a short-name builder; "WrapText" is loose but not wrong, and the plate gives
  the exact algorithm.
* `Radio_ReportContact` `0x140238460` - `RADIO_SAVE` banner, bearing from
  creature `+0x150/+0x154`, `TUTORIAL` trigger, `EscadraName_WrapText` on the
  creature name, `Text_ExpandSignedDigitRuns` with the wealth/force/faith/right
  stats, result to `+0xc10`. Matches.
* `Tutorial_UpdateHuntedAlarm` `0x140253300` - `enigmaGot1` gate,
  `Dronish_descent`, `enigmaGot5..12`, `TUTORIAL_HUNTED` forced to 1.0 when
  unset, then `TUTORIAL_ALARM` + `PETR`. Matches.

| addr | name | verdict |
|---|---|---|
| 0x1401ae060 | `Gui_DisplayStringOnUI` | ok (unwrap std::string → `displayOnUI_`) |
| 0x14016f290 | `Text_DrawSingleLineFormat` | ok (vsprintf into `0x1439e8240` → `displayLableRotation_`) |
| 0x14016cfa0 | `hgeSprite_SetFrame` | ok (frame % count +0x1c0, corner normalisation) |
| 0x14011a320 | `Escadra_UpdateMapMarkers` | ok (per-ship map icons, +0xc04 contact count) |
| 0x140123c00 | `FXPS_Constructor` | ok (`"FXPS"` at +8, class word at +0x28) |
| 0x14018d2a0 | `KeyBindings_ResetAll` | ok (frees the three binding trees) |
| 0x1401ce910 | `Cinematic_BuildArgumentPanels` | ok (`DIALOG_ARGUMENT` sort + columns) |
| 0x14016bc70 | `Gui_ResolveMediaName` | ok (name cache +0xa98 → handle +0xb78) |
| 0x1402521f0 | `Shop_GiveItemToPlayerIfMissing` | ok (owned-flag +0xb0 bit 0x40) |
| 0x1402697e0 | `Shop_SellPartValue` | ok (`BOOL_147fc6f80` branch, +0x2a8 credit) |
| 0x1402694b0 | `Shipworks_TransferPartToShip` | ok (detach, +0x1330 vector, `CalculateStats`) |
| 0x14023a2e0 | `Ship_RebuildAfterPartEdit` | ok (flags 0x1f, `Body_RebuildSubtreeList`) |
| 0x140215b80 | `Fleet_TallyPartNameCounts` | ok (RbTree name→count) |
| 0x14022a900 | `Creature_CanRefuelAtNearestDesign` | ok (fuel − distance < 100) |
| 0x140239a00 | `Math_RaySegmentIntersection` | ok (parametric t + AABB reject) |
| 0x1402490a0 | `Gfx_DrawDashedWorldLine` | ok (alternating dash colours) |
| 0x14024aa50 | `Hud_DrawVerticalScale` | ok (`vcr_30`, `HUD_point`, "%i") |
| 0x140283f00 | `RbTree_InsertNode56` | ok (lower_bound, 0x58 node) |
| 0x14022c6f0 | `String_StripAngleBracketTags` | ok (`<...>` → `variousHUDDisplays_`) |
| 0x140225f30 | `Map_FindFreeSpawnPosition` | ok (10000-attempt rejection sampling) |
| 0x1402db880 | `Sound_PlayNextQueued` | ok (sorted queue head, `PlayRadioSounds_`) |
| 0x1402c99e0 | `Sound_QueueThrottled` | ok (per-id cooldown tables, max 3) |
| 0x1402e2d00 | `Sound_StopAllInTable` | ok (count table 0x1403c2cc0, HGE +0x1e0) |

Also checked but not treated as errors: `Body_Kill` and `b2BroadPhase_BufferMove`
each appear twice because one copy is a 5-byte `JMP` thunk (both plates say so);
the `deallocate` / `Load` / `Save` / `Serialize` duplicates are template or
per-class instantiations.

## Hand-offs

* The 4 renames are address-keyed here; agent 10 can fold them into
  `rep-audit-2026-10-29.tsv` (0x1402e3580 and 0x1403182a0 belong to q3,
  0x140336ea0/0x140336f00 to q4). I did not append to the q-files to avoid
  interleaving with the agents that own them.
* `0x140013160` itself (`std::vector<4-byte>::_Insert_range`, 3,397 B, only
  caller `copyOverBody`) is still `rep_*` in agent 3's slice; naming it
  `Vector4_InsertRange` would complete the family.
* `Sound_IsFinished`-style inversions are worth a second look in the
  `Sound_CommitChannelPosition` / `Sound_UpdateActiveChannels` cluster; the rest
  of that cluster (0x1402e4dc0, 0x1402e4c00) was left untouched.
