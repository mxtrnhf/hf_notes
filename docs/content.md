# Dialogue, characters, events, textures

Goal under study: add NEW characters, events and art, not only convert existing ones. Status: **analysis only, nothing built.** Sources: the decoded English pack (2914 entries), `Media/*.res`,
the code strings, and the community guides (`../ref/community-guides.md`).

## What is plainly data (and therefore moddable)
* **Dialogue text and flow** (`Data/Dialogs/*.seria_enc`, cipher in `formats.md`): entries `#KEY<TAB>text`; a line mixes `<TAG=value>` commands with spoken text and `{style}` markup.
  Entries chain by key name (`PETR_DAUD_1` -> `<SCR=CONTINUE|PETR_DAUD_2|...>`).
* **Art** (`Media/media.res`, `Tex/*.res`): `Texture` + `Animation` text records over 4096x4096 PNG atlases (`formats.md`). Names are looked up everywhere by string.
* **Event rewards/penalties** live in the dialogue tags (`<SCR=STOP|GOLD=10000|FASIL=-1>`, `MORAL|3`, `LEVEL_WEALTH=-1`); a few outcomes are hard-coded (new ships, forced stays, no repair/refuel).

## Tags seen in the English pack (60 kinds; count of uses)
`SCR` 1010 script action (223 distinct: `CONTINUE|KEY`, `STOP`, `EXIT`, `SKIP|KEY`, `CHECK_JOINED|NAME|KEY`, `END_BRIEFING|n`, `MORAL|n`, `JOIN=Ship,NPC`, `GOLD=n`, `<NPC>=n` loyalty change such as `FASIL=-1`, ...) ·
`NPC` 722 speaker · `SIDE` 496 (1 = left per the guide) · `ANS` 473 answer button (`<ANS=text|NEXT_KEY|effect>`; `|EXIT` only worked on answer lines, not NPC lines [guide]) ·
`EVENT_CARD` 172 (`<EVENT_CARD>{font..}TITLE@10 {animation=event_diana} @30...`) · `NOSPEAK` 141 · `SHADOW` 80 · `MUSIC` 55 · `APPROVE` 48 · `TRG` 47 (trigger counter, e.g. `<TRG=INTERCOM_FASIL|1>`) ·
`HANDSHOW_*` · `AMBIENT` 42 · `BLUR*` · `SOUND` 25 · `GLOW_GUI` · `RAM` · `EVENT` · `ACTIVE` · `BACKGROUND` (`background_crowd_01`) · `ILLUSTRATION=-1` · `SALUTE` · `CORNER_SPEAK` · `FADEAWAY` ·
map-vessel tags `POSITION/COURSE/SPEED/ROUTE/ROUTE_TIME/CONTACT_*/CARGO/NEEDS` · `RENDER_LAMP_ON/OFF` (Config reference).

## Characters
* 16 `<NPC=NAME>` values: PETR (294 lines), DAUD, FASIL, BOY, HIRE, OMAR, GOVERNOR, AIRBORNE, LOCAL, HISSID, HARISHID, GIRL, SCOUT, VETERAN, KNIGHT, PROPHET.
* Art per character is uniform [game]: portraits **`NAME_C`** and **`NAME_S`** (about 900-2100 px wide, `Static*.res` atlases; confirmed by a guide: `PETR_S rect=3,3,1007,1115` in `Static7`),
  icon **`icon_name`** (87x87), and for some a full-screen scene **`alarm_name` / `inter_name`** (1920x1080, `Hall*.res`). `LOCAL` and `HIRE` have no portraits.
  Replacing a portrait = edit the PNG region named by its `rect` (known to work, guide).
* Code [code]: a generic NPC system (saved lists `m_npcs`, `m_npcs_known`, `m_npc_index`; events `NPC_JOINED`, `NPC_LEFT`, `NPC_STATUS`, `NPC_TAKEOFF`; UI `LANDMODE_NPC`, `icon_npc_black`; script
  `CHECK_JOINED`), plus hard-coded story flows by key name (`PETR_DEPARTURE(_CHANCES)`, `PETR_DAUD`, `PETR_ANYTIME`, `TUTORIAL_*`, `ISAIAH_*`, `INTERCOM_*`, `NUCLEAR_ESCALATION_*`).
* [guess] NPC names are strings, not an enum: a dialogue-only new character may need only art + text. A character with mechanics (joins the fleet, loyalty, perks) may need code.

