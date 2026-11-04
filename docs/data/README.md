# Reference data

[Home](../../README.md) · [Detailed catalog](../README.md)

Reusable tables, captures and reference code, grouped by purpose. Dated Ghidra reports and their audit tables are in [Ghidra history](../ghidra/README.md), not mixed into this directory.

## Porting 1.151 → 1.163

Read the [porting guide](../porting-1151-1163.md) and [version differences](../version-differences.md) before using these tables. Files are in `porting-1151-1163/`.

- [Function names and addresses](porting-1151-1163/port-1151-1163-functions.tsv)
- [Address matches](porting-1151-1163/port-1151-1163-matches.json)
- [Signatures](porting-1151-1163/port-1151-1163-signatures.tsv)
- [Signature v17 fixes](porting-1151-1163/port-1151-1163-signatures-v17-fixes.tsv)
- [Signature reverts](porting-1151-1163/port-1151-1163-signature-reverts.tsv)
- [Signature measurements](porting-1151-1163/port-1151-1163-signature-measure.tsv)
- [Thiscall signatures](porting-1151-1163/port-1151-1163-thiscall.tsv)
- [Callsite-based names](porting-1151-1163/port-1151-1163-callsite.tsv)
- [WriteString fix](porting-1151-1163/port-1151-1163-writestring-fix.tsv)
- [Variable names](porting-1151-1163/port-1151-1163-variables.tsv)
- [Data labels](porting-1151-1163/port-1151-1163-labels.tsv)
- [Label review](porting-1151-1163/port-1151-1163-labels-review.tsv)

## Rendering and GUI

- [ClickFunc element catalog](rendering/clickfunc-elements.tsv), companion to [ClickFunc](../rendering/click-func.md).
- [Pre-combat ammo GUI dump, 2026-10-16](rendering/gui-dump-precombat-ammo-2026-10-16.txt), evidence for the [pre-combat screen](../rendering/precombat-screen.md).

## Terrain

- [Landscape generator](terrain/landscape_gen.py), companion to the [generator specification](../findings/strategy/landscape-generator-spec.md).
