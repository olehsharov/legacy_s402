# Tuning Progress — A2UG000K / EJ20Y

**Position in the guide: Step 1 complete. Step 1c (MAF scaling) is the next work.**

Tracks progress through *A Complete Tuning Guide* (Bad Noodle), distilled in `CLAUDE.md`.
**Keep this current — update it at the end of any session that moves a step.**

| | |
|---|---|
| Car | 2006 JDM Legacy GT spec.B, 6MT, EJ20Y, rebuilt ~2024 |
| ECU | `A2UG000K` / `4B04785007` / Denso SH7058 / `subarucan` |
| Last updated | 2026-09-06 |

---

## The guide's order — do not reorder

| # | Step | Status |
|---|---|---|
| 0 | Safe-state baseline | ✅ already in place (WGDC 0 = spring pressure only) |
| 1a | Injector **flow scaling** | ✅ **DONE** — verified 3 ways |
| 1b | Injector **latency** | ✅ **DONE** — factory values, stock injectors |
| 1c | **MAF scaling** (closed loop, to ~2.6 V) | ⬅️ **NEXT** |
| 2 | Tune **boost** | ⛔ blocked — see blockers |
| 3 | Tune **fuel** | ⛔ needs step 2 |
| 4 | Tune **timing** | ⛔ **hard-blocked** — no FBKC on this ECU |
| 5 | Tune **AVCS** | ⛔ needs wideband; after 2–4 |
| 6 | Retune fuel + timing | ⛔ last |

---

## ✅ Step 1a — Injector flow scaling (2026-08-30)

Guide's criterion: `AF correction (STFT) + AF learned (LTFT)` **summed, at warm idle, ≤ ±5%**.

| Warm-idle sum | |
|---|---|
| pre-flash | −2.13% |
| post-flash ×3 | −4.29% / −5.43% / −2.76% |
| final, after 53 min | **−0.04%** |

Confirmed three independent ways:
1. Measured −0.04% against a ±5% threshold
2. `0xC4E0C` = `45 a2 a0 00` — **byte-identical to the factory reference**
3. Owner confirmed **stock EJ20Y injectors** fitted

**Result: 520.19 cc/min is correct. No change.**

> ⚠️ An earlier conclusion of "600 cc injectors" was **wrong** — built on LTFT −13.28%,
> which was the *minimum sample across a mixed-load drive*, not the guide's warm-idle
> sum. See the RESOLVED section in `current_limits.md`.

## ✅ Step 1b — Injector latency (2026-08-31)

`Injector Latency` @ `0xC5B78` is **byte-identical to the factory reference**. With stock
injectors and step 1a measuring −0.04%, there is nothing to correct. Revisit only if
injectors or fuel pressure ever change.

## ⬅️ Step 1c — MAF scaling — NEXT

Guide's procedure:
> 1. Drive a **flat** road for 30–60 minutes logging AF correction, AF learned, MAF voltage, CL/OL status
> 2. Drop all OL rows
> 3. Compute MAF voltage change per row
> 4. Drop rows with Δvoltage/sec > 0.2
> 5. Scatter-plot summed corrections vs MAF voltage
> 6. Any cell >5% error: multiply g/s by `1 + %correction` if positive, `1 − %correction` if negative
> 7. Repeat

**Readiness:**

| Needed | Have? |
|---|---|
| AF correction (STFT) | ✅ |
| AF learned (LTFT) | ✅ |
| **MAF voltage** | ✅ added 2026-08-30 as `P18 @ 0x00001D` (`x/50`); verified live, 0.68–1.34 V at idle |
| CL/OL status | ⚠️ no such parameter or switch in this ECU's def — **infer from STFT activity** (oscillating = closed loop, frozen = open loop) |

**Baseline table read out of the ROM (2026-09-06):** `work/MAF_TABLE_BASELINE.md` —
54 big-endian floats, g/s at `0xCCCB8`, volts axis at `0xCCBE0`, 0.898–5.000 V /
1.43–348.02 g/s. **Rows 0–27 are ≤2.6 V** = the closed-loop region this step touches.
Rows 28–53 are open-loop and belong to step 3 (needs the wideband).

**Action:** 30–60 min on the flattest road available, steady light-load cruising (closed
loop is where this data lives), warm. One continuous log. Then analysis is desk work.

**Sequence decided 2026-09-06:** log **first**, then flash. Fuel trims are mature right
now (no flash since 2026-08-29, a week of driving); flashing the IAM change first would
wipe LTFT and throw away that maturity, and the MAF log would be measuring a blank
learning table. IAM affects timing, not fuelling, so it cannot corrupt MAF data — the
order is safe. Then flash **MAF correction + IAM `0xC875C` together**, one flash, one relearn.

---

## Blockers

| Blocker | Effect | Notes |
|---|---|---|
| **No FBKC** | **Hard-blocks step 4.** The guide's timing procedure is built on watching FBKC during WOT pulls. | `P23` returns `0xFF`; 4-byte ecuparam `0xFF7BD0` refused (`NRC 0x12`), incl. extended session. Not fixable in software. |
| **No wideband O2** | Blocks fuel + AVCS tuning as written | Guide calls it a hardware prerequisite. Factory A/F sensor works but is less trustworthy rich. |
| **AFR ~14.7 at WOT** | **Must fix before boost.** Low load keeps the ECU in closed loop so it never enriches at full throttle. | Harmless at spring pressure; dangerous under boost. |
| **Compression unknown** | Sets the whole boost/timing envelope | Owner's notes say 11:1→8:1; factory EJ20X/Y is **9.4–9.5:1**. Numbers match no factory spec. **Ask the builder.** |
| **Turbo identity** | Affects boost targets | TD04HLA-19T vs IHI VF44/45 — 2006 straddles the changeover. Check the compressor tag. |
| **Definition may be AT-derived** | Any table could be mis-referenced | RomRaider t=12826: author "may have based it off an AT model". Cross-check load-bearing tables vs A2UI000K. |

---

## Pending flash batch — NOT yet written

Batch changes: **one flash, one relearn.** Every flash resets IAM and fuel trims.

| Change | Address | From → To | Why |
|---|---|---|---|
| Advance Multiplier (Initial) | `0xC875C` | `0.5` → `1.0` | IAM starts maxed after every reflash; otherwise iterative tuning is impractical *and* intermediate measurements are taken on a car running half its bonus timing. Guide sanctions it. |

---

## Done outside the guide's sequence

- **Rev limit restored** 3900/3700 → 6800/6600 (2026-08-29). Break-in limiter from the
  rebuild, never lifted. Verified byte-for-byte; peak 6888 RPM warm, zero knock.

## Live observations

- **IAM pinned at 0.500** since the reflash. Learns only at RPM 2100–5700 **and** load
  1.20–2.90 g/rev; a 53-min drive spent 3% of its time there. Resolved by the pending
  flash above.
- **FLKC `0.00`** across ~50,000 samples — no knock anywhere, including 6888 RPM.
- **~200 crank hp** at 148 g/s peak. Target 280 hp (the factory rating) needs ~215–235 g/s.

## ABS / VDC investigation (2026-10-22) — outside the guide's sequence

The new tuner's `kramar/` ROMs are in play, and the flashed `(OEM ABS)` image leaves ABS/ESP dead. Findings and the one-hypothesis
test file (`(OEM ABS WITH 2 BYTE FIX)`, bytes `0xC1AD2/3 = A2`) are in `work/ABS_RESEARCH.md`. Not flashed. Note: the tuner's maps are not part of the guide sequence above; the position in the guide (step 1c) is unchanged.
