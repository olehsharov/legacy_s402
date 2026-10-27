# CAN TX trace: frame built at 0x1A58C, cal byte 0xC1AD3 (A2UG000K)

Static analysis only (rom.bin / rom_disassembly.asm). Nothing was written to the car or the cable.
Tags: VERIFIED = read directly from bytes or code. INFERRED = reasoned from strong evidence. UNKNOWN = not determined.

## Summary
The routine at 0x1A58C builds the 8 data bytes of **CAN ID 0x600**. The ID is an 11-bit standard ID, the frame goes out on HCAN channel 0 from mailbox 8, and it is sent once every 50 calls of its parent routine (VERIFIED).
Byte 5 of that frame is a calibration constant (0xC1AD3 on this car). The car's ROM has 0xA2 there; the reference stock ROM has 0x22.
The public reverse-engineering of the Subaru EE20 diesel ECU (subdiesel, MY10 Impreza EDM) records ID 0x600 as "ECU, every 50 ms", with byte 5 = "const 0xA2 (from data segment)" and byte 7 = 0xFF. Its layout matches this ROM byte for byte.
No public source says what byte 5, or its bit 7, means, so the meaning stays **UNKNOWN**.
Our ROM gives no code consumer for that byte: the ECU just copies it into the frame. Whatever it means is decided by the node that receives it.

## 1. Send path (VERIFIED)
- 0xD66C = CAN send for a fixed DLC. Argument r4 = pointer to a 16-byte record.
  1. 0x2438(6) runs a short busy-wait delay.
  2. 0x3B1C(0x90) raises SR.IMASK to 9 to enter a critical section. 0x3B30 restores it.
  3. The routine reads TXPR, at 0xFFFFD020 (MB16-31) or 0xFFFFD022 (MB0-15), and tests the mailbox bit. If the bit is set, the mailbox is busy and it returns 1.
  4. Otherwise it writes the bit to TXACK at 0xFFFFD030/32, which clears it.
  5. It copies `rec[6]` bytes from the RAM buffer `*(rec+8)` into the mailbox data area at MB+8. This is 0xDB56, which copies with write-verify.
  6. It writes the bit to TXPR, which requests transmission, and returns 0.
- 0xD706 is the variable-DLC variant. It also writes MB+4 (DLC / MBC, via 0xFFBE).
- Helpers:
  - 0x101FE(mb, off) returns the mailbox register address: 0xFFFFD100 + 32·mb + off for mb<32, or 0xFFFFD900 + 32·(mb&31) + off for channel 1.
  - 0x1019C(mb, reg) selects the high or low word of a 32-bit flag register and the channel offset (+0x800).
  - 0x1022A(mb) returns 1<<(mb&15), using the table at 0x12638.
  - 0x101EA(ch, reg) adds 0x800 for channel 1.
- Hardware: SH7058 HCAN2. Module 0 is at 0xFFFFD000 and module 1 at 0xFFFFD800. Mailboxes start at +0x100, each 32 bytes: ID at +0, MBC/DLC at +4, data at +8..+15.
  - The register names (TXPR, TXACK, BCR, MBIMR) come from the SH7058 HCAN2 layout (INFERRED). The addresses and the bit behaviour are VERIFIED from the code.

## 2. Message table and init (VERIFIED)
- 0x18310 calls 0xD39C(ch=0, table=0x5A0C8, n=17). For each record, 0xD39C calls 0xFD32 → 0xDA48. That writes MB+0 = `(ID & 0x7FF) << 4`, with IDE = rec[7] = 0 for every record, so all IDs are 11-bit standard.
- MBC is set from rec[4]: 0 → MBC 0 (transmit), 1 → MBC 3 (receive).
- rec[12] is written as the mailbox's bit in MBIMR (0xFFFFD050/52): 1 = interrupt masked (polled), 0 = interrupt. Only the diagnostic records use 0.
- Record layout, 16 bytes: `+0 u32 CAN ID | +4 dir (0=TX, 1=RX) | +5 mailbox | +6 DLC | +7 IDE | +8 u32 RAM buffer | +12 irq-mask flag`.
- Note: the 0x660A record starts at **0x5A138**, not 0x5A140. 0x5A140 is its buffer-pointer field.

