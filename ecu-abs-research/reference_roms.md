# Reference ROMs & the 280 hp Question — A2UG000K / EJ20Y / 8:1 rebuild

*Research report, 2026-08-30. Documentation only — nothing in this file is a tune,
nothing referenced here should be flashed. Sources are cited inline; ranges are
community-derived and vary; the final numbers for this engine can only come from a
tuner with a wideband and knock monitoring on this car.*

---

## Summary

There is a healthy supply of stock reference ROMs for this exact calibration and its
JDM Legacy siblings — the community copy of A2UG000K on GitHub is byte-identical to the
reference already in `roms/reference/`, and at least eight sibling spec.B / GT images
are downloadable from the same repository. However, **no factory ROM exists for an 8:1
EJ20 twin-scroll — the factory EJ20Y calibration assumes 9.4–9.5:1 compression and
Japanese ~100 RON premium — so every stock image is comparison material, not a flash
candidate**; notably, the owner's recollection of "~11:1 stock" does not match any
factory spec for this engine and needs checking with the builder. The 280 crank hp goal
is essentially the car's own factory rating (280 PS / 276 hp), which makes it modest and
plausible on the stock turbo and stock-sized injectors — roughly 220–235 g/s of air and
about 15.5–16.5 psi peak boost at 8:1 instead of the stock 14.5 — but only after the
currently broken fueling reference (LTFT pegged at −13.28%, injectors possibly larger
than the declared 520 cc) and the 9.88 psi lowest fuel-cut bin are resolved. The fuel
question ("e95") is read here as **95 RON Ukrainian pump petrol, not 95% ethanol** — the
two readings have opposite tuning implications and the owner must confirm.

---

## 0. First, the fuel: what does "regular e95" mean?

> **Assumed reading: А-95 — ordinary Ukrainian 95 RON pump petrol.**

Reasoning:

- The owner's locale is Europe/Kyiv. Ukrainian pumps sell А-92, А-95, А-98/А-100 and
  diesel; "95" is the default petrol. The word **"regular"** fits a pump grade, not a
  specialty fuel.
