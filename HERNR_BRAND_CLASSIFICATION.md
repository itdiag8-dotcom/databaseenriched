# HERNR car-brand classification

The placeholder values matching `hernr_<number>` in `database_enriched/car_database.db` were classified from their vehicle model names and replaced in the `brands`, `models`, `vehicle_variants`, and `brand_logos` tables. `models.brand_id` was also re-linked to the canonical brand row.

The database no longer contains any `hernr_` brand values.

## Classification map

```text
hernr_124 Yugo; hernr_171 Santana; hernr_178 Tata; hernr_181 Piaggio; hernr_609 AC; hernr_694 Renault; hernr_701 Lamborghini; hernr_705 Rolls-Royce; hernr_774 Pontiac; hernr_775 Daewoo; hernr_788 Bugatti; hernr_802 Lotus; hernr_803 Morgan; hernr_815 Bentley; hernr_907 Caterham
hernr_1138 Smart; hernr_1139 ZAZ; hernr_1280 Mahindra; hernr_1480 Abarth; hernr_1490 Caterham; hernr_1505 Acura; hernr_1506 Hummer; hernr_1513 Lada; hernr_1516 MZ; hernr_1518 McLaren; hernr_1520 London Taxi; hernr_1526 Infiniti; hernr_1533 Perodua; hernr_1553 UAZ; hernr_1556 Venturi; hernr_1558 Wiesmann
hernr_2164 Maybach; hernr_2242 Proton; hernr_2589 Landwind; hernr_2590 Geely; hernr_2755 Donkervoort; hernr_2760 KTM; hernr_2852 Zhonghua; hernr_2855 Mitsubishi; hernr_2857 Rover; hernr_2863 Kandi; hernr_2864 Ford; hernr_2866 Haima; hernr_2867 Foton; hernr_2887 Chery; hernr_2888 JAC; hernr_2901 Mitsuoka; hernr_2902 Jiangling; hernr_2903 Great Wall; hernr_2904 Mitsuoka; hernr_2906 Eagle
hernr_3035 Volkswagen; hernr_3047 London Taxi; hernr_3070 Proton; hernr_3071 Foton; hernr_3076 Brilliance; hernr_3086 Lifan; hernr_3122 BYD; hernr_3124 BMW; hernr_3127 Kia; hernr_3129 Honda; hernr_3130 Toyota; hernr_3133 BMW; hernr_3137 Toyota; hernr_3141 Nissan; hernr_3156 Landwind; hernr_3158 XML; hernr_3208 Renault Samsung; hernr_3276 Holden; hernr_3297 Ford; hernr_3300 Maxus; hernr_3332 Geely; hernr_3495 Zenvo; hernr_3497 DR Automobiles; hernr_3514 Honda; hernr_3652 Bufori; hernr_3677 Isuzu; hernr_3697 GTA Motor; hernr_3742 FAW; hernr_3762 FAW; hernr_3913 Vencer; hernr_4176 Haval; hernr_4260 Renault Samsung
```

The classification is model-name based; the less common entries (for example XML, GTA Motor, Vencer, Bufori, Kandi, and Eagle) should be manually reviewed if the source catalog needs a stricter regional-brand taxonomy.