| rec addr | ID | dir | MB | buffer | builder / user | public match (subdiesel EE20, MY10) |
|---|---|---|---|---|---|---|
| 0x5A0C8 | 0x411 | TX | 1 | 0xFFFF65FA | 0x1A09E (every 10) | ECU, 10 ms: gear, cruise speed, brake SW, MIL |
| 0x5A0D8 | 0x501 | RX | 2 | 0xFFFF657F | 0x195DE | VDC/ABS, 20 ms: torque request / flags |
| 0x5A0E8 | 0x512 | RX | 3 | 0xFFFF6587 | 0x19642 | VDC/ABS, 20 ms: vehicle speed, counter |
| 0x5A0F8 | 0x410 | TX | 4 | 0xFFFF65F2 | 0x19E3E / 0xBF080 (every 10) | ECU, 10 ms: torque, accel pedal, RPM |
| 0x5A108 | 0x420 | RX | 5 | 0xFFFF64D8 | 0x185B2 | none (probably TCU, UNKNOWN) |
| 0x5A118 | 0x412 | TX | 6 | 0xFFFF6602 | 0x1A46A (every 10) | none (petrol-only?) |
| 0x5A128 | 0x601 | TX | 7 | 0xFFFF6612 | 0x1A70E (every 10) | none |
| **0x5A138** | **0x600** | **TX** | **8** | **0xFFFF660A** | **0x1A58C (every 50)** | **ECU, 50 ms: coolant, lamps, counter, byte5 = const 0xA2, byte7 = 0xFF** |
| 0x5A148 | 0x514 | RX | 9 | 0xFFFF651D | 0x18DCE | BIU, 20 ms: ambient temp, switches, fuel level |
| 0x5A158 | 0x422 | RX | 10 | 0xFFFF64E8 | 0x18690 | none |
| 0x5A168 | 0x421 | RX | 11 | 0xFFFF64E0 | 0x18612 | none |
| 0x5A178 | 0x513 | RX | 12 | 0xFFFF658F | 0x196BA | VDC/ABS, 20 ms: four wheel speeds |
| 0x5A188 / 0x5A1B8 | 0x7E8 | TX | 15 | 0xFFFF9F60 | diagnostic response | OBD-II / SSM-over-CAN |
| 0x5A198 | 0x7DF | RX | 13 | 0xFFFF9F58 | functional diagnostic request | OBD-II |
| 0x5A1A8 | 0x7E0 | RX | 14 | 0xFFFF9F58 | physical diagnostic request | OBD-II |
| 0x5A1C8 | 0x620 | RX | 16 | 0xFFFF6525 | 0x18FF8 | BIU/A-C, 20 ms: heater / A-C flags |

- The 0x7DF / 0x7E0 / 0x7E8 entries are standard OBD-II IDs. They confirm that field +0 really is the CAN ID.
- Bus timing: BCR1 (0xFFFFD004) = 0xA731 and BCR0 (0xFFFFD006) = 0x0001, written at 0xD3D4. With the HCAN2 layout (TSG1=10, TSG2=7, BRP=1) that is 20 Tq per bit, so Pφ/80. At Pφ = 40 MHz that gives **500 kbit/s** (INFERRED; Pφ is not verified).
- Period: the parent 0x19D72 (called from task 0x6B4C, task-table entry 0x4A40) sends 0x410/0x411/0x412/0x601 every 10 calls and 0x600 every 50 calls (VERIFIED). The public 10 ms / 50 ms rates imply a 1 ms tick, so **0x600 ≈ 50 ms** (INFERRED; the RTOS alarm period was not traced).
- opendbc (comma.ai) Subaru DBCs, both preglobal_2015 and global: none of these IDs appear. They describe a later ID plan (0x40, 0x140, ...), so they do not apply to this 2006 car.

## 3. ID 0x600 payload (built at 0x1A58C, buffer 0xFFFF660A)
| byte | source in A2UG000K | status | subdiesel EE20 doc |
|---|---|---|---|
| 0 | 0 | VERIFIED | glow / DPF lamp bits (diesel-only) |
| 1-2 | u16 little-endian = 0x2574(cal 0xC1B98 [8.75] × InjPW 0xFFFF78CC [RomRaider E60] × RPM 0xFFFF6D34 × 3.333e-8, step 0.001) | VERIFIED code; meaning INFERRED | fuel consumption u16 LE |
| 3 | 0xFFFF666F = coolant(°C)+40, or 0xFF on sensor fault (0x1B8FE: offset −40, fault test 0x2B960, source float 0xFFFF6AA4) | VERIFIED code; coolant INFERRED | coolant x−40 °C, 0xFF on fault |
| 4 | rolling counter 0xFFFF65EC, incremented right before the send | VERIFIED | message counter |
| 5 | 0xFFFF65ED, set by 0x1B8DC: if 0xFFFF6CDB==1 then cal **0xC1AD3**, else cal **0xC1AD2** | VERIFIED | "const 0xA2 (from data segment)" |
| 6 | 0xFFFF66AE: bit5=0xFFFF6682, bit4=0xFFFF6684, bit3=0xFFFF6683, bit1=0xFFFF6640, bit0=0xFFFF6CDD (each ==1). Bits 7, 6 and 2 are always 0 | VERIFIED | bit 2 = clutch SW (diesel) |
| 7 | 0xFF | VERIFIED | const 0xFF |

