# hf_voice: key-bound sounds from loose .wav files

> Debug and experiment mod (it shares a hook with `hf_ally`, so the two are not run together). See the table in [README.md](README.md).

Standalone modloader DLL (crate `hf-voice`, `hf_voice`, local git, no remote; build `cargo xwin build --release`, DLL archived as `hf_voice_build/hf_voice_v<version>.dll`). Steam **1.163** only. Plays a `.wav` through the game's own sound player when a key is pressed; the mechanism is [../sound.md](../sound.md).

## Install
1. Copy `hf_voice_v0.1.0.dll` into `<game dir>/Modloader/mods/`.
2. Put the sound files in `<game dir>/Media/Snd/custom/` (a folder of our own; no vanilla file is edited).
3. Start the game (restart after any DLL swap). `Modloader/config/voice.json` is created on first run.

## Config (`Modloader/config/voice.json`)
```json
{ "enabled": true,
  "bindings": [ { "key": 120, "sound": "Media\\Snd\\custom\\quite_sure.wav" } ] }
```
`key` is a decimal Windows virtual-key code (120 = 0x78 = F9); `sound` is a path below the game folder (backslashes, under ~150 characters) or a `sound.res` name such as `radio_stall_01`. Several bindings are allowed. Keys act only while the game window has the focus.

## Hook
`SomethingInputTask` `0x14018dbf0` (padded `Trampoline`, see [../sound.md](../sound.md); v0.1.0/0.1.1 used `patch_call` and crashed on the first frame), 11-byte entry precheck, plus a 15-byte precheck on `playSFXSound_` `0x1402e30e0`; either mismatch refuses to start ([../hooks.md](../hooks.md)). With `hf_probe` loaded, its `mark_key` is also F9 and its sound hook changes the `playSFXSound_` entry: do not run both.

## Log lines
`hf_voice vX config: ...`, `hf_voice: hook installed on the input task`, then one `VOICE <path> -> 1` per press (1 = queued, -1 = dropped). A bad path logs `ERR: SX::play failed to get effect = <path>` in `client.log`.

## Package for players
`hf_voice_pack_v0.1.2.zip` (folder `hf_voice_pack/`, next to the other packs in the workspace): `Modloader/mods/hf_voice_v0.1.2.dll`, `Modloader/config/voice.json` (F9 = `Media\\Snd\\custom\\quite_sure.wav`, F10 = `mission_start_01`, F11 = `mission_end_01`, the last two are stock lines), `Media/Snd/custom/quite_sure.wav`, and a `README.txt` (install, key-code table, list of stock sound names, how to add a `.wav`, troubleshooting by log line). The pack edits no game file (path method). Its README says "tested in the main menu" only: battle and map use are untested.

## Two ways to name a sound
* **File path** (`Media\\Snd\\custom\\quite_sure.wav`): no `.res` edit, relies on the fallback in `CopyNameIntoMedia` ([../sound.md](../sound.md)).
* **Resource name** (`hf_quite_sure`): a `Sound` block appended to `Media/Snd/sound.res` (backup kept next to it).

## Status
v0.1.0 and v0.1.1 crashed (misaligned stack, above). v0.1.2 (2026-10-17): F9 = `quite_sure.wav`, F10 = `radio_stall_01` (a `sound.res` name, to tell a bad file-path load from a bad call): **all three keys work in play** (F9 file path, F10 stock name, F11 `.res` name) [game].
