# Cross-ROM survey: CAN 0x600 byte 5 ("spec byte", 0xC1AD2/0xC1AD3 in A2UG000K)

Written 2026-10-22. This was static analysis of public stock ROM images only. No ECU, cable or serial device was touched, and nothing was flashed.
- Source: github.com/bludgod/RomRaider. All 337 images of 1 MiB were downloaded (raw binaries, despite the `.hex` names) into `tmp/xrom/dl/`.
- Scripts are in `tmp/xrom/scripts/`. The per-ROM results are in `tmp/xrom/rows.csv`.
- Labels:
  - **VERIFIED** means the bytes were read from the image and the code path was matched.
  - **INFERRED** means a ROM's model, engine or transmission was taken from its file name, from the RomRaider definition (`<market>/<model>/<submodel>/<transmission>`), or from general model knowledge.

## Summary

Byte 5 of frame 0x600 is a bit-packed engine/vehicle spec word. In the petrol ROMs, six bits line up exactly with the six "spec" signals the service manual lists: cylinders, SOHC/DOHC, turbo/NA, 2.5 L, 3.0 L and AT/MT.
- Petrol ROMs never set bit 7 or bit 6.
- All 5 public Subaru **diesel** ECU images (EE20, JZ2F/JP3F, 2009-11 EDM Impreza and Forester) send exactly **0xA2**, from one constant at 0xB0389.
- That decodes as **bit 7 = diesel**, plus MT, DOHC, turbo and 2.0 L. The value is the same as the frame on our car.
- So the previous tuner's `A2 A2` makes our petrol ECU announce itself on CAN as a **diesel, manual, 2.0 DOHC turbo**, whichever transmission path is selected.

## Method (VERIFIED)
- I matched the function at 0x1B8DC by an SH-2 instruction-shape pattern with register wildcards. It is a getter jsr, then `tst`/`bf`, two `mov.l` calibration addresses, `mov.b` reads, and a store to RAM.
- Match count: 185 ROMs.
- Getter result 0 selects the first address ("AT path", 0xC1AD2 equivalent). Non-zero selects the second ("MT path", 0xC1AD3 equivalent).
- For all 185 ROMs, I confirmed the RAM byte feeds byte 5 of the 0x600 TX buffer. The buffer was taken from the CAN record `00000600 00 mb 08 00 <buf>`. The feed goes through either a literal-pool store (77 ROMs) or a GBR-relative store (108 ROMs, the 2008+ code base).
- Other ROM families did not match the pattern, so I traced them by hand or with a small symbolic tracer:
  - **H6 EZ30 (2005-08):** a single calibration byte copied to byte 5. There is no AT/MT branch, so the value is hard-coded per ROM.
  - **Diesel:** a single byte, cal 0xB0389 → RAM 0xFFFF9C0D → byte 5 (`mov.b r0,@(5,r14)` at 0x66300 in JZ2F401A).
  - **GD/GG Impreza and SG Forester ECUs, 2005-07** (A2WC Forester/Baja, A8DH/A8DK, E2UE/E2VG/E2VH/E2ZJ Impreza/Forester): 0x600 is built with byte 5 = constant **0** (`mov.b r0,@(5,r4)`, r0=0). These 64 ROMs carry no spec byte.
  - **66 ROMs** have no 0x600 TX record in that form. These are 2005-07 USDM STI and 2010+ BM Legacy, 2014+ STI and FB20 Impreza. I did not examine them further.
- Transmission selector: I found it in 70 ROMs (the A2 family and the EZ1 family). The code is the same as at 0x27E58: cal == 0xAA → flag 0, == 0x55 → flag 1, otherwise a hardware input.

## Table (bytes VERIFIED; spec INFERRED from names and definitions)

| byte5 AT path / MT path | n | engine (inferred) | ROMs (examples) |
|---|---|---|---|
| **02 / 22** | 29 | 2.0 DOHC turbo EJ20 | JDM Legacy GT incl. A2UG000K/B (5MT/6MT/AT); JDM Impreza STI and WRX STI spec C, R205, S206 (AZ1G/AZ1K/AZ1L); JDM Forester XT; Exiga 2.0GT; Impreza SGT |
| **0A / 2A** | 76 | 2.5 DOHC turbo EJ255/257 | USDM/ADM Legacy GT, Outback XT; WRX/STI 08-14 (ADM/EDM/USDM); Forester XT 09-13; JDM STI A-Line AT (AZ1G502L/800F) |
| **2A / 2A** | 21 | 2.5 turbo, MT-only car | USDM WRX/STI 2011-14 (AE5I/AE5K/AE5L/AE5Q): both paths carry the MT bit |
| **0C / 2C** | 45 | 2.5 SOHC NA EJ253 | Legacy/Outback/Impreza/Forester 2.5i 2005-11 (E2.., EZ1.., EE5I) |
| **04 / 24** | 1 | 2.0 SOHC NA EJ203 | E2UD001E JDM Legacy 2.0 SOHC B-sport AT |
| **06 / 26** | 2 | 2.0 DOHC NA FB20 | EP5D003Q JDM Forester 2.0, EP5D700X EDM Forester 2.0X 2013 |
| **0E / 2E** | 5 | 2.5 DOHC NA FB25 | EP5D201D, EP5D202N, EP5G211A (Forester 2.5 FB). Also EP5D004L and EP5D202A, which are *labelled* 2.0X: probable mislabels |
| **17** (single) | 15 | 3.0 H6 EZ30, AT | Legacy/Outback/Liberty 3.0R AT, 2005-08 (D0XJ, D2xx) |
| **37** (single) | 2 | 3.0 H6 EZ30, MT | D2UH001M (ADM Liberty 3.0R, definition: MT), D2WD701C (EDM Legacy 3.0R MT) |
| **1F / 1F** | 4 | 3.6 H6 EZ36, AT-only | Tribeca 3.6 2011-13 (DE5F/DE5I/DE5K/DE5L) |
| **1F / 3F** | 2 | 3.6 H6 EZ36 | Tribeca 2009 (DZ1E402B, DZ1G001F) |
| **A2** (single) | 5 | 2.0 DOHC turbo **diesel** EE20, MT | JZ2F401A/411A/430A/441A (EDM Impreza 2.0D), JP3F522A (EDM Forester 2.0D) |
| 00 (const) | 64 | various | GD/GG Impreza, SG Forester, Baja, 2005-07 |

