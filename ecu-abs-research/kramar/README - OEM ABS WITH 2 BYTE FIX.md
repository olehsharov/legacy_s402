# JDM LGT 06 MT DIESEL SWAP 12bar OKKO 95 (OEM ABS WITH 2 BYTE FIX).bin

**Status: CANDIDATE. NOT FLASHED. NOT TESTED ON THE CAR.** Prepared 2026-10-22 for the tuner to review.

## What it is

The file `(OEM ABS).bin` (the tuner's map work on an A2UG000B ROM) with **two calibration bytes changed**:

| Address | `(OEM ABS)` | This file |
|---|---|---|
| `0xC1AD2` | `0x02` | `0xA2` |
| `0xC1AD3` | `0x22` | `0xA2` |

Because the ROM checksums cover these bytes, three bytes of the checksum-fix triple at `0xFFB88` also change
(`0xFFB89` CC→CB, `0xFFB8A` 75→D4, `0xFFB8B` 3C→BC). **5 bytes differ in total.** All 14 checksum slots verify.

| | sha256 |
|---|---|
| `(OEM ABS).bin` | `901a392ac9f50696b0ef4a663f4b08252b6cf4d10afcd50c25f2ee9d0404dc6b` |
| this file | `805116cb931f44214e2f967bde378daa6bbc5f36986f0a876103358ad89374c4` |

Built by `work/make_abs_2byte_fix.py` (read-only on the source, refuses to overwrite).

## Why

**Symptom with `(OEM ABS).bin` flashed:** ABS light ON, ABS and ESP (VDC) do not work, wheel-spin/braking behaviour is wrong.
**Symptom with the previous ROM** (dump taken from the car before the ECU was replaced): no ABS light, ESP works and can be switched off
(but the dash lamp does not show the off/on state).

The previous ROM was compared with the stock ROM it came from. **It has no code patch.** Every instruction byte is stock. Besides map edits and
28 diagnostic-code switches (which the OEM file also has), its only non-map edit is exactly these two bytes: stock `0x02`/`0x22` → `0xA2`/`0xA2`.

What the ECU does with the byte (from the disassembly, Ghidra + hand reading):

- Function `0x1B8DC` copies `0xC1AD3` (or `0xC1AD2`, depending on a configuration flag) into RAM `0xFFFF65ED`.
- Function `0x1A58C` puts that RAM byte into **byte 5 of CAN frame ID `0x600`** (11-bit, 8 bytes, sent about every 50 ms).
- The ECU never reads the byte itself. It is a label sent to other modules on the bus.
- A public analysis of the Subaru diesel ECU (subdiesel.wordpress.com, "CAN Messages", draft) lists frame `0x600` from the ECU every 50 ms with byte 5 = **"const 0xA2 (from data segment)"**.
  The same page shows the ABS/VDC unit and the body control unit (BIU) on the same bus. This car has diesel-model parts.

So the old ROM made the petrol ECU's frame `0x600` match the diesel ECU's in that byte, and the stock petrol value is `0x22`.

## What is proven and what is not

| Claim | Status |
|---|---|
| Old ROM has no code patch; only these two bytes differ outside maps and DTC switches | **Verified** (byte comparison) |
| The bytes end up in CAN frame `0x600` byte 5 | **Verified** (disassembly) |
| Diesel ECU sends `0xA2` in that byte | **Source says so** (a 2011 draft page, "expect errors", different engine/model year) |
| Which module reads frame `0x600` | **Unknown.** Candidates: ABS/VDC unit, BIU, instrument cluster |
| What the byte is | **Decoded 2026-10-22** from 212 public stock ROMs (`work/CROSS_ROM_CAN600_BYTE.md`): a bit-packed engine/vehicle spec. Bit 5 = manual, bit 1 = DOHC, bit 2 = non-turbo, bit 7 = **diesel** (set only in the 5 public diesel ECU images, which all send exactly `0xA2`). So `0xA2` = diesel, manual, 2.0 L DOHC turbo; stock `0x22` = petrol, manual, 2.0 L DOHC turbo |
| That a diesel-spec VDC unit needs the diesel spec bit | **Plausible, not proven.** The service manual says the VDC checks the ECM spec. No one has shown the VDC reads this byte. The spec-mismatch code C0045 was not among the three codes read |
| That this byte alone restores ABS and ESP | **Hypothesis** |

## Why this base file

- It keeps the tuner's work, which the owner reports runs very smoothly.
- It is the 5-speed calibration (A2UG000B), which matches the 5-speed gearbox.
- The bytes sit at the same addresses in both ROM families and the code that reads them (`0x1B8DC`, literal pool `0x1B95C`) is byte-identical.

## Before anyone flashes this

1. **Read and keep a backup of what is on the ECU now.** No verified backup, no flash.
2. Charged battery, firmly seated connector. A failed flash can leave the car undrivable.
3. Flash with the vendor-supported tooling only. This file has **not** been written to anything.
4. The file is one hypothesis in one experiment. Do not change anything else in the same flash, or the result cannot be interpreted.

## How to read the result

| After flashing | Meaning |
|---|---|
| ABS and ESP work, no ABS light | Hypothesis confirmed |
| No change | The byte is not the cause. Next step: a listen-only CAN capture and the ABS unit's own fault codes |
| New faults appear | Revert to the backup and report which |

The ESP on/off lamp not showing state in the old ROM is **not** explained by this byte. If it persists, expect it to be a different frame.

## Not touched here

All maps, rev limit, fuel, timing and boost in this file are the tuner's, unchanged. Not reviewed or validated by this work.
Research record: `work/ABS_RESEARCH.md`.
