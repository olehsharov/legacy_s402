# Step 1c — MAF scaling, iteration 1 (2026-09-06)

Source log: `logs/maf_0906_1613.csv` — 40.0 min, 22,699 rows, 9.5 Hz.

## Guide procedure, applied

| Guide step | Result |
|---|---|
| 1. Log flat road 30–60 min | 40.0 min ✅ |
| 2. Drop all OL rows | 22,699 → 12,296 (OL = STFT frozen at exactly 0 for ≥3 consecutive rows; also dropped coolant <75 °C) |
| 3–4. Drop Δvoltage/sec > 0.2 | 12,296 → **7,191** |
| 5. Summed corrections vs MAF voltage | binned to nearest of the 54 voltage cells |
| 6. Cells >5% error corrected | idx 9–24 (1.250–2.227 V), tapered at 8 and 25 |

**CL/OL had to be inferred** — this ECU exposes no CL/OL parameter. STFT frozen at exactly
0.00 across a run = no O₂ feedback = open loop. Validated against decel fuel-cut events
(A/F sensor 20.33, STFT 0) which the filter correctly rejected.

## Finding

The MAF **over-reports airflow across the whole light-cruise band**, peaking around −17% at
1.37–1.41 V. Idle (≤1.21 V) is clean, consistent with step 1a's −0.04% warm-idle sum — which
is why this never showed up before. LTFT drifted −5.5% → −11% over the 40 minutes as the ECU
kept pulling fuel out.

Shape matters: a *constant* offset would mean injector scaling; a *hump* means MAF scaling.
This is a hump. Step 1a's conclusion stands.

## Proposed table (NOT flashed)

| idx | volts | g/s old | n | measured % | applied % | g/s new |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 1.211 | 2.94 | | | 2.86 |
| 9 | 1.250 | 3.31 | | | 3.04 |
| 10 | 1.289 | 3.68 | | | 3.27 |
| 11 | 1.328 | 4.16 | | | 3.61 |
| 12 | 1.367 | 4.58 | | | 3.88 |
| 13 | 1.406 | 5.05 | | | 4.33 |
| 14 | 1.484 | 6.05 | | | 5.22 |
| 15 | 1.562 | 7.18 | | | 6.27 |
| 16 | 1.641 | 8.49 | | | 7.31 |
| 17 | 1.719 | 9.91 | | | 8.62 |
| 18 | 1.797 | 11.51 | | | 10.17 |
| 19 | 1.875 | 13.23 | | | 12.06 |
| 20 | 1.953 | 15.13 | | | 14.11 |
| 21 | 2.031 | 17.32 | | | 16.44 |
| 22 | 2.109 | 19.65 | | | 18.77 |
| 23 | 2.188 | 22.44 | | | 21.42 |
| 24 | 2.227 | 23.84 | | | 22.75 |
| 25 | 2.344 | 28.31 | | | 27.66 |

Unchanged: idx 0–7 and 26–53. Curve remains strictly increasing.
Largest single-cell change: **15.2%**.

Thin data (n=5) at idx 10–12 — those three corrections are interpolated from
their solid neighbours, not taken from the 5 samples.

## Did the tuner deliberately enrich via the MAF? — NO (checked, 2026-09-06)

Compared `dumps/after_write.bin` against `roms/reference/STOCK_A2UG000K_reference.bin`:

| Table | Address | vs factory |
|---|---|---|
| **MAF Sensor Scaling** | `0xCCCB8` | **IDENTICAL** |
| **MAF Sensor Scaling axis** | `0xCCBE0` | **IDENTICAL** |
| Injector Flow Scaling | `0xC4E0C` | IDENTICAL |
| Injector Latency | `0xC5B78` | IDENTICAL |
| Primary OL Fueling Comp (ECT) | `0xC6474` | IDENTICAL |
| CL Fueling Target Comp A/B (Load) | `0xC7D10/88` | IDENTICAL |
| **Primary Open Loop Fueling** | `0xC701C` | **DIFFERS — 236/512 bytes** |
| **Primary OL Fueling (Failsafe)** | `0xC71F0` | **DIFFERS — 235/512 bytes** |
| Throttle Tip-in Enrichment | `0xC69B0` | DIFFERS — 33/512 |
| Tip-in Comp (ECT) | `0xC69D2` | DIFFERS — 6/512 |

The tuner worked in **Primary Open Loop Fueling** — the correct place to set richness —
and left the MAF curve factory. Axes unchanged (18 load × 18 RPM).

Direction of their edit vs factory: **leaner through the midrange** (up to +1.14 AFR at
4400 rpm / 1.10 g/rev), **slightly richer at high-RPM high-load** (−0.4 to −0.6 AFR at
5200–6400 rpm, ≥2.10 g/rev → 10.2–10.5 AFR, matching the guide's TMIC target).

**Therefore the −17% MAF error is not a deliberate edit.** It is a genuine mismatch
between the factory MAF curve and what this engine actually flows.

**Second, independent reason the theory cannot hold:** in *closed loop* the O₂ sensor
drives AFR to 14.7 regardless of what the MAF reports. Inflating the MAF there cannot
make the car richer — the ECU cancels it through the trims. That cancellation is exactly
what we measured (LTFT walking to −11%).

**Scope check:** the cells being corrected are 1.250–2.227 V = **3–24 g/s**. At 3000 rpm
that is 0.06–0.48 g/rev — the leftmost columns of the OL fuel map, which are all 14.70
(closed loop). WOT lives at 3.5–5.0 V / 100–350 g/s, in cells **we are not touching**.
This correction cannot change WOT fuelling or intake temperatures.
