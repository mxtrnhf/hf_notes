# Tester test plan for the ally pack (2026-10-16)

The list shipped in the pack's `README.txt` (`/home/maksim/Development_Highfleet/hf_release_pack/`). Items 4, 7 and 8 are the ones with **no evidence in play yet** (an ally destroyed in battle with a replacement; control passing to an ally when the flagship is disabled is seen, but not a destroyed flagship; prize-safe targeting after the v0.9.1 fix). What each test checks in the code is described in [../findings/battle-ally.md](../findings/battle-ally.md) and [ally-runs.md](ally-runs.md).

```
TESTS WE WOULD LIKE YOU TO RUN  (all optional; tell us which ones you did)
  Each test: play it, then send the newest log (and a screenshot where marked). In the log,
  the line "ALLY SUMMARY" is printed after each battle (at the next battle plan screen, end
  screen or when you quit).
  1. BASIC: fleet of 2 or more ships, leave ship 2 switched on, fight a normal battle.
     Expect: ship 2 joins ~1.5 s after the start. Does it fight? Does the summary say so?
  2. NO ALLY: switch every button OFF ("ORDER UNSET"), fight. Expect: no ally, you fight alone.
  3. TWO ALLIES: 4+ ships, switch on ships 2, 3 and 4 (max_allies is 2). Expect: 2 and 3 join
     (3 about 3 s after 2); 4 waits in reserve.
  4. REPLACEMENT BY LOSS (not yet seen!): in test 3 let an ally get destroyed. Expect: ship 4
     steps in after a few seconds; the log shows "ALLY lost" and the summary counts it.
     If nothing steps in, or "lost" never appears, that is exactly what we want to know.
  5. REPLACEMENT BY RETREAT: press F8 with allies out. Expect: they fly off and leave, the
     next switched-on ships step in.
  6. YOU RETREAT: fly your own ship to the retreat point with allies out.
     6a. flagship_leaves "handover" (default): an ally becomes your ship and can retreat too.
     6b. set "flagship_leaves": "retreat" in ally.json: the whole squad should leave with you.
  7. YOUR SHIP IS DISABLED OR DESTROYED with allies alive: control should pass to an ally
     instead of a loss screen. Does it, and can you then win or retreat?
  8. PRIZE SHIPS (not yet confirmed!): fight a trade convoy (Pegasus, Odissey, Kastor, Pollux
     or Kadesh Mk1 as the trade ship, with escorts). Expect: allies do NOT shoot the trade
     ship; kill the escorts yourself and the trade ship is captured. Send the log: look for
     "prize enemies" and "ALLY target:" lines. If an ally shot the prize, tell us.
  9. FLARES: let enemies fire missiles at an allied ship. Expect flares and dodging (also
     for the ally). To compare, set "allies": false in qol.json and try once more.
 10. BATTLE PLAN SCREEN: swap the order of your ships; the ally buttons should stay under the
     numbers 2, 3, 4 ... (the on/off choice belongs to the number, not the ship). Send a
     screenshot if a button is missing, overlaps something or does not respond.
 11. AMMO SELECTOR: with ships that have an ammo choice (the round shell icon), check that the
     ally button and the ammo selector do not overlap and both still work.
 12. BIG FLEETS AND ODD SHIPS: 6 to 9 ships; carriers, missile ships, aircraft. Buttons exist
     for ships 2 to 9 only.
 13. SCREEN SIZE: other resolutions, windowed, ultrawide: are the buttons where they should
     be? Screenshot please, with your resolution.
 14. QUIT: close the game from the end screen and from inside a battle; the next launch's log
     (or the same log) should still have a summary line for the last battle.
 ANY CRASH: send the newest log immediately; the last lines before the crash matter most.
 Known and expected: allies shoot the default shell, are not tactically smart, and may
 ignore the ammo you picked.
```

## Added after the first tester crash reports (2026-10-16, v0.9.3)
Reports: re-engaging a convoy crashed; ELINT plus missiles from a strike group crashed (without opening the battle screen); the ally choice is missing when a convoy is re-engaged; all sound is relative to the last spawned ship (an ally spawn moves the listener, NOT investigated: Ghidra was offline). Patched by static analysis only, **not run**: v0.9.3 arms the ally logic only for a battle entered through the pre-combat screen (log line `ALLY battle start ... armed / NOT armed`), the prize hook only touches ships the mod brought in, F8 needs a flying flagship (0.9.2), log caps reset per battle and the log is flushed at key lines.
Note: the vanilla missile and plane defense battles already have allied AI ships (side > 0, AI flag set); the QoL `ai_flares.allies` option treats them like our allies and is NOT narrowed yet.
Checklist for the next round (each with `ai_flares.allies` true and then false):
1. Re-engage a convoy after a retreat: expect `NOT armed`, vanilla play, no ally.
2. Let a strike group fire missiles at the fleet with ELINT on, do not open the battle screen.
3. Missile or plane defense battle with allies in the fleet.
4. If it still crashes: send the log, name the last `ALLY battle start` line; then bisect `ai_flares.allies: false`, then remove hf_ally.
