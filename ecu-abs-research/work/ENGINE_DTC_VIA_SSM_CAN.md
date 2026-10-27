# Engine DTCs via SSM-over-CAN (read-only) — investigation 2026-10-23

Desk investigation only. Nothing talked to the OpenPort or the car, and no project files were changed except this one.

## Summary

The datalogs in `logs/*.csv` were captured with `tuneforge logger-ssm-can`. That command uses Subaru SSM cmd `0xA8` (ReadAddresses) on CAN `0x7E0`→`0x7E8`, sends `0xAA` ECU-init first, stays in the default session, and reads the hardcoded `SUBARU_SSM_PARAMS` table. It uses no XML log-def and no OBD-II. The same SSM address space already used for the logs also serves the engine DTC status bytes. RomRaider's `<dtcodes>` `tmpaddr`/`memaddr` values (`0x00008E…0x000181`) are SSM addresses, not RAM addresses, so they are valid on 32-bit CAN ECUs too. Reading them on this ROM is confirmed from the disassembly: the ECU's SSM dispatch table (`0x5AB30`) routes exactly those addresses to getters that return bytes from two DTC flag arrays in RAM (`0xFFFF9282+idx` and `0xFFFF291C+2*idx`). The ROM's own DTC descriptor table (`0x734E0`, 213 records) matches RomRaider's P-code/bit map on all 202 engine-code records. The dispatch table, translation table, getters and descriptor table are byte-identical in the currently flashed A2UG000B image. **Feasible with the existing documented command `peek-ram-can` (which actually sends `0xA8` on 24-bit SSM addresses), using the 7 reads listed below.**

---

## 1. How the logs were captured

| Finding | Status |
|---|---|
| Command: `tuneforge logger-ssm-can --all --out logs/<name>.csv` (default `--interval-ms 100`) | **Inferred, high confidence.** The CSV column set and order match `SUBARU_SSM_PARAMS` + `SUBARU_DERIVED_PARAMS` in `tuneforge/crates/tuneforge-protocol/src/subaru.rs`, emitted in table order. That happens with `--all`. Derived columns (`AVCS Diff (R-L)`, `Boost (gauge)`, `Injector Duty Cycle`) exist only in that code. The GUI default set (`SSM_CAN_DEFAULTS`, 11 params, auto-named files under `~/Documents/RomRaider/logs`) does not match. No shell history records the command; `~/.zsh_history` predates the project. |
| Protocol: SSM cmd `0xAA` init → `EA …`, then `A8 00 <addr 3B>…` → `E8 <1 byte per addr>`. CAN request `0x7E0`, response `0x7E8`, ISO15765 @ 500k | **Verified (source)** `subaru.rs` `CAN_REQUEST_ID`/`CAN_RESPONSE_ID`, `ecu_init_can`, `read_addresses_can` |
| Default session, no `10 03`, no security access | **Verified (source)** `logger_ssm_can_cmd` in `tuneforge-cli/src/main.rs:1099` |
| Addresses are SSM "standard parameter" addresses `0x000007…0x000199` (e.g. RPM `0x00000E`, IAM `0x0000F9`, FLKC `0x000199`), not `0xFFxxxx` RAM | **Verified (source)**. Raw `0xFFxxxx` RAM via `A8` → NRC `0x12` (project notes, `subaru.rs` comment at P91) |
| Log-def XML: none. Params are hardcoded, scalings copied from RomRaider | **Verified (source)** |
| Header variants: `baseline_1514` (2026-08-27) still has `Knock Correction` (P23, later removed) and no IAM. Logs from 2026-08-30 on add `MAF Voltage` (P18) | **Verified (files)** |
| All logs (2026-08-27 … 2026-09-06) were taken on the A2UG000K-era ROM, before the A2UG000B image was flashed | **Inferred** from dates vs `work/ROM_CHANGELOG.md` |

## 2. RomRaider `<dtcodes>` — what the addresses are

- `logger_METRIC_EN_v370.xml` lines 1984–2574: 590 `<dtcode>` entries under `<protocol id="SSM">`. There is **no per-ECU-id gating** (no `ecubyteindex`, no ECU id list). They belong to the SSM address space, the same space as `P8 RPM @ 0x00000E`. **Verified (file).**
- They are **not** 16-bit RAM addresses. On this ECU they go through the SSM dispatch table (section 4). **Verified (disassembly).**
- RomRaider semantics: `tmpaddr` = temporary/current detection, `memaddr` = memorized/stored. The RAM mapping below is verified. That one array means "current" and the other "stored" is RomRaider's convention and is **not independently verified** from the code.
- The ROM-definition tables `(P0xxx) …` at `0x73400–0x734DC` (A2UG000K/A2UG000B defs, scaling `PXXXX enable`, 00 = disabled / 01 = enabled) are **DTC enable switches in flash**, not fault flags. **Verified (def + 32BITBASE scaling).**
- Address groups that RomRaider lists for newer ECUs (`0x1C5/6`, `0x20A–0x211`, `0x263–0x26C`, `0x2A6–0x2AE`, `0x2B6/0x2B8`) are **NOT DTC bytes on this ROM**. The dispatch table routes them to the "unsupported" getter, which returns constant `0xFF` from ROM `0x5AB2D`. **Do not read or decode them.** **Verified (disassembly).**

