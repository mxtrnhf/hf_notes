# highfleet-multicharge  (repo `hf_multicharge`)

Parts that launch several times before they are used up. **Charge level = part id**: `MDL_AA_X3 > X2 > X1` (S-4 Triumph, combat AA) and `MDL_A101_4 .. _1` (A-101, four launches of the A-100, map).

* Launch with charges left: fire a **clone** of the part (editor-style copy added to the level), then rewrite the real part's id in place and refresh its stats index (`FUN_140281cc0` -> +0x188).
  Last level: the real part launches and the game removes it. The id is saved with the part, so the count survives landing, saves, restarts; each level has its own name and price.
* New id must fit the old string's **capacity**, so no level id may be longer than the first. Roll back if the game does not know the id.
* Hooks (owner): combat AA launch `0x14002e590`, `0x14002e3a0` (**not** the Zenith launch, which goes through `FUN_14002ff60` and is not hooked, so multicharge does not affect Zenith: [../findings/combat-missile-launch.md](../findings/combat-missile-launch.md)); map launch `0x1400eced0` (the queue entry's part ref is repointed at the clone with `FUN_140194de0`).
* AI ships use the same rule; failed attempts (AI retries every frame) are silent and a part is left alone for 250 ms after a failed clone launch.
* Config `multicharge.ini`: `enabled`, `log_verbose`, one `[section]` per part (`ids`, `copy_from`, `prices`, `name_*`, `desc_*`, `legacy_counter`). Read by the DLL **and** by `tools/apply_data.py`.
* **Data tool** (Python, once, game closed): adds stats (`OL.seria`), body (`parts.seria`), names (both language packs), palette entry (`Shipworks.json`) for every level; `.bak` once; idempotent.
  From pristine files it reproduces the hand-built Triumph and A-101 exactly (diffed). Needed because the DLL can only swap to ids that already exist as data.
* Status: Triumph and A-101 work [game] incl. last charge. Old `m_logic_i4` counter parts migrate once (`legacy_counter=1`).
* Limits: one A-101 part = one launcher switch = one queued launch at a time. Interplay with salvos on the map is intentionally undecided (`../open-questions.md`).
