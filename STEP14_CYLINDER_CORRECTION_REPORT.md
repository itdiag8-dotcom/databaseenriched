# Step 14 — Cylinder counts: an external cross-check, then the data checking itself

**Date:** 2026-10-01 · **Scripts:** `step67_step14_cylinders.py`, `step67b_valve_count_cylinders.py`,
`step67c_cylinder_change_ledger.py` · **Decision CSVs:** `csv_exports/80`, `81`, `82`

**127 engine rows corrected, carrying 658 variants.** 29 came from the MagicMotorsport layout
tokens; **98 came from our own descriptors contradicting our own cylinder counts** — found only
because the first script's verification query was written to fail loudly.

---

## 1. What the external source could and could not do

The MagicMotorsport `Engine` column often states a layout outright: *"3.6L Pentastar V6"*,
*"2.5L R5 TDI"*, *"6.8L V12"*. Parsing it with

```
(?<![A-Za-z0-9])(V|I|L|R|H|B|W)\s?(3|4|5|6|8|10|12|16)(?![0-9vV])
```

yielded a unanimous layout for **413 of 414 codes**, of which **28 contradicted our `cylinders`**.
The trailing `(?![0-9vV])` guard is load-bearing: without it *"16v"* and *"24v"* — valve counts —
parse as cylinder counts and poison the whole result.

The source was **not** treated as an oracle. Four of its claims were rejected:

| code | source says | why we kept ours |
|---|---|---|
| `EDZ` | 2.4L **V6** | Chrysler's EDZ is the 2.4 DOHC inline-four; our own descriptor says I4. The source is simply wrong. |
| `G6DC` | 3.5 V6 | we hold 1,997 cc 2.0 TDCi — the **code is mis-assigned**, not the cylinder count |
| `LFY` | 3.6 V6 | we hold 1,800 cc — same identity problem |
| `CYRB` | 2.0 TFSI petrol | we hold a 2,198 cc diesel — same |

Changing cylinders on the last three would have *concealed* a worse defect by making a
mis-assigned engine code look internally consistent. They are exported, not fixed.

**The strongest 15 of the 29 did not really come from the source at all.** The VW 2.5 TDI codes
(`AXD AXE BNZ BPC CECA CECB CEBA BBE BBF AVR AJT ANJ APA ACV AUF`) were stored as six cylinders
while **our own descriptor read "2.5 10v TDI"**. A ten-valve six-cylinder cannot exist. The source
agreed ("2.5L R5 TDI"), but the contradiction was already sitting inside our own row.

Three Mercedes `OM642` rows also carried the Step 11 leaked-designation corruption in
`displacement_cc` (2873, 2444, 3393 for what is one 2,987 cc V6), repaired alongside.

---

## 2. The verification query that opened the real finding

Each step ends with checks written to **fail**, not to pass. This one asked whether any `10v`
descriptor still sat on a six-cylinder row, and answered **14**. The trick generalised, so it was
run over the whole table.

**A valve count constrains a cylinder count**, because engines have 2, 3, 4 or 5 valves per
cylinder and nothing else. So a valve total `v` is only compatible with cylinder counts in
`{v/2, v/3, v/4, v/5}`. Testing every descriptor against its own stored `cylinders` found
**129 arithmetically impossible rows**.

Two false-positive classes had to be removed first, and both are worth recording:

- **`48V` is a battery, not a valve count.** *"2.0 I4 Turbo MHEV 48V"* is a mild-hybrid system
  voltage. Mild-hybrid descriptors are excluded.
- **Five valves per cylinder is real.** A first pass assumed 20v ⇒ five cylinders and flagged the
  VW/Audi 1.8 20v and the Audi 4.2 V8 40v — but those are a four (4×5) and an eight (8×5). That
  pass would have "corrected" 91 rows that were already right.

## 3. Only fixing what a second signal confirms

An impossibility says the row is wrong; it does not say *which* number is wrong. A fix was applied
only where an independent signal identifies the culprit — usually the engine code's own prefix:

| rule | rows | evidence |
|---|---:|---|
| `B5xxx`/`D5xxx` → 5 | 35 | Volvo's code prefix encodes the cylinder count (`B5244S`, `D5244T`) |
| `M5x`/`N5x` → 6 | 27 | BMW M52/M54/N51/N52/N53 are straight-sixes; 24v = 6×4 |
| any `10v` → 5 | 14 | by elimination — the only other arithmetic option is a two-cylinder with five valves each, which has never been built |
| VW/Audi 2.5 20v → 5 | 11 | the 2.5 TFSI/FSI inline-five, confirmed at ~500 cc per cylinder |
| Fiat/Alfa 2.4 JTD 20v → 5 | 8 | the 2.4 JTD inline-five |
| `4Mxx`/`4Gxx` → 4 | 3 | Mitsubishi's leading digit is the cylinder count (`4M41`) |

**31 rows remain flagged and were deliberately not touched**, because the second signal is absent
or points at the *descriptor* instead:

- **`B10D1`** — "1.0 16v" on 3 cylinders. Here the stored 3 is right and the **descriptor** is
  wrong; a naive fixer would have made it a four.
- **Ford `SAFA`** — "3.2 16v TDCi" on 6 cylinders. The Duratorq 3.2 is an inline-*five*, so
  *both* numbers are wrong and no rule can recover that. A displacement-ratio tiebreak would have
  confidently written "V8" here, which is why no such tiebreak was used.

## 4. Audit trail

`step67b` was run twice (the second run added the `10v` rule) and overwrote its own decision CSV
with only the second run's rows. Rather than patch the CSV, `step67c` rebuilds the ledger **from
the data** — diffing the pre-Step-14 backup against the live database — so
`csv_exports/82_cylinder_changes_step14_ledger.csv` is complete by construction: 127 rows, old and
new values, evidence string each, fully revertible.

## 5. Result

| | before | after |
|---|---:|---:|
| engine rows with an impossible cylinder count | 129 | **31** (all exported, each explained) |
| rows contradicting a `10v` descriptor | 29 | **0** |
| five-cylinder engines correctly recorded | 7 | **94** |
| `displacement_cc` corruptions repaired | — | 4 |

Cylinder distribution is now 3:188 · 4:2,824 · 5:94 · 6:1,795 · 8:614 · 10:44 · 12:62 · 16:1.
The five-cylinder count moving from 7 to 94 is the headline: VW, Volvo, Fiat and Audi inline-fives
had been almost entirely mis-recorded as sixes.

Invariants after apply: **0 fuel conflicts · 0 orphan refs · 0 count mismatches** ·
engines 5,670 · variants 37,444 — all unchanged.
