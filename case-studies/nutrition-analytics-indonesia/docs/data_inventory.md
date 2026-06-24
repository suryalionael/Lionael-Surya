# Data Inventory

Generated automatically from `data/raw/_manifest.jsonl`, `config/metadata.yml`, and `docs/data_contracts/`. Do not hand-edit this file -- run `python -m src.ingestion.build_inventory` (or `make inventory`) after any ingestion change.

| Dataset | Source | Vintage | Granularity | Rows | Validation | Manifest file |
|---|---|---|---|---|---|---|
| Province Administrative Boundaries | GADM (derived from official boundary data) | gadm | province | 34 | passed | `data/raw/boundaries/boundaries_gadm/boundaries_gadm_2026-06-23T022012Z.geojson` |
| School Participation Rate | BPS (Badan Pusat Statistik) | 2023 | province | 105 | passed | `data/raw/education/education_2026-06-23T022005Z.csv` |
| Adjusted Per-Capita Expenditure | BPS (Badan Pusat Statistik) | 2025 | province | 110 | passed | `data/raw/expenditure/expenditure_2026-06-23T022011Z.csv` |
| Human Development Index | BPS (Badan Pusat Statistik) | 2024 | province | 117 | passed | `data/raw/ipm/ipm_2026-06-23T021743Z.csv` |
| Population | BPS (Badan Pusat Statistik) | 2020 | province | 105 | passed | `data/raw/population/population_2026-06-23T021750Z.csv` |
| Poverty Rate | BPS (Badan Pusat Statistik) | 2025 | province | 78 | passed | `data/raw/poverty/poverty_2026-06-23T021741Z.csv` |
| Child Stunting Prevalence | Kemenkes / TP2S (dashboard.stunting.go.id) -- manual export (xlsx crosstab) | 2024 | province | 38 | passed | `data/raw/stunting/stunting_2026-06-23T022016Z.csv` |

## Dataset Detail

### Province Administrative Boundaries (`boundaries`)

- **Source organization & URL:** GADM (derived from official boundary data) — https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IDN_1.json
- **Unit:** polygon geometry
- **Publication / fetch vintage:** gadm
- **Fetched at (UTC):** 2026-06-23T02:20:15Z
- **Geographic granularity:** Province
- **Required columns:** province_name
- **Rows / columns:** 34 / 1
- **File size:** 2963425 bytes
- **SHA-256:** `6bbc25b5f96d2b45fae45ac3e3a74712d56d24584d9341303358a6702653398a`
- **Validation status:** passed

### School Participation Rate (`education`)

- **Source organization & URL:** BPS (Badan Pusat Statistik) — https://www.bps.go.id/id/statistics-table/2/MzAxIzI=/angka-partisipasi-sekolah--aps--menurut-provinsi.html
- **Unit:** percent
- **Publication / fetch vintage:** 2023
- **Fetched at (UTC):** 2026-06-23T02:20:05Z
- **Geographic granularity:** Province
- **Required columns:** province, year, participation_rate
- **Rows / columns:** 105 / 3
- **File size:** 2525 bytes
- **SHA-256:** `5b62a37dd370501a03e21fa32bab6f2f1e9f81b223d9f29d6f801150fe1a04d7`
- **Validation status:** passed

### Adjusted Per-Capita Expenditure (`expenditure`)

- **Source organization & URL:** BPS (Badan Pusat Statistik) — https://www.bps.go.id/
- **Unit:** thousand IDR/person/year (PPP-adjusted, IPM-component basis)
- **Publication / fetch vintage:** 2025
- **Fetched at (UTC):** 2026-06-23T02:20:11Z
- **Geographic granularity:** Province
- **Required columns:** province, year, expenditure_per_capita
- **Rows / columns:** 110 / 3
- **File size:** 2683 bytes
- **SHA-256:** `62ffea6cbf9a8553a43e2dcc7476ea1c56c6d2bfee006b091acf0a9c92e3e058`
- **Validation status:** passed

### Human Development Index (`ipm`)

- **Source organization & URL:** BPS (Badan Pusat Statistik) — https://www.bps.go.id/indicator/26/413/1/-metode-baru-indeks-pembangunan-manusia.html
- **Unit:** index (0-100)
- **Publication / fetch vintage:** 2024
- **Fetched at (UTC):** 2026-06-23T02:17:43Z
- **Geographic granularity:** Province
- **Required columns:** province, year, ipm
- **Rows / columns:** 117 / 3
- **File size:** 2823 bytes
- **SHA-256:** `d34c0316dcd5f7c91d05da125d57a2cd63b3a81ac710dbc81e07cad120060931`
- **Validation status:** passed

### Population (`population`)

- **Source organization & URL:** BPS (Badan Pusat Statistik) — https://www.bps.go.id/
- **Unit:** people
- **Publication / fetch vintage:** 2020
- **Fetched at (UTC):** 2026-06-23T02:17:50Z
- **Geographic granularity:** Province
- **Required columns:** province, year, population
- **Rows / columns:** 105 / 3
- **File size:** 2653 bytes
- **SHA-256:** `5e47ee1700cdbb99408129b13f979e39f87dbc2e37c7808eabca1b44c45da776`
- **Validation status:** passed

### Poverty Rate (`poverty`)

- **Source organization & URL:** BPS (Badan Pusat Statistik) — https://www.bps.go.id/indicator/23/192/1/persentase-penduduk-miskin-menurut-provinsi.html
- **Unit:** percent
- **Publication / fetch vintage:** 2025
- **Fetched at (UTC):** 2026-06-23T02:17:41Z
- **Geographic granularity:** Province
- **Required columns:** province, year, poverty_rate
- **Rows / columns:** 78 / 3
- **File size:** 1854 bytes
- **SHA-256:** `dd1d0a07451eb1b5027da17d7832224353a30eb9ea7c922ca537936e9e48654e`
- **Validation status:** passed

### Child Stunting Prevalence (`stunting`)

- **Source organization & URL:** Kemenkes / TP2S (dashboard.stunting.go.id) -- manual export (xlsx crosstab) — https://dashboard.stunting.go.id/masalah-gizi-pada-balita/
- **Unit:** percent
- **Publication / fetch vintage:** 2024
- **Fetched at (UTC):** 2026-06-23T02:20:16Z
- **Geographic granularity:** Province
- **Required columns:** province, year, stunting_rate, stunting_category
- **Rows / columns:** 38 / 4
- **File size:** 1640 bytes
- **SHA-256:** `ce43c41f04deb0c871ad7a94a0b73aaeb2c89342485e33eb1b804ae5c1f1c5eb`
- **Validation status:** passed

