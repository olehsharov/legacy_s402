#!/bin/bash
# READ-ONLY: reads the ECU's engine fault-flag bytes with the project's documented peek-ram-can
# (SSM 0xA8 read, same request as the datalogger). Run with sudo, ignition ON, engine OFF.
# Addresses and bit map: work/ENGINE_DTC_VIA_SSM_CAN.md. All-00 = no faults. A wall of FF = read failed.
TF=<project>/tmp/tf-build/release/tuneforge
OUT=<project>/work/dtc_read_$(date +%Y%m%d_%H%M%S).txt
{
for spec in "0x00008E 32" "0x0000AE 32" "0x0000F0 8" "0x000123 16" "0x000150 10" "0x000160 10" "0x000174 14"; do
  set -- $spec
  echo "=== addr $1 len $2 ==="
  "$TF" peek-ram-can --addr "$1" --len "$2" 2>&1
  sleep 1
done
} | tee "$OUT"
echo "saved: $OUT"
