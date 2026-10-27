# CAN: old ROM (A) vs currently flashed ROM (C)

Written 2026-10-22. Static analysis only. No ECU, cable or serial device was touched, and nothing was flashed.

| Tag | File | Family |
|---|---|---|
| A | `read_image_2026-08-25_16h39m11s.bin` (old ROM; ABS/ESP worked) | A2UG000K |
| B | `kramar/... (DIESEL ABS).bin` | A2UG000K |
| C | `kramar/... (OEM ABS).bin` (flashed; ABS light, ABS/ESP dead) | A2UG000B |
| R | `roms/reference/STOCK_A2UG000K_reference.bin` | A2UG000K |

Labels: **V** = verified from bytes or code, **I** = inferred, **?** = unknown.
Method: A's disassembly (`re/rom_disassembly.asm`), plus every literal-pool pointer read again from C's own bytes. Code is identical between A and C. The only differences in the code area are 3,703 literal-pool pointer words. Every calibration address below was read from C's literal pool, not assumed.
Scratch scripts are in `/tmp/canan/` (not part of the repo).

## Summary

The CAN machinery is the same in both ROMs (**V**). This covers the driver, the bit timing, the 17-record mailbox table, the frame builders, the send gating, the RX unpackers, the timeouts and the DTC enables.
In normal operation, the only static difference the VDC unit can see is frame `0x600` byte 5: `0xA2` in A, `0x22` in C. Bit 7 is the only bit that differs (**V**).
The clutch switch is read by the ECU, but no ROM ever puts it in any CAN frame. `0x600` byte 6 bit 2 is never set, so this path is identical in A and C (**V**). Taken alone, it cannot explain why C0076 would appear with C and not with A.
C0047 and C0072 are communication-type codes, and the ROM cannot change bus-level behaviour. That points to either a consequential fault mode inside the VDC unit or a physical/bus cause (**I**). The old ROM's VDC codes were never read, so it is not known whether the same codes were present with A.
The strongest ROM-side candidate is still byte 5 bit 7. A coherent reading is that it is a diesel-ECU flag saying "clutch information is carried on CAN" (**I**, undocumented).

---

## 1. Outgoing frames: payload sources

General facts:
- All five TX frames are built from RAM. The builders contain no calibration reads except in `0x600`.
- All five TX frames are sent only when `0xFFFF86A8==0`, `0xFFFF9AB4==0` and `0xFFFF64AA==0` (bus-off/fault latch) (**V**).
- Period: `0x410`/`0x411`/`0x412`/`0x601` go out every 10 ticks and `0x600` every 50 ticks. Parent routine `0x19D72` (**V**).
- `0x25B4(x, scale, offset)` converts a float to a byte by dividing by the scale (consistent with how `0x600` bytes 1-2 use it). `0x2574` is the u16 version.

### 0x410 (builder `0x19E3E`, buffer `0xFFFF65F2`, record `0x5A0F8`)
| byte | source | status |
|---|---|---|
| 0 | `0xFFFF6620` ÷ 2.0 | V (meaning ?) |
| 1 | `0xFFFF6644` ÷ 1.6 (const `0x1A000`) | V; torque-type value, I |
| 2 | `0xFFFF6658` ÷ 1.6 | V |
| 3 | `0xFFFF6650` ÷ 1.6 | V |
| 4 | `0xFFFF665C` ÷ 0.392 (const `0x1A010`), pedal % | V; meaning I |
| 5-6 | RPM `0xFFFF6D34`, u16 little-endian | V |
| 7 | b7 `698C`, b6 `7FDC` (idle switch, same flag as SSM 0x62 bit 6), b5 `663B`, b4 `663C`, b3 `6B60` (power-steering switch: input `0xFFFF5BEA` bit 5 low, SSM 0x62 bit 2), b2 `6328` (diesel page: A/C compressor), b1 = DTC-status getter `0x2C28C()==2`, b0 `65D4` | V; names I |

There is an alternate builder at `0xBF080`, selected by `0xFFFF66B0` bit 0, which is set at `0xBF004` from input pins `0xFFFF5BE6` bits 5 and 6 plus voltage checks. In that mode the frame carries ROM bytes `0xFFAF8..A` and a checksum (`0x4EDE6`).
- `0xFFAF8..A`: A/B/R = `34 22 21`, C = `34 21 11`. Family/ID difference (**V**).
- This is a test/plant-mode path, inactive in normal driving (**I**).