## 3. Read-only commands (proposed, not run)

`peek-ram-can`'s doc string says "UDS 0x23", but the implementation (`main.rs:1354`, `subaru::read_block_can`) sends SSM `AA` init, then **`A8` on consecutive 24-bit addresses**. That is the same request type as the working logger. The built binary `tmp/tf-build/release/tuneforge` contains that code path (verified by string match). The code caps `--len` at 64 (the help text says 255). Run it the way tuneforge is normally run (sudo/libusb), engine running or ignition on:

```
tuneforge peek-ram-can --addr 0x00008E --len 32   # TMP  idx 0-31   (0x8E-0xAD)
tuneforge peek-ram-can --addr 0x0000AE --len 32   # MEM  idx 0-31   (0xAE-0xCD)
tuneforge peek-ram-can --addr 0x0000F0 --len 8    # TMP 0xF0-F3, MEM 0xF4-F7      (idx 32-35)
tuneforge peek-ram-can --addr 0x000123 --len 16   # TMP 0x123-12A, MEM 0x12B-132  (idx 36-43)
tuneforge peek-ram-can --addr 0x000150 --len 10   # TMP 0x150-154, MEM 0x155-159  (idx 44-48)
tuneforge peek-ram-can --addr 0x000160 --len 10   # TMP 0x160-164, MEM 0x165-169  (idx 49-53)
tuneforge peek-ram-can --addr 0x000174 --len 14   # TMP 0x174-17A, MEM 0x17B-181  (idx 54-60)
```

Every address above is documented in RomRaider's `<dtcodes>` **and** routed to a DTC getter by this ROM's dispatch table. There are three exceptions, all still read-only getters: `0x0000AB`/`0x0000CB` are the immobilizer byte (separate getters, RAM `0xFFFF7D16` / `0xFFFF26B8`), and `0x000174`/`0x00017B` return constant 0 on this ROM. No `--extended-session` is needed or wanted.

Expected all-clear: every byte `00`. A byte of `FF` everywhere would mean the read did not reach the DTC getters (that is the "unsupported" value) and should be treated as a failed read, not as 8 faults.

**Decode:** for each byte at SSM address `A`, each set bit `b` (bit 0 = LSB, mask `1<<b`) → look up `(A, b)` in the table below. The `tmp` column is "current" and the `mem` column is "stored" (RomRaider convention).

## 4. Disassembly evidence (A2UG000K stock, `re/rom_disassembly.asm` + `roms/STOCK_A2UG000K…bin`)

| Item | Address | What it does | Status |
|---|---|---|---|
| SSM dispatch table | `0x5AB30`, 0x6A1 × 4-byte function pointers indexed by SSM address | Called at `0x507B0`: `jsr @(0x5AB30 + 4*addr)`. Live check: SSM `0x22` (P23) → `0x50C6C` → returns ROM byte `0x5AB2D = 0xFF`, which is exactly the `0xFF` the project measured live for P23 | **Verified** |
| TMP getter | `0x51772` | `idx = xlat[addr-0x8E]` (table `0x5C5B0`) → `jsr 0x4AFBE` → `mov.b @(0xFFFF9282 + idx)` | **Verified** |
| MEM getter | `0x5178E` | same xlat → `jsr 0x4AFC6` → `mov.b @(0xFFFF291C + 2*idx)` | **Verified** |
| SSM addrs routed to TMP getter | `0x8E–0xAA, 0xAC–0xAD, 0xF0–0xF3, 0x123–0x12A, 0x150–0x154, 0x160–0x164, 0x175–0x17A` | identical to RomRaider `tmpaddr` set (minus immobilizer/remote-start) | **Verified** |
| SSM addrs routed to MEM getter | `0xAE–0xCA, 0xCC–0xCD, 0xF4–0xF7, 0x12B–0x132, 0x155–0x159, 0x165–0x169, 0x17C–0x181` | identical to RomRaider `memaddr` set | **Verified** |
| DTC descriptor table | `0x734E0`, 213 × 20-byte records: `[u16 byte-idx][u8 bitmask][u8][u16 P-code]…` | All 202 engine-code records match RomRaider `(tmpaddr,bit)` → P-code exactly (0 mismatches) | **Verified** |
| DTC collector | `0x1B054` | loops the 0xD5 (=213) records, tests `0xFFFF291C+2*idx` or `0xFFFF9282+idx` against the mask, collects up to 4 P-codes into `0xFFFF65F0` (probably the meter/CAN DTC broadcast) | **Verified (code)** / purpose **inferred** |
| DTC monitors | `0x76A08…0x7EE1C` | ~40 routines reference `0xFFFF9282` and `0xFFFF291C` | **Verified** (refs) |
| Flashed A2UG000B image (`kramar/… (OEM ABS).bin`) | — | dispatch table, xlat table, getters, literal pools, descriptor table and collector are **byte-identical** to A2UG000K | **Verified** |

