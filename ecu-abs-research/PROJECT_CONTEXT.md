# Subaru ECU Tuning — Project Context

This repo is a working space for Subaru (WRX/STi) ECU tuning: reading, understanding,
datalogging and eventually reflashing engine maps via a Tactrix OpenPort 2.0 cable.

Primary reference: `A-Subie-Newbie-Tuning-Guide-1_0 (1).pdf` — *"A Complete Tuning Guide"*,
Bad Noodle, compiled by Wideboy, 16/07/2014. Everything in the **Reference** sections below
is distilled from that document. Extracted plaintext can be regenerated from the PDF with a
zlib + `Tj`/`TJ` operator scrape (no external deps needed).

---

# 📍 WHERE WE ARE IN THE GUIDE — READ THIS FIRST, EVERY SESSION

**`TUNING_PROGRESS.md` is the single source of truth for what step we are on.**
Read it before advising on anything tuning-related, and **update it at the end of any
session that moves a step, closes one, or discovers a blocker.** Sessions are long and
spread over days — without it, work gets repeated and conclusions get rebuilt from
scratch (this has already happened once).

## Standing rules for any agent working here

1. **Follow the guide strictly.** Check what the guide (below, distilled from the PDF)
   actually says *before* advising. Do not improvise a procedure, skip its order, or
   ignore its preconditions. When it settles a question, quote it. When it does not
   cover something, say so plainly rather than inventing.
2. **Measure the way the guide specifies, under the conditions it specifies.** A
   min/max across a whole log is *not* a measurement. Fuel trims mean nothing except
   warm, idling, in closed loop, and **summed** (`AF correction + AF learned`). A wrong
   measurement produced a completely wrong injector conclusion once already — see the
   RESOLVED section in `current_limits.md`.
3. **Respect the guide's order:** air/fuel → boost → fuel → timing → AVCS → retune.
   Do not let enthusiasm reorder it.
4. **Batch ROM changes.** Every flash resets the ECU: IAM drops to its Initial value and
   fuel trims are wiped. One flash, one relearn. Never judge a change against a
   freshly-flashed car — you would be measuring the reset, not the change.
5. **Keep the other records current too:** `current_limits.md` (findings on this car's
   limits), `work/ROM_CHANGELOG.md` (every ROM image, why it exists, what changed),
   `reference_roms.md` (research on stock ROMs and the 280 hp goal).

---

# ⛔ SAFETY — READ THIS BEFORE ANYTHING ELSE

**This project can destroy an engine, brick an ECU, or strand a vehicle. Software mistakes
here have physical, expensive, and potentially dangerous consequences. Treat every action
that touches the car as irreversible until proven otherwise.**

## Hard rules for any agent working in this repo

1. **NEVER write, flash, or modify anything on the ECU without explicit, specific,
   in-the-moment user confirmation.** Not "the user said tuning is fine" — confirmation for
   *this flash, of this ROM, right now*. Reading and logging are fine; writing is not.
2. **NEVER generate map values and present them as safe to flash.** Any table values produced
   here are a starting point for a human who understands the car, not a tune.
3. **NEVER shotgun-probe the OpenPort command space.** The device answers `at<letter>` ASCII
   commands; unmapped letters may reach firmware-update or flash-entry paths. Only send
   commands that are known and documented. See *Hardware* below.
4. **NEVER suggest bypassing, disabling, or ignoring a safety mechanism** — knock control,
   IAM, FBKC/FLKC, rev limiter, boost limit fuel cut, failsafe fueling. These exist to keep
   the engine alive.
5. **Always keep and verify a backup of the stock ROM before any write.** No backup, no flash.
6. **If the user reports knock, stop.** Do not "tune around it" until the cause is understood.
   Recommend aborting the pull, not finishing it.
7. **Never act on assumptions about the vehicle.** Year, ECU bit-width (16 vs 32), turbo,
   injectors, intercooler type and intake all change the correct answer. Ask; do not guess.

## Why the guide itself warns so hard

- A bad flash **disables the car** — it probably will not start.
- Even with a spare ECU on hand, the **immobilizer must be reprogrammed by a dealer**, which
  requires a master key and getting the car *to* the dealer. A spare ECU is not a roadside fix.
- Flash endurance: ~**1000 cycles** on 16-bit ECUs, ~**10000** on 32-bit.
- Most flash failures are **physical**: poorly seated connectors, bent pins, worn contacts,
  or a **low battery charge**. Check the connection and battery before every flash.
- Tactrix offers an ECU recovery service for drive-by-wire ECUs; used ECUs run ~$250.
- Knock ("pinging"/detonation) is an *explosion*, not a burn. One good knock event can score
  the bearings and cost a shortblock.

## The guide's own disclaimer — do not lose this