Send gating (VERIFIED): the counter is incremented and the frame sent only when 0xFFFF86A8==0, 0xFFFF64AA==0 and 0xFFFF9AB4==0. Otherwise the frame is skipped.

## 4. Byte 5 / 0xC1AD3
- Values (VERIFIED, checked in every 1 MiB image in the repo):
  - reference stock `roms/reference/STOCK_A2UG000K_reference.bin`: 0xC1AD2 = 0x02, 0xC1AD3 = 0x22.
  - the car (`roms/STOCK_..._2026-08-25.bin`, `re/rom.bin`, `dumps/*`, `work/*`): 0xC1AD2 = **0xA2**, 0xC1AD3 = **0xA2**.
  - So on the car both selector paths give 0xA2, and the frame carries 0xA2 whatever 0xFFFF6CDB is.
- Selector 0xFFFF6CDB (VERIFIED): set at 0x27E58 from cal 0xC2D80. 0xAA → 0, 0x55 → 1, anything else → 0. Both ROMs hold 0x55, so 6CDB=1 and the **0xC1AD3** path is the live one.
  - The stock ROM therefore sends 0x22 in byte 5, and the car sends 0xA2.
  - What 6CDB means is UNKNOWN. Calling it "AT flag" is not supported: it is 1 on this 6MT car.
  - In stock, the two paths differ only in bit 5 (0x02 vs 0x22). Bit 5 thus follows 6CDB, which looks like an MT/AT or variant flag (INFERRED).
- Readers (VERIFIED for this ROM): 0xFFFF65ED has no reader other than the frame builder. The ECU never uses the value itself.
- Receiver: the subdiesel table gives no reader for 0x600. Plausible nodes on the high-speed bus are VDC/ABS, TCU and BIU/combination meter (the meter would use coolant and the lamps) (INFERRED, receiver UNKNOWN).
- Bit 7 (0x22 → 0xA2): **meaning UNKNOWN.** The only public data point is that the MY10 EE20 diesel ECU sends 0xA2. That is consistent with a vehicle-configuration byte (engine / market / drivetrain variant) read by another module, but nothing found documents it. Reading it as "diesel" or "VDC present" would be a guess.

## 5. Byte 6 flag sources
- 0xFFFF6682 is set at about 0x1BF54. Its logic tests 0xFFFF6504 == 6 and 0xFFFF66D5 / 0xFFFF66DC (UNKNOWN).
- 0xFFFF6684 and 0xFFFF6683 come from a 3-state variable 0xFFFF6690 at 0x1C0DC. The pattern looks like a lamp on / blink / off driver (INFERRED: indicator lamps).
- 0xFFFF6640 is set at 0x1BBE0 (UNKNOWN).
- 0xFFFF6CDD is set at 0x27ECE from 0xFFFF6CCF. It sits in the 0xFFFF6CC9..6CE7 block of discrete-input / config flags and is used by 0x174B4 together with RPM (UNKNOWN).
- None of these can be tied to ABS, VDC, immobiliser, neutral or clutch from static evidence. Bit 2, the diesel clutch-SW bit, is never set on this ECU.

## 6. What a CAN capture would settle
Use a passive, listen-only capture at 500 kbit/s on OBD pins 6 and 14.
- It would confirm ID 0x600 at about 50 ms and the bit rate.
- It would confirm byte 5 = 0xA2 on the car.
- Comparing the frame with stock 0x22, by flashing a ROM with the stock value, would show which node changes behaviour: warning lamps, VDC/TCS lamps, meter, TCU DTCs, or SSM-reported config.
- It would also identify the senders of 0x420/0x421/0x422 (none seen = no TCU, as expected on a 6MT).
- A capture still cannot show how a receiver interprets bit 7. That needs receiver firmware or Subaru documentation.