Raw RAM `0xFFFF9282…`/`0xFFFF291C…` is **not** the way to read these. Raw `0xFFxxxx` via `A8` is refused (NRC `0x12`) in the default session. Use the SSM addresses above, which the ECU translates itself.

## 5. Why `dtc-can` timed out

- `orchestrator::read_dtcs` (`tuneforge-kernel/src/orchestrator.rs:283`) runs Mode `03`, then `07`, then `0A`, and **returns the first error with `?`**. A timeout on any one mode throws away the others, including a successful Mode 03. **Verified (source).**
- Mode `0A` (permanent DTCs) postdates a 2006 ECU and is a likely culprit. It is also possible that this JDM ECU does not implement generic OBD-II DTC services at all. The ROM does accept `0x7DF`/`0x7E0` (`work/CAN_TX_TRACE_C1AD3.md`). **Not determined.** Which mode timed out is not known from the information available.

## 6. Not determined

- Whether "TMP" (`0xFFFF9282`) is *current-cycle* and "MEM" (`0xFFFF291C`) is *stored/CEL-lit*: this is RomRaider's convention only, and the monitor logic was not traced.
- Whether bits persist across key-off (depends on ECU backup-RAM supply). Not traced.
- How the `(Pxxxx)` enable switches gate the bits (presumably a disabled DTC never sets). In the flashed A2UG000B image, 28 engine DTCs are switched off (rear O2 P0037/P0038/P0140, secondary air, TGV P2004–P2022, purge P0458/P0459). For 106 records the def has no switch entry. A clean read therefore does **not** clear those systems.
- Whether the ECU answers `A8` for these addresses in practice. This is very likely, because it is the same dispatch path that serves the logged params, but it has not been run.

## 7. Bit map — authoritative for this ROM

Generated from the ROM descriptor table `0x734E0` (flashed A2UG000B image) and cross-checked 1:1 against RomRaider v370 `<dtcodes>`. Enable state comes from `Legacy GT/A2UG000B.xml` switch addresses read in the flashed image.

Immobilizer byte (RomRaider only; served by separate getters): `0xAB`/`0xCB` bit0 P1577, bit1 P1576, bit2 P0513, bit3 P1574, bit4 P1578, bit5 P1572, bit6 P1571, bit7 P1570. `0x174`/`0x17B` (P1579) always reads 0 on this ROM.

