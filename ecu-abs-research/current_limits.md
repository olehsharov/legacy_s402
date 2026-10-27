# Current Limits — A2UG000K (2006 JDM Legacy GT spec.B MT)

Findings on **rev limits** and **boost limits** for this specific car, established by
diffing the car's own ROM against a known-stock reference.

| | |
|---|---|
| ROM ID | `A2UG000K` (at 0x2000, 0xC0000, 0xCC680) |
| ECU ID | `4B04785007` |
| Processor / flash method | SH7058 / `subarucan` |
| Car's ROM (read 2026-08-25) | `read_image_2026-08-25_16h39m11s.bin` |
| Stock reference | `roms/reference/STOCK_A2UG000K_reference.bin` |
| Definition used | `RomRaider/definitions/SubaruDefs/RomRaider/ecu/2006JDMLegacySpecBMT-A2UG000K.xml` |
| Diff | **7467 bytes across 58 regions** — a full retune, not a few tweaks |

> **Engine is NOT stock.** Rebuilt ~2024 with compression dropped from ~11:1 to ~8:1.
> Stock values below are **forensic reference, not restore targets** — see *Why stock is
> not the target* at the end.

---

## Rev limits

### Rev Limit (Fuel Cut) — `0xC5380`

`float`, 2 values, big-endian. Fuel is cut at/above the first value; fuelling resumes
below the second.

| | On Above | Off Below |
|---|---|---|
| **Stock** | **7500 RPM** | **7300 RPM** |
| **Currently in car** | **3900 RPM** | **3700 RPM** |

Raw bytes as stored:

```
stock : 45 ea 60 00   45 e4 20 00      (7500.0 / 7300.0)
yours : 45 73 c0 00   45 67 40 00      (3900.0 / 3700.0)
```

**Why 3900:** deliberate break-in limiter set by the tuner immediately after the engine
rebuild, intended to be lifted later. It never was.

### Rev Limit Fuel Resume (Boost) — `0xC5388`

`float`, 1 value. After the limiter engages and revs drop below "Off Below", fuelling
will not resume until manifold pressure falls below this.

- **Stock: 9.67 psi** — **UNCHANGED** in this car (`44 9d 80 00` in both ROMs).

### Engine's designed rev ceiling

Not a limiter, but the bound everything else is built around: **6800 RPM**.

- Boost tables' RPM axis runs `800 … 6800` in 400 RPM steps
- Feedback knock correction is active to `6700 / 6800` RPM

So the current 3900 cap uses roughly **56%** of the designed range.

### Observed in logs

RPM peaks of 3811–4052 across five logs. Coasting a little past the 3900 cut point is
normal — fuel stops, inertia carries the revs slightly higher.

---

## Boost limits

### Max Wastegate Duty Limit Post-Compensation — `0x1802C`  ← **the master switch**

`float`, 1 value. Definition's own description:

> *"This is the maximum limit for wastegate duty. Regardless of the values in the
> 'Max Wastegate Duty' table, wastegate duty will not exceed this value."*

| | Value |
|---|---|
| **Stock** | **90.00 %** |
| **Currently in car** | **0.00 %** |

```
stock : 42 b4 00 00      (90.0)
yours : 00 00 00 00      ( 0.0)
```

**This one setting disables boost entirely.** It overrides every other boost table, so
the wastegate is never commanded shut and the turbo makes wastegate-spring pressure only.
This is why the other boost tables look normal but produce nothing.

**Confirmed empirically:** `Primary WGDC` reads `0.00` in **every row of all five logs**
(31,000+ samples). Measured boost peaks at **+6.54 psi** — spring pressure.

### Boost Limit (Fuel Cut) — `0xC6A5C`

`uint16`, 6 values, **psi absolute**. Hard overboost protection — fuel cut.

| Bin | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Stock (psi abs) | 23.26 | 25.70 | 28.12 | 30.55 | 33.07 | 33.07 |
| **Yours (psi abs)** | **24.58** | **27.01** | **29.43** | **31.87** | **34.38** | **34.38** |
| Yours (psi gauge) | 9.88 | 12.31 | 14.73 | 17.17 | 19.68 | 19.68 |

The tuner **raised** this by ~1.3 psi across the board — preparing headroom.

> ⚠ Note the **lowest bin cuts at 9.88 psi gauge**. This is a 6-element table, not one
> number. Raising boost early in the range can hit fuel cut long before 19.68.

### Target Boost — `0xC1650`

`uint16`, 16×16. Axes: **Y = RPM (800…6800)**, **X = throttle/requested torque (0…350)**.

| | Peak | Change |
|---|---|---|
| Stock | 14.50 psi | — |
| **Yours** | **15.01 psi** | mean **+1.16 psi** — **raised** |

Target reaches its maximum from ~2000 RPM upward at high throttle, i.e. the boost is
already mapped across the whole rev range and is waiting on the master switch.

### Wastegate duty tables

| Table | Address | Stock peak | Yours peak | Mean change |
|---|---|---|---|---|
| Initial Wastegate Duty | `0xC11D8` | 52.00 % | 44.24 % | −6.86 |
| Max Wastegate Duty | `0xC0D68` | 62.00 % | 50.94 % | −8.43 |

Both **softened**, but both irrelevant while `0x1802C` is 0.

For reference, the post-compensation cap must be **≥ 58.75 %** to stop limiting anything
(Max WGDC peak 50.94 % + max IAT compensation 7.81 %).

---

## Other limits found (context)