The torque values (bytes 0-3) come from the engine-load model (`0x1A814`: manifold pressure `6970`, `7EDC`, `7874`, `6C24`, ...). The calibration scalars that `0x1A814` reads directly (`C1AF4..C1B0C`) are identical. Their live values still follow each tune's maps (**I**).

### 0x411 (builder `0x1A09E`, buffer `0xFFFF65FA`, record `0x5A0C8`)
| byte | source | status |
|---|---|---|
| 0 | b7 `65DA`, b6 `65DB`, b5 = (`0x2C1D8()==2` or `0x2C1EC()==2`, DTC-status getters), b4 `663D` (= `6A1C` > 50.0), b3 = NOT `65DD`, b2 `6662`, b1 always 0, b0 `65DC` | V |
| 1-2 | `0xFFFF65F0`: a rotating list of the ECU's **active DTC codes**. `0x1B054` walks the DTC descriptor table at `0x734E0` (213 × 20 bytes). Bits 14-15 hold a 0-3 slot index; byte 1 is the low byte | V |
| 3 | `0xFFFF662C` ÷ 0.392. `662C` = f(`6A34`) using cal `0xC1B58` = 2.0 (A=B=C=R) and constants 84 and 100 | V |
| 4 | gear: `0xFFFF6F08` if the MT flag `6CDB`=1, else 0 (`0x1B1EA`) | V |
| 5 | `0xFFFF6630` = `0xFFFF20B4` (cruise set speed per the diesel page) | V; meaning I |
| 6 | b7 `68F4`, b6 `68F5`, b5 `6887`, **b4 `6701` = debounced brake switch** (raw `66F8` = `0xFFFF5BE6` bit 7 low; SSM 0x121 bit 3; the diesel page also says "Brake SW"), b3 `670C`, b2 `670B` (cruise main state), b1 `6890`, b0 `66FE` | V; names I |
| 7 | b7 `65D9`, **b6 `66A6`** (upshift-indicator request, `0x1B872`), b5 `6686`, b4 `663F`, b3 `663E`, b2 `65D6` (`0x1B2C0`, gated by cal `0xC1AD0`==0x5A; `0xC1AD0` = 00 in all four), b1 `666A`, b0 `65E3` (MIL per the diesel page) | V; names I |

Calibration that affects 0x411 (all at the same address in both families, +0):

| cal | used at | A | B | C | R | effect |
|---|---|---|---|---|---|---|
| `0xC1AD1` (gear count) | `0x1B708/0x1B768/0x1B794` | 06 | 06 | 05 | 06 | upshift-indicator state `66A5`/`66A4` → **byte 7 bit 6** |
| `0xC1B78..0xC1B90` (per-gear factor, gear 1-6, +offset) | `0x1B630..0x1B6B8` | 1.4 1.2 1.0 1.0 0.9 0.9 0.8 | = A | 1.4 1.2 1.0 **0.9 0.8 0.8** 0.8 | = A | same |
| table `0xC1D34` (desc `0x82D98`, 16 floats) | `0x1B688` | 1600…2400 | = A | 1600…2200 (different shape) | = A | same |
| `0xC1AE0/2/4`, `0xC1B94` | `0x1B750..0x1B8C0` | identical | | | | |

### 0x412 (builder `0x1A46A`, buffer `0xFFFF6602`, record `0x5A118`)
- b0 = `0xFFFF6639` (from `0x1C254`)
- b1-2 = `0xFFFF6628` ÷ 0.1, u16 little-endian
- b3-4 = `0xFFFF6624` ÷ 0.1, u16 little-endian
- b5 = `0xFFFF6A1C` ÷ 0.392 (%)
- b6 = `0xFFFF20A8`, b7 = `0xFFFF20AA`
- No calibration in the builder. The sources (`0x1C130..0x1C25E`) read `0xC1BD0/0xC1BD4`, which are identical (**V**).

