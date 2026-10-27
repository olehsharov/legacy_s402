# Is the ECU now in the car a Denso SH7058? — desk investigation 2026-10-23

Desk-only. Nothing talked to the OpenPort or the car. No project file was changed except this one.
Scratch scripts were written to `/tmp/ecuhwid/` (outside the project).
Labels: **VERIFIED** = checked in bytes, source code or definition files in this repo. **INFERRED** = reasoning or outside knowledge, not checked here.

## Summary

The ECU in the car runs the A2UG000B image byte for byte where we can see it. Its SSM-CAN init reply (`A2 10 0F 4B 04 58 50 07 F3 FA C9 8C 0B 83 FE AC`) is a constant stored at `0xCDAC9` inside that image, so the reply comes straight from the flash contents. Every definition that knows this ID (ECUFlash, RomRaider, FastECU) lists it as a **Denso SH7058** using flash method `subarucan`, with a 1 MiB image. In ECUFlash, `subarucan` appears only on SH7058 entries (292 of 292). The image is 1 MiB of SuperH code with Denso's layout (ID at `0x2000`) and a reset stack pointer of `0xFFFFBFA0`, which sits inside SH7058 RAM. SH-family code cannot run on a different CPU family such as Hitachi's M32R, so "not an SH7058-family Denso unit" is very unlikely. What the data **cannot** do is identify the physical part: the exact chip (SH7058 or SH7058S), the board revision, the Denso part number, or the bootloader in its boot block. Only the label on the ECU, or a successful bootloader or kernel read, can settle those. The failed bootloader handshake does not show that the chip is different. FastECU ran the same steps on the same timing in August and the same ROM code accepted them then. So the likely causes are the car's state at the time of the attempt, a different factory boot block on the replacement unit, or a weak link. Today's log does show link timeouts. A different CPU is the least likely cause.

---

## A. What the ECU's answer and the definitions say

| Finding | Status |
|---|---|
| Today's init reply starts `A2 10 0F` (SSM ID) · `4B 04 58 50 07` (ECU ID) · `F3 FA C9 8C 0B 83 FE AC` (capability bits) — `work/dtc_read_20261023_093724.txt` | VERIFIED (file) |
| The same bytes sit in the A2UG000B image at `0xCDAC9`: `a2 10 0f 4b 04 58 50 07 00 f3 fa c9 8c 0b 83 fe ac` (the ECU skips the `00` pad). Both `kramar/...(OEM ABS).bin` and the public stock `tmp/xrom/dl/JDM__Legacy__A2UG000B-2006-JDM-Legacy-GT.hex` have them | VERIFIED (bytes) |
| The August ROM (A2UG000K, `dumps/after_write.bin`, `roms/reference/STOCK_A2UG000K_reference.bin`) has `a2 10 0f 4b 04 78 50 07 00 f3 fa c9 8c 0b 83 fe` at `0xCDACD`. It differs from today's reply **only** in the 3rd ECU-ID byte (`78` → `58`) | VERIFIED (bytes) |
| So the init reply identifies the **software** (a constant in flash), not the silicon. Any ECU running this image would send it | VERIFIED (mechanism) / the conclusion is INFERRED |
| SSM ID `A2 10 0F` across 337 public ROMs: found only in 12 ROMs, all `SH7058` + `subarucan` (A2PG420A, A2UG000B/K, A2UH000A, A2UI000K, A2TB/A2SB…). Neighbouring IDs `A21002/A21011/A21012` are also SH7058 only. The sample holds no SH7055/SH72531 images (336 of 337 are exactly 1 MiB), so this cannot rule other SSM IDs in or out | VERIFIED (scan) |

ECUFlash definitions (`RomRaider/definitions/SubaruDefs/ECUFlash/subaru standard/`):

| File | xmlid / internalid @0x2000 | ecuid | memmodel | flashmethod | checksum |
|---|---|---|---|---|---|
| `Legacy GT/A2UG000B.xml` | A2UG000B | **4B04585007** | **SH7058** | **subarucan** | subarudbw (06 JDM Legacy GT MT) |
| `Legacy GT spec.B/A2UG000K.xml` | A2UG000K | **4B04785007** | **SH7058** | **subarucan** | subarudbw (06 JDM spec.B MT) |