## Events
* ~48 event pictures: animations `event_*` (diana, triumph, murder_01, caravan, ... and `event_noimage`), shown by `{animation=name}` in an `EVENT_CARD`. A new one = a new Animation record.
* What triggers a given key is in code or in earlier entries' scripts. The guide lists "triggering specific events" and "expanding/branching existing events" as unsolved.
* Enemy strike groups are stored in the **save** and can be rewritten (rebalance repo: `sg_editor.py`); levels cannot be added (`formats.md`).

## How the code reaches entries [code: key strings in the exe vs. references between entries]
* 2914 `#KEY` lines (the Hara Vera study counted 2902 by a stricter rule, so its deltas are relative to that). Only 442 are referenced by another entry's `<SCR|ANS|TRG>`; ~860 entry points are **literal strings in the executable** (the code triggers them by name);
  ~1250 are built from a prefix + name/number at run time. Prefix constants found in the exe: `HELLO_GREETING_`, `INTERCOM_`, `DIALOG_`, `SHIP_NAME_`, `SHIP_DESC_`, `LOCATION_NAME_`,
  `ESCADRA_NAME_`, `FILM_`, `VERSE_`, `SUPPLIES_`, `PRECOMBAT_PLAYER_`, `GLITCH_LEVEL_`, `MAPMARK_`, `MAPMODE_`, `LANDMODE_`, `BUY_`, `CRAFT_`, `RAM_`, `EDC_`.
  A new entry under such a prefix may be found without code changes (e.g. `SHIP_NAME_<new ship>`); whether the code takes a random/last index (e.g. more greetings) is unknown.
* **Correction after studying a total conversion (`total-conversion-hara-vera.md`):** counting only explicit `<SCR|ANS|TRG>` references misses chains: an entry whose `<SCR=CONTINUE>` has no target advances `KEY_n` to `KEY_n+1`. And new events do NOT need code: that mod attaches 892 new keys by rewriting 85 original entries to jump into them.
* **Random events** are families `EVENT_<NAME>[_NN]` (194 entries, ~38 events: ASSAULT, BLASPHEMY, BLESSING_01, BURN_FUEL, CARAVAN_01-04, CHASE, CLOTH, DAAVAT, DILEMA, DISASTER, DISCONTENT_01,
  DISHONOR, EHUDA, EXECUTION, HEADS, HUSH_01, LEGEND_01, LOYALISTS, MONK_01, MURDER_01, NAME, PARTISANS_01, RADIORELAY, REVOLT, ROBE, SILO, SLAVERY_01/02, STEALING_01, TRAITOR). The **root name is in
  code**; branches/outcomes (`_YES`, `_NO_FAIL`, `_RES2`...) are reached by text scripts only. Consequence: existing events can be rewritten or extended freely, and new events can be hung on any original entry (that mod does it); only a new *random-event root picked by the game* would need code.
* Outcome effects seen inside events (`<SCR=...|EFFECT=n>`): `MORAL`, `GOLD`, `FORCE`, `<NPC>=n` (loyalty), `FEAR`, `GERAT`, `DICE`, `LEVEL_FEAR`, `HUSH`, `WEALTH`, `CREW`, `RIGHT`, `WOUND`, `CRUELTY`, `INTEL`.

## Experiment plan (safe, reversible; back up `Media/`, `Data/Dialogs/`, saves first)
1. New art: **already proven by the Hara Vera conversion** (new `.res` files, `Include` lines in `media.res`, part icons as animations named after the part id). Our own test: add `TESTNPC_C` / `TESTNPC_S` Animations (a copied portrait PNG) in a new `.res` listed in `media.res`, or in `Tex_Extra/Extra.res`. The engine's `Include` is generic and new names are accepted (`formats.md`), and `hge.log` reports script errors, so this is the safest first test.
2. Replace the text of one easily reached, harmless entry with `<NPC=TESTNPC>...`; does the portrait appear, does an unknown name break anything?
3. New event picture: `event_test` Animation + an `EVENT_CARD` entry using it.
4. Only then: reach a NEW key: chain it from an existing entry (`<SCR=CONTINUE|NEWKEY>` or an answer button), or hang a new branch on an existing event root. A brand-new event root needs a code hook.
5. Characters with mechanics (`JOIN=`, `CHECK_JOINED`) afterwards, by watching `m_npcs` in a save.
Open risk: dialogue and `Media/` are overwritten by game updates; runtime injection (a mod DLL) would avoid editing files but is not designed.
