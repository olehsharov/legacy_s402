# Manifest: files deliberately NOT published

ROM images and ECU dumps from this project are **not** in this repository. They contain proprietary
Denso/Subaru firmware and third-party tuned maps. The hashes below let anyone holding a copy confirm it
is the same file the notes describe. Paths are relative to the original project folder.

| File | Size (bytes) | sha256 | Notes |
|---|---|---|---|
| `kramar/JDM LGT 06 MT DIESEL SWAP 12bar OKKO 95 (DIESEL ABS).bin` | 1048576 | `7ca41caca47bbe435cd31fdc1f7e7be08519340d629494be2b54511b6f896b2f` | Tuner's maps on the car's old A2UG000K dump |
| `kramar/JDM LGT 06 MT DIESEL SWAP 12bar OKKO 95 (OEM ABS).bin` | 1048576 | `901a392ac9f50696b0ef4a663f4b08252b6cf4d10afcd50c25f2ee9d0404dc6b` | A2UG000B, currently flashed (ABS/ESP dead) |
| `kramar/JDM LGT 06 MT DIESEL SWAP 12bar OKKO 95 (OEM ABS WITH 2 BYTE FIX).bin` | 1048576 | `805116cb931f44214e2f967bde378daa6bbc5f36986f0a876103358ad89374c4` | 2-byte candidate, untested |
| `dumps/after_write.bin` | 1048576 | `77f585690531796397202faa8e35d116fdf482d2e5b6451de33135ea648755af` | Read-back after the 2026-08-29 rev-limit write |
| `dumps/backup_before_abs_fix_20261023_1008.bin` | 1048576 | `901a392ac9f50696b0ef4a663f4b08252b6cf4d10afcd50c25f2ee9d0404dc6b` | Verified backup 2026-10-23 (= `(OEM ABS).bin`) |
| `dumps/cli_read_.bin` | 1048576 | `c510bc45d8ac54244adfc7a1a10866d91640c6a573b3c8554d5517370895fbd7` | CLI read 2026-08-29 (= car's original ROM) |
| `dumps/kernel_test.bin` | 1048576 | `c510bc45d8ac54244adfc7a1a10866d91640c6a573b3c8554d5517370895fbd7` | Kernel test read (= car's original ROM) |
| `roms/BACKUP_ECU_before_abs_fix_A2UG000B_2026-10-23.bin` | 1048576 | `901a392ac9f50696b0ef4a663f4b08252b6cf4d10afcd50c25f2ee9d0404dc6b` | Read-only copy of the 2026-10-23 backup |
| `roms/STOCK_A2UG000K_2006_JDM_Legacy_SpecB_MT_2026-08-25.bin` | 1048576 | `c510bc45d8ac54244adfc7a1a10866d91640c6a573b3c8554d5517370895fbd7` | Car's ROM as found (a retune, not factory stock) |
| `roms/reference/STOCK_A2UG000K_reference.bin` | 1048576 | `de582f47363ab65b1db60b6052debf5588799d6054e6ac82642c1dd08a05734d` | Public factory reference A2UG000K |
| `read_image_2026-08-25_16h39m11s.bin` | 1048576 | `c510bc45d8ac54244adfc7a1a10866d91640c6a573b3c8554d5517370895fbd7` | First GUI read 2026-08-25 (the "old ROM") |
| `read_image_2026-08-25_16h39m11s.bin.bak` | 1048576 | `c510bc45d8ac54244adfc7a1a10866d91640c6a573b3c8554d5517370895fbd7` | Copy of the above |
| `work/A2UG000K_2026-08-29_rev-6800-6600_NOCHECKSUM.bin` | 1048576 | `e663b10305e55c2291e8ad92893f665d36d718a1d93cca4179fa872ae855b4c2` | Intermediate, stale checksums, never flash |
| `work/A2UG000K_2026-08-29_rev-6800-6600_ck.bin` | 1048576 | `77f585690531796397202faa8e35d116fdf482d2e5b6451de33135ea648755af` | Rev-limit image with checksums fixed |
| `re/rom.bin` | 1048576 | `c510bc45d8ac54244adfc7a1a10866d91640c6a573b3c8554d5517370895fbd7` | Copy used for disassembly |

Also not published:

- `re/rom_disassembly.asm`, `re/rom_decompiled.c`, `re/*.c`: disassembly/decompilation of proprietary Denso firmware.
- Public stock ROM set used for the cross-ROM survey (`tmp/xrom/dl/`): available at github.com/bludgod/RomRaider.
- The third-party tuning guide PDF and the saved subdiesel page text (link in `README.md`).
- Datalogs (`logs/*.csv`), FastECU and tuneforge source trees, RomRaider install.
