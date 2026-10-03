# Amperia DC-150 Fast Charger Technical & Maintenance Manual

**Document ID:** `MAN-DC150-2026-REV3`  
**Applicable Hardware:** Amperia DC-150 High-Power EVSE (Dual CCS2 Output, 150 kW)  
**Target Audience:** Certified Amperia Field Service Engineers & Technical Operations  

---

## 1. System Overview and Architecture

The Amperia DC-150 is a commercial-grade, grid-tied direct current fast charging station engineered for highway corridors, fleet hubs, and heavy-use retail charging plazas. The system delivers up to 150 kW continuous power across single or dual CCS2 liquid-cooled charging outlets with dynamic power arbitration.

### 1.1 Key Technical Specifications
- **AC Input Voltage:** 415 V AC nominal, 3-Phase + Neutral + Protective Earth (PE), 50 Hz (+/- 5%).
- **AC Input Full-Load Current:** 240 A RMS per phase at 150 kW rated power.
- **Output DC Voltage Range:** 150 V DC to 1000 V DC continuous.
- **Maximum Output Current:** 350 A DC continuous (500 A peak boost for up to 10 minutes with active liquid cooling).
- **Power Module Topology:** Modular silicon carbide (SiC) resonant inverter modules arranged in a 3 x 50 kW parallel bus configuration.
- **Cooling Mechanism:** Closed-loop dielectric fluid loop with external radiator and variable-speed brushless fans.
- **Operating Ambient Temperature:** -25°C to +55°C (linear thermal de-rating active above 45°C ambient).
- **Enclosure Rating:** IP55 ingress protection, IK10 vandal resistance rating.

---

## 2. Installation, Commissioning and Safety Tolerances

### 2.1 Earthing and Ground Resistance
The DC-150 cabinet requires a low-impedance dedicated copper earth pit. Measured ground loop impedance must be strictly below 5.0 Ohms under all seasonal soil conditions. If ground resistance exceeds 5.0 Ohms, the internal ground monitoring circuit (GMC) will inhibit charging and flag an earth fault.

### 2.2 Baseline Insulation Resistance
Prior to initial commissioning or after replacing any high-voltage DC component, technicians must perform a 1000 V DC insulation resistance test using a calibrated Megohmmeter:
- **Phase-to-Earth / DC Bus-to-Earth Baseline:** Minimum 500 Megaohms (> 500 MΩ) in factory-new condition.
- **Field Minimum Threshold:** Any circuit reading below 100 Megaohms (< 100 MΩ) requires immediate physical cable and busbar inspection.

---

## 3. Hardware Warranty and Coverage Schedule

Amperia Charging Networks guarantees component warranty schedules according to the contractual terms below:

| Component Category | Standard Warranty Period | Coverage Details |
| :--- | :--- | :--- |
| **SiC Power Modules (50 kW units)** | **5 Years (60 Months)** | Full parts and depot repair coverage against component degradation, IGBT/MOSFET dielectric breakdown, and thermal fatigue under normal operating duty cycles. |
| **Liquid-Cooled Charging Cables & CCS2 Guns** | **2 Years (24 Months)** | Covers internal fluid conduit integrity, temperature thermistor failures, and electrical contact resistance. Excludes direct vehicular impact and mechanical vandalism. |
| **Main DC Contactors & Pre-Charge Relays** | **3 Years (36 Months)** | Covers contact tip erosion, coil failure, and auxiliary microswitch feedback faults up to 100,000 switching operations. |
| **Main Controller (MCU) & HMI Touchscreen** | **3 Years (36 Months)** | Covers logic board processor, CAN transceivers, cellular modem, and display digitizer against electronic failure. |
| **Auxiliary Cooling Radiator & Fans** | **2 Years (24 Months)** | Covers coolant pump motor, radiator core corrosion, and variable-speed fan bearings. |

---

## 4. Comprehensive Error Code Diagnostic Reference

The DC-150 controller classifies internal faults into two distinct families: **Hardware Faults (`E-1xx`)** requiring physical inspection and part replacement, and **Communication/Firmware Logic Faults (`E-2xx`)** involving protocol, software timing, or network handshakes.

### 4.1 Hardware Error Codes (`E-1xx`)
- **`E-101` - AC Grid Phase Loss / Voltage Imbalance:** Measured AC line imbalance exceeds 8% across phases for > 200 ms. Caused by utility grid instability or blown primary input fuses.
- **`E-104` - Power Module Over-Temperature:** Internal SiC heatsink temperature exceeded 92°C. Check coolant level and verify radiator fan operation.
- **`E-109` - DC Output Contactor Weld Fault:** Auxiliary microswitch indicates contactor remained physically closed after the de-energize command. **Critical Safety Fault:** Cabinet must be de-energized; replace contactor assembly immediately.
- **`E-112` - Liquid Coolant Flow Interruption:** Coolant flow rate dropped below 2.5 Liters/min during active high-current charging session.

### 4.2 Communication and Firmware Error Codes (`E-2xx`)
- **`E-201` - OCPP Central System Timeout:** Loss of WebSocket ping-pong packet response to Amperia Cloud back-office for > 90 seconds. Station enters autonomous offline mode.
- **`E-208` - ISO 15118 PLC Communication Failure:** Power Line Communication (PLC) modem failed to establish digital EV-to-EVSE handshake within 15 seconds of cable insertion.
- **`E-214` - Internal CAN-Bus Communication Packet Loss:** Intermittent packet drop detected between Main Controller (MCU) and Power Module Rack.
- **`E-217` - Pre-Charge Isolation Check Handshake Timing Mismatch:** Occurs during the safety pre-charge evaluation sequence prior to main contactor closure. The controller monitors the voltage rise slope across the vehicle inlet. If the insulation evaluation routine does not complete within the firmware-configured timing window, `E-217` is thrown.
  - *Classification:* **Firmware / Timing Logic Issue.**
  - *Important Note:* `E-217` is **NOT** a physical contactor weld or hardware module burnout unless accompanied simultaneously by hardware error `E-109`. Do not swap power modules or contactors for isolated `E-217` occurrences without first checking the installed firmware build version.
