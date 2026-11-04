# Mercenary / reinforcement ships: where the buyable list lives (1.163)

Program: `Highfleet.exe.unpacked.exe` v1.163. Researched 2026-10-30.

**Answer:** the ships offered for money at a city are **not** generated from the
city. They come from a hard-coded table in `addReinforceingShips`
(`0x14021b8c0`), chosen by a tier argument from the caller plus one
`HGE_RandInt` roll. The city/dialog only decides when to call it and with which
tier.

## The table

`addReinforceingShips(profile, extraName, tier, flagA, flagB, name2)`

* **tier 0** — `HGE_RandInt(0,4)`, one ship:
  `Navarin` (0), `Scarab` (1), `Meteor Mk3` (2), `Fatman` (3), `Lightning Mk2` (4)
* **tier 1** — `HGE_RandInt(0,7)`, one ship:
  `Navarin` (0), `Intrepid` (1), `Jaguar` (2), `Voskhod X2` (3),
  `Triumphant` (4), `Longbow` (5), `Vega` (6), `Kormoran` (7)
* **tier 2** — `HGE_RandInt(0,7)`, **two copies** of the same eight-name set

A non-empty `extraName` is pushed before the roll, so a caller can add one named
ship on top of the random pool. Each name is resolved through the property/design
library and instantiated as a `NEW_SHIP` appended to the player's escadra.

## Who chooses the tier

| caller | site | tier |
|---|---|---|
| `Dialog_ExecuteChoiceActions` `0x1400b1440`, branch `ASK_REINFORCE` | `0x1400b4b69` | 1 |
| same, name from `somethingNPC_[5]` | `0x1400b4f14` | 1 |
| same, names from a comma-split string | `0x1400b5316` | 1 |
| `creatureLogic` `0x140033b90` (event/script path) | `0x1400432a9` | 0 |

`ASK_REINFORCE` exists only in the exe, not in `Data/*.seria`: the dialog is
built by code.

## Consequences

* No per-city stock; `Location+0x25c` (city type, 6 = mercenary) is never
  consulted here and nothing compares it to 6.
* Mods cannot add a mercenary ship via data files — the table in
  `addReinforceingShips` must be extended.
* `Profile+0x2c0` (`m_npcs`) is the Tarkhan/NPC roster (land-mode NPC panel with
  `FOR_TARKHAN` / `FOR_HIRE` / `FOR_JOIN`), a separate mechanism.
* The Shipworks path (`City_EnterShipworks` `0x140211220`) sells/repairs
  **parts**, not whole ships.

## Open

Tier 2 has no caller found in the sweep; it may be reached from a path that
computes the tier in a register rather than an immediate.