### 0x600 (builder `0x1A58C`, buffer `0xFFFF660A`, record `0x5A138`)
| byte | source | A | B | C | R |
|---|---|---|---|---|---|
| 0 | constant 0 | | | | |
| 1-2 | `0x2574`(cal **`0xC1B98`** × InjPW `78CC` × RPM × 3.333e-8, step 0.001) | 8.75 | 8.75 | 8.75 (`0xC1B98`, +0) | 8.75 |
| 3 | coolant + 40, or 0xFF on sensor fault (`0x1B8FE`) | code | | | |
| 4 | counter `65EC` | | | | |
| **5** | `0x1B8DC`: MT flag (`0x280FC` → `6CDB`) ? cal **`0xC1AD3`** : cal `0xC1AD2` | **A2** / A2 | A2 / A2 | **22** / 02 | 22 / 02 |
| 6 | `66AE`: cleared to 0, then b5 `6682`, b4 `6684`, b3 `6683`, b1 `6640` (from `0x1B97C`), b0 `6CDD`. **Bits 7, 6 and 2 are never set.** | | | | |
| 7 | constant 0xFF | | | | |

Notes on 0x600:
- The literal pool in C (`0x1B95C`/`0x1B960`) points at the same `0xC1AD2`/`0xC1AD3` (**V**).
- The MT flag `6CDB` comes from cal `0xC2D80` = 0x55 in all four ROMs, so the `0xC1AD3` path is the live one in A and in C (**V**).
- `6CDD` = (input `0xFFFF5BE9` bit 3 low) OR (`0x514` byte 4 bits 0-1 ≠ 0, the BIU blower bits). This is an electrical-load/blower flag, **not** clutch (**V** logic, **I** name).
- The difference in byte 5 comes from a **tuner edit in A** (stock K = `02 22`). C carries the stock family value. It is not a family difference.

### 0x601 (builder `0x1A70E`, buffer `0xFFFF6612`, record `0x5A128`)
- b0: b3 `6668`, b2 `6687`, b1 `6688`, b0 `6689`. Bytes 1-7 = 0.
- `6668` (`0x1C25E`) = 1 while RPM < the rev-limit resume value (with further conditions).
- That value comes from cal `0xC5384` in A/B/R and `0xC5380` in C (pointer shifted −4). A = 3700 (old break-in limit), B = C = R = 7300 (**V**).
- So with A, byte 0 bit 3 dropped above 3700 rpm; with C it drops above 7300. This is a tuner/limit difference (**V**), receiver unknown.

## 2. Clutch signal