Neighbour bytes:
- In the A2UG/A2UI/A2TB family the run is always `xx 02|0A 22|2A 14 00 3F 1E`.
- The byte before the pair (0xC1AD1 equivalent) is 06/05/04. It is 06 for 6MT, 05 for 5MT, 04 for SGT 4EAT, but **AT ROMs vary**: JDM Legacy GT AT = 05, USDM/ADM GT AT = 06. So "forward gears" holds for MT only, and the byte's meaning stays UNKNOWN.
- In other families the neighbours are unrelated calibration (5A, BE, 80, B0 ...). No neighbour byte co-varies with the spec in a way that is consistent across families.

## Bit decode

| bit | mask | meaning | evidence |
|---|---|---|---|
| 0 | 0x01 | 3.0 L | set only in H6 ROMs (EZ30 0x17/0x37, EZ36 0x1F). **Strong** |
| 1 | 0x02 | DOHC | set in EJ20/EJ25 turbo, FB20/FB25, EZ30/36 and diesel; clear in EJ203/EJ253 SOHC. FB20 06 vs EJ203 04, and FB25 0E vs EJ253 0C, differ only here. **Strong** |
| 2 | 0x04 | non-turbo (NA) | set in every NA engine and clear in every turbo engine, diesel included. FB20 06 vs EJ20T 02 differ only here. **Strong** |
| 3 | 0x08 | 2.5 L | set in EJ25x/FB25; also set in 3.6 (0x1F = 2.5 + 3.0 bits) |
| 3+0 | — | displacement field: 00 = 2.0, 08 = 2.5, 01 = 3.0, 09 = 3.6 | **Strong** for 2.0/2.5/3.0. 3.6 rests on 6 Tribeca ROMs |
| 4 | 0x10 | 6 cylinders | set only in H6 (EZ30, EZ36). **Strong** |
| 5 | 0x20 | MT | always the flag=1 path; selector 0x55 = MT (see below); 0x37 vs 0x17 on H6 MT vs AT; MT-only WRX/STI = 2A/2A; AT-only Tribeca = 1F/1F. **Strong** |
| 6 | 0x40 | never set in any ROM | UNKNOWN |
| 7 | 0x80 | diesel | set only in, and in all, 5 diesel ROMs (0xA2). No petrol ROM of 185 + 22 has it. **Strong but n=5, one engine.** No document names it |

- Selector byte vs labelled transmission: 0x55 ↔ MT and 0xAA ↔ AT held in all 26 A2-family ROMs where the selector was found, and in most EZ1 ROMs.
- Four EZ1 ROMs conflict (EZ1G108N ×2, EZ1G109J, EZ1D303B). The definition or file name says MT, or the market/model disagree with each other, while the byte says 0xAA.
- Their ECU IDs follow the AT pattern seen in correctly labelled siblings ("…14x007"), so a labelling error is the likely cause (INFERRED).

## What this means for our car (INFERRED)
- Stock A2UG000K sends **0x22** (2.0 DOHC turbo, MT). The tuner's ROM sends **0xA2**, which adds the diesel bit.
- The diesel ABS/VDC unit in the car would expect the diesel spec. That is consistent with the owner's report: 0x22 gives ABS/VDC dead, 0xA2 gives it working.
- It is also consistent with DTC C0045 "incorrect VDC control module specifications". This is a hypothesis; the receiver's logic is not visible.
- Writing A2 into the AT-path byte (0xC1AD2) as well is harmless on this car, because the selector 0xC2D80 is 0x55.

## Unknowns
- Bit 6 has no observed use. Bit 7 = diesel rests on one engine family, and no Subaru document was found that states it.
- I did not check whether other diesel-specific frames or bytes also matter to the VDC unit.
- 66 ROMs (2010+ BM Legacy, late STI, 2005-07 USDM STI) were not decoded.
- The 64 GD/SG ROMs send byte 5 = 0, so on those platforms the spec must travel elsewhere or not be checked.
- Spec labels come from file names and community definitions. At least 5 look wrong:
  - EP5D004L and EP5D202A: labelled 2.0X, byte says 2.5.
  - DE5L510K: labelled 3.0R, byte says 3.6, and the 2013 Tribeca was 3.6 only.
  - AE5I500N: labelled JDM STI AT, byte says 2.0T.
  - The three EZ1 AT/MT conflicts above.
