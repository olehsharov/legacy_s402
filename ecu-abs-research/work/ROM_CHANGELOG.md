# ROM image changelog — A2UG000K (2006 JDM Legacy GT spec.B MT)

Every modified image gets its own file. **Nothing is ever edited in place.**
Naming: `A2UG000K_<date>_<what-changed>_<checksum-state>.bin`

`_ck`        = checksums recalculated, **flashable**
`_NOCHECKSUM`= checksums NOT recalculated, **NEVER flash this**

All files are `chmod 444`. Always work on a copy.

---

## Lineage

```
roms/STOCK_A2UG000K_..._2026-08-25.bin      as-found state of the car (baseline)
   |                                         verified 3x + by ECU's own block CRCs
   +-- work/..._rev-6800-6600_NOCHECKSUM.bin rev limit edited, checksums stale
         +-- work/..._rev-6800-6600_ck.bin   checksums fixed  <-- FLASH CANDIDATE
```

---

## 0. Baseline — the car as found

| | |
|---|---|
| File | `roms/STOCK_A2UG000K_2006_JDM_Legacy_SpecB_MT_2026-08-25.bin` |
| sha256 | `c510bc45d8ac54244adfc7a1a10866d91640c6a573b3c8554d5517370895fbd7` |
| Verified | GUI read 2026-08-25 · CLI read 2026-08-29 · CLI read #2 — all byte-identical |
| ECU-side proof | all 16 block CRC32 matched, computed **by the ECU**, 2026-08-29 13:39 |

Not stock Subaru — a full retune (7467 bytes / 58 regions vs factory) done after the
~2024 engine rebuild (compression 11:1 -> ~8:1). Contains a **break-in rev limiter**
the tuner never lifted.

---

## 1. `A2UG000K_2026-08-29_rev-6800-6600_NOCHECKSUM.bin` — ⚠ DO NOT FLASH

| | |
|---|---|
| Parent | baseline (above) |
| sha256 | `e663b10305e55c2291e8ad92893f665d36d718a1d93cca4179fa872ae855b4c2` |
| Bytes changed | 3 |
| Status | **intermediate only** — checksums stale, ECU would reject or misbehave |

```
0x0C5381  73 -> d4
0x0C5382  c0 -> 80
0x0C5385  67 -> ce
```

**What:** `Rev Limit (Fuel Cut)` @ `0xC5380` — On Above `3900 -> 6800` RPM,
Off Below `3700 -> 6600` RPM. Two big-endian float32 fields.

**Why:** the 3900/3700 values are a break-in limiter applied at the ~2024 rebuild and
never removed. 6800/6600 restores usable revs while staying **inside the mapped
calibration** — the boost table RPM axis ends at 6800 and knock correction is active to
6700/6800. Factory is 7500/7300 but that sits above the tune's mapped range.
200 RPM hysteresis matches factory.

**Written as typed floats**, not raw integers — see the integer-in-float trap documented
in `current_limits.md`, which previously produced an image that would have prevented the
engine running at all.

---

## 2. `A2UG000K_2026-08-29_rev-6800-6600_ck.bin` — FLASH CANDIDATE

| | |
|---|---|
| Parent | image 1 |
| sha256 | `77f585690531796397202faa8e35d116fdf482d2e5b6451de33135ea648755af` |
| Bytes changed vs the car | **6** |
| Blocks erased+written | FB14, FB15 |
| Boot block FB00 | **not involved** |
| Status | verified, **not yet flashed** |

```
0x0C5381  73 -> d4   rev limit
0x0C5382  c0 -> 80   rev limit
0x0C5385  67 -> ce   rev limit
0x0FFB88  51 -> 50   checksum
0x0FFB89  28 -> 60   checksum
0x0FFB8A  28 -> 68   checksum
```

**What:** image 1 plus recalculated Subaru checksums
(`tuneforge fix-checksum`, 14 entries). The checksum lives at `0x0FFB88`, which is in a
**different flash block** (FB15) from the rev limit (FB14) — hence two blocks are written.

**Why:** the ECU validates ROM checksums; editing any byte invalidates them.

**Control test:** running the same command on the *unmodified* car ROM changed **zero
bytes**, confirming the tool only touches genuinely stale checksums.

### Deliberately NOT changed

| Setting | Address | Value | Why left alone |
|---|---|---|---|
| Max WGDC Post-Compensation | `0x01802C` | `0.00 %` | Boost master switch. Still disabled. Restoring boost is a separate, far higher-risk change needing the engine builder — and the −13.28% fuel trim explained first. |
| Rev Limit Fuel Resume (Boost) | `0xC5388` | `1260.00` | Already factory-stock. |
| Everything else | — | — | The tuner's 8:1 calibration is preserved. Only 6 bytes differ from what the car is running. |

---

## Verification performed on the flash candidate

- values decode as float `6800.00` / `6600.00` — **not** the integer trap
- hysteresis sane: On Above > Off Below, 200 RPM gap
- every differing byte lies in the rev-limit fields or the checksum field
- remaining 1,048,570 bytes byte-identical to the running ROM
- size exactly 1,048,576
- boot block FB00 untouched; only FB14 + FB15 written

---

## 2026-10-22 — `kramar/` images from the new tuner (not flashed by us)

| Image | ID | Notes |
|---|---|---|
| `JDM LGT 06 MT DIESEL SWAP 12bar OKKO 95 (DIESEL ABS).bin` | A2UG000K | Car's old dump + tuner's maps. Carries `0xC1AD2/3 = A2 A2`. Boost edits are in the unused boost set 1. |
| `... (OEM ABS).bin` | A2UG000B | **Currently flashed on the car** (reported). Tuner's maps, runs smoothly, but ABS light on, ABS/ESP dead. `0xC1AD2/3 = 02 22`. |
| `... (OEM ABS WITH 2 BYTE FIX).bin` | A2UG000B | **Candidate, not flashed.** Previous image with `0xC1AD2/3 = A2 A2` and checksums recomputed (5 bytes differ). sha256 `805116cb…74c4`. See `kramar/README - OEM ABS WITH 2 BYTE FIX.md` and `work/ABS_RESEARCH.md`. |