| SSM tmp | SSM mem | bit | DTC | Description (RomRaider) | Enable switch in flashed A2UG000B image |
|---|---|---|---|---|---|
| 0x00008E | 0x0000AE | 0 | P0335 | Crankshaft Pos. Sensor A Malfunction | enabled |
| 0x00008E | 0x0000AE | 2 | P0336 | Crankshaft Pos. Sensor A Range/Perf | no switch in def |
| 0x00008E | 0x0000AE | 3 | P0341 | Camshaft Pos. Sensor A Range/Perf | no switch in def |
| 0x00008E | 0x0000AE | 4 | P0340 | Camshaft Pos. Sensor A Malfunction | enabled |
| 0x00008E | 0x0000AE | 6 | P0604 | Control Module Ram Error | enabled |
| 0x00008F | 0x0000AF | 0 | P0102 | Maf Sensor Low Input | enabled |
| 0x00008F | 0x0000AF | 1 | P0103 | Maf Sensor High Input | enabled |
| 0x00008F | 0x0000AF | 4 | P0500 | Vehicle Speed Sensor A | enabled |
| 0x00008F | 0x0000AF | 6 | P0332 | Knock Sensor 2 Low Input | no switch in def |
| 0x00008F | 0x0000AF | 7 | P0333 | Knock Sensor 2 High Input | no switch in def |
| 0x000090 | 0x0000B0 | 2 | P0327 | Knock Sensor 1 Low Input | enabled |
| 0x000090 | 0x0000B0 | 3 | P0328 | Knock Sensor 1 High Input | enabled |
| 0x000090 | 0x0000B0 | 4 | P0122 | Tps A Low Input | enabled |
| 0x000090 | 0x0000B0 | 5 | P0123 | Tps A High Input | enabled |
| 0x000091 | 0x0000B1 | 0 | P0117 | Coolant Temp Sensor Low Input | enabled |
| 0x000091 | 0x0000B1 | 1 | P0118 | Coolant Temp Sensor High Input | enabled |
| 0x000091 | 0x0000B1 | 2 | P0464 | Fuel Level Sensor Intermittent | no switch in def |
| 0x000091 | 0x0000B1 | 3 | P0125 | Insufficient Coolant Temp (Fueling) | no switch in def |
| 0x000091 | 0x0000B1 | 4 | P0462 | Fuel Level Sensor Low Input | enabled |
| 0x000091 | 0x0000B1 | 5 | P0463 | Fuel Level Sensor High Input | enabled |
| 0x000091 | 0x0000B1 | 6 | P0461 | Fuel Level Sensor Range/Perf | no switch in def |
| 0x000092 | 0x0000B2 | 5 | P0350 | Ignition Coil Primary/Secondary | no switch in def |
| 0x000092 | 0x0000B2 | 6 | P1518 | Starter Switch Low Input | enabled |
| 0x000092 | 0x0000B2 | 7 | P0512 | Starter Request Circuit | enabled |
| 0x000093 | 0x0000B3 | 0 | P0452 | Evap Pressure Sensor Low Input | no switch in def |
| 0x000093 | 0x0000B3 | 1 | P0453 | Evap Pressure Sensor High Input | no switch in def |
| 0x000093 | 0x0000B3 | 3 | P0451 | Evap Pressure Sensor Range/Perf | no switch in def |
| 0x000094 | 0x0000B4 | 3 | P0851 | Neutral Switch Input Low | enabled |
| 0x000094 | 0x0000B4 | 4 | P0182 | Fuel Temp Sensor A Low Input | no switch in def |
| 0x000094 | 0x0000B4 | 5 | P0183 | Fuel Temp Sensor A High Input | no switch in def |
| 0x000094 | 0x0000B4 | 6 | P0181 | Fuel Temp Sensor A Range/Perf | no switch in def |
| 0x000094 | 0x0000B4 | 7 | P0852 | Neutral Switch Input High | enabled |
| 0x000096 | 0x0000B6 | 0 | P1492 | Egr Solenoid Signal 1 Malfunction (Low) | no switch in def |
| 0x000096 | 0x0000B6 | 1 | P1493 | Egr Solenoid Signal 1 Malfunction (High) | no switch in def |
| 0x000096 | 0x0000B6 | 2 | P1494 | Egr Solenoid Signal 2 Malfunction (Low) | no switch in def |
| 0x000096 | 0x0000B6 | 3 | P1495 | Egr Solenoid Signal 2 Malfunction (High) | no switch in def |
| 0x000096 | 0x0000B6 | 4 | P1496 | Egr Signal 3 Circuit Low | no switch in def |
| 0x000096 | 0x0000B6 | 5 | P1497 | Egr Solenoid Signal 3 Malfunction (High) | no switch in def |
| 0x000096 | 0x0000B6 | 6 | P1498 | Egr Signal 4 Circuit Low | no switch in def |
| 0x000096 | 0x0000B6 | 7 | P1499 | Egr Signal 4 Circuit High | no switch in def |
| 0x000098 | 0x0000B8 | 3 | P0506 | Idle Control Rpm Lower Than Expected | no switch in def |
| 0x000098 | 0x0000B8 | 4 | P0507 | Idle Control Rpm High Than Expected | no switch in def |
| 0x000099 | 0x0000B9 | 2 | P0691 | Radiator Fan Circuit Low | no switch in def |
| 0x000099 | 0x0000B9 | 3 | P0692 | Radiator Fan Circuit High | no switch in def |
| 0x000099 | 0x0000B9 | 6 | P0483 | Radiator Fan Rationality Check | no switch in def |
| 0x00009A | 0x0000BA | 2 | P0011 | Camshaft Pos. - Timing Over-Advanced 1 | no switch in def |
| 0x00009A | 0x0000BA | 3 | P0021 | Camshaft Pos. - Timing Over-Advanced 2 | no switch in def |
| 0x00009A | 0x0000BA | 4 | P1400 | Fuel Tank Pressure Sol. Low | no switch in def |
| 0x00009A | 0x0000BA | 5 | P1420 | Fuel Tank Pressure Sol. High Input | no switch in def |
| 0x00009A | 0x0000BA | 6 | P0458 | Evap Purge Valve Circuit Low | **DISABLED** |
| 0x00009A | 0x0000BA | 7 | P0459 | Evap Purge Valve Circuit High | **DISABLED** |
| 0x00009B | 0x0000BB | 2 | P1443 | Vent Control Solenoid Function Problem | no switch in def |
| 0x00009B | 0x0000BB | 6 | P0447 | Evap Vent Control Circuit Open | no switch in def |
| 0x00009B | 0x0000BB | 7 | P0448 | Evap Vent Control Circuit Shorted | no switch in def |
| 0x00009F | 0x0000BF | 0 | P0133 | Front O2 Sensor Slow Response | no switch in def |
| 0x00009F | 0x0000BF | 2 | P0139 | Rear O2 Sensor Slow Response | no switch in def |
| 0x00009F | 0x0000BF | 4 | P1152 | Front O2 Sensor Range/Perf Low B1 S1 | no switch in def |
| 0x00009F | 0x0000BF | 5 | P1153 | Front O2 Sensor Range/Perf High B1 S1 | no switch in def |
| 0x0000A0 | 0x0000C0 | 0 | P0420 | Cat Efficiency Below Threshold | no switch in def |
| 0x0000A0 | 0x0000C0 | 1 | P0442 | Evap Leak Detected (Small) | no switch in def |
| 0x0000A0 | 0x0000C0 | 3 | P0456 | Evap Leak Detected (Very Small) | no switch in def |
| 0x0000A0 | 0x0000C0 | 4 | P0400 | Egr Flow | no switch in def |
| 0x0000A1 | 0x0000C1 | 0 | P0301 | Misfire Cylinder 1 | enabled |
| 0x0000A1 | 0x0000C1 | 1 | P0302 | Misfire Cylinder 2 | enabled |
| 0x0000A1 | 0x0000C1 | 2 | P0303 | Misfire Cylinder 3 | enabled |
| 0x0000A1 | 0x0000C1 | 3 | P0304 | Misfire Cylinder 4 | enabled |
| 0x0000A1 | 0x0000C1 | 4 | P0305 | Misfire Cylinder 5 | no switch in def |
| 0x0000A1 | 0x0000C1 | 5 | P0306 | Misfire Cylinder 6 | no switch in def |
| 0x0000A1 | 0x0000C1 | 7 | P0457 | Evap Leak Detected (Fuel Cap) | no switch in def |
| 0x0000A3 | 0x0000C3 | 0 | P0137 | Rear O2 Sensor Low Voltage | no switch in def |
| 0x0000A3 | 0x0000C3 | 2 | P0131 | Front O2 Sensor Low Input | enabled |
| 0x0000A3 | 0x0000C3 | 3 | P0151 | O2 Sensor Circuit Low B2 S1 | no switch in def |
| 0x0000A3 | 0x0000C3 | 4 | P0132 | Front O2 Sensor High Input | enabled |
| 0x0000A3 | 0x0000C3 | 5 | P0152 | O2 Sensor Circuit High B2 S1 | no switch in def |
| 0x0000A3 | 0x0000C3 | 6 | P0138 | Rear O2 Sensor High Voltage | no switch in def |
| 0x0000A3 | 0x0000C3 | 7 | P0153 | O2 Sensor Circuit Slow Response B2 S1 | no switch in def |
| 0x0000A4 | 0x0000C4 | 0 | P0112 | Iat Sensor Low Input | enabled |
| 0x0000A4 | 0x0000C4 | 1 | P0113 | Iat Sensor High Input | enabled |
| 0x0000A4 | 0x0000C4 | 2 | P0111 | Iat Sensor Range/Perf | no switch in def |
| 0x0000A4 | 0x0000C4 | 4 | P0038 | Rear O2 Sensor High Input | **DISABLED** |
| 0x0000A4 | 0x0000C4 | 5 | P0032 | Front O2 Sensor High Input | enabled |
| 0x0000A4 | 0x0000C4 | 6 | P0037 | Rear O2 Sensor Low Input | **DISABLED** |
| 0x0000A4 | 0x0000C4 | 7 | P0031 | Front O2 Sensor Low Input | enabled |
| 0x0000A5 | 0x0000C5 | 4 | P0107 | Map Sensor Low Input | enabled |
| 0x0000A5 | 0x0000C5 | 5 | P0108 | Map Sensor High Input | enabled |
| 0x0000A7 | 0x0000C7 | 4 | P1154 | O2 Sensor Range/Perf Low B2 S1 | no switch in def |
| 0x0000A7 | 0x0000C7 | 5 | P1155 | O2 Sensor Range/Perf High B2 S1 | no switch in def |
| 0x0000A7 | 0x0000C7 | 6 | P0052 | Ho2S Circuit High B2 S1 | no switch in def |
| 0x0000A7 | 0x0000C7 | 7 | P0051 | Ho2S Circuit Low B2 S1 | no switch in def |
| 0x0000A8 | 0x0000C8 | 0 | P0128 | Thermostat Malfunction | no switch in def |
| 0x0000A8 | 0x0000C8 | 1 | P1491 | Pcv (Blowby) Function Problem | no switch in def |
| 0x0000A9 | 0x0000C9 | 3 | P1560 | Back-Up Voltage Malfunction | enabled |
| 0x0000A9 | 0x0000C9 | 6 | P0562 | System Voltage (Low) | enabled |
| 0x0000A9 | 0x0000C9 | 7 | P0563 | System Voltage (High) | enabled |
| 0x0000AA | 0x0000CA | 0 | P0245 | Wastegate Solenoid A Low | enabled |
| 0x0000AA | 0x0000CA | 1 | P0246 | Wastegate Solenoid A High | enabled |
| 0x0000AA | 0x0000CA | 3 | P0244 | Wastegate Solenoid A Range/Perf (High) | no switch in def |
| 0x0000AC | 0x0000CC | 4 | P0261 | Fuel Injector #1 Circuit Low | no switch in def |
| 0x0000AC | 0x0000CC | 5 | P0264 | Fuel Injector #2 Circuit Low | no switch in def |
| 0x0000AC | 0x0000CC | 6 | P0267 | Fuel Injector #3 Circuit Low | no switch in def |
| 0x0000AC | 0x0000CC | 7 | P0270 | Fuel Injector #4 Circuit Low | no switch in def |
| 0x0000AD | 0x0000CD | 0 | P0545 | Egt Sensor Circuit Low | no switch in def |
| 0x0000AD | 0x0000CD | 1 | P0546 | Egt Sensor Circuit High | no switch in def |
| 0x0000AD | 0x0000CD | 2 | P1312 | Egt Sensor Malfunction | no switch in def |
| 0x0000AD | 0x0000CD | 3 | P1544 | Egt Too High | no switch in def |
| 0x000126 | 0x00012E | 0 | P0502 | Vehicle Speed Sensor Low Input | no switch in def |
| 0x000126 | 0x00012E | 1 | P0230 | Fuel Pump Primary Circuit | enabled |
| 0x000126 | 0x00012E | 3 | P0068 | Map Sensor Range/Perf | no switch in def |
| 0x000126 | 0x00012E | 5 | P0519 | Idle Control Malfunction (Fail-Safe) | enabled |
| 0x000126 | 0x00012E | 7 | P0101 | Maf Sensor Range/Perf | no switch in def |
| 0x000127 | 0x00012F | 0 | P0154 | O2 Sensor Circuit Open B2 S1 | no switch in def |
| 0x000127 | 0x00012F | 1 | P0134 | Front O2 Sensor No Activity | enabled |
| 0x000127 | 0x00012F | 4 | P0050 | O2 Sensor Heater Circuit Range/Perf B2 S1 | no switch in def |
| 0x000127 | 0x00012F | 5 | P0030 | O2 Sensor Heater Circuit Range/Perf B1 S1 | no switch in def |
| 0x000127 | 0x00012F | 7 | P0503 | Vehicle Speed Sensor Malfunction At High Speed | no switch in def |
| 0x000128 | 0x000130 | 3 | P0159 | O2 Sensor Circuit Slow Response B2 S2 | no switch in def |
| 0x000129 | 0x000131 | 0 | P0057 | Ho2S Heater Circuit (Low) B2 S2 | no switch in def |
| 0x000129 | 0x000131 | 1 | P0058 | Ho2S Heater Circuit (High) B2 S2 | no switch in def |
| 0x000129 | 0x000131 | 4 | P0157 | O2 Sensor Circuit (Low) Voltage B2 S2 | no switch in def |
| 0x000129 | 0x000131 | 5 | P0158 | O2 Sensor Circuit (High) Voltage B2 S2 | no switch in def |
| 0x00012A | 0x000132 | 0 | P2109 | Tps A Minimum Stop Perf | enabled |
| 0x000150 | 0x000155 | 0 | P0222 | Tps B (Low) Input | enabled |
| 0x000150 | 0x000155 | 1 | P0223 | Tps B (High) Input | enabled |
| 0x000150 | 0x000155 | 2 | P1160 | Abnormal Return Spring | enabled |
| 0x000150 | 0x000155 | 3 | P2102 | Throttle Actuator Circuit Low | enabled |
| 0x000150 | 0x000155 | 4 | P2103 | Throttle Actuator Circuit High | enabled |
| 0x000150 | 0x000155 | 5 | P2101 | Throttle Actuator Circuit Range/Perf | enabled |
| 0x000150 | 0x000155 | 7 | P0638 | Throttle Actuator Range/Perf | enabled |
| 0x000151 | 0x000156 | 0 | P0607 | Control Module Performance | enabled |
| 0x000151 | 0x000156 | 1 | P2138 | Tps D/E Voltage | enabled |
| 0x000151 | 0x000156 | 2 | P2127 | Tps E Circuit Low Input | enabled |
| 0x000151 | 0x000156 | 3 | P2128 | Tps E Circuit High Input | enabled |
| 0x000151 | 0x000156 | 4 | P2122 | Tps D Circuit Low Input | enabled |
| 0x000151 | 0x000156 | 5 | P2123 | Tps D Circuit High Input | enabled |
| 0x000151 | 0x000156 | 6 | P2135 | Tps A/B Voltage | enabled |
| 0x000152 | 0x000157 | 0 | P0600 | Serial Communication Link | enabled |
| 0x000152 | 0x000157 | 1 | P0390 | Camshaft Pos. Sensor B Bank 2 | enabled |
| 0x000152 | 0x000157 | 2 | P0365 | Camshaft Pos. Sensor B Bank 1 | enabled |
| 0x000152 | 0x000157 | 3 | P0345 | Camshaft Pos. Sensor A Bank 2 | enabled |
| 0x000152 | 0x000157 | 4 | P0340 | Camshaft Pos. Sensor A Malfunction | enabled |
| 0x000152 | 0x000157 | 5 | P0605 | Control Module Rom Error | enabled |
| 0x000153 | 0x000158 | 0 | P2095 | Ocv Solenoid B2 Circuit Short | enabled |
| 0x000153 | 0x000158 | 1 | P2094 | Ocv Solenoid B2 Circuit Open | enabled |
| 0x000153 | 0x000158 | 2 | P2091 | Ocv Solenoid B1 Circuit Short | enabled |
| 0x000153 | 0x000158 | 3 | P2090 | Ocv Solenoid B1 Circuit Open | enabled |
| 0x000153 | 0x000158 | 4 | P2093 | Ocv Solenoid A2 Circuit Short | enabled |
| 0x000153 | 0x000158 | 5 | P2092 | Ocv Solenoid A2 Circuit Open | enabled |
| 0x000153 | 0x000158 | 6 | P2089 | Ocv Solenoid A1 Circuit Short | enabled |
| 0x000153 | 0x000158 | 7 | P2088 | Ocv Solenoid A1 Circuit Open | enabled |
| 0x000154 | 0x000159 | 0 | P0197 | Oil Temp Sensor Low | no switch in def |
| 0x000154 | 0x000159 | 7 | P0700 | Transmission Control System | enabled |
| 0x000160 | 0x000165 | 0 | P0028 | Osv Solenoid Valve Circuit Range/Perf B2 | no switch in def |
| 0x000160 | 0x000165 | 1 | P0083 | Intake Valve Control High (Bank 2) | no switch in def |
| 0x000160 | 0x000165 | 2 | P0082 | Intake Valve Control Low (Bank 2) | no switch in def |
| 0x000160 | 0x000165 | 3 | P0026 | Osv Solenoid Valve Circuit Range/Perf B1 | no switch in def |
| 0x000160 | 0x000165 | 4 | P0077 | Intake Valve Control High (Bank 1) | no switch in def |
| 0x000160 | 0x000165 | 5 | P0076 | Intake Valve Circuit Low (Bank 1) | no switch in def |
| 0x000160 | 0x000165 | 6 | P0196 | Oil Temp Sensor Range/Perf | no switch in def |
| 0x000160 | 0x000165 | 7 | P0198 | Oil Temp Sensor High | no switch in def |
| 0x000161 | 0x000166 | 2 | P2504 | Charging System Voltage High | no switch in def |
| 0x000161 | 0x000166 | 3 | P2503 | Charging System Voltage Low | no switch in def |
| 0x000163 | 0x000168 | 0 | P2004 | Tgv - Intake Manifold Runner 1 Stuck Open | **DISABLED** |
| 0x000163 | 0x000168 | 1 | P2006 | Tgv - Intake Manifold Runner 1 Stuck Closed | **DISABLED** |
| 0x000163 | 0x000168 | 2 | P2005 | Tgv - Intake Manifold Runner 2 Stuck Open | **DISABLED** |
| 0x000163 | 0x000168 | 3 | P2007 | Tgv - Intake Manifold Runner 2 Stuck Closed | **DISABLED** |
| 0x000163 | 0x000168 | 4 | P2227 | Baro. Pressure Circuit Range/Perf | no switch in def |
| 0x000163 | 0x000168 | 5 | P0126 | Insufficient Coolant Temp (Operation) | no switch in def |
| 0x000163 | 0x000168 | 6 | P2229 | Baro. Pressure Circuit High Input | no switch in def |
| 0x000163 | 0x000168 | 7 | P2228 | Baro. Pressure Circuit Low Input | no switch in def |
| 0x000164 | 0x000169 | 0 | P2016 | Tgv - Intake Manifold Runner 1 Pos. Sensor Low | **DISABLED** |
| 0x000164 | 0x000169 | 1 | P2017 | Tgv - Intake Manifold Runner 1 Pos. Sensor High | **DISABLED** |
| 0x000164 | 0x000169 | 2 | P2021 | Tgv - Intake Manifold Runner 2 Pos. Sensor Low | **DISABLED** |
| 0x000164 | 0x000169 | 3 | P2022 | Tgv - Intake Manifold Runner 2 Pos. Sensor High | **DISABLED** |
| 0x000164 | 0x000169 | 4 | P2009 | Tgv - Intake Manifold Runner 1 Circuit Low | **DISABLED** |
| 0x000164 | 0x000169 | 5 | P2012 | Tgv - Intake Manifold Runner 2 Circuit Low | **DISABLED** |
| 0x000164 | 0x000169 | 6 | P2008 | Tgv - Intake Manifold Runner 1 Circuit Open | **DISABLED** |
| 0x000164 | 0x000169 | 7 | P2011 | Tgv - Intake Manifold Runner 2 Circuit Open | **DISABLED** |
| 0x000176 | 0x00017D | 0 | P2444 | Secondary Air Pump 1 Stuck On B1 | **DISABLED** |
| 0x000176 | 0x00017D | 1 | P0411 | Secondary Air Pump Incorrect Flow | no switch in def |
| 0x000176 | 0x00017D | 2 | P0410 | Secondary Air Pump System | **DISABLED** |
| 0x000176 | 0x00017D | 3 | P2431 | Secondary Air Pump Circuit Range/Perf | no switch in def |
| 0x000176 | 0x00017D | 4 | P2433 | Secondary Air Pump Circuit High | **DISABLED** |
| 0x000176 | 0x00017D | 5 | P2432 | Secondary Air Pump Circuit Low | **DISABLED** |
| 0x000176 | 0x00017D | 6 | P0413 | Secondary Air Pump A Open | **DISABLED** |
| 0x000176 | 0x00017D | 7 | P0418 | Secondary Air Pump Relay A | **DISABLED** |
| 0x000177 | 0x00017E | 0 | P0140 | O2 Sensor Circuit Range/Perf B1 S2 | **DISABLED** |
| 0x000177 | 0x00017E | 1 | P0160 | O2 Sensor Circuit Range/Perf B2 S2 | no switch in def |
| 0x000177 | 0x00017E | 3 | P1602 | Control Module Programming Error | no switch in def |
| 0x000177 | 0x00017E | 4 | P0414 | Secondary Air Pump A Shorted | **DISABLED** |
| 0x000177 | 0x00017E | 5 | P1418 | Secondary Air Pump Circuit Shorted | **DISABLED** |
| 0x000177 | 0x00017E | 6 | P0018 | Crankshaft/Camshaft Correlation 2A | no switch in def |
| 0x000177 | 0x00017E | 7 | P0016 | Crankshaft/Camshaft Correlation 1A | no switch in def |
| 0x000178 | 0x00017F | 1 | P1410 | Secondary Air Pump Valve Stuck Open | **DISABLED** |
| 0x000178 | 0x00017F | 2 | P2443 | Secondary Air Pump 2 Stuck Closed | no switch in def |
| 0x000178 | 0x00017F | 3 | P2442 | Secondary Air Pump Valve 2 Stuck Open | no switch in def |
| 0x000178 | 0x00017F | 4 | P2441 | Secondary Air Pump Valve 1 Stuck Closed | **DISABLED** |
| 0x000178 | 0x00017F | 5 | P2440 | Secondary Air Pump Valve 1 Stuck Open | **DISABLED** |
| 0x000178 | 0x00017F | 6 | P0417 | Secondary Air Pump B Shorted | no switch in def |
| 0x000178 | 0x00017F | 7 | P0416 | Secondary Air Pump B Open | no switch in def |
| 0x000179 | 0x000180 | 5 | P0441 | Evap Incorrect Purge Flow | no switch in def |
| 0x000179 | 0x000180 | 6 | P2419 | Evap Switching Valve Low | no switch in def |
| 0x000179 | 0x000180 | 7 | P2420 | Evap Switching Valve High | no switch in def |
