# Ghidra changes, 2026-10-27 (ghidra-curator, after the hot-reload study)
Program `Highfleet.exe.unpacked.exe` v1.163 (path `/Highfleet.exe.unpacked.exe v1.163`); the check-in to the shared project is the user's. Old names are in the plate comments (rule of 2026-10-26). Study: [../findings/hot-reload-feasibility.md](../findings/hot-reload-feasibility.md).

| kind | address | change |
|---|---|---|
| rename | 0x140224c60 | `FUN_140224c60` -> `ReadConfigIniFile` (`LoadConfigIni` collided with `Load`) |
| rename | 0x14024d520 | `FUN_14024d520` -> `WriteConfigIniFile` (`SaveConfigIni` collided with `Save`) |
| rename | 0x14018d3d0 | `FUN_14018d3d0` -> `SetDefaultKeyBindings` (VK codes W S A D ... for ids 0x1000..0x1017; the ds4-files report called it "apply keys") |
| rename | 0x140211e10 | `FUN_140211e10` -> `ExitGame` (log string `APP::exit_game`) |
| rename | 0x1402db350 | `FUN_1402db350` -> `SetSkirmishFlagsFromLevelName` |
| rename | 0x1402e4b50 | `FUN_1402e4b50` -> `FreeFlaggedAudioObjects` |
| rename (data) | 0x143a11909 | `doRecoil_global` -> `g_bGameTimeFreezeFlag` (it freezes game time only) |
| rename (data) | 0x143a11901 | unnamed -> `g_bExitRequested` |
| comment (eol) | 0x1401a8eb8 | hot-reload hook site S1 (`CALL SomethingPreTask`, bytes `E8 83 DF 0D 00`) |

Verified this session by re-reading decompile/bytes: the S1 bytes, `ExitGame` body, the freeze byte's writers and readers, both config functions, `SomethingPreTask` flow, `SetLevelSeriaToLoad_`, `LoadSeriaFile` (no cache), `LoadDialogue`, `GetStats`, gate byte 0x1403c2b11 (value 1, one reader). Not renamed on purpose: 0x14000e430, 0x140281fa0, 0x1400beea0 (purpose not confirmed).
