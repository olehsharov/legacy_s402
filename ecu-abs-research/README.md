# ECU / ABS research: diesel ABS-VDC on a petrol Legacy GT

Research notes from one car: a **2006 JDM Subaru Legacy GT spec.B (EJ20Y, petrol)** running a
**Denso SH7058** engine ECU, fitted with an **ABS/VDC unit from a diesel car** as part of the
diesel-gearbox / s402 conversion.

Problem: with the new tuner's `(OEM ABS)` ROM (A2UG000B family) flashed, the ABS light is on and
ABS and ESP (VDC) do not work. With the car's previous ROM, ABS and ESP worked.

> ## Safety disclaimer
> - These are **research notes from one car, not a tune.** Nothing here is verified safe to flash.
> - The **2-byte fix is an untested hypothesis.** It has not been confirmed to restore ABS/VDC.
> - **Never flash anything without a verified backup of the ROM currently on your ECU.** A bad
>   flash can leave the car unable to start, and a replacement ECU needs dealer immobilizer pairing.
> - The ROM images discussed here are **not published** (see `MANIFEST.md`).
> - Everything here is at **your own risk.**

## Status (as of the latest notes, 2026-10-23)

| Item | Status |
|---|---|
| 2-byte candidate ROM `(OEM ABS WITH 2 BYTE FIX)` | Prepared 2026-10-22 (5 bytes differ from `(OEM ABS)`, all 14 checksum slots valid) |
| Verified backup of the ECU as it is now | Done 2026-10-23, byte-identical to `(OEM ABS).bin` |
| Test-write (FastECU compare/validate pass) of the candidate | Reported as passed in the working session; not yet recorded in these notes |
| Real flash of the candidate | **Not reported done.** No result exists yet |

## Headline findings

1. **The old, working ROM has no code patch.** Apart from map edits and 28 DTC enable switches, its only
   non-map change versus stock is two calibration bytes: `0xC1AD2/0xC1AD3` = `02 22` -> `A2 A2`.
2. **Those bytes go onto the CAN bus.** Function `0x1B8DC` copies the byte to RAM `0xFFFF65ED`, and
   function `0x1A58C` puts it into **byte 5 of CAN frame `0x600`** (11-bit ID, ~50 ms). The ECU never
   reads it back. It is a label for other modules.
3. **Byte 5 is a vehicle-spec bitfield.** Decoded from 212 public stock ROMs: bit 0 = 3.0 L, bit 1 = DOHC,
   bit 2 = non-turbo, bit 3 = 2.5 L, bit 4 = six cylinders, bit 5 = manual, bit 6 = never seen,
   **bit 7 = diesel**. All 5 public diesel ECU images send exactly `0xA2`. No petrol ROM sets bit 7.
   `0xA2` = diesel, manual, 2.0 L DOHC turbo; stock `0x22` = the same but petrol.
4. **The CAN machinery is otherwise identical** between the old ROM and the flashed one. The only static
   difference the VDC unit can see is that one bit.
5. **The 2-byte candidate** is the tuner's `(OEM ABS)` file with only those two bytes set to `0xA2` and
   the checksums recomputed. It tests exactly one hypothesis: the diesel VDC unit needs the diesel bit.
6. **Not proven:** that the VDC unit reads this byte. The service manual's spec-mismatch code C0045 was
   *not* among the VDC codes read (C0072, C0047, C0076), and it is unknown whether those codes predate
   the ROM change.

## File index

| File | What it is |
|---|---|
| `kramar/README - OEM ABS WITH 2 BYTE FIX.md` | The 2-byte candidate: what changed, why, what is proven, how to read the result |
| `work/ABS_RESEARCH.md` | Main research log for the ABS/VDC problem, with VDC codes, service-manual evidence, backup result |
| `work/CAN_TX_TRACE_C1AD3.md` | Disassembly trace from the calibration byte to CAN frame `0x600` byte 5 |
| `work/CAN_TX_OLD_VS_CURRENT.md` | All CAN TX/RX behaviour compared between the old ROM and the flashed ROM |
| `work/CROSS_ROM_CAN600_BYTE.md` | Cross-ROM survey decoding byte 5 from public stock ROMs |
| `xrom/rows.csv` | Per-ROM data table behind the survey (bytes read from public stock ROMs) |
| `xrom/scripts/*.py` | Scripts used for the survey (originally under `tmp/xrom/scripts/`; need the public ROM set to run) |
| `work/ECU_HARDWARE_IDENTIFICATION.md` | Is the ECU now in the car a Denso SH7058? (desk investigation) |
| `work/ENGINE_DTC_VIA_SSM_CAN.md` | Reading engine fault flags read-only over SSM-on-CAN |
| `work/read_engine_dtc.sh` | Read-only DTC flag read script (needs the project's `tuneforge` build; not included) |
| `work/make_abs_2byte_fix.py` | Builds the 2-byte candidate from `(OEM ABS).bin` (input ROM not included) |
| `work/ROM_CHANGELOG.md` | Every ROM image, why it exists, what changed |
| `work/MAF_ANALYSIS_2026-09-06.md`, `work/MAF_TABLE_BASELINE.md` | MAF scaling work (tuning step 1c) |
| `TUNING_PROGRESS.md` | Position in the tuning guide sequence, blockers |
| `current_limits.md` | Rev and boost limit findings for this car |
| `reference_roms.md` | Stock reference ROMs and the 280 hp question |
| `PROJECT_CONTEXT.md` | The project's working context and safety rules (includes a distillation of a third-party tuning guide) |
| `MANIFEST.md` | ROM / binary files deliberately not published, with sizes and sha256 |

Paths inside the notes refer to the original project layout (`roms/`, `dumps/`, `re/`, `tmp/`, ...).
Those folders are not published. `<project>` and `<serial>` are placeholders for a local path and a
device serial number.

## Sources

- Subaru diesel ECU CAN message analysis (subdiesel, draft, 2011):
  https://web.archive.org/web/20110524225302/http://subdiesel.wordpress.com/ecu-analysis/can-messages/
- Public stock ROM images used for the cross-ROM survey: github.com/bludgod/RomRaider
- Subaru factory service manuals (VDC and LAN diagnostics chapters), cited in `work/ABS_RESEARCH.md`

## Known erratum in the notes

`work/ABS_RESEARCH.md` (Result 2026-10-23 10:08) abbreviates the backup's sha256 as `901a392a…fbd7`.
The full hash is `901a392ac9f50696b0ef4a663f4b08252b6cf4d10afcd50c25f2ee9d0404dc6b` (ending `dc6b`),
the same as `(OEM ABS).bin`. See `MANIFEST.md`.
