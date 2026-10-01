# 🔧 Remapping Review — Batch 3: Web Research (93 fuel pendings) + G6DA/G6DG Disambiguation

**Date:** 2026-09-29 • **Script:** `step6_batch3_research.py`
**Backup:** `backups/car_database_backup_pre_step6_2026-09-29.db` • **Decisions:** `csv_exports/14_remap_batch3_decisions.csv`

## Result

| | Before batch 3 | After |
|---|---:|---:|
| Variants with specs (`v_vehicle_with_service`) | 39,045 | **39,099** (+54) |
| Variants with NULL engine_code | 137 | **82** |
| Queue: remapped | 331 | **386** |
| Queue: pending | 136 | **81** (every row carries a documented reason) |

Integrity ok • 0 hard fuel conflicts among resolved rows.

---

## 1. G6DA / G6DG / BAA engine-row disambiguation ✅

**BAA** — already resolved in batch 2 (both Touareg rows remapped to `AZZ`); the Ford Ka 1.3 row keeps the code. No action needed.

**G6DA / G6DG — the collision is real.** Both codes are used *simultaneously* by Ford (Duratorq 2.0 TDCi diesel, Focus/C-Max/Kuga) and Hyundai (Lambda petrol V6). Since `engine_code` is the primary key, the Ford rows keep the plain codes (15+ variants each) and two new disambiguated rows were created:

| New row | Identity | Evidence |
|---|---|---|
| **`G6DA (Hyundai)`** | 3.8 V6 MPi Lambda, 3778cc, 266hp | Wikipedia Lambda: G6DA 3.8 MPi 263hp/267PS [en.wikipedia.org](https://en.wikipedia.org/wiki/Hyundai_Lambda_engine); parts listing "GRANDEUR 2006-2011 PETROL 3.8 G6DA TG / CARNIVAL/GRAND CARNIVAL 3.8 G6DA VQ" [allcarpartsonline.com.au](https://www.allcarpartsonline.com.au/kia-grand-carnival-engine-3.8-petrol-g6da-vq-01-06); applications incl. Opirus/Amanti [xinlinautoparts.com](https://xinlinautoparts.com/products/xinlin-engine-g6da) |
| **`G6DG (Hyundai)`** | 3.0 V6 GDI Lambda II, 2999cc, 270hp | Wikipedia: G6DG 3.0 GDI 266hp/270PS, Grandeur HG + K7/Cadenza VG [en.wikipedia.org](https://en.wikipedia.org/wiki/Hyundai_Lambda_engine); mymotorlist: 2999cc, 250-270hp, Grandeur HG/Cadenza [mymotorlist.com](https://mymotorlist.com/engines/hyundai/g6dg/) |

**Bonus engine-row fix:** the existing `G6DH` row was mislabeled "3.0 / 3000cc / 247hp" — G6DH is actually the **3.3 GDI (3342cc, 290-294PS)** → corrected (Wikipedia Lambda applications: Grandeur HG, Santa Fe DM, Cadenza VG, Carnival YP).

**7 Lambda variants remapped:**
| Variant | → Code |
|---|---|
| Hyundai Grandeur HG 3.0 266hp | `G6DG (Hyundai)` (266hp exact) |
| Kia Cadenza VG 3.0 271hp | `G6DG (Hyundai)` |
| Hyundai Genesis Coupe 3.8 303hp (pre-GDI) | `G6DA (Hyundai)` |
| Kia Grand Carnival VQ 3.8 275hp | `G6DA (Hyundai)` |
| Hyundai Grandeur TG 3.8 265hp | `G6DA (Hyundai)` |
| Kia Opirus GH 3.8 267hp | `G6DA (Hyundai)` (267PS exact) |
| Kia Cadenza "3.5" 290hp | `G6DH` (mislabeled displacement — it's the 3.3 GDI 292hp) |

## 2. Web-verified remaps (highlights)

| Group | Resolution | Citation |
|---|---|---|
| **Alpina D3/D4/D5/XD3 350PS (7 rows)** | `N57D30B` (Alpina-tuned N57 3.0 biturbo; row displacement fixed 4004→2993cc) | Wikipedia Alpina B5/D5 F10: D5 = modified N57, 352PS [en.wikipedia.org](https://en.wikipedia.org/wiki/Alpina_B5_(F10)); automobile-catalog: N57D30 2993cc 350PS [automobile-catalog.com](https://www.automobile-catalog.com/car/2012/1762115/alpina_d5_biturbo.html) |
| **Alpina B10 V8S 375hp (2 rows)** | new row `M62B48` 4837cc | BMW blog: M62 4.8 (Alpina code F5) 375hp [bmwblog.com](https://www.bmwblog.com/2020/05/02/the-rare-bmw-alpina-roadster-v8-limited-edition/) |
| **Rolls-Royce Park Ward 5.4 326hp** | `M73B54` (new row, 5379cc) | carsart: Silver Seraph = M73B54 326hp [carsart.net](https://www.carsart.net/en/cars/rolls-royce/silver-seraph/silver-seraph/5400cc-i-v12-326hp) |
| **Maserati MC12 632hp** | `F140B` (Enzo-derived F140 V12, detuned) | FastestLaps: MC12 632PS on Enzo F140 chassis/engine [fastestlaps.com](https://fastestlaps.com/models/maserati-mc12) |
| Land Rover Discovery IV / RR IV / RR Sport 340hp ×3 | `AJ126` 3.0 SC V6 | (batch-2-verified row) |
| Jaguar XF 3.0D S 275hp | `3.0 V6 D S` (Lion AJ-V6D; description-code flagged) | in-DB row 271hp |
| Sprinter Classic 109hp ×2 | `OM611.981` | batch-2 citation family |
| BMW E92 325i 211hp ×2 | `N53B30A` (exact power) | in-DB |
| BMW 535d/X5 diesel-labelled-Petrol ×3 | restored `N57D30A/T` + fuel→Diesel (name-verified) | — |

## 3. Internal remaps (24 more)

Murano→`VQ35DE`, Lagreat→`J35A8`, L300→`4G64(SOHC16V)`, Move→`EF-VE`, BE-GO→`K3-VE`, Picanto→`G4HG`, Sentra 1.8/2.5→`QG18DE`/`QR25DE`, NV350→`YD25DDTi` (tune spread noted), Solara→`1MZ-FE`, Kluger Hybrid→`3MZ-FE` (system power noted), Astra TwinTop→`Z22SE`, C200K→`M271E18ML`, CLK63→`M156.985`, E500T→`M113E50`, Daily IV→`F1CE3481L`, Ypsilon diesel→`A13DTE`, Octavia 170→`CFGB`, Rapid→`CMXA`, **Subaru Impreza/XV 2.0D 109hp→`EE20Z`** (early EU 110PS tune of the same boxer diesel), Murciélago Roadster→Lamborghini `6.2 V12` row, Combo 1.6→`Y16YNG` (marginal, flagged).

## 4. Still pending (81) — all with documented notes

| Category | Rows | Note |
|---|---:|---|
| DISPLACEMENT_MISMATCH | 40 | incl. multi-candidate cases (Touareg 3.0 TDI has 18 VAG candidates: BKN/CLAB/CCWB…; Golf 1.6 FSI: BAG/BLF/BLP; Passat 1.8T: 19 candidates) |
| HARD_FUEL_CONFLICT | 38 | LEMON US-truck rows without power/engine data (8), corrupt power values (E81 90hp, 218d 95hp), brand-identification-first rows (hernr_1516 TS, TENGYI, SEVEN CF), EVs (Venturi/Piaggio/Berlingo/CITY — need EV data model), research cases (Diamante 205hp, Honda City 95hp, Tanto KF-DET missing, Morgan Aeromax) |
| POWER_MISMATCH_CROSSBRAND | 3 | 520i 156hp, CTS SW 2007, Equinox 2002 (impossible year/power combos) |

**Engine-row fixes this batch:** `G6DH` (3.3 GDI), `N57D30B` (2993cc), `N57D30T` (was Petrol + NULL cc — N57 is a diesel!).

⚠️ **Known gap:** the 4 new engine rows (`G6DA (Hyundai)`, `G6DG (Hyundai)`, `M62B48`, `M73B54`) have correct identity but **empty service-spec rows** — they need specs filled from OEM data (candidates: 5W-30/6.9L for Lambda per mymotorlist).

## 5. Cumulative queue progress

| | Start | After B1 | After B2 | After B3 |
|---|---:|---:|---:|---:|
| Quarantined variants | 0 | 481 | 440 | 82 |
| Remapped/verified | — | 45 | 348 | 403 |
| Variants with specs | 39,182* | 38,701 | 39,045 | **39,099** |

*including 481 wrong ones before Step 1 — i.e. **39,017 correct** at start vs 39,099 now, with the dangerous ones removed rather than displayed.

**Rollback:** `cp database_enriched/backups/car_database_backup_pre_step6_2026-09-29.db database_enriched/car_database.db`