The author states plainly: *"I am NOT a tuner. I only have experience with my car; none of
this information is guaranteed to be accurate."* And: **DO NOT** use it as a definitive
resource; **DO NOT** tune your car using it as the definitive resource; **DO** your own
research and make your own judgements.

**Treat this file the same way.** It is a distillation of a 2014 forum-sourced hobbyist
document. It is context, not authority.

## Safe-state baseline before any experimental session

Before tuning anything after a significant mechanical change, put the car in a deliberately
detuned, safe state:

- Set **all WGDC to 0** (wastegate spring pressure only)
- Set **open-loop fueling rich**: ~10.2 AFR for TMIC, ~10.5 for FMIC
- **Pull ~4 degrees of timing** in the WOT areas

Then add power back progressively. Slow and safe first.

---

# Hardware & Host Environment (verified 2026-08-25)

| Item | Value |
|---|---|
| Interface | Tactrix OpenPort 2.0 |
| USB IDs | VID `0x0403`, PID `0xcc4d` |
| Serial number | `<serial>` |
| Device node | `/dev/cu.usbmodem<serial>1` |
| Firmware | `1.17.4877` |
| Baud | 115200 |
| Driver | Apple USB-CDC (enumerates as a modem). The `FTDIKext.kext` in `/Library/Extensions` is unloaded and **not needed**. |
| Host | macOS 15.2, arm64, Java 21, python3 with pyserial 3.5 |

## OpenPort serial protocol (what is actually known)

ASCII, CRLF-terminated. Commands are `at<letter>`, replies are `ar<letter>`:

```
ati  ->  ari main code version : 1.17.4877     (info)
ata  ->  aro                                   (ok)
atv  ->  are 7                                 (error — unknown command)
```

`aro` = ok, `are N` = error N, `ari ...` = info. **Do not enumerate the rest of the letter
space to find out what else exists** (see hard rule 3).

## Verified vs unverified

- ✅ **Mac ↔ cable link works.** Confirmed by live serial exchange, not just enumeration.
- ❓ **Vehicle side is untested.** Whether the cable is in the OBD port with ignition on, and
  whether the ECU answers, has not been established.

---

# The macOS Toolchain Gap

The guide's required tools are Windows-centric:

**Must haves (per the guide):** a clean, virus-free laptop · RomRaider with latest definitions ·
EcuFlash with latest definitions · a wideband O₂ sensor/meter that works with RomRaider ·
Tactrix cable.