| Limit | Address | Value |
|---|---|---|
| Speed Limiting Enable (Fuel Cut) | `0xC53D0` | 116.75 mph (~188 km/h) |
| Speed Limiting Disable (Fuel Cut) | `0xC53DC` | 114.89 mph |
| Speed Limiting (Throttle), all SI-DRIVE modes | `0xDB844/850/85C` | 113.02 / 115.51 mph |
| MAF Limit (Maximum) | `0xC2F30` | 300.00 g/s |
| Engine Load Limit (Maximum) | `0x2584C` | 4.00 g/rev |
| Injector Flow Scaling | `0xC4E0C` | 520.19 cc/min — **byte-identical to factory reference; CONFIRMED CORRECT**, see below |

---

## ⚠ The encoding trap — read before editing anything here

Both rev-limit values and the wastegate cap are **IEEE-754 floats, big-endian**. A
previous edit attempt (`_no_limit`, since deleted) wrote the *integers* 7500 and 7400
into these float slots:

```
intended : 7500 RPM
written  : 00 00 1d 4c      <- integer 7500
reads as : 1.05e-41 as a float  ->  effectively 0 RPM
```

With both rev-limit values at ~0, fuel cut is active at any engine speed and never
resumes — **the engine would not run**. The checksum had been recalculated, so the ECU
would have accepted the image. Nothing would have caught it.

**Always write these through a tool that knows the field type** (RomRaider editor, or
`tuneforge write-table`) — never a raw hex edit plus a separate checksum fix.

Correct encodings, for verification after any edit:

```
3900.0 -> 45 73 c0 00        7500.0 -> 45 ea 60 00
3700.0 -> 45 67 40 00        7300.0 -> 45 e4 20 00
   0.0 -> 00 00 00 00          90.0 -> 42 b4 00 00
```

---

## Why stock is not the restore target

The stock reference is calibrated for an **11:1** engine. This engine is **~8:1**.

- **Timing:** lower compression burns slower and has more knock margin, so it generally
  wants *more* advance than stock, not less. Stock timing would be safe but flat.
- **Boost:** stock boost is what an 11:1 engine tolerated. This build gave up compression
  specifically to make room for more.
- **Fuelling:** roughly transferable, since it is airflow-based.

There is no correct calibration for an 8:1 EJ20 in either ROM. The right values come from
the person who built the engine and wrote the current map.

---

## Engine health at these limits (from logs, 2026-08-27/28)

| Reading | Result |
|---|---|
| **IAM** (how happy the ECU is, 0–1) | **1.000 in all 31,073 samples** — maximum |
| **FLKC** (learned knock retard) | **0.00 everywhere** — nothing learned |
| **FBKC** (live knock retard) | **not available** on this ECU via the standard path |
| Boost achieved | +6.54 psi max (spring only) |
| Injector duty | 33 % max — plenty of headroom |

**The engine is not knocking.** Whatever else is unfinished, the timing side is healthy.

---

## ✅ RESOLVED 2026-08-30 — the injector / fuel-trim question

**Earlier conclusion in this document was wrong. Injector scaling is correct; nothing needs changing.**

### What the −13.28% actually was

It was the **single most negative LTFT sample across an entire mixed-load drive** — a
transient, not a settled value. The tuning guide specifies measuring
`A/F Correction (STFT) + A/F Learning (LTFT)` **summed, at warm idle**. Re-analysing the
*same pre-flash log* under that condition gives a completely different answer:

| pre-flash log `baseline_1453.csv` | value |
|---|---|
| LTFT minimum across whole log | **−13.28 %** ← where the old figure came from |
| **STFT+LTFT at warm idle (3531 samples)** | **−2.13 %** |

### Warm-idle measurements, apples to apples

| session | STFT+LTFT sum |
|---|---|
| pre-flash | −2.13 % |
| post-flash #1 | −4.29 % |
| post-flash #2 | −5.43 % |
| post-flash #3 (after 15 min steady cruise) | −2.76 % |

Mean ≈ **−3.7 %**, comfortably inside the guide's **≤ ±5 %** criterion.

### Cross-checks

- Owner confirms **stock EJ20Y injectors** are fitted.
- `0xC4E0C` is **byte-identical** (`45 a2 a0 00`) in the car's ROM and the factory
  reference — the tuner never altered it, and it is the value Subaru calibrated for
  this hardware.

**Conclusion: the guide's Step 1 (injector flow scaling) PASSES. No flash required.**
The implied ~540 cc from −3.7 % is within normal fuelling scatter for a 520 cc injector
and chasing it would be tuning noise.

> **Lesson for this document:** a min/max across a whole log is not a measurement.
> Fuel-trim figures are only meaningful under the conditions the guide specifies —
> warm, idling, closed loop, summed.

---

## Genuinely open items

1. **IAM pinned at 0.500** across five sessions since the reflash. ROM constants say
   `Advance Multiplier (Initial) = 0.5` @ `0xC875C` and step `0.125` @ `0xC8760`, with a
   verified code path climbing to 1.0 — but it has never incremented. Engine gets only
   half its bonus timing until it does.
2. **AFR reads ~14.7 at wide-open throttle.** Low load (boost disabled) keeps the ECU in
   closed loop, so it never enriches for full throttle. Harmless at spring pressure;
   **must be fixed before boost is ever restored.**
3. **FBKC unavailable on this ECU** — standard `P23` returns `0xFF`, the 4-byte ecuparam
   at `0xFF7BD0` is refused (`NRC 0x12`). The guide's timing procedure depends on it.