Signal path (all **V**; names **I**, matched against RomRaider's SSM switch layout):
- Raw clutch input: `0xFFFF5BE9` bit 5, active low.
- Raw flag `66FA` = pin low AND MT flag (`0x1C7C6`, through `0x280EE`).
- Debounced copy `0xFFFF6704` (cal `0xC213E`, identical). Its only readers are the cruise-cancel reason logic (`0x1ED9E`, `0x20EDE`, `0x2113C`, `0x213BE`, cancel-reason bit 0x20).
- Second copy `0xFFFF6CE5` (`0x27F6E`): MT AND pin low, with a release delay of cal `0xC2D7F` = 0x07 (0xFF disables it). Readers: `0x17078`, `0x36050`, `0x39EFE`, `0x497C6`, and the SSM switch byte at `0x51EBC`. That is **SSM 0x121 bit 7, "Clutch Switch"**, laid out next to stop light `66F9`, cruise set/resume `66F6`/`66F7` and brake `66F8`.
- Neutral switch: `0xFFFF6CE2`/`6CD6`, from `0xFFFF5BE9` bit 0 (SSM 0x62 bit 7). It is not in any TX frame either.

What reaches CAN:
- **No TX builder reads `6704`, `6CE5`, `66FA` or `6CE2`.**
- `0x600` byte 6 has exactly two writers (`0x1A5EE` clear and `0x1A6CA` store, through `66AE`), and no code sets bit 2. The raw ROM has no other reference to `0xFFFF660A..6611` or to `66AE`.
- **The earlier finding is confirmed: this ECU never sends a clutch bit** (**V**).

Calibration that matters here:

| cal | A | B | C | R |
|---|---|---|---|---|
| `0xC2D80` (MT selector) | 55 | 55 | 55 | 55 |
| `0xC2D7F` (clutch release delay) | 07 | 07 | 07 | 07 |
| `0xC213E` (debounce) | identical | | | |

- DTC enable table `0x73300..0x73600`: A = C byte for byte. P0851/P0852 (`0x73423`/`0x73427`) = 01 in all four (**V**). A differs from R only in the 28 known EVAP/O2/TGV/secondary-air switches.
- The clutch path is the same in A and C (**V**).

## 3. Received frames: absence and implausibility handling

All of the following is code-identical between A and C. Every calibration read in `0x18000-0x1C600` is identical, apart from the rows in the table in §6 (**V**).

**0x501/0x512/0x513 (VDC)** (`0x19564`):
- Per-ID missing counters `65CC`/`65CD`/`65CE`. A counter ≥ **63** (hard-coded `mov #63`, not calibration) latches `6598`.
- The `0x501` message counter (byte 5) is checked: if it does not change for 63 cycles, `659A` latches.
- On a fault, `0x19970` substitutes defaults: torque request 0, `0x512` flags = 0xC0, speeds 0.
- Effects:
  - Vehicle-speed selection (`0x2850C`) falls back from the CAN speed to `0xFFFF6D08`.
  - Cruise (`0x1D028`) reacts.
  - The CAN DTC monitor at `0x5E6C0` combines `6598`/`659A`, bus-off `64AA` (`0x184F0`), the TCM getters (`0x18CBE`/`0x18CCC`) and the BIU getters (`0x1949A`/`0x194A8`). Its voltage gate is cal `0xC42C0` (A) / `0xC42D0` (C) = 10.9 V in both.
- This is probably P0600 "serial communication link" (enable `0x73497` = 01 in all four) (**I**).

**0x514/0x620 (BIU/AC)** (`0x18DA0..0x19260`):
- Uses cal `0xC1AD7` = 0x1E, `0xC1AD8` = 0x00FA and `0xC1BDC` = 8.0, all identical.
- `0x514` byte 4 bits 0-1 feed `6CDD` (`0x600` byte 6 bit 0).

**0x420/0x421/0x422 (TCM)** (`0x18528`): the whole handler is **skipped when the MT flag is 1**. No processing and no timeout on this car (**V**).

**Bus monitor** (`0x1834C`):
- Battery hysteresis cal `0xC1AEC`/`0xC1AF0` = 9.0/9.5 V.
- 10.9 V gate (above).
- Bus-off/error counter vs cal `0xC1ADA` = 1000 and constant 500.
- All identical.

## 4. Bus level

- Bit timing: `0xD3D4` writes BCR1 = `0xA731` and BCR0 = `0x0001` from constants in `0xD4C0..0xD4D4`. `0xD000-0xE000` is byte-identical in A and C (**V**).
- The mailbox/ID table `0x5A0C8..0x5A1D8` (all 17 records) is **byte-identical** in A, B, C and R (**V**). The init call `0x18310 → 0xD39C(0, 0x5A0C8, 17)` is identical.
- The HCAN helpers `0xFD00-0x10300` are identical.
- No calibration item touches the bus configuration. **The ROM cannot make C behave differently from A on the wire** (bit rate, ACK, IDs, DLC, period) (**V**).

## 5. Selector bytes 0xC2D70..0xC2DD2

- Byte-identical in A, B, C and R (**V**).
- All of them are read at +0 in C as well (`0xC2D80` via `0x27F0C` and others).

Decoded:
- `0xC2D80` = 0x55 → MT flags `6CCE`/`6CDB` = 1. 0xAA forces 0 (AT). Any other value reads input `0xFFFF5BE9` bit 7.
- `0xC2D7F` = clutch release delay (07).
- `0xC2D7E` (`0x28052`) = counter limit for `6CE0`.
- `0xC2D81` (`0x25B5C`) = power-steering switch debounce (02).
- `0xC2D82/83` and `0xC2DC8..0xC2DD0` = the gear-estimation module (`0x28E44`, `0x2938C`, ...). The gear calibration `0xC30C8..0xC315C` is also identical in A and C.
- `0xC2DC2` = 0x0019 threshold for counter `6CEA`.
- The rest (`0xC2D70..7D`, `0xC2D84..0xC2DBE`, `0xC2DC4/6`) are diagnostic thresholds for the module at `0x217D8..0x2A13C`. They were not decoded individually (?).

## 6. A vs C differences that the VDC unit could see, or that change how the ECU handles VDC frames

| # | item | A | C | source of difference | VDC-visible? | status |
|---|---|---|---|---|---|---|
| 1 | `0x600` byte 5 (`0xC1AD3`) | 0xA2 | 0x22 | tuner edit in A (stock = 0x22) | yes, static, every 50 ms | V |
| 2 | `0x411` byte 7 bit 6, upshift indicator (`0xC1AD1`, gear factors, table `0xC1D34`) | 6-gear logic | 5-gear logic | family | yes, dynamic | V code, I meaning |
| 3 | `0x601` byte 0 bit 3 (`0xC5384` / C `0xC5380`) | clears above 3700 rpm | clears above 7300 rpm | tuner / break-in limit in A | yes, dynamic | V |
| 4 | `0x410` bytes 0-4, `0x600` bytes 1-2 (torque, pedal, fuel use) | A's maps | C's maps | tuner maps | yes, dynamic values, same encoding | I |
| 5 | `0x411` bytes 1-2 (active ECU DTC list) | whatever ECU faults were active | same | depends on the car's state, not on the ROM tables (DTC enables and descriptor table identical) | yes | V mechanism, ? content |
| 6 | `0x410` test-mode ID bytes `0xFFAF8` | 34 22 21 | 34 21 11 | family | only in test mode | V/I |
| 7 | SSM ECU ID `0xCDAD0..4` (C: `0xCDACC`) | 4B 04 78 50 07 | 4B 04 58 50 07 | family | no (diagnostic tool only) | V |
| — | bus timing, mailbox table, RX timeouts, CAN DTC enables, clutch/neutral/brake paths, MT selector | same | same | — | — | V |

## 7. Candidate explanations for C0047 / C0076 / C0072, ranked

### 1. `0x600` byte 5 bit 7 (0xA2 → 0x22)
For:
- It is the only static difference the VDC can see.
- It is diesel-specific (the subdiesel page shows the diesel ECU sending 0xA2).
- The VDC/ABS parts are diesel-model.
- The owner's report matches: A works, C does not.
- A plausible mechanism fits C0076 specifically. On the diesel, the clutch switch travels on CAN (`0x600` byte 6 bit 2). Bit 7 may tell the VDC "this ECU supplies clutch/MT data on CAN". With 0x22 that capability disappears, the MT-spec VDC logs "clutch signal", and it may enter a fail state that adds the communication codes (**I**, undocumented).

Against:
- C0045 (spec mismatch) is absent.
- No source decodes the byte.
- C0047/C0072 name the bus and the yaw-sensor link, and a payload byte would not normally produce those directly.

### 2. A physical, bus or hardware cause coinciding with the swap
For:
- C0047 (CAN line) and C0072 (yaw-sensor communication) are exactly what wiring, termination, a connector or a yaw-sensor fault produces.
- The ROM cannot alter bus behaviour (§4, V).
- The README says the old dump was taken "before the ECU was replaced". If the ECU **hardware** was changed, termination, connector pins or harness handling are all new variables (?).

Against:
- The owner ties the fault to the ROM change. Whether the ECU unit itself was swapped is not established.

### 3. The clutch signal is missing on CAN (byte 6 bit 2 never set)
For:
- It directly matches the code name C0076.
- A diesel MT VDC may expect the clutch switch over CAN.

Against:
- It is **identical in A and C** (V), so on its own it cannot explain why A worked. It only matters if the VDC's use of the bit depends on #1, or if C0076 was also present with A (never checked).

### 4. Dynamic payload differences (#2, #3, #4 in the table)
For: these are real differences.

Against:
- They are meter, limiter and torque values in the same encoding.
- Nothing ties them to communication or clutch codes.
- Least likely.

## 8. Unknown

- Which VDC codes were present with ROM A. This is the decisive missing control.
- Whether the ECU hardware was physically replaced between A and C.
- The meaning of `0x600` byte 5 bit 7, and whether the VDC (or the BIU) reads `0x600`.
- Whether the diesel VDC also reads `0x411` byte 7 bit 6 or `0x601`.
- The SSM3 detail values `1EBF` / `1504` / `2620`.
- The ECU's own DTCs with C flashed. The CAN monitor at `0x5E6C0` (probably P0600) would show whether the ECU also sees VDC frames missing, which would point to a bus problem rather than a payload problem.
- The meaning of the remaining RAM flags (`65DA`, `65DB`, `6662`, `68F4`, `68F5`, `6682-6689`, ...).

Cheap, read-only checks that would separate these:
1. Read the ECU DTCs with C flashed.
2. Ask whether the ECU unit was replaced.
3. Use a listen-only CAN capture to confirm the yaw-sensor IDs and whether `0x501/0x512/0x513` are present.
4. Read the VDC codes again after flashing the 2-byte-fix file. That would test #1 against #2 directly.
