# Ship self-knowledge profiles: how the game computes mass, TWR and reach (1.163)

Status: derived from the `.seria` files and validated against the game's own stored `m_tele_*` values (164 designs) and telemetry. The profile tables are not yet consumed by the AI; the strategic-TWR scalar is (hf_ai v0.10.8+). Data and details: the local `tuning_telemetry/ship_profiles/` (`report.md`, `ship_profiles*.json`, `scripts/`). Purpose: let the hf_ai tactic layer derive "this ship is quick / heavy / short-ranged" from numbers instead of hard-coded ship rules. Tags: [code], [data], [guess].

* `Creature::CalculateStats` = `0x14007fcf0` (calls the per-part accumulator `FUN_140071380`). Mass (+0x15b8) = sum of `m_mass` (body +0x1d8) over bodies with a null/root master; no fuel or ammo mass. Engines add stats +0xf8 to bank +0x1664 (spasmcode 102, left) or +0x1668 (103, right). Battle TWR (+0x1604) = (L+R)/(mass x 9.82), 0 if a bank is empty, not damage-scaled; map TWR (+0x160c) uses the map thrust (damage-scaled); map speed = 50 x sqrt(map TWR - 1). [code]
* Gun reach (creature +0x1838 / +0x183c per fire group) is a caliber table: 37/57mm 800, 100/130mm 1500, 180/203/305mm 3000, 220mm rocket 6000, else 1000; 500 with AP loaded. [code]
* Stock designs are in `Objects/Designs/`, not `Ships/` (rewritten by the speed mod; `Ships/Lightning.seria` hand-edited). Live parts = Frame/Body count + 9, start hp = sum of m_health + 810 (unverified for designs with other than 2 antennas). [data]
* Lightning: TWR 12.99, thrust/mass 128, reach 1500; Intrepid: 5.76 / 56 / 1500; Navarin: 5.31 / 52 / 800 (6 flare launchers, 3 bombs, 2 Zenith). Enemy heavies (Gryphon, Borey, Kormoran, Kadesh, Kastor) have thrust/mass 22-28 and 20k hp: they park rather than kite. Measured p99 acceleration is 1.26-1.75 x thrust/mass.
* Unknown: drag, engine bank semantics, mass vs fuel/ammo at runtime.

## hf_ai strategic cutoff (2026-10-31)

Verified against the live Steam 1.163 Ghidra program: `displayinShipworks?`
(`0x1400d6f70`) reads the float at creature `+0x160c` at `0x1400d7443`, converts
it to double and passes it to the numeric TWR display (`0x1400d7489`), following
the `TWR_STAT` label. This is the shipbuilder's strategic TWR, not battle TWR at
`+0x1604`. hf_ai v0.10.8 uses the same guarded scalar read for `twr_cutoff`;
comparison uses the unrounded value and is inclusive. Existing maneuver scopes,
flare exceptions and the zero-cutoff bypass are unchanged. Upstream highfleet-rs
at `8a6a8a399d89af035adb0087b19ac1021fc9c2f8` has no Creature layout.
Native display/offset verified statically; new cutoff behavior still needs an
in-game A/B check.

Validation/deployment (historical, 2026-10-31): both crates cross-built for Windows MSVC; the regression
`cutoff_uses_shipworks_twr_not_battle_twr` passed under Wine in both. The automated suites were removed in v0.10.8, so these runs are not repeatable from the current tree. Consolidated
`highfleet-allies/ai` suite: 91 passed, 1 ignored. Standalone `hf_ai`: 88 passed,
1 pre-existing failure (`v0_2_0_config_without_tactics_loads_with_tactics_off`
still expects removed `k_center`). Formatting checks have existing baseline
failures; no broad reformat was applied. Installed the standalone v0.10.8 DLL
as `HighFleet/Modloader/mods/hf_ai_v0.10.8.dll`, SHA-256
`cfca07fccc7b734c99d9a25651b282bb56ef2499e9e6859c9d0811f2519b60ae`.
Previous v0.10.6 DLL and config preserved under
`HighFleet/Modloader/backups/hf_ai_pre_strategic_twr_20261030T222512Z/`.
Installed config is byte-for-byte unchanged (`twr_cutoff: 2.0`); only one AI DLL
is active. The game was not running during deployment; next launch needs an
in-game comparison against the shipbuilder TWR.
