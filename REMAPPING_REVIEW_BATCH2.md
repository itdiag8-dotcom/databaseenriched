# 🔧 Remapping Review — Batch 2: Fuel Conflicts (278) + Displacement Mismatches (158)

**Date:** 2026-09-29 • **Script:** `step5_batch2_fuel_disp.py`
**Backup:** `backups/car_database_backup_pre_step5_2026-09-29.db` • **Decisions:** `csv_exports/13_remap_batch2_decisions.csv`

## Result

| Queue status after batch 2 | Rows |
|---|---:|
| remapped (250 internal + 37 web-verified + 44 batch-1) | **331** |
| engine_fuel_fixed (engine row's fuel was wrong) | 13 |
| fuel_label_fixed (variant's fuel label was wrong) | 3+18 |
| pending (documented, needs research) | 136 |
| invalid_data | 1 |

**Variants with usable specs (`v_vehicle_with_service`): 38,742 → 39,045 (+303)**
**Variants with NULL engine_code: 440 → 137** — integrity ok, 0 unexpected fuel conflicts.

## 1. Fuel-direction fixes (34) — the "quick label fixes"

Where the original engine matched displacement + power and only the fuel differed, the direction of the error was decided by evidence:

- **Variant label wrong (21):** e.g. VW Golf VI / Audi A3 / Octavia "1.6 (corr.) 102hp Petrol" → really the **1.6 TDI** (→ `CAYC`, fuel → Diesel); Touareg "3.6 V6 **FSI** 249hp" → 249hp is the **TDI** (kept `CMTA`, fuel → Diesel); Effedi "Gasolone" Diesel → Petrol.
- **Engine row's fuel wrong (13):** the engine_type text had the truth — Opel/Vauxhall `Y30DT` "**3.0 V6 CDTI**" (177hp) and Ford `SDBA` "**2.0 DI/TDDi**" (90hp) were stored as Petrol → `engines.fuel` corrected to Diesel, variant was right all along.

## 2. Web-verified overrides (37)

| Case | Code | Citation |
|---|---|---|
| Golf VI/A3/Octavia/Leon 1.6 TDI 102hp (CCSA → real code) | **CAYC** | auto-data.net Golf VI 1.6 TDI 105hp = CAYC [auto-data.net](https://www.auto-data.net/en/volkswagen-golf-vi-variant-1.6-tdi-105hp-16799), RTA manual CAYB/CAYC [tmbbooks.com](https://www.tmbbooks.com/en/autom_Vwrep24.html) |
| **Audi A6 2.7 TDI 163hp (your example)** | **CANB** | DB code 'CANB' = exact engine_type match '2.7 V6 TDI (163) DPF', 5 existing variants; real-world A6 2.7 TDI 180hp = BPP [auto-data.net](https://www.auto-data.net/en/audi-a6-avant-4f-c6-2.7-tdi-v6-180hp-26824) |
| Sprinter 216/316/416/616 CDI 156hp | **OM612.981** | autoparts24 OM612.981 156hp 5-cyl [autoparts-24.com](https://www.autoparts-24.com/engine/code/om-612-981/14447/), fair-motors applications [fair-motors.com](https://fair-motors.com/shop/engine-om612-981-om612981-mercedes-benz-sprinter-3-t-b903-2-t-b901-b902-4-t-b904-5-t-b905-316-cdi-4x4-216-416-616-156hp/) |
| Sprinter 211/411 CDI 109hp / 208 CDI 82hp | **OM611.981 / OM611.987** | same OM611 family |
| Honda CR-V IV 2.0 150hp | **R20A4** | Wikipedia CR-V gen IV: R20A 150hp [en.wikipedia.org](https://en.wikipedia.org/wiki/Honda_CR-V) |
| VW Touareg 3.2 V6 217hp | **AZZ** | autodoc: 3.2 V6 codes AZZ/BAA/BKJ/BMV/BMX/BRJ [autodoc.parts](https://www.autodoc.parts/spares/vw/touareg/touareg-7la-7l6-7l7/16819-3-2-v6), auto-data [auto-data.net](https://www.auto-data.net/en/volkswagen-touareg-i-7l-3.2i-v6-24v-220hp-4motion-8515) |
| Renault Kangoo 1.6 16V bivalent 82hp | **K4M850** | exact engine_type + power match in DB |
| Hyundai ix35/Tucson 2.0 161–165hp | **G4KD** | Theta II 2.0 GDI (19 DB variants, exact power) |
| Peugeot 508 SW/3008 **Hybrid4** 200hp | **RHC (DW10CTED4)** | combined 200PS = 163hp diesel + 37hp e-motor — power "mismatch" was system-power accounting |
| Mercedes S 300 h 231hp | **OM651.921** | same hybrid system-power logic |
| BMW i3 170hp REX | **IB1P25B** | same motor family, 94Ah tune |

## 3. Internal remaps (250) — rules + quality audit

Accepted only when: fuel matches the variant's claim, displacement ±6%, power within tolerance, brand/family matches, and (score ≥7 with margin, or same-brand with ≤3hp difference). **Power sanity after apply: 0 rows >25% off.** Sample of correct matches: Integra DC5 → `K20A3`, Lexus ES350 → `2GR-FE`, Cruze 1.7 D → `A17DTS`, Alpina B7 → `N62B44A19`, CLK 500 → `M273.967`, Geely MR → `MR479Q`.

⚠️ Known soft spots (kept, flagged for later): 29 remaps targeted Vivid **description-codes** (e.g. "2.4 DI", "2.2 MZR-CD") — specs join correctly but the "code" isn't an OEM code; ~3 borderline matches (Kia Carens → `J-J3-CR`, Smart Forfour `M135.930`, Passat `CJKB`) — power within 15% but application uncertain.

## 4. Discoveries worth knowing 🧠

1. **G6DA/G6DG are real cross-brand code collisions** — Ford (2.0 TDCi Duratorq diesel, Focus/C-Max/Kuga) *and* Hyundai (Lambda petrol V6: G6DA 3.8 MPI, G6DG 3.0 GDI) use the same codes. Parts catalogues sell "G6DG Ford/Hyundai 2.0 TDCi 136hp / 3.0 GDI 249hp" [fair-motors.com](https://fair-motors.com/shop/engine-g6dg-ford-hyundai-focus-c-max-ii-2-kuga-i-1-genesis-2-0-tdci-4x4-3-0-gdi-4wd-136hp-249hp/), Ford Kuga engine number G6DG [mychiptuningfiles.com](https://mychiptuningfiles.com/en/chiptuning-files/ford/ford-kuga/ford-kuga-2-0-tdci-136hp). Since `engine_code` is the primary key, one row can't serve both → the Hyundai Grandeur 3.0 / Genesis Coupe 3.8 rows stay **pending** until engine rows are disambiguated (e.g. suffixed rows).
2. Same story with **BAA** (Ford Ka 1.3 vs VW Touareg 3.2 V6).
3. Hybrid power labels store *system* power (diesel + e-motor) — my quarantine power rule correctly exempts them but the engine-row power can never match; noted in `remapping_queue`.

## 5. Remaining pending queue (136) — all documented in `note`

| Reason | Rows | Nature |
|---|---:|---|
| HARD_FUEL_CONFLICT | 93 | no confident in-DB candidate; needs web research (Honda 31, Mercedes, Ford, Alpina 18…) |
| DISPLACEMENT_MISMATCH | 40 | incl. the G6DA/G6DG collision rows |
| POWER_MISMATCH_CROSSBRAND | 3 | 520i 156hp, CTS SW 2007, Equinox 2002 (from batch 1) |
| (of which EV) | 10 | Venturi Fétish/Astrolab, Piaggio Porter EV — need an EV data model, not an engine |

## 6. Suggested next

1. **Batch 3 (research):** the 93 fuel-conflict pendings — group by model family, web-verify codes (Honda/Alpina/Ford are the big blocks)
2. **Engine-row disambiguation** for G6DA/G6DG/BAA collisions (create `G6DG (Hyundai)`-style rows or switch to manufacturer codes)
3. **Step 3:** hernr_* brand resolution (fixes Venturi/Piaggio EVs too)
4. LEMON_* replacement program continues in parallel

**Rollback:** `cp database_enriched/backups/car_database_backup_pre_step5_2026-09-29.db database_enriched/car_database.db`