- The RomRaider `ecu/standard/ecu_defs.xml` (line ~100993) entry for A2UG000B also says `SH7058`, `subarucan`, `<filesize>1024kb</filesize>`. VERIFIED.
- Across ECUFlash defs, the memmodel/flashmethod pairs are: `SH7058 subarucan` 292, `SH7058 sti05` 120, `SH7055 sti04` 73, `68HC16Y5 wrx02/04` 105, `SH72531 subarubrz` 30, `SH7059 subarucand` 1. **`subarucan` never appears with anything other than SH7058.** VERIFIED.
- **No definition says anything other than SH7058 for either ID.** The definitions hold **no Denso part numbers** (`22611…`). The only `22611` string in the repo is in an unrelated `D2WD612A.xml`. So the definitions cannot settle a `22611AR…` versus `22611AQ…` question. VERIFIED.
- FastECU `config/protocols.cfg` maps the alias `subarucan` to `sub_ecu_denso_sh7058_can` ("Denso SH7058 … 2007+ CAN (SH7058S/1MB)", seed/key through the running application). The protocol used in August and today is a **different** one: `sub_ecu_denso_sh7058_densocan` ("SH7058 DensoCAN bootloader", 29-bit `0x000FFFFE`). A third protocol, `sub_ecu_denso_sh7058s_densocan`, uses the same MCU and the same kernel `ssmk_can_sh7058.bin`. VERIFIED.

## B. Sibling ROMs sharing the ID prefix

| ROM | ECU ID | Market / model | memmodel / method | Image size | ID offset |
|---|---|---|---|---|---|
| A2UG000B | 4B04**58**5007 | 06 JDM Legacy GT MT | SH7058 / subarucan | 1 MiB | 0xCDACC |
| A2UG000K | 4B04**78**5007 | 06 JDM Legacy GT spec.B MT | SH7058 / subarucan | 1 MiB | 0xCDAD0 |
| A2UI000K | 4B04785207 | 07 JDM spec.B MT | SH7058 / subarucan | 1 MiB | 0xCDB2C |
| A2UH000A | 4B04505107 | 06 JDM GT AT | SH7058 / subarucan | 1 MiB | 0xCDC2C |
| A2UI000A | 4B04505207 | 07 JDM GT AT | SH7058 / subarucan | (def only) | — |
| A2PG420A | 4B04535107 | 07 JDM GT AT | SH7058 / subarucan | 1 MiB | 0xCE874 |

Every `4B04…` ROM is a 1 MiB, SH7058, `subarucan` image. The only 1 MiB Subaru memory model in FastECU is SH7058 (`kernelmemorymodels.h`: SH7055 = 512 KiB, SH7059 = 1.5 MiB, SH72531 = 1.25 MiB, SH72543 = 2 MiB). VERIFIED.

The tuner's A2UG000B image compared with the public stock A2UG000B: 0 bytes differ in `0x0–0x8000`, 28 in `0x8000–0xC0000`, and 4475 in the calibration. Compared with the August A2UG000K image, it differs in only 2 bytes below `0x8000` (`0x2007` 'K'→'B', and `0x2010`). VERIFIED.

## C. Why the DensoCAN bootloader handshake could fail on an ECU that answers SSM-CAN

What `connect_bootloader()` does (`FastECU/modules/ecu/flash_ecu_subaru_denso_sh705x_densocan.cpp:272-396`, VERIFIED):
1. Over ISO15765 `0x7E0`, it sends a kernel-ID request (`BE EF 00 01 01`) and waits 200 ms plus the long timeout. **No answer is normal** when no kernel is running. It got no answer in August as well.
2. It reopens the link as raw CAN with 29-bit IDs, then sends `00 0F FF FE  FF 86 00…` **1000 times, 3 ms apart (~3 s)**.
3. It sends one `00 0F FF FE  7A 90 …` and expects a reply whose bytes 4–5 are `7A 96`. Anything else gives "No valid response from ECU".
4. The GUI version shows "**Press OK and then turn ignition ON**" between steps 1 and 2 (line 321). That is the author's intended procedure: power the ECU up while the flood is running. `run_headless()` skips that prompt. The CLI asks for "Turn ignition ON, then press ENTER" **before** step 1 (`fastecu_cli.cpp:674`).

August, successful (`dumps/cli_read_.log`): ENTER, then kernel-ID request at 13:33:12.151 → no answer at +1.0 s → "Initializing bootloader" at +2.3 s → check at +5.4 s → connected. Today's quoted failed run had the same shape (kernel ID at t+0, flood at t+1.3 s, check at t+4.4 s → no response). **Same tool, same timing, and the same ROM code** (identical below `0x8000` apart from the ID; the literal `0x000FFFFE` sits at `0x360` and `0x12618` in both images). In August this pattern entered the bootloader with the ignition already ON. VERIFIED (logs, bytes).