- Since 1 May 2025 all Ukrainian A-95 must contain **at least 5% bio-components**
  ([Ukrainian Oil & Gas Association](https://oilers.org.ua/en/2025/08/11/high-octane-mustang-100-petrol-now-available-at-115-wog-filling-stations/)),
  and EU-style pump labels write this as **"E5"/"E10"** next to the octane number — a
  very plausible origin for the stray "e" in "e95".
- Fuel that is actually 95% ethanol exists (ED95) but is a fleet fuel for *converted
  diesel* engines; it is not sold at Ukrainian filling stations. E85 is likewise not a
  normal pump option there.

**Why it matters — the two readings point in opposite directions:**

| | 95 RON petrol (assumed) | 95% ethanol (rejected reading) |
|---|---|---|
| Knock resistance | Modest; *below* the ~100 RON Japanese premium the factory map assumes | Enormous; timing/boost ceiling set by hardware, not knock |
| Fuel volume | Baseline | Stoich ≈ 9:1 → **~35–40% more injector flow needed**; the 520–565 cc injectors and stock pump would be badly undersized |
| Cold start | Normal | Problematic below ~10 °C without hardware provisions |
| Consequence for this report | Timing/boost constrained by octane; low CR helps | Nearly every number below would change |

One more point in the assumed reading's favor: **98 and 100 RON are available in
Ukrainian cities** — OKKO "Pulls 100" ([OKKO](https://www.okko.ua/en/fuels)), WOG
"Mustang 100" at 115+ stations as of Aug 2025
([UOGA](https://oilers.org.ua/en/2025/08/11/high-octane-mustang-100-petrol-now-available-at-115-wog-filling-stations/)),
and UPG "upg100" ([UPG](https://upg.ua/en/the-upg-national-gas-station-chain-bring-high-octane-upg100-gasoline-to-the-ukrainian-market/)).
Since the JDM factory calibration was written for Japanese premium (~98–100 RON — spec
sheets list the car as "Premium Gasoline",
[carfromjapan](https://carfromjapan.com/specifications/subaru/legacy-touring-wagon/5817269c2afaa2c4b2872f1f)),
the *choice between A-95 and A-98/100 is a real calibration decision*: the tuner must
calibrate for the worst fuel that will ever go in the tank, not the best.

> **Owner must confirm:** (a) that "e95" means 95 RON pump petrol; (b) whether they are
> willing to commit to 98/100 RON, which materially relaxes the knock constraint.

---

## 1. The honest structural point: there is no stock ROM for this engine

**Every factory EJ20Y calibration — including the A2UG000K in this car — was written for
a 9.4–9.5:1 compression engine burning ~100 RON Japanese premium.** The EJ20X/EJ20Y
factory compression ratio is 9.5:1 per the
[Subaru EJ engine reference](https://en.wikipedia.org/wiki/Subaru_EJ_engine) (9.4:1 per
[carfolio's spec.B sheet](https://www.carfolio.com/subaru-legacy-b4-2.0gt-spec.b-332112)).
This engine is now ~8:1. **"Find a stock ROM matching this engine" therefore has no
answer.** No such ROM was ever made. The closest thing to a calibration for this
specific engine is the 58-region retune already in the ECU, written by whoever built it.

Two nuances worth stating precisely:

1. **The "~11:1 before the rebuild" figure does not match any factory spec for this
   engine.** Factory EJ20Y is 9.4–9.5:1. Possible explanations: the builder measured
   something (e.g., a compression *test* in bar — a healthy EJ20 turbo reads ~11–12 bar,
   and a drop "from 11 to 8" would describe *wear*, not a build); or the numbers are
   recalled loosely; or the engine had been changed before. This must be resolved with
   the builder — the arithmetic of "how much compression was given up" (and therefore
   how much boost/timing the engine now wants) depends on it.
2. **Factory 8.0:1 EJ20s did exist** — the GC8-era EJ207 STI ran 8.0:1, early EJ20G
   8.5:1, EJ205 8.0–9.0 depending on market
   ([Wikipedia EJ engine](https://en.wikipedia.org/wiki/Subaru_EJ_engine)). Those
   calibrations show what Subaru's engineers did with a low-compression EJ20 on 100 RON
   (short version: more boost, generous fuel). But they belong to different heads, cams,
   turbos, injectors and ECU generations — **study value only, zero transfer value**,
   and obviously never flashable to this SH7058 ECU.

**What stock ROMs are good for here:**

- **Diffing and triangulation.** With two or three sibling calibrations, differences in
  the car's ROM can be separated into "tuner intent" vs "factory revision noise".
- **Definition validation.** Checking that a table address in the A2UG000K definition
  holds the same kind of data in sibling ROMs (important — see §2.4).
- **Pattern study.** The *shape* of factory Target Boost, Primary OL Fueling and timing
  maps (where the factory enriches, where it tapers boost) — patterns, not values, per
  the tuning guide's own advice.

> **Never a flash candidate.** A sibling CAL belongs to different hardware pairings.
> And flashing even the *exact* stock A2UG000K image back would be actively dangerous
> here, not "safe": it would restore Max WGDC to 90% and immediately chase 14.5 psi
> targets on an engine whose fueling reference is currently broken (§4) — on top of
> being calibrated for a compression ratio this engine no longer has.

---

## 2. Reference ROM availability

### 2.1 What is already on this machine

| File | Identity | MD5 |
|---|---|---|
| `roms/reference/STOCK_A2UG000K_reference.bin` | Stock A2UG000K community reference | `f6d6b1f4f205f18746c10d7ed16eb858` |
| `roms/STOCK_A2UG000K_2006_JDM_Legacy_SpecB_MT_2026-08-25.bin` | **This car's own read** (the tuned state — 58 regions differ from stock) | `17be55e26dcc5391fbc540d3703d4e5f` |

Note the naming trap: the file *named* "STOCK_…2026-08-25" is the car's own dump, i.e.
the tuner's map, not stock. The actual stock image lives in `roms/reference/`.

### 2.2 Primary community source — verified

**[bludgod/RomRaider](https://github.com/bludgod/RomRaider) ("RomRaider Stock Rom
Repository")** on GitHub archives the stock ROMs shared on the RomRaider forum. Verified
during this research:

- It contains `JDM/Legacy/A2UG000k-2006-JDM-Subaru-Legacy-GT-spec.B-MT.hex` — despite
  the `.hex` extension it is a **raw 1,048,576-byte binary** (SH7058 vector table at
  offset 0), and it is **byte-identical to the reference already in `roms/reference/`**
  (same MD5 `f6d6b1f4…`). So the local reference's provenance is confirmed: it is the
  community copy.
- A mirror exists at
  [walterstypula/RomRaider-1](https://github.com/walterstypula/RomRaider-1)
  ("Romraider Stock Roms").

**Siblings available in the same repository** (`JDM/Legacy/`), most relevant first:

| File (CAL ID) | What it is | Value here |
|---|---|---|
| `A2UI000K` | 2007 JDM Legacy GT **spec.B MT** | Closest sibling; next-year revision of the same car |
| `A2TB100K` | 2007 JDM Legacy GT **spec.B MT** | Second spec.B MT sibling |
| `A2TB100Y` | 2007 JDM Legacy GT **"Tuned by STI"** | STI's own factory-adjacent take on this platform — instructive comparison |
| `A2UG000B` | 2006 JDM Legacy GT | Same year, non-spec.B |
| `A2UH000A` | 2006 JDM Legacy GT AT | Same year, automatic (useful for spotting AT-vs-MT table differences — see §2.4) |
| `A2TB100B` | 2007 JDM Legacy GT MT | |
| `A2SB000A` | 2008 JDM Legacy GT spec.B AT | |
| `A2WD00x/01x`, `A2ZJx` | 2004–2005 JDM Legacy GT family | Earlier EJ20X/Y generation |

Verification habit worth keeping: hash every downloaded image and record it (as
`roms/README.txt` already does), and sanity-check size (1,048,576 bytes) and the CAL ID
string at 0x2000 before using any image for diffs.

### 2.3 Forum and other sources

- **RomRaider forum "Stock Maps" subforum** —
  [viewforum f=35](https://www.romraider.com/forum/viewforum.php?f=35), including the
  [Stock ROM List thread (t=7591)](https://www.romraider.com/forum/viewtopic.php?f=35&t=7591).
  Request threads work; members dump and share
  (e.g. [t=5340](https://www.romraider.com/forum/viewtopic.php?f=15&t=5340)).
- **LegacyGT.com** tuning forum — e.g.
  ["need stock Subaru legacy rom"](https://www.legacygt.com/topic/112587-need-stock-subaru-legacy-rom/).
- **Commercial firmware databases** — e.g. Lab-R (c4ip.ru) lists
  ["Subaru Legacy GT 2.0T 6MT Denso SH7058 … A2UG000K 24UDOM_6MT ORI.bin"](https://c4ip.ru/en/subaru/54316-subaru-legacy-gt-2-0t-6mt-denso-sh7058-90e098ec-a2ug000k-24udom_6mt-ori-bin).
  These are paid, provenance unverifiable; the community GitHub copy is already verified
  identical to the local reference, so there is no need to pay for anything.
- **EcuFlash definitions as a map of what exists.** The local SubaruDefs checkout lists
  the full spec.B calibration family: `A2TB000L, A2TB001L, A2TB002C, A2TB100K,
  A2UG000K, A2UG000L, A2UI000K, A2UI001L, D0XJ001L`
  (`RomRaider/definitions/SubaruDefs/ECUFlash/subaru standard/Legacy GT spec.B/`).
  Definitions prove a calibration exists and give its table addresses even where no
  public image has surfaced (the `L` and `C` suffixed ones appear to be EDM/other-market
  variants; images for those were not found in the GitHub archive).

### 2.4 A definition caveat that directly affects this project

The RomRaider forum thread
[“Definition alteration Request: A2UG000K” (t=12826, 2016)](https://www.romraider.com/forum/viewtopic.php?t=12826)
documents that the A2UG000K EcuFlash definition had a troubled history: a user
(andy_mac, with a 2006 BP5 spec.B wagon) reported via his tuner that *"a lot of the
tables were for auto not manual"*, and the definition author (dschultz, RomRaider
developer) acknowledged *"I may have based it off an AT model and missed a few MT
tables."* The thread also carries a working **logger definition attachment**
(`logger_A2UG000K_v317.xml`) built for this exact ECU ID `4B04785007`.

Implications for this repo:

- Any table in the A2UG000K definition that matters for a decision (boost, fuel cut,
  injector scaling) is worth **cross-checking against the 2007 MT sibling definition
  (A2UI000K) and against the AT sibling ROM (A2UH000A)** — if a "manual" table in the
  def shows identical bytes in the AT ROM but a different plausible block exists nearby,
  that is the 2016 bug pattern.
- The definitions in the local checkout are newer than the 2016 thread and the local
  copy was already hand-corrected once (the lowercase-k `internalidstring` fix in
  `roms/README.txt`) — the def lineage is community-maintained and imperfect. Trust it
  the way the tuning guide says to trust everything: verified, not assumed.

---

## 3. What 280 crank hp actually requires on this platform

### 3.1 Calibrating expectations: 280 hp is the factory rating

The 2006 Legacy 2.0GT spec.B was rated **280 PS (276 hp) @ 6400 rpm and 343 Nm @ 2400
rpm** from the factory
([automobile-catalog](https://www.automobile-catalog.com/car/2006/3260765/subaru_legacy_b4_2_0_gt_spec_b.html),
[carfolio](https://www.carfolio.com/subaru-legacy-b4-2.0gt-spec.b-332112)). (280 PS was
the JDM industry self-limit of the era, so the true number was likely at or a bit above
the rating.) The goal is therefore **"give me back roughly what the factory rated"** —
modest and sane. It does *not* require a bigger turbo, bigger injectors by necessity, or
exotic boost. What it does require is undoing the compression the rebuild took away,
which shifts every number a little (below).

### 3.2 Which turbo is actually on the car? (genuinely unresolved)

Per the [EJ engine reference](https://en.wikipedia.org/wiki/Subaru_EJ_engine), manual
EJ20Y cars ran a **Mitsubishi TD04HLA-19T twin-scroll (2003–06)**, switching to **IHI
VF44 (2006MY) and then VF45 (2006–09)** at the facelift. A "2006" spec.B 6MT sits
exactly on that changeover, and the 2024 rebuild could have changed the turbo anyway.
**The tag on the compressor housing decides, not the calendar.** (The often-repeated
"VF38" belongs to the *automatic* EJ20X of 2003–06.)

Capacity-wise it matters little at this power level: Kinugawa rates the TD04HL-19T
frame at roughly **230–260 whp**
([Kinugawa](https://store.kinugawaturbosystems.com/products/kinugawa-turbo-td04hl-19t-for-subaru-bp5-bl5-legacy-liberty-gt-replace-vf38-2)),
and the VF44/45 supported the same 280 PS rating from the factory. 280 crank hp on an
AWD manual is roughly **225–240 whp** (15–20% driveline loss, the usual hand-waving
range) — i.e. **at or near the top of the stock turbo's comfortable range, but inside
it**. This is the factory operating point plus a little; expect rising intake temps to
be the practical ceiling, with the stock top-mount intercooler as the weak link.

### 3.3 Airflow

Community rule of thumb: **crank hp ≈ MAF g/s × 1.25** (or whp ≈ g/s × 1.1)
([clubwrx thread with logged datapoints](https://www.clubwrx.net/threads/using-g-s-from-maf-for-hp-numbers.134323106/),
e.g. 238 g/s ↔ 233 whp; see also
[this rule-of-thumb explainer](https://precisionremapsuk.com/blogs/car-diagnostics/maf-g-s-vs-horsepower-the-airflow-rule-of-thumb-explained)).
That puts 280 crank hp at roughly **215–235 g/s**. The stock MAF ceiling is 300 g/s and
this car's MAF Limit table is at 300 — **no MAF or intake hardware problem** at this
level. This is folklore-grade math, good to ±10%, but it is the same math the community
uses to size everything else.

### 3.4 Boost: what 8:1 changes

The stock calibration's own Target Boost table (this ROM, from `current_limits.md`)
peaks at **14.5 psi** — that is what 280 PS took at 9.4–9.5:1 on ~100 RON. Lower
compression extracts less work from the same charge (ideal Otto efficiency
η = 1 − CR^−0.4):

| CR | Ideal-cycle η | Torque at same airflow vs 9.5:1 |
|---|---|---|
| 11.0 | 0.617 | +4% |
| 9.5 | 0.594 | baseline |
| 8.0 | 0.565 | **≈ −5%** |

So at 8:1, matching the factory 280 PS needs roughly **5% more airflow ⇒ ~+1–1.5 psi ⇒
~15.5–16 psi peak** (if the pre-rebuild engine really was 11:1, the deficit is ~8–9% and
the estimate becomes ~16.5–17 psi). This is first-principles arithmetic, not a dyno
fact — AVCS, timing and intercooling all move it — but it sets the scale: **the goal
lives in the 15–17 psi region, which the stock twin-scroll can deliver and the raised
fuel-cut table (max bin 19.68 psi gauge) can tolerate.** It is also comfortably beyond
the 9.88 psi lowest fuel-cut bin, which is why §4 matters first.

### 3.5 Injectors and fuel pump

Stock EJ20X/Y injectors are side-feed units commonly listed at **~525 cc/min nominal
(flowing ~550–565)**
([Aus Auto Store fitment listing](https://www.ausautostore.com/products/fuel-injectors-for-subaru-legacy-gt-gt-spec-b-bl-bp-ej20x-ej20y-2-0l-turbo-06-2003-04-2009),
[trinituner discussion](https://www.trinituner.com/v4/forums/viewtopic.php?t=485534));
this car's calibration declares **520.19 cc/min**, unchanged from stock.

Duty-cycle math at 280 crank hp (BSFC 0.50–0.58 lb/hp·hr for a rich turbo car, fuel SG
0.745):

```
fuel = 280 hp × (0.50…0.58) lb/hp·hr = 140…162 lb/hr  ≈ 1420…1650 cc/min total
per injector = 355…412 cc/min  →  duty on 520 cc: 68…79%
```

**68–79% duty — workable, but snug**, right at the community's preferred ≤80% ceiling
([scoobynet](https://www.scoobynet.com/drivetrain-11/390604-max-power-from-550cc-injectors.html)
puts 550s at ~400 bhp with more aggressive duty assumptions; the conservative reading
is the one that matters). Two caveats:

- **On 95 RON the tune will run rich** (safe AFR targets of ~10.5–11:1 per the tuning
  guide), which is the top end of that BSFC range — expect the high side of the duty
  estimate.
- **All of this math is void until the injectors are identified** — see §4. If the
  rebuild installed larger injectors (the −13.28% LTFT peg suggests something is
  oversupplying fuel), duty headroom improves but every open-loop fueling number in the
  ROM is currently wrong.

Fuel pump: at ~stock power on petrol the stock BL5 in-tank pump is generally regarded
as adequate; verify fuel pressure holds under load during tuning rather than assuming.
If an upgrade is ever wanted, note that drop-in fitment on the 05+ Legacy hanger
requires modification
([IAG on the Walbro 255 for Subaru](https://www.iagperformance.com/walbro-255lph-fuel-pump-for-subaru/)).
Whether the rebuild already touched the pump is another builder question.

---

## 4. This car's own constraints — what must move before boost does

The owner's analysis (`current_limits.md`) found four constraints. Their interaction
defines the order of work:

| # | Constraint | Value | Implication for 280 hp |
|---|---|---|---|
| 1 | Long-term fuel trim | **pegged at −13.28% floor** | The ECU is pulling the maximum fuel it can and still running rich. The fueling reference (injector scaling and/or MAF scaling and/or base fuel pressure) is wrong by *at least* 13%. **Nothing built on top of this math is trustworthy.** |
| 2 | Injector Flow Scaling | declares **520.19 cc/min** (stock) | If the rebuild installed different injectors, the declaration is fiction. Identify the physical injectors (part number off the rail), correct the scaling, then re-verify trims to within ±5% per the tuning guide's procedure. |
| 3 | Boost Limit (Fuel Cut), lowest bin | **9.88 psi gauge** | A 6-element table, not one number. Raising boost without understanding which conditions select bin 1 means hitting fuel cut just above spring pressure. Map the table's axis (and cross-check the definition per §2.4) before any boost increase. |
| 4 | Max WGDC Post-Compensation | **0.00%** | The deliberate master switch holding the car at ~7 psi spring pressure. It is doing its job. It should be the **last** thing restored, not the first. |

Also relevant: the **3900 rpm break-in rev limiter**. Factory power peaks at 6400 rpm —
280 hp is physically unreachable until the limiter is restored toward the engine's
designed ~6800 ceiling, and whether the break-in is complete is a builder question, not
a software one.

**The resulting order** (which is just the tuning guide's own order applied to this
car):

1. Identify the actual hardware: injectors, fuel pump, turbo, intercooler state.
2. Fix the air/fuel relationship: correct injector scaling (and latency), verify MAF
   scaling, get trims inside ±5%. A wideband O2 is a prerequisite for the open-loop
   part.
3. Understand and, with the tuner, adjust the Boost Limit (Fuel Cut) bins coherently
   with the planned target boost.
4. Only then restore Max WGDC Post-Compensation (owner's own calculation: ≥58.75% to
   stop clipping the current WGDC tables; stock was 90%) and tune boost upward
   incrementally.
5. Timing and AVCS after boost and fuel, then re-verify fuel and timing — per the
   guide.

Steps 3–5 are tuner work on a dyno or with disciplined road logging. Steps 1–2 are
where a beginner-owner adds real value without touching risk.

---

## 5. The low-compression calibration question

What the community and professional tuners say about calibrating an 8:1-class engine on
pump petrol:

**Direction of timing: more advance, not less.** Lower compression means lower
in-cylinder temperature and pressure, hence more knock margin and a slower burn — both
push MBT timing earlier. A practical datapoint from the
[Miata Turbo forum](https://www.miataturbo.net/engine-performance-56/ignition-advance-low-compression-vs-factory-100118/):
*"about two degrees more timing with 8.6 vs. 9.4 compression"*. HP Academy's moderator
Raymond Herchenroder states the same relationship inverted: *"At any given level of fuel
knock resistance and charge air temperature you need to run less boost, richer AFR, and
more retarded spark as compression ratio increases"*
([HP Academy](https://www.hpacademy.com/forum/efi-tuning/show/why-do-people-choose-low-compression-pistons-for-turbo-4-cylinder-builds)).
The folklore scaling — roughly 1–2° per point of CR — is folklore; the direction is
established, the magnitude is per-engine.

**The boost/timing trade shifts toward boost.** The reason people build 8:1 engines is
to spend the knock margin on boost rather than on advance. On pump fuel there is still
a point of diminishing returns — HP Academy's general-tuning discussion describes the
classic trap of adding boost, pulling timing to suppress knock, and making the same
power with more heat and stress
([HP Academy](https://www.hpacademy.com/forum/general-tuning-discussion/show/knock-limited-engine-high-boost-low-timing-or-vice-versa/)).
At a 280 hp target this engine should be nowhere near that regime.

**One offset to keep in mind:** this build also *dropped octane* relative to the
factory's assumptions (Japanese ~100 RON → Ukrainian 95 RON). The CR reduction buys
knock margin; the octane reduction spends part of it. Net margin is probably still
better than the factory's situation, but only logging decides — and running 98/100 RON
(§0) would keep the whole margin.

**The costs, which are permanent:**

- **Off-boost torque and drivability.** The ~5% ideal-cycle efficiency loss (vs 9.5:1)
  applies *everywhere*, including at zero boost, where nothing compensates. The car is
  simply softer below spool, and cruise fuel economy is worse.
- **Spool.** Community opinion is split on the mechanism (less pumping work vs more
  exhaust enthalpy), but the practical consensus is that low-CR street cars feel lazier
  getting into boost. Not tunable away; a fact of the build.
- **Modern context:** current professional opinion (same HP Academy thread) is that 8:1
  is old-school-low — modern knock control and fuels favor 8.5–9.5 even for boosted
  builds. Irrelevant now that the engine is built, but it explains why no contemporary
  factory map resembles what this engine needs.

**What no source can provide:** actual timing numbers for *this* combination. The
factory 8.0:1 EJ207 maps (different heads/cams/turbo/ECU) and the factory 9.5:1 EJ20Y
map bracket the problem from opposite sides; neither is an answer. The answer comes
from WOT logging with knock feedback on this car, per the guide's timing procedure.

---

## 6. What to ask the tuner / engine builder

The rebuild's paperwork answers more of this project than any ROM download. Questions,
in order of importance:

1. **What is the actual compression ratio, and how was it established?** (Pistons part
   number, head/gasket spec, measured or calculated?) And what was the *actual*
   pre-rebuild CR — factory spec was 9.4–9.5:1, so where does "~11:1" come from? Was it
   perhaps a compression-test reading in bar?
2. **What injectors are installed** (part number off the rail)? The ROM declares stock
   520 cc but the fuel trims say otherwise. Same question for the **fuel pump**.
3. **Which turbo is on the car** — original TD04HLA-19T / VF44 / VF45, or replaced
   during the rebuild? (Tag on the compressor housing.)
4. **Is the break-in complete?** Mileage/hours since rebuild, oil analysis if any —
   i.e., may the 3900 rpm limiter be lifted, and to what ceiling do they warrant the
   rotating assembly (factory designed range suggests ~6800)?
5. **What fuel was the build specced for?** 95 RON, or did the builder assume 98/100?
6. **What was the basis of the current 58-region retune** — which map was the starting
   point, what AFR and boost targets were intended, and can they share their notes?
   (Their map is the only calibration in existence written for this engine.)
7. **What is their plan for the fuel trim problem** — do they know the ROM still
   declares 520 cc injectors?
8. Cams, head work, gasket thickness — anything else that moves VE or true CR?

## 7. Open questions

- **Fuel:** "e95" reading unconfirmed (assumed 95 RON petrol, §0); willingness to run
  98/100 RON unknown.
- **True compression ratio** and the provenance of the "11:1 → 8:1" figures.
- **Turbo identity** (TD04HLA-19T vs VF44 vs VF45 vs replaced) — unverified.
- **Injector and pump identity** — unverified; LTFT anomaly unexplained until then.
- **Wideband O2:** none known to be present. Without one, the open-loop fueling work
  in §4 cannot be done as written — this is a hardware prerequisite for the whole plan.
- **Boost Limit (Fuel Cut) table axis** — which conditions select which bin is not yet
  established (and the definition's history, §2.4, means it should be verified, not
  read off the XML).
- **Definition reliability** for the specific tables this project will touch —
  cross-check against A2UI000K (2007 MT) and A2UH000A (2006 AT) per §2.4.
- **Who tunes this car going forward** — the original builder, or a new tuner who will
  need this report's context handed to them.

---

## Sources

**ROM availability:**
[bludgod/RomRaider stock ROM repository](https://github.com/bludgod/RomRaider) ·
[walterstypula/RomRaider-1 mirror](https://github.com/walterstypula/RomRaider-1) ·
[RomRaider Stock Maps subforum](https://www.romraider.com/forum/viewforum.php?f=35) ·
[Stock ROM List (t=7591)](https://www.romraider.com/forum/viewtopic.php?f=35&t=7591) ·
[A2UG000K definition thread (t=12826)](https://www.romraider.com/forum/viewtopic.php?t=12826) ·
[LegacyGT.com stock ROM thread](https://www.legacygt.com/topic/112587-need-stock-subaru-legacy-rom/) ·
[Lab-R commercial listing](https://c4ip.ru/en/subaru/54316-subaru-legacy-gt-2-0t-6mt-denso-sh7058-90e098ec-a2ug000k-24udom_6mt-ori-bin)

**Engine and car specs:**
[Wikipedia — Subaru EJ engine](https://en.wikipedia.org/wiki/Subaru_EJ_engine) ·
[automobile-catalog — 2006 Legacy B4 2.0 GT spec.B](https://www.automobile-catalog.com/car/2006/3260765/subaru_legacy_b4_2_0_gt_spec_b.html) ·
[carfolio — 2006 Legacy B4 2.0GT spec.B](https://www.carfolio.com/subaru-legacy-b4-2.0gt-spec.b-332112) ·
[carfromjapan — spec sheet (premium fuel)](https://carfromjapan.com/specifications/subaru/legacy-touring-wagon/5817269c2afaa2c4b2872f1f) ·
[Flatirons Tuning — EJ20X/EJ20Y overview](https://www.flatironstuning.com/blog/everything-you-need-to-know-about-the-ej20x-ej20y-engine)

**Sizing and capability:**
[Kinugawa TD04HL-19T (230–260 whp)](https://store.kinugawaturbosystems.com/products/kinugawa-turbo-td04hl-19t-for-subaru-bp5-bl5-legacy-liberty-gt-replace-vf38-2) ·
[clubwrx — MAF g/s vs hp datapoints](https://www.clubwrx.net/threads/using-g-s-from-maf-for-hp-numbers.134323106/) ·
[MAF rule-of-thumb explainer](https://precisionremapsuk.com/blogs/car-diagnostics/maf-g-s-vs-horsepower-the-airflow-rule-of-thumb-explained) ·
[Aus Auto Store — EJ20X/Y injector fitment](https://www.ausautostore.com/products/fuel-injectors-for-subaru-legacy-gt-gt-spec-b-bl-bp-ej20x-ej20y-2-0l-turbo-06-2003-04-2009) ·
[trinituner — stock injector size discussion](https://www.trinituner.com/v4/forums/viewtopic.php?t=485534) ·
[scoobynet — max power from 550cc injectors](https://www.scoobynet.com/drivetrain-11/390604-max-power-from-550cc-injectors.html) ·
[IAG — Walbro 255 Subaru fitment note](https://www.iagperformance.com/walbro-255lph-fuel-pump-for-subaru/)

**Low-compression tuning:**
[HP Academy — why low compression pistons](https://www.hpacademy.com/forum/efi-tuning/show/why-do-people-choose-low-compression-pistons-for-turbo-4-cylinder-builds) ·
[HP Academy — high boost/low timing trade](https://www.hpacademy.com/forum/general-tuning-discussion/show/knock-limited-engine-high-boost-low-timing-or-vice-versa/) ·
[Miata Turbo forum — ignition advance, low vs factory CR](https://www.miataturbo.net/engine-performance-56/ignition-advance-low-compression-vs-factory-100118/)

**Fuel in Ukraine:**
[UOGA — Mustang 100 rollout, A-95 bio requirement](https://oilers.org.ua/en/2025/08/11/high-octane-mustang-100-petrol-now-available-at-115-wog-filling-stations/) ·
[OKKO fuels](https://www.okko.ua/en/fuels) ·
[UPG — upg100](https://upg.ua/en/the-upg-national-gas-station-chain-bring-high-octane-upg100-gasoline-to-the-ukrainian-market/) ·
[Getmancar — Ukrainian station overview](https://getmancar.com/blogs/top-gas-stations-in-ukraine-rating-guide)

*Local evidence referenced: `current_limits.md`, `roms/README.txt`,
`roms/reference/STOCK_A2UG000K_reference.bin` (hash-verified against the GitHub copy),
`RomRaider/definitions/SubaruDefs/…` (sibling definition inventory).*
