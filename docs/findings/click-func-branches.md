# ClickFunc: decompiled branches (v1.163)

Four branches of `FUN_14012f120` (`ClickFunc`, see [click-func.md](click-func.md); element catalog in [click-func-elements.md](click-func-elements.md)). Code blocks are cleaned by hand from the Ghidra decompilation [observed, read-only]. Decompiled line numbers are for the default decompiler settings of that session. Ghidra function names are guesses [guess] and are marked with `?`. Each `if (stringCompLengthAndContent(name, "X"))` test is a sibling in the chain, not nested.

## BUY_BUY (compare at `0x140138564`, decompiled lines 4119-4174)
```c
if (stringCompLengthAndContent(name, "BUY_BUY")) {
    panel  = FindGuiElement("BUY_PNL");
    slider = FindGuiElement("BUY_SLIDER");
    CopyEscadraName(buf, panel + 0xc10);
    ammo   = filterAmmos(escadraStringToStr?(buf));
    wanted = (int) slider->vtable[+0x2f8]();
    owned  = FUN_14028c460(Get_Profile?(), escadraStringToStr?(buf));
    delta  = wanted - owned;
    if (delta == 0) {
        sound = "switch_press"; volume = 0x42a00000;   // 80.0f
    } else {
        <adjust location stock>(CURRENT_LOCATION, name, -delta);
        if (delta < 1) <profile remove>(profile, name, abs(delta));  // Ghidra: ...free
        else           loadAmmoForLocation?();
        price = *(int *)(ammo + 0x170);
        FUN_1400ba3a0(Get_Profile?(), price * delta, 0);   // gold change
        sound = "sold_01"; volume = 0x41c80000;        // 25.0f
    }
    playSFXSound?(0xb, sound, GlobalNode?, volume);
    <gui virtual +0x48>();
    supplyRoom();
    free(buf);
    goto LAB_14013e3fe;   // end of click handler
}
```
Interpretation [code for the data flow, guess for the names]: the shop slider is a **target total**. BUY_BUY applies `delta = slider - owned`, so it both buys (delta > 0) and sells (delta < 0). The gold change is `ammo+0x170` (unit price, matches the structures/ammo notes) times `delta`; this ties to the GOLD lines of the probe log (-18660 etc).

## FUEL_BUY_SLIDER (`0x140137140`, decompiled lines 3504-3556)
```c
if (stringCompLengthAndContent(name, "FUEL_BUY_SLIDER")) {
    if (CURRENT_LOCATION == 0) goto end;
    value = *(float *)(gui + 0xc0c);
    // tutorial path
    if (DAT_143a11880 == value && profile.cash(+0x2a8) == 0) {
        CreateTriggerBlank(&profile + 0x3f0);      // trigger "TUTORIAL_FUNDS"
        validateNpc?(profile, "PETR");
        formDialogStrings?(... "TUTORIAL_FUNDS_1" ...);   // dialog
    }
    if (*(float *)(CURRENT_LOCATION + 0x274) == value) goto end;
    sound = "sold_01"; volume = 25.0f;
    goto LAB_140131632;     // shared fuel-apply code, not decompiled yet
}
```
Interpretation [guess]: `CURRENT_LOCATION+0x274` (f32, previously unexplained in [open-questions.md](../open-questions.md) item 18) is compared against the fuel slider value, so it likely holds the fuel amount currently set/bought at the location. The actual apply code is at `LAB_140131632` (not read). Note `structures.md` and `systems.md` already call `+0x274` the station fuel stock (it feeds the fleet refuel formula); both readings may hold, unchecked.

## MAPMODE_MISSION_FULLTANK (`0x140134722`, lines 2362-2382) and MAPMODE_MISSION_HALFTANK (`0x1401347fe`, lines 2383-2387)
```c
// FULLTANK
if (stringCompLengthAndContent(name, "MAPMODE_MISSION_FULLTANK")) {
    el = FindGuiElement("MAPMODE_MISSION_FUEL");
    if (el) {
        el->vtable[+0x2f0]();
        CopyString(el + 0x195 * 8, &DAT_140364d08);
    }
    addShipsToSilentStrikeGRP?();
LAB_14013476f:
    **(param_2[0x118]) + 0x114 = 0;
    if (param_2[0x17b])
        genericPressButton(param_2[0x17b], "button_01_check", 0, 0);
    // clears locals, then goes to the common tail LAB_1401347c8
}
// HALFTANK
if (stringCompLengthAndContent(name, "MAPMODE_MISSION_HALFTANK")) {
    memcmp(...);          // Ghidra: VCRUNTIME140.DLL::memcmp, probably a mislabel
    goto LAB_14013476f;   // same code as FULLTANK's tail
}
```
Interpretation [guess from names]: mission-planning fuel-load presets for a strike group ("SilentStrike"), NOT the fleet refuel rate. The refuel rate lives in the Escadra.cpp fleet update at `0x140111ff0` (see [mods/refuel.md](../mods/refuel.md)).
