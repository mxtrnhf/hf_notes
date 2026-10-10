# Open questions

## Gameplay / mods
* **Salvos on the map:** AI fleets defending against our salvo: same `Missile.seria` setup, so the merge applies to them too? Map-level AA against a group (the three-crafts-per-pass rule, `FUN_140111110`)
  has not been read for bigger groups. A volley as ONE map object with count N (it would also fly as a group) is possible in principle; the `MapCraft` scenario `SCR_BOMBERS` is unread.
* **Multi-charge x salvo:** deliberately undecided. One A-101 part is one launcher switch (one queued launch at a time); several A-101 parts queue as separate launches and the merge treats them like any missile.
  Decide the intended use before testing or documenting it.
* `CraftsVsMissile` / `CraftsVsCrafts` flows never observed. Triumph in a fresh campaign's shops (highfleet-qol rolls a city's shop once).
* The arc scan being "gated off by data" (stats +0x128 == 0) versus a patched call is not settled (gun-side blocking itself is solved by highfleet-qol).
* Refuel: the buy-fuel slider and `REFUEL_TIME` are untraced. GOG 1.163 may share addresses with Steam 1.163; untested.

## Engine (see `engine-hge.md`)
* Which assets go through `Resource_Load` (textures? sounds? particles?) and whether `Resource_AttachPack` can override `media.res`: needs a log-only hook run. Which stock System_ method is missing from the interface table (Launch or Snapshot).

## Content (see `content.md`, `total-conversion-hara-vera.md`)
* Hara Vera proves new art, parts, dialogue and event branches as data; untested: a brand-new NPC *name* (the mod reused the 14 originals), a new random-event root, and whether its installer's 101 entries without data are duplicates (needs a real run into an empty folder).
* Does the game read an extra `.res` listed in `media.res`? Does an unknown `<NPC=...>` work with only `_C/_S` art? How to reach a brand-new dialogue key? Which characters need code (`JOIN`, loyalty)?
* Whether `CORE_LAST_LOADED_VERSION` recompute also fixes ships saved with old part data in our mods' situations.
* Config.ini optional keys (`ref/config-ini.md`) are untested.

## Release
* Run the reinstall checklist; README follow-ups (troubleshooting, a worked "add a part" guide); optional move to the modloader's logging SDK; push the repos; LICENSE names are set (`mxtrnhf`).
* Longer term: inject names/descriptions and part definitions at runtime instead of editing game files (removes the Python step and the update-overwrite problem).