**Nice to haves:** cigarette-lighter power converter (so the laptop doesn't die mid-log) ·
an old ECU Explorer build (trouble codes only) · Airboy's spreadsheet · RomRaider tuning-utilities
sub-forum tools.

**Problem:** Tactrix ships **no J2534 driver for macOS**, and EcuFlash is Windows-only. Nothing
from that list is currently installed on this machine.

**Approach:**

- **Flashing → Windows.** Use a Windows VM or machine with the official Tactrix driver and
  EcuFlash. Do not attempt ECU writes over a reverse-engineered protocol on macOS. This is the
  single highest-risk operation in the whole project; use the vendor-supported path.
- **Datalogging → possibly native.** RomRaider is Java and Java 21 is present on arm64. Reaching
  the OP2 from it on macOS is the open question.
- **Wideband O₂ is a hardware prerequisite**, not a software problem. Without one, fuel tuning
  and AVCS tuning cannot be done as written.

---

# Reference: How the ECU Works

## Boost

Boost is positive intake-manifold pressure created by the turbo. **Changing boost changes
everything else, which is why it is tuned first.**

Every turbo has a **compressor efficiency map**: pressure ratio (y) vs CFM (x), with efficiency
islands. Pressure ratio × 14.7 psi (sea level) − 14.7 = gauge boost. Higher pressure ratios move
you into lower-efficiency islands, where more input energy becomes heat instead of compression —
hotter, less dense air.

Working the math through with intercooler efficiency, the guide concludes that **with an
intercooler, more boost does keep adding lbs/min** across the map — so the real limits are not
airflow but:

- Air into the throttle body should be ~**110°F, 130°F max**. Beyond that you must compensate
  with richer fuel and less timing, which *costs* power.
- The turbo tops out around **190k rpm** and **950°F**. Chasing e.g. 22 psi on a TD04 will kill
  it quickly.

Stock intercooler efficiency, per TurboXS testing (the guide notes these are debatable; some
claim ~56%):

| Boost | Temp in | Temp out | Efficiency |
|---|---|---|---|
| 14 psi | 92.5°C | 41.5°C | 73.4% |
| 16 psi | 106°C | 49.5°C | 68.1% |
| 18 psi | 103°C | 50°C | 66.3% |

## Wastegate & WGDC

The wastegate diverts exhaust gas around the turbine so the turbo stays in its efficiency range.
It is controlled by a **spring** (holds it closed, OEM typically ~7 psi) and a **diaphragm**
(works to open it). Below spring pressure the gate stays shut; above it, the gate cracks open,
bleeds off, pressure drops, gate closes — oscillating fast around an average.

An **electronic boost control solenoid (EBCS)** exposes the diaphragm to different pressures so
it can be made to work *with* or *against* the spring — that's how you hold 16 psi on a 7 psi
spring.

**Wastegate Duty Cycle (WGDC)** = the percentage of a short time window during which the
diaphragm works *with* the spring. Higher WGDC → gate held closed longer → more boost.

## Turbo Dynamics (32-bit)

TD corrects WGDC when actual boost misses target. `Boost error = Target boost − Actual boost`.

- **TD Proportional (TDP)** — immediate correction: error is X, add Y.
- **TD Integral (TDI/TDIC)** — accumulates over milliseconds; a temporary learning mechanism.
  Positive and negative variants for under- and over-boost.

```
Applied WGDC = Initial WGDC + TDP + TDI + other small corrections
```

Capped at **Maximum WGDC**.

Behaviour to expect: at first sight of boost error, correction is mostly *immediate*; as the pull
continues it shifts to mostly *cumulative*. Both maxing out = you cannot reach target boost.

TD is **not** a band-aid for a lazy tune — it exists to correct for temperature, humidity,
elevation and air density. Even a perfect tune needs it in the real world.

## Fuel & AFR

Stoichiometric gasoline AFR is **14.7:1 = 1.0 lambda**. Best compromise for emissions, economy
and power — but too energetic to run under high boost, where it can pre-ignite or detonate.
Cooler air and higher octane raise the abuse tolerance.

- **Closed loop (CL):** ECU targets 14.7 using the narrowband O₂ sensor, which only answers
  rich/not-rich (yes/no). It guesses and checks, fast. AFRs visibly bouncing around in CL on a
  wideband is **normal** — it helps the cats.
- **Open loop (OL):** no feedback. The ECU reads MAF voltage → g/s of air → looks up target AFR →
  applies compensations → computes injector pulse width. **The ECU never knows the real AFR in
  OL.** That's the tuner's job.

A wideband in place of the stock sensor does not help the ECU — it can't interpret the signal.

**Target AFRs:** 12:1 is good power but dangerous (aggressive tune, engine you don't mind losing).
Daily-driver reliable: **10.5:1–11:1 with TMIC**, **11:1–11.5:1 with FMIC**.

**The MAF** is a heated wire; airflow cools it, and the voltage needed to hold temperature maps
to grams of air per second. E.g. 2.6 V ≈ 126 g/s.

### CL → OL transition

Deliberately hard to trigger (emissions), and a known source of WRX hesitation/drivability
complaints. A counter increments while a throttle or load threshold is exceeded and **resets to 0**
the moment nothing is exceeded. When it passes **CL to OL Delay**, transition starts. Extreme
conditions in the max/min maps skip the counter entirely.

Final gate: the transition only completes if the desired AFR from the **Primary Open Loop Fueling**
table is richer than the **minimum primary open loop enrichment** value (usually 14, rarely changed).

### Per-cycle fueling sequence

1. Read MAF voltage
2. MAF scaling → g/s of air
3. Look up target AFR
4. Adjust AFR for environmental conditions
5. Determine required fuel
6. Injector flow scaling → pulse width
7. Apply injector latency to the pulse width
8. Energize injector — and hope for the best

## Timing & Knock Control

Knock/detonation is the AF mixture *exploding* instead of burning, creating a pressure spike
beyond design limits. It hammers the crank into the bearings. Analogy from the guide: punching a
vase on a skateboard (knock) vs pushing it (combustion) — you want the hardest push that doesn't
break the vase.

Peak cylinder pressure should occur ~**15° after TDC**. Timing is set in degrees *before* TDC.

The knock sensor is an **audio sensor** filtered to knock-characteristic frequencies. It can
report **false knock** (a loose bolt rattling near it has done exactly this). That is a limitation,
not permission to ignore a knock signal.

```
Total Timing = Base Timing + (IAM × Timing Advance) + FBKC + FLKC + other compensations
```

- **Base Timing** — tuner-controlled lookup by RPM/Load.
- **Timing Advance (Maximum)** — tuner-controlled; equivalent to "dynamic advance" in
  Street Tuner.
- **IAM** (Ignition Advance Multiplier, aka Rough Correction) — how *happy* the ECU is. Scales how
  much of Timing Advance is applied, **across the board**. Kept separate from Base Timing precisely
  so the ECU can save the engine by pulling timing globally.
- **FBKC** (Feedback Knock Correction) — applied mainly during WOT pulls.
- **FLKC** (Fine Learning Knock Correction) — applied mainly during cruise, per load/RPM cell.

**Only one correction mode is active at a time.** The ECU spends most of its time in FLKC. Sharp
load changes / WOT switch it to FBKC. Corrections of −4° or more in FLKC send it to IAM correction,
because it now thinks something is genuinely wrong.

### FBKC behaviour

Active within the *feedback knock correction range*. On a knock event, the **Feedback Correction
Retard Value** (typically **1.4°**) is subtracted. With no further knock, timing is returned
*gradually* (−1.4 → −1.0 → −0.6 → −0.2 → 0). Any new knock subtracts another 1.4° from wherever it
currently sits.

### Conditions required to leave FBKC and start learning

- Coolant temp > 140°F
- A/C off, or not just turned on
- In IAM mode: load and RPM within **Rough Correction Ranges**
- In FBKC mode: load and RPM within **Fine Correction Ranges**
- Immediate load change < ±0.05 g/rev
- Not in test mode
- Not in limp-home mode from specific CEL groups
- No active throttle-change timing compensation

### IAM correction

Entered first after an ECU reset. Adjustable only if Timing Advance (Max) map value > 3.9°, not in
limp mode, and IAM step value > 1. On entry (once per entry): IAM set to *Advance Multiplier
(Initial)*, step value set to 4, learning delay counter zeroed, **and the entire FLKC table in RAM
is cleared**.

Then: knock → reset counter, halve the step value. No knock for the *Rough Correction Learning
Delay* → increment counter; past the delay target → raise IAM by the step value, reset counter.
"Settled" = step ≤ 1 (16-bit) or ≤ 0.25 (32-bit), or IAM is 0 or maxed.

### FLKC behaviour

Learned values are **always applied**; adjustment requires: in fine correction mode, FBKC disabled,
load/RPM within *Fine Correction Range*, not in limp-home.

- Advance step: **+0.35°** (*Fine Correction Advance Value*), limited by *Fine Correction Advance
  Delay* counter, and blocked if current timing advance + FLKC would exceed *Timing Advance
  (Maximum)*.
- Max correction: **8°** (*Fine Correction Advance Limit*).
- Knock → current cell decreased ~**1°** (*Fine Correction Retard Value*).
- **FLKC can only go positive if IAM is not at 100%.** Healthy engine = IAM maxed, FLKC all zeros.

Return to rough (IAM) correction requires all of: load/RPM in Rough Correction Range · Timing
Advance (Max) > 4.9° · some FLKC change last execution · |last applied FLKC| > 3.9° · last FLKC raw
difference × 2.84 > last Timing Advance (Max) value · (IAM > 1) or (IAM ≤ 1 and last applied FLKC
was positive).

## AVCS

Advances intake valve opening (higher value = more advance); duration is unchanged. Subaru's stated
intent: smooth idle at low load, better emissions at mid load, more power at high load — so **0 at
low load, more at high load, tapered between**.

The stock WRX map has a **~40° spike** in a couple of low-RPM/low-load columns purely for emissions
(exhaust gas back into the intake). JDM maps such as the s202 don't have it; the guide removes it.

AVCS makes power by raising **volumetric efficiency (VE)** — how easily air gets in. In a turbo
application, manifold psi measures air *not* getting in, so at the same lbs/min, lower psi is
actually better.

**Reversion** is the limit: too much advance pushes exhaust gas back into the intake, polluting the
charge and adding restriction against the incoming air. Bigger turbo + freer exhaust = more advance
usable at higher RPM. **Changing AVCS changes VE, which changes fuel and timing** — hence the
retune step.

---

# Reference: The Tuning Procedure

Tuning means **finding the limits of the engine** — how much boost the turbo can push, how lean it
will run, how much advance it will take. The closer to any threshold, the more likely you break
something. *"A lot of people say the car felt the best right before the engine blew."* The margin
you leave is your call — **leave one.**

Goals differ: max peak power (highest dyno point) · max usable power (most area under the curve) ·
quickest spool · most boost. The guide recommends **max usable power**.

## Order — do not reorder

1. Establish air/fuel relationship
2. Tune boost
3. Tune fuel
4. Tune timing
5. Tune AVCS
6. Retune fuel and timing
7. (Then cruise/daily driving)

**Before starting:** apply the safe-state baseline from the Safety section.

## 1. Air & fuel relationship

Required whenever intake or fuel delivery changed. **Tune only one at a time** — changing both and
tuning together leaves you unable to tell which is causing the error.

- Preferred: fit the **stock airbox**, tune fuel, then fit the aftermarket intake and tune the MAF.
  The stock box gives the cleanest data; aftermarket intakes disperse the data points.
- Fallback: theoretical fuel values, compensating for the difference while tuning the MAF.

**Injector flow scaling** — cc/min at standard fuel pressure/density. Either the RomRaider injector
tool, or by hand:

1. Get theoretical values (forums, manufacturer, Cobb DB). Convert: `2707090 / Cobb value = RomRaider value`
2. Bring the car to temperature
3. **Reset the ECU** to flush learned fuel values
4. Idle and watch AF immediate + AF learned correction; the sum should be **≤ ±5%**
5. Positive = ECU adding fuel; negative = pulling fuel. Adjust in small steps.
6. Re-flash, idle, re-check, repeat

Do this even with "known" injectors — 850cc injectors are not necessarily 850cc without a flow sheet.

**Injector latency** — time for the injector to fully open; depends on battery voltage and fuel
pressure. Fuel pressure rises with boost, so incorrect latency shows as **larger errors at low fuel
pressure, smaller at high**. By hand:

1. Enter theoretical values
2. Log fuel corrections, MAF voltage, FBKC
3. Compute volts/sec of MAF change from timestamps
4. **Discard rows where |Δvolts/sec| > 0.2**
5. Plot corrections vs MAF voltage
6. Check whether corrections approach 0 as MAFv rises
7. Corrections negative → decrease latency; positive → increase
8. Flash, repeat until within **5%** across the MAF voltage range

**MAF scaling (closed-loop part, up to ~2.6 V)** — RomRaider MAF tool, or by hand:

1. Drive a **flat** road for 30–60 minutes logging AF correction, AF learned, MAF voltage, CL/OL status
2. Drop all OL rows
3. Compute MAF voltage change per row
4. Drop rows with Δvoltage/sec > 0.2
5. Scatter-plot summed corrections vs MAF voltage
6. Any cell with >5% error: multiply g/s by `1 + (%correction)` if positive, `1 − (%correction)` if negative
7. Repeat

## 2. Boost

**Find mechanical properties first** — WGDC all 0, rich, timing pulled, so you see what the turbo
and wastegate do unassisted:

1. Log RPM, throttle position, relative pressure corrected (boost), FBKC
2. Build a blank boost map with your table's RPM/TP axes
3. Bin each log row to the nearest RPM/TP cell, average per cell
4. Graph it, smooth any rough transitions
5. Flash, re-log, re-check

**Tune to reach target boost:**

1. Look at other people's maps for your turbo — for *patterns*, not values to copy
2. Pick an RPM in the 100% TP column for full boost; enter **75% of theoretical target boost**
3. Interpolate horizontally and vertically for a smooth progression
4. Add a little WGDC — roughly 2D for now: 0 at 0 TP, ~10% at 100%, interpolate
5. Set `Max WGDC = Min WGDC + Max TDIC + Max TDI + 2`
6. Three WOT runs, **2k rpm → redline**, in the gear closest to 1:1. Log RPM, TP, WGDC,
   TD Integral Cumulative + Immediate, FBKC
7. Discard anything not at ~100% throttle
8. Take the TDI being added at your target RPM and add that to the 100% WGDC column
9. Repeat until you hit the 75% target
10. Then raise target boost slowly toward the theoretical limit, matching WGDC — until you reach it
    or find it unattainable

**Healthy signature:** during spool TDIC builds and TDI maxes; on reaching target, TDI drops to 0
and TDIC holds constant.

### Watch for — every one of these is a stop-and-think

1. **Boost spikes** — too much WGDC too early. A spike at 4000 rpm means too much WGDC *before* 4000; lower the WGDC in the preceding cells.
2. **Compressor surge** — audible from inside the car, on spool, left side of the compressor map. Lower target boost *and* WGDC in that area.
3. **Compressor stall** — sounds like surge but on lift-off; BPV/BOV not venting cleanly. **Mechanical fix**, not a tuning fix.
4. **WGDC > 95%** — wears the wastegate; it can stick open or closed. Keep under 95%.
5. **Knock** — you shouldn't see any with rich fuel and pulled timing. If you do, something is wrong.
6. **Turbo limit** — WGDC rising or steady while boost *drops* = mechanical efficiency limit reached, or more boost is no longer more airflow.
7. **Turbo Dynamics values** — negative = WGDC too high, over-boosting. Positive = WGDC too low, under target. Done when TD is low and slightly positive.

**Fine tuning:** extend peak boost earlier and hold it longer by nudging cells around your max-boost
cell and matching WGDC. **Do not force the car to match someone else's numbers** — different setup,
different car. Forcing it produces spikes and surge.

**Rescaling Turbo Dynamics:** a more sensitive boost controller (3-port Prodrive, Grimmspeed, Perrin)
needs less WGDC for the same boost, but the ECU still assumes the stock solenoid — causing boost
fluctuation during rapid changes. Multiply TDI/TDIC by the ratio of new to old max duty
(90% → 60% is ×0.66), then hand-dial from there.

**Rescaling tables:** put axis resolution where boost changes fastest. If you spool 2000–3500 and
hold to 6000, respace e.g. `1000,2000,...,7000` → `1500,2500,3000,3500,4000,6000,7000`. More cells
during spool = fewer spikes, less ECU interpolation.

## 3. Fuel

Set targets in the Primary OL Fueling map, then scale the MAF so actual matches. Three parts:
middle of the MAF, top of the MAF, then lean toward theoretical AFR.

**MAF Maximum Value:** set ~**50 higher** than your max g/s in the MAF scaling table — headroom for
atmospheric compensation. Precautionary; changes little else.

**Scaling the OL part of the MAF** (needs a wideband):

1. Set all WGDC back to 0
2. Three pulls to redline logging MAF voltage, throttle position, load, RPM, wideband O₂, FBKC
3. By hand, or with Airboy's spreadsheet + the MAF tool
4. Discard rows not near 100% throttle
5. Per row: `%error = (wideband AFR vs map target)`
6. Bin each error to a MAF scaling cell by MAF voltage
7. Average the errors per cell
8. Correction factor = `100% + average %error`
9. Apply per cell
10. Plot the MAF curve — it must be a smooth progression
11. Flash, repeat until within **5%** for the pull
12. **Then** add boost back in and repeat until AFRs are within 5% for the whole pull at full boost
13. Only then start leaning fuel targets: study the OEM map's pattern (leanest around peak boost),
    lean the lean OL areas slightly, smooth, small changes, test each time

### Watch for

1. **Knock** — shouldn't happen with timing pulled; if it does, that cell doesn't want to run that lean
2. **Jagged MAF curve** — likely a mechanical problem: bad intake or a leak. Small kinks OK, **no spikes**
3. **Large target/measured AFR differences** — MAF is mis-scaled, rescale
4. **Loads beyond your max load column** — rescale load
5. **MAF maxed** — MAF voltage climbing while g/s pegged at 300. Needs a larger-diameter intake (e.g. Perrin big MAF), which forces a full MAF rescale

**Wideband O₂ delay:** the MAF and the wideband are separated by feet of plumbing, so AFR readings
lag MAF readings — the guide saw **2–3 rows** on an FMIC setup. Find the lag by matching a
distinctive MAF spike/dip to its AFR response. Note that logging more parameters means more rows per
second, changing the row count of the lag.

**Scaling load** (Primary OL Fueling): if a bigger turbo pushes loads well past the map's max (e.g.
map maxes at 2.5, logs show 3.6), rescale so you reach WOT targets gradually rather than hitting
target AFR long before max load. Log load, RPM, CL/OL status, boost, wideband, FBKC; find where CL→OL
happens (or where stock targets start dropping from 14.7), find max load, put it in the rightmost
column, smooth back to the column where enrichment begins, then re-log to verify. Optional — some
people prefer running rich during spool.

**Tip-in enrichment** — extra, *separate* injector firing to cover the air burst from rapid throttle
changes. Needs a wideband. Three parts: throttle, boost, coolant.

- **Tip-in coolant:** mostly left alone; with bigger injectors consider multiplying by
  `old injector size / new injector size`.
- **Tip-in throttle:** zero the boost corrections, get the car up to temp, then drive erratically
  logging engine speed, CL/OL, throttle, boost error, wideband, tip-in throttle. Stab the throttle
  from idle and *hold* until AFRs settle; vary the stab size; repeat in 1st–4th. Then discard OL rows
  and large-boost-error rows, and per row compute `error = (wideband − 14.7)/14.7`,
  `correction factor = (1 − error)/2`, bin by throttle change, apply, flash. Repeat until within **15%**.
- **Tip-in boost:** leave zeroed with an FMIC (long piping makes boost error largely irrelevant).
  With a TMIC: restore the boost error corrections, multiply by `old injector size / new injector size`,
  repeat the tip-in procedure in **5th or 6th gear**, keep the boost-error rows, bin by boost error, apply.

## 4. Timing

The car is most likely to knock at **peak torque** — that's where you can run the least advance.
Timing rises with RPM (faster pistons) and as load drops (lower VE).

**Which table to modify is genuinely controversial.** You want enough in Timing Advance that a
dropped IAM still runs, but not so much that a dropped IAM makes the car undriveable. One accepted
method: smooth Timing Advance and make its peaks slightly above stock, then do the rest in Base Timing.

Get the ECU Learning tool to read stored learned knock correction values (Street Tuner has an
equivalent). **Check FLKC and IAM repeatedly as you tune and drive.**

**Precondition: IAM must be at 16 (16-bit) or 1 (32-bit).** If it isn't, the engine is not happy —
fix that first. It may simply be that the ECU was reset and IAM starts from the *Initial IAM Value*
table; the guide set theirs to max so IAM starts maxed. Otherwise drive until it maxes. If it never
maxes, you have a mechanical problem or timing that needs pulling in the trouble areas.

**If you have FLKC or a non-maxed IAM:**

1. Compare timing maps for similar setups on the forums
2. Ask around if nothing matches
3. **Inspect the car mechanically** — including things rattling in the engine bay (false knock)
4. Log RPM, load, FLKC, FBKC; line every knock up with an RPM/load cell. Note how many events and how
   severe. A little knock here and there is normal; **large repeated corrections are not**
5. Lower timing where knock repeats — but **too little timing can also cause knock**, which is why you
   compare against other maps. Don't get paranoid and pull too much
6. Continue until IAM is full and FLKC is empty

**Tune timing at WOT:**

1. Research what others run — especially at redline (usually highest) and peak torque (usually lowest)
2. Start from the conservative map (4° pulled)
3. Three WOT runs to redline per iteration, logging RPM, engine load, applied FLKC, FBKC, IAM, throttle position
4. **If you hear knock — a tinny rattle, like metal balls in a coffee can — get off the gas and do
   NOT finish the pull.** A second person watching FBKC on the laptop helps. Any knock: stop logging
   and fix the timing.
5. Verify no knock anywhere in the log
6. Only then add timing back, a little at a time, smoothing as you go
7. When knock appears, **pull back 0.5–1°** for headroom
8. Done when: a conservative tune shows no knock at all; an aggressive tune shows at most 2 individual
   knock events in a full WOT pull. A little scattered FBKC is normal — don't chase a permanent 0.

The guide's own caution about tuning to the very edge of knock: if anything isn't right, you *will*
knock. Pulling a little back out is the safer choice.

**Rescaling timing load:** same method and rationale as rescaling the OL fueling table.

## 5. AVCS

VE, via Freon's formula:

```
VE = MAF(g/sec) / (2.457 * A * RPM * 0.003871098 / (IAT + Temp))
A    = (boost pressure + sea level pressure) / (14.7 * 760)
Temp = IAT °C + 273.5        (or (5/9)*(IAT_F - 32) + 273.15)
```

1. **Reduce timing and add fuel first** — raising VE can cause a lean condition that leads to knock
2. Rescale the AVCS table for load (as with OL fueling)
3. WOT pull logging RPM, load, MAF g/s, boost, IAT
4. Compute VE per row
5. Bin by load and RPM, average per bin → baseline
6. Make **small** changes, flash, re-log, see whether VE improved
7. Repeat to best VE
8. **Retune fuel and timing** — VE changed, so they are now wrong

## 6. Cruise / daily driving

- **Smooth idle:** with larger injectors consider raising idle RPM ~100 to stop stumbling; double-check MAF scaling at idle.
- **MAF Engine Load Compensation:** key to a big MAF idling and running smoothly; corrects MAF readings by engine load and boost, mostly for the CL region. Use Airboy's engine-load-comp worksheet from the RomRaider utilities sub-forum.
- **Requested Torque:** maps pedal input to throttle plate opening; Target Throttle Plate Position holds the angles per requested torque, scaled only to a given value (e.g. 320 — above that, 100% open). No real method; small changes, observe response.
- **Cruise VE and timing:** boost isn't tunable at cruise (wastegate and turbo dictate it) and AFRs are closed-loop at 14.7. So the job is: no knock anywhere in the cruise map, and good VE. Use merchgod's knock/VE tracking spreadsheet.

---

# Quick Reference

## Formulas

```
Applied WGDC = Initial WGDC + TDP + TDI + other small corrections     (capped at Max WGDC)
Total Timing = Base Timing + (IAM * Timing Advance) + FBKC + FLKC + other compensations
Boost error  = Target boost - Actual boost
VE           = MAF(g/sec) / (2.457 * A * RPM * 0.003871098 / (IAT + Temp))
Cobb -> RomRaider injector value = 2707090 / Cobb value
Max WGDC     = Min WGDC + Max TDIC + Max TDI + 2
Tip-in: error = (wideband - 14.7)/14.7 ; correction factor = (1 - error)/2
MAF cell correction: positive %  -> multiply g/s by 1 + %
                     negative %  -> multiply g/s by 1 - %
```

## Constants & thresholds

| Value | Meaning |
|---|---|
| 14.7:1 / 1.0 lambda | Stoichiometric gasoline AFR |
| 10.5–11:1 | Reliable WOT AFR, TMIC |
| 11–11.5:1 | Reliable WOT AFR, FMIC |
| 12:1 | Power AFR — knock-prone, aggressive |
| ~10.2 / ~10.5 | Safe baseline OL AFR (TMIC / FMIC) |
| IAM 16 (16-bit) / 1 (32-bit) | Fully happy engine |
| 1.4° | Typical Feedback Correction Retard Value |
| 0.35° | Fine Correction Advance Value |
| ~1° | Fine Correction Retard Value |
| 8° | Fine Correction Advance Limit |
| −4° FLKC | Threshold that sends the ECU to IAM correction |
| 3.9° / 4.9° | Timing Advance (Max) gates for IAM adjust / return to rough |
| ±0.05 g/rev | Max immediate load change for learning |
| 140°F | Min coolant temp for learning |
| <95% | WGDC ceiling for wastegate longevity |
| 110°F / 130°F max | Throttle body air temp target / limit |
| 190k rpm / 950°F | Turbo speed and temperature limits |
| ±5% | Fuel correction convergence target |
| 15% | Tip-in convergence target |
| 0.2 V/s | Discard threshold for MAF rate-of-change when filtering logs |
| 2.6 V | Approx CL/OL MAF voltage boundary used in the guide |
| 300 g/s | Stock MAF ceiling |

## Tables

**Almost always changed:** Target Boost · Boost limit fuel cut · Initial wastegate duty cycles ·
Max wastegate duty cycles · Primary open loop fueling · Failsafe open loop fueling · Base Timing ·
Timing Advance Maximum · CL to OL Delay · CL Delay Max engine speed (gear)

**Sometimes changed (more advanced tunes):** AVCS · Initial Multiplier · Rev limiter ·
Requested Torque · CL to OL transition (RPM) · CL to OL Transition (Load)

Each table has a description in RomRaider under **View Table Properties** — read it.
Keep experimental changes **small**.

## Logging parameter sets

| Stage | Log |
|---|---|
| Injector latency | Fuel corrections, MAF voltage, FBKC |
| MAF scaling (CL) | AF correction, AF learned, MAF voltage, CL/OL status |
| Boost — mechanical | RPM, throttle position, relative pressure corrected, FBKC |
| Boost — WGDC | RPM, throttle position, WGDC, TD Integral Cumulative + Immediate, FBKC |
| MAF scaling (OL) | MAF voltage, throttle position, load, RPM, wideband O₂, FBKC |
| Load rescaling | Load, RPM, CL/OL status, boost, wideband O₂, FBKC |
| Tip-in throttle | Engine speed, CL/OL, throttle, boost error, wideband, tip-in throttle |
| Timing (WOT) | RPM, engine load, applied FLKC, FBKC, IAM, throttle position |
| AVCS | RPM, load, MAF g/s, boost, IAT |

**FBKC is in nearly every list for a reason: it is the knock canary. Always log it.**

---

# Open Questions (do not assume answers)

- **Vehicle:** year, model, ECU bit-width (16 vs 32), turbo, injectors, intercooler type (TMIC/FMIC),
  intake — all change the correct answer to nearly every question here.
- **Wideband O₂:** present or not? Without one, fuel and AVCS tuning cannot proceed as written.
- **Is the OpenPort actually connected to the car** (OBD port, ignition on)? Only the Mac↔cable link
  is verified.
- **Goal:** datalogging only, or reading/flashing ROMs? These have very different risk profiles and
  very different tooling answers.

---

# Further Reading (from the guide)

Cobb Tuning Guide · Turbocharger Compressor Calculations (Turbo Regal) · Compressor Maps (zTechz) ·
Heat Exchanger Theory and Intercoolers (Turbo Regal) · How intercoolers work (Rap Worlds) ·
Guide to boost controllers (SPL Parts) · Turbo dynamics and boost control explained (RomRaider,
Nasioc) · Closed Loop to Open Loop fueling transition explained (RomRaider) · Subaru's Knock Control
Explained (Nasioc) · Active Valve Control (Subaru Drive) · Volumetric Efficiency (Wikipedia) ·
Let's talk AVCS tuning (Nasioc) · HOWTO: One Man's Way of Scaling a MAF (Nasioc) · AccessTUNER
Tuning Guide (Cobb) · How to adjust the requested torque table (RomRaider) · Speed Density FAQ
(RomRaider) · AVCS Research – 03" ADM STi (RomRaider) · Spreadsheet to track Knock and VE (merchgod,
RomRaider) · RomRaider/EcuFlash getting started FAQ

Contributors credited: Bad Noodle, Wideboy, Tea Cups, merchGod, mickeyd2005, Tgui, Clark Turner,
the Cobb Tuning Team.