Likely explanations, most likely first (all INFERRED):
1. **The car was in a different state from August.** Engine running instead of ignition-on/engine-off, ignition switched on only moments before, or low battery. Denso firmware commonly gates programming entry on engine stopped and vehicle stationary. The car's state during today's attempt is not recorded. This is the cheapest explanation and fits the evidence.
2. **The replacement unit has a different factory boot block or bootloader.** That would be a different hardware revision or part number. The tuner's tool may write only the application and calibration blocks, so the physical ECU's own boot code may not be the one in our image. It might then use another entry method: for example the seed/key `subarucan` path, or a power-up-only window that needs the GUI's "OK, *then* ignition ON" order. Our data cannot show what is in that unit's boot blocks. This explanation is consistent with the owner's report that the ECU was replaced.
3. **Link/bus problem today.** The same morning's SSM-CAN session had Tactrix error frames (`info=9`, plausibly J2534 ERR_TIMEOUT) and init timeouts on the first two runs. The `0x8E` block (current-DTC array) never read. A bus that is marginal for ISO15765 could also drop the raw 29-bit exchange.
4. **A non-SH7058 CPU.** Least likely, because the ECU is executing this SH7058 image (see D).

## D. What can and cannot be concluded

**Can be concluded:**
- (1) The ECU answers SSM-CAN on `0x7E0/0x7E8`. Its reply is the A2UG000B constant from flash, and SSM `A8` reads route through that ROM's dispatch table as `work/ENGINE_DTC_VIA_SSM_CAN.md` predicted. **This is strong evidence of a Denso-layout Subaru CAN ECU executing the A2UG000B image.** VERIFIED (bytes) / INFERRED (that the whole image matches; only the reply and DTC paths were observed).
- The image is SuperH machine code for an SH7058 memory map: 1 MiB flash, reset SP `0xFFFFBFA0`, inside the SH7058 RAM range `0xFFFF3000–0xFFFFBFFF` per `FastECU/kernelmemorymodels.h`. The disassembly header `re/rom_disassembly.asm` says "SH-2A". INFERRED: the SH7058 core is more precisely SH-2E. SH code cannot execute on a Hitachi M32R or any non-SuperH CPU. A 512 KiB SH7055 cannot hold a 1 MiB image. Hitachi-made Subaru SH7058 ECUs use a different layout (FastECU puts their cal ID at `0x802A`, not `0x2000`). VERIFIED (cfg) / INFERRED (that it therefore cannot be a Hitachi unit).

**Cannot be concluded:**
- (2) The exact silicon: SH7058 versus SH7058S, or another pin-compatible SH705x with at least 1 MiB flash and the same peripheral map. Also unknown: the Denso part number (`22611…`), the board revision, and the bootloader version in the unit's boot block. The SSM reply carries no hardware ID. No documented read-only command reads hardware ID registers; raw RAM through `A8` returns NRC `0x12`.
- Whether this physical unit is the August unit. The owner's two answers conflict (`work/ABS_RESEARCH.md`, Correction 2026-10-23).

**Bottom line:** the ECU is almost certainly an SH7058-family Denso CAN ECU. "Not a Denso SH7058" fits none of the data, unless the owner means a different SH7058 variant or a different Denso part number. That distinction matters for the flash method, and only the label or the tuner can settle it.

## E. Safe path

Check physically (no tools on the car):
- The ECU label: maker (DENSO or Hitachi), Subaru part number `22611xxxxx`, Denso number (`112300-xxxx` / `MBxxxxxx-xxxx`), and any "SH7058S" or "S" revision mark. Photograph it.

Ask the tuner:
- Which tool and method they used to flash it (EcuFlash `subarucan`, FastECU `densocan` or `subarucan`, Cobb, EcuTek, bench/BDM).
- Whether they wrote the whole 1 MiB, including the boot blocks, or only the calibration/application.
- Where the unit came from (donor car, part number), and whether the immobilizer was paired by a dealer.

Do NOT:
- Retry bootloader entry blindly or in a loop. Do not try the SH7055 kernel or any other kernel or protocol (`sub_ecu_denso_sh7058_can`, `sh7058s`, Hitachi), and do not try the GUI "ignition ON during flood" order until the label and the tuner's method are known.
- Send unknown `at…` commands to the OpenPort (CLAUDE.md hard rule 3).
- Flash `(OEM ABS WITH 2 BYTE FIX)`. It stays ON HOLD.

Read-only test that is safe: only the documented SSM-CAN reads, `tuneforge peek-ram-can` / `work/read_engine_dtc.sh` (SSM `AA` + `A8`), with ignition ON and engine OFF. These confirm the **software ID** again and can re-read the missed `0x8E` block. They **cannot** identify the CPU or the part number. **No read-only command in the project identifies the hardware.**
