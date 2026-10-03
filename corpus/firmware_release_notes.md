# Amperia EVSE Firmware Suite - Official Release Notes

**System Package:** `AMP-OS-CORE`  
**Target Hardware:** Amperia DC-60, DC-150, and AC-22 Charging Stations  
**Release Distribution:** Over-The-Air (OTA) Fleet Management & Local USB Service Tool  

---

## Release Version 4.1.0 (Build 4102) - General Availability
**Release Date:** January 15, 2026  
**Status:** Stable Production Baseline  

### Summary
Initial production baseline release deployed across all 1,200 deployed Amperia fast charging stations.

### Key Features & Improvements
- **Protocol Compliance:** Full native implementation of OCPP 1.6-JSON with core smart charging profiles.
- **EV Handshake:** Integrated ISO 15118-2 basic authentication and DIN 70121 legacy charging state transitions.
- **Power Arbitration:** Dynamic load sharing across dual CCS2 charging outlets (150 kW single outlet or 75 kW + 75 kW concurrent split).
- **Insulation Check Baseline:** EV pre-charge safety isolation check timing window configured to default standard of **850 milliseconds (ms)**.

---

## Release Version 4.2.0 (Build 4208) - Stability & CAN-Bus Optimization
**Release Date:** March 10, 2026  
**Status:** Certified Long-Term Support (LTS) Baseline  

### Summary
Maintenance release addressing field communication stability, power module telemetry buffering, and spurious OCPP disconnects.

### Key Fixes & Optimizations
- **CAN-Bus Queue Reliability:** Enlarged circular ring buffer on the Main Controller Unit (MCU) from 64 to 256 messages, completely eliminating intermittent `E-214` packet loss errors under full 350 A DC load.
- **Grid Brownout Tolerance:** Added 150 ms voltage ride-through smoothing for unstable utility grid feeds on rural highway spurs.
- **Safety Pre-Charge State Machine:** Re-validated the DC bus pre-charge insulation monitoring loop. The evaluation timing window was maintained at **850 ms**, providing generous capacitance stabilization margins across all cable lengths up to 10 meters.
- **Spurious Contactor Warnings:** Fixed an edge-case timing glitch where cold ambient temperatures (< 5°C) caused auxiliary microswitch bounce during contactor pull-in.

---

## Release Version 4.3.0 (Build 4314) - Fast-Start Performance Rollout
**Release Date:** May 02, 2026  
**Status:** Restricted / Known Anomaly Advisory  

### Summary
Feature enhancement release aimed at reducing session start latency and accelerating EV pre-charge handshakes.

### Key Changes & Critical Modifications
- **Accelerated Session Handshake:** Modified the pre-charge insulation evaluation timing window: reduced from **850 ms down to 420 ms**. This aggressive change was intended to cut average session startup delay from 12 seconds to 6.2 seconds.
- **Dynamic Tariff Display:** Added real-time peak/off-peak rate display on the 10-inch HMI screen.
- **Modem Keep-Alive:** Implemented automated SIM reconnect logic for remote 4G LTE cellular modems.

### ⚠️ Known Field Advisory & Root Cause Anomaly (Notice #FWA-2026-03)
Following the automated OTA rollout of firmware version 4.3.0 to select highway clusters, multiple field sites reported false `E-217` error trips ("Pre-Charge Isolation Check Handshake Timing Mismatch").
- **Root Cause Mechanism:** When charging stations are equipped with heavy-duty liquid-cooled cables longer than 7.5 meters (such as 8.5 m highway cables) or when connected to EV battery packs with high input capacitance, the DC voltage stabilization curve takes **580 ms to 650 ms** to settle.
- Because firmware v4.3 reduced the timeout window to **420 ms**, the controller aborts the handshake prematurely and locks the charger with error code `E-217`.
- **Engineering Advisory:** `E-217` under firmware v4.3 is a pure **software timing false positive**, not a physical hardware failure.
- **Field Recommendation:** In case of persistent `E-217` trips following v4.3 installation, immediately roll back the charger firmware to **v4.2.0 (Build 4208)** via local USB service tool (`AmperiaTool v2.1`).

---

## Release Version 4.4.0 (Build 4410) - Adaptive Pre-Charge & Highway Cable Hotfix
**Release Date:** June 01, 2026  
**Status:** Certified Hotfix & General Availability  

### Summary
Critical firmware hotfix addressing the `E-217` false-positive pre-charge isolation trip on high-capacitance liquid-cooled cables (> 7.5 meters).

### Key Features & Bug Fixes
- **Dynamic Adaptive Pre-Charge Timing:** Implemented intelligent cable impedance sensing that dynamically expands the pre-charge isolation evaluation window from 420 ms up to **1,000 milliseconds (ms)** for extended cable runs (e.g. 8.5m highway cables).
- **Permanent E-217 Resolution:** Permanently resolves Notice #FWA-2026-03 without requiring manual rollback to v4.2.0.
- **OTA Distribution Resume:** Automated OTA fleet rollout resumed for all Tier-1 highway charging hubs.

