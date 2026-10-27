# ABS / VDC research — why the old ROM had working ABS

Written 2026-10-22. Question: the owner's old ROM made ABS/ESP work on a diesel-parts car. The tuner's `(OEM ABS)` file does not.
What changed? Everything below is from the ROM files, the project's disassembly (`re/`), and one saved web page.

## Files compared

| Tag | File | ID @0x2000 |
|---|---|---|
| A | `read_image_2026-08-25_16h39m11s.bin` (car's old dump) | A2UG000K 24UDOM_6MT |
| B | `kramar/... (DIESEL ABS).bin` (A + tuner's maps) | A2UG000K |
| C | `kramar/... (OEM ABS).bin` (currently flashed; ABS/ESP dead) | A2UG000B 24UDOM_5MT |
| R | `roms/reference/STOCK_A2UG000K_reference.bin` | A2UG000K |

The car: 2006 JDM Legacy GT, EJ20Y with a **5-speed diesel-model gearbox** (owner-stated; the logs show five gears matching neither stock gearbox).

## Findings

1. **No code was patched.** A and B equal stock A2UG000K in every instruction byte. Differences are calibration tables, 28 DTC enable switches
   (EVAP, rear O2, TGV, secondary air; C has the same 28), and a wastegate-duty-limit float at `0x1802C` (0% in A/B, 90% in C and stock).
2. **C is a different ROM family** (A2UG000B). Its ~35,000 byte differences from B are factory pointer shifts and 172 calibration regions, not a tuner patch. Code is identical apart from literal-pool pointers.
3. **Gear/speed calibration:** stock K and B tables for gear thresholds, speed limits, CL delays are identical. The ECU stores no gear ratios. It estimates gear from speed/RPM. A changed none of it.
4. **The only unexplained non-map edit in A:** `0xC1AD2/0xC1AD3` = `02 22` → `A2 A2`. Not covered by the RomRaider or ECUFlash definitions of A2UG000K or A2UG000B.
5. **Where it goes** (`work/CAN_TX_TRACE_C1AD3.md`): `0x1B8DC` → RAM `0xFFFF65ED` → byte 5 of frame ID `0x600` built at `0x1A58C`, sent through the on-chip CAN controller (send routine `0xD66C`, record at `0x5A138`, mailbox 8, standard 11-bit, ~50 ms, probably 500 kbit/s). The ECU never reads the byte back.
6. **Public data point:** the subdiesel "CAN Messages" page (saved at `work/subdiesel_can_page.txt`, MY10 Impreza 2.0 diesel, marked "Draft, expect errors") lists ECU frame `0x600` byte 5 as "const 0xA2 (from data segment)", coolant temp, lamps and clutch switch in the other bytes. The reader of `0x600` is blank on that page. ABS/VDC sends `0x501/0x512/0x513`; BIU sends `0x514/0x620`.
7. **Owner-reported symptoms** match: stock `0x22` (file C) → ABS light on, ABS/ESP dead. `0xA2` (file A) → no light, ESP works.

## Conclusion and test

Hypothesis: the ABS/VDC unit (or something it depends on) expects the diesel value in frame `0x600` byte 5 and disables itself otherwise.
Test: file C with only `0xC1AD2/3` set to `0xA2` → `kramar/... (OEM ABS WITH 2 BYTE FIX).bin` (see its README). **Not flashed, not tested.**

## Open questions

- Who receives frame `0x600`, and what bit 7 means. A listen-only CAN capture shows the traffic but not how a receiver interprets it.
- Why the ESP on/off lamp did not show state with the old ROM (probably a different frame).
- Why the previous tuner wrote `A2` in both `0xC1AD2` and `0xC1AD3` (the second is the unused automatic path on this ROM).
- Whether the hardware needs anything beyond this byte (ABS module coding, wiring).

## Side findings (not about ABS, recorded so they are not lost)

- **Boost table sets.** The ROM has two complete sets. With `0xC2D80 = 0x55` (all files here) the flag `0xFFFF6CDB` is 1 (manual) and the ECU reads **set 2**: target boost `0xC18D0`, initial WGDC `0xC1410`, max WGDC `0xC0FA0`. Set 1 (`0xC1650`/`0xC11D8`/`0xC0D68`) is not read. The A2UG000K definition names only set 1, so tuning from it lands in unused tables. File C's boost edits are in set 2; file B's are in set 1; set 2 in B is the previous tuner's leftover (17.42 psi peak).
- **Gear detection** is wrong for this gearbox (2nd–4th misread). Candidate threshold values from the logs were derived but not applied. Per-gear features are zero in every file, so the effect is currently small.
- Rev limit in B/C is 7500/7300 (stock), up from the break-in 3900/3700 in A.

## Earlier statements that were wrong (corrected here)

- "Set 2 is the automatic boost set" — wrong; flag 1 means manual (gear computed from speed/RPM).
- "Revert `0xC1AD2/3` to stock" — withdrawn; that likely removes the ABS fix.
- "The diesel gearbox needs the 5MT family" — the gear count byte `0xC1AD1` differs (6 vs 5) but it is not known to matter for ABS.

## Addendum 2026-10-22 — Subaru service manual evidence (MT/AT variants, VDC spec check)

Sources: Subaru FSM 2006 and 2008 Legacy/Outback (BL/BP), 2008 Impreza WRX/STI, VDC(diag) and LAN(diag) chapters (hosted at jdmfsm.info);
subdiesel "CAN Messages" 2011 and 2015 revisions; RomRaider threads t=7951 and t=17059. Labels: V = verified from the cited text, I = inferred.

- **V:** ABS/VDC units are transmission-specific. 2008 BL/BP VDC identification mark: AT = T3/T7, MT = T4. ABS-only: AT = J9/JB, MT = JA/JE.
- **V:** The VDC unit compares its specification with the ECM's. DTC **C0045 "Incorrect VDC control module specifications"**, symptom "ABS does not operate. VDC does not operate." The procedure ends in "CHECK ECM SPECIFICATION ... replace the ECM".
- **V:** Other VDC codes with the same symptom: C0044 (no CAN signal from TCM), C0057 (no CAN signal from ECM), C0047 (CAN line fault), C0041 (parameter selection, 2008+ units).
- **V:** The body control unit lists CAN inputs for number of cylinders, SOHC/DOHC, turbo, 2.5 L, 3.0 L and **AT/MT Model ID signal**. The sender is not named in the table.
- **I (strong):** frame `0x600` byte 5 is the only static calibration byte in an ECU transmit frame, and its bit 5 follows the ECU's transmission selector, so bit 5 = AT/MT.
- **I (weak):** bit 7 is the only difference between the petrol MT value `0x22` and the diesel `0xA2`. No listed petrol flag explains it, so an engine-family flag is the best guess.
- **V:** no public source decodes the bits of byte 5. Both subdiesel revisions say only "const 0xA2".
- **V:** on this ROM only `0xC1AD3` is ever sent, because the selector flag is 1. `0xC1AD2` is the other path.

### Cheap checks, no flash
1. Read the VDC fault codes from the dash with the currently flashed ROM (2005-09 Legacy/Outback procedure: key on, headlights on within 3 s, then Trip/Odo presses). C0045 supports the byte theory. C0044 suggests an AT-spec unit. C0057/C0047 point elsewhere.
2. Note the VDC unit's identification mark and part number. Dismantlers list 27536AG250 for the 2008-09 2.0D (weak source).
3. FreeSSM cannot read the VDC/ABS unit; it covers engine and transmission only.

### Open
- Whether the VDC unit or the body control unit consumes the byte.
- The 0x601 and 0x412 frame builders have not been checked for further calibration constants.
- The ESP-off lamp may be a separate frame (the 2015 subdiesel revision lists a VDC switch bit in frame `0x512`).

## Result 2026-10-22 — VDC fault codes read with Subaru Select Monitor III (SDI cable) while `(OEM ABS)` is flashed

All three are current (not stored history). Photo from the owner; screen is in Russian.

| Code | Screen text (translated) | Detail value |
|---|---|---|
| C0072 | Yaw rate sensor communication | `1EBF` |
| C0047 | CAN communication line malfunction | `1504` |
| C0076 | Clutch signal | `2620` |

- **C0045 ("different VDC specification") is NOT present.** The simple "spec mismatch" reading of the byte theory is not confirmed by these codes.
- The detail values are not decoded here.
- Frame `0x600` byte 6 bit 2 is the clutch switch on the diesel ECU (subdiesel page). This ROM never sets that bit. That is a lead for C0076, not a finding. The old ROM used the same code and ABS worked, so something else must differ.
- The owner's SSM3 can read the VDC and, presumably, the body control unit. The body control unit's data list contains the CAN-received spec rows (cylinders, SOHC/DOHC, turbo, displacement, AT/MT model ID). Comparing those rows between the two ROMs would decode what byte 5 changes.

## Owner-stated hardware (2026-10-22)

- The ECU on the car is the same physical unit the old ROM ran on (owner confirmed). Only the firmware changed between "ABS works" and "ABS dead".
- ABS/VDC module is from a **diesel** car. ECU is a **petrol spec.B ECU from a JDM car** (owner: "I think", not verified from part numbers).
- Consequence: the diesel VDC unit expects to see a diesel-style ECU on the bus. The old ROM made the petrol ECU's frame `0x600` byte 5 match the diesel value. Whether other frames (clutch bit, torque scaling in `0x410`) matter is being checked, see `work/CAN_TX_OLD_VS_CURRENT.md` when it exists.
- Pending owner checks (no flash): details screen for each VDC code, OBD pins 6-14 resistance, whether SSM3 reads the engine ECU, and codes from the old ROM era if any exist.

**Caveat (owner, 2026-10-22):** the owner cannot confirm whether C0072, C0047 and C0076 were already present with the old ROM. They may predate the firmware change. Do not read them as caused by `(OEM ABS)`. The only established difference between the two states is behaviour: old ROM, ABS and ESP work and no ABS light; flashed ROM, ABS light on and ABS/ESP dead.
Plan consequence: save the current codes (SSM3 F9 Save, or a photo with the detail values) as the baseline before any flash, then re-read after the two-byte file. Codes that survive the flash are not explained by byte 5.

## Result 2026-10-22 — the byte is a vehicle-spec bitfield (cross-ROM decode)

From 212 public stock ROMs (`work/CROSS_ROM_CAN600_BYTE.md`, data in `tmp/xrom/rows.csv`). Bits of `0x600` byte 5: bit 0 = 3.0 L, bit 1 = DOHC, bit 2 = non-turbo, bit 3 = 2.5 L, bit 4 = six cylinders, bit 5 = manual, bit 6 = never seen, **bit 7 = diesel**. These match the six spec signals the service manual lists as CAN inputs, plus the diesel bit. All 5 public diesel ECU images send exactly `0xA2` from one constant. No petrol ROM sets bit 7.
- `0xA2` = diesel, manual, 2.0 L DOHC turbo (the donor ABS unit's car). `0x22` = petrol, manual, 2.0 L DOHC turbo.
- Writing `A2` into `0xC1AD2` too has no effect on this car (flag `0xC2D80` = `0x55` selects the manual path).
- Still unproven: that the VDC unit reads the byte. C0045 (VDC specification mismatch) was not in the codes read; the three codes were C0072, C0047, C0076. 66 ROMs (2010+ BM Legacy, late STI, 2005-07 USDM STI) have no `0x600` record in this form and were not decoded.

## Owner report 2026-10-22 — hydraulic unit swap test

The owner earlier replaced the ABS/VDC hydraulic block with one from a WRX. With "the same ABS flash" (which ROM exactly is not stated yet) the ABS light was on. Open: which ROM was flashed during that test, the WRX unit's year and part number, and whether it was a VDC or ABS-only unit. If the flashed ROM sent `0x22`, a petrol unit failing too weakens the "diesel unit needs the diesel bit" reading and points toward a common cause (wiring, sensors, bus, or other spec bits).

## Result 2026-10-23 — engine ECU fault flags read over SSM-CAN (`work/dtc_read_20261023_093724.txt`)

Read-only `peek-ram-can` blocks per `work/ENGINE_DTC_VIA_SSM_CAN.md`, ignition on, engine off, with `(OEM ABS)` flashed.
- ECU init answered with ID bytes `4B 04 58 50 07` = `4B04585007`, the A2UG000B calibration. This confirms the flashed ROM family.
- **Read OK, all bytes `00`:** stored flags `0xAE-0xCD`, and both groups for `0xF0`, `0x123`, `0x150` (includes P0600 serial communication), `0x160`, `0x174`.
- **Not read:** the current-flags block `0x8E-0xAD`. The first request after the ignition cycle timed out (init timeout plus a Tactrix error frame). It holds, among others, P0500 vehicle speed, P0335/P0340 cam/crank, P0851/P0852 neutral switch as current flags.
- Meaning: no stored engine fault flags among the blocks read, and no P0600 flag. The ECU does not report a communication fault with the VDC/BIU on the bus. A clean read does not cover the 28 DTCs switched off in this ROM or the codes with no switch in the definition.
- Open: whether "memorized" flags equal stored codes, and the current block. Retry only that one block once.

## Correction 2026-10-23 — the ECU may have been replaced

Earlier in this session the owner answered "yes it is" to whether the ECU on the car was the same physical unit the old ROM ran on. On 2026-10-23, asked whether the ECU was replaced since the 29 August flash, the owner answered "it was" (replaced) and suspects it is "not a Denso 7058". These conflict, so neither is relied on until the ECU label is read.
- Evidence it runs a Denso SH7058-family ROM: over SSM-CAN it returned ID bytes `4B 04 58 50 07` (the A2UG000B calibration), so some ECU is running that image.
- The FastECU read attempt on 2026-10-23 failed at the bootloader handshake (kernel ID request got no answer, bootloader entry got no answer). Nothing was written.
- Everything about flash method, kernel and the August read/write only applies to the unit flashed in August.
- Flash of `(OEM ABS WITH 2 BYTE FIX)` is ON HOLD until the ECU part number and maker are known.

## Update 2026-10-23 — cause of the failed bootloader handshake

Owner: the failed read was a weak link (poor physical connection). The handshake failure is therefore not evidence of a different chip. The conflicting answers about whether the ECU was replaced since 29 August are still unresolved. The ECU label (part number, maker) is still unread. Plan: retry the read-only backup once with a solid connection; the flash stays gated on that read succeeding and matching the `(OEM ABS)` image.

## Result 2026-10-23 10:08 — verified backup of the ECU as it is now

`dumps/backup_before_abs_fix_20261023_1008.bin` (copy: `roms/BACKUP_ECU_before_abs_fix_A2UG000B_2026-10-23.bin`, read-only), read with FastECU `cli read` after the connection was fixed.
- sha256 `901a392a…fbd7`: **byte-identical to `(OEM ABS).bin`** (0 differing bytes). Size 1 MiB, ID `A2UG000B`, ECU-ID `4B04585007`, all 14 checksum slots valid.
- The ECU therefore accepted the SH7058 Denso CAN bootloader and kernel and returned its flash. That settles the chip question for the unit now in the car: a Denso SH7058 with the Denso CAN bootloader.
- Difference to `(OEM ABS WITH 2 BYTE FIX).bin`: exactly 5 bytes: `0xC1AD2` 02→A2, `0xC1AD3` 22→A2, and 3 checksum bytes at `0xFFB89-0xFFB8B`.
- This backup is the restore point for the two-byte flash.
