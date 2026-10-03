# Amperia Technical Operations - Major Incident Post-Mortem

**Incident Reference:** `INC-2026-0518-PUN`  
**Location:** Pune Expressway Super-Hub (Site ID: `MH-PUN-EXP-04`)  
**Impacted Equipment:** Units `DC150-01`, `DC150-02`, and `DC150-03` (All 150 kW Dual-Gun Chargers)  
**Incident Date:** May 18, 2026 – May 19, 2026  
**Incident Lead:** Rajesh Kumar (Senior Field Operations Lead, West Region)  
**Severity Level:** Severity 1 (Critical Highway Super-Hub Outage)  

---

## 1. Executive Incident Summary

On the night of May 18, 2026, all three 150 kW DC fast chargers (Units DC150-01, DC150-02, and DC150-03) at the Pune Expressway Super-Hub experienced total service disruption. Every unit consistently threw error code `E-217` ("Pre-Charge Isolation Check Handshake Timing Mismatch") whenever an electric vehicle attempted to initiate a DC charging session.

The incident occurred 4 hours after an automated central OTA firmware push updated the site controllers from firmware version `v4.2.0` to `v4.3.0`.

Total station downtime lasted 3 hours and 42 minutes before resolution, narrowly avoiding contractual Tier-1 SLA credit penalties.

---

## 2. Chronological Timeline of Events

- **May 18, 22:00 IST:** Automated OTA push deployed firmware `v4.3.0 (Build 4314)` to Pune Expressway site.
- **May 18, 22:45 IST:** First failure logged on Unit DC150-02 during initiation with a commercial fleet EV. Error `E-217` generated.
- **May 18, 23:10 IST:** Units DC150-01 and DC150-03 logged repeated `E-217` faults. Entire 6-gun charging hub unavailable.
- **May 19, 00:05 IST:** Network Operations Center (NOC) dispatched on-call field technician to site under Tier-1 2-hour emergency response protocol.
- **May 19, 01:15 IST:** Field technician arrived on site. Observed all LED status rings pulsing yellow (Isolation Fault lockout).
- **May 19, 01:30 IST:** Technician conducted initial visual inspection. Noticed power module LEDs were solid green. However, assuming `E-217` was a physical contactor weld or insulation breakdown, the technician prepared a critical RMA requisition for 3 replacement DC contactor assemblies and 2 power modules ($7,800 estimated parts expense).
- **May 19, 02:00 IST:** Technical escalation lead intervened and cross-referenced the newly released `Notice #FWA-2026-03` in firmware v4.3 notes.
- **May 19, 02:15 IST:** Technician connected service laptop using the local USB `AmperiaTool v2.1` utility and initiated a manual firmware rollback from `v4.3.0` to `v4.2.0 (Build 4208)` on all three cabinets.
- **May 19, 02:35 IST:** Units rebooted. Test charging session initiated with field test vehicle. Pre-charge completed cleanly in 620 ms without throwing `E-217`. Peak power reached 148 kW.
- **May 19, 02:45 IST:** All 3 chargers restored to full commercial operation. Emergency part requisition was formally cancelled.

---

## 3. Comprehensive Root Cause Analysis (RCA)

### 3.1 Hardware vs. Firmware Root Cause Determination
The incident was conclusively determined to be a **firmware timing regression**, and **NOT a physical hardware defect**.

1. **Hardware Verification:** Physical megohmmeter insulation resistance measurements on all three units confirmed insulation resistance of 620 MΩ (DC150-01), 580 MΩ (DC150-02), and 410 MΩ (DC150-03), well above the 100 MΩ safety threshold. DC contactors showed zero mechanical pitting or weld degradation.
2. **Firmware Timing Mechanism:** The Pune Expressway Super-Hub utilizes extended 8.5-meter liquid-cooled CCS2 charging cables (longer than the standard 6.0-meter urban cables) to accommodate high-roof commercial e-buses. The additional cable length and cooling jacket introduce higher parasitic line capacitance.
3. Firmware `v4.3.0` reduced the pre-charge isolation evaluation window from 850 ms to 420 ms. Under the higher capacitance of the 8.5 m cables, the pre-charge voltage ramp required 610 ms to stabilize. The firmware interpreted the incomplete voltage ramp as an insulation leakage fault, aborting the session with code `E-217`.

---

## 4. Remediation, Solution, and Preventive Corrective Actions

| Action Item | Description | Responsible Party | Status |
| :--- | :--- | :--- | :--- |
| **Immediate Site Fix** | Roll back firmware on all 3 DC-150 units from `v4.3.0` to `v4.2.0 (Build 4208)` via local USB service tool. | Field Service Lead | **Completed** (Restored Site) |
| **Fleet OTA Freeze** | Immediately halt automated OTA rollouts of firmware `v4.3.0` across all highway locations equipped with > 7.5 m cables. | NOC / Firmware Team | **Completed** |
| **Firmware Patch (v4.4)** | Release firmware `v4.4.0` incorporating dynamic adaptive pre-charge timing (allowing up to 1000 ms based on detected cable impedance). | Embedded Software Team | In Progress |
| **Technician Guidance** | Update field diagnostic playbook: `E-217` without `E-109` is a firmware timing issue and must never trigger part replacements. | Field Training Dept | **Completed** |
