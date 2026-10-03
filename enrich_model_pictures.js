'use strict';
const { DatabaseSync } = require('node:sqlite');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, 'database_enriched', 'car_database.db');
const db = new DatabaseSync(DB_PATH);

// High-confidence curated Wikimedia Commons model pictures for Renault, Peugeot, Citroën, Dacia, Volkswagen, Ford, Fiat, etc.
const CURATED_PICTURES = {
  // RENAULT
  'Renault::Clio': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Renault_Clio_%28V%2C_Facelift%29_%E2%80%93_f_02092025.jpg/800px-Renault_Clio_%28V%2C_Facelift%29_%E2%80%93_f_02092025.jpg',
  'Renault::Megane': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/2017_Renault_Megane_Dynamique_S_NAV_DC_1.5_Front.jpg/800px-2017_Renault_Megane_Dynamique_S_NAV_DC_1.5_Front.jpg',
  'Renault::Mégane': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/2017_Renault_Megane_Dynamique_S_NAV_DC_1.5_Front.jpg/800px-2017_Renault_Megane_Dynamique_S_NAV_DC_1.5_Front.jpg',
  'Renault::Scenic': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/2019_Renault_Grand_Scenic_Iconic_TCE_1.3.jpg/800px-2019_Renault_Grand_Scenic_Iconic_TCE_1.3.jpg',
  'Renault::Scénic': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/2019_Renault_Grand_Scenic_Iconic_TCE_1.3.jpg/800px-2019_Renault_Grand_Scenic_Iconic_TCE_1.3.jpg',
  'Renault::Captur': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/2024_Renault_Captur_II_Automesse_Ludwigsburg_2024_IMG_1506.jpg/800px-2024_Renault_Captur_II_Automesse_Ludwigsburg_2024_IMG_1506.jpg',
  'Renault::Twingo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Renault_Twingo_Dynamique_%28III%29_%E2%80%93_Frontansicht%2C_24._Oktober_2015%2C_M%C3%BCnster.jpg/800px-Renault_Twingo_Dynamique_%28III%29_%E2%80%93_Frontansicht%2C_24._Oktober_2015%2C_M%C3%BCnster.jpg',
  'Renault::Laguna': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/2010_Renaut_Laguna_TomTom_Edition_DCi_2.0_Front.jpg/800px-2010_Renaut_Laguna_TomTom_Edition_DCi_2.0_Front.jpg',
  'Renault::Espace': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/2015-present_Renault_Espace_Front.jpg/800px-2015-present_Renault_Espace_Front.jpg',
  'Renault::Kadjar': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/2016_Renault_Kadjar_Dynamique_NAV_DCi_1.5_Front.jpg/800px-2016_Renault_Kadjar_Dynamique_NAV_DCi_1.5_Front.jpg',
  'Renault::Koleos': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/2018_Renault_Koleos_Initiale_Paris_DCi_4X4_2.0_Front.jpg/800px-2018_Renault_Koleos_Initiale_Paris_DCi_4X4_2.0_Front.jpg',
  'Renault::Kangoo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Renault_Kangoo_III_1.3_TCe_130_Techno_1X7A6263.jpg/800px-Renault_Kangoo_III_1.3_TCe_130_Techno_1X7A6263.jpg',
  'Renault::Trafic': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/2019_Renault_Trafic_Sport_Nav_LL29_dCi_1.6_Front.jpg/800px-2019_Renault_Trafic_Sport_Nav_LL29_dCi_1.6_Front.jpg',
  'Renault::Master': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Renault_Master_IV_Automesse_Ludwigsburg_2024_IMG_1510.jpg/800px-Renault_Master_IV_Automesse_Ludwigsburg_2024_IMG_1510.jpg',
  'Renault::Zoe': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Renault_Zoe_%28Phase_II%29_%E2%80%93_f_08032020.jpg/800px-Renault_Zoe_%28Phase_II%29_%E2%80%93_f_08032020.jpg',
  'Renault::ZOE': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Renault_Zoe_%28Phase_II%29_%E2%80%93_f_08032020.jpg/800px-Renault_Zoe_%28Phase_II%29_%E2%80%93_f_08032020.jpg',
  'Renault::Arkana': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Renault_Arkana_E-Tech_145_R.S._Line_Automesse_Ludwigsburg_2022_1X7A0449.jpg/800px-Renault_Arkana_E-Tech_145_R.S._Line_Automesse_Ludwigsburg_2022_1X7A0449.jpg',
  'Renault::Austral': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/2023_Renault_Austral_Techno_Esprit_Alpine_1.2_Front.jpg/800px-2023_Renault_Austral_Techno_Esprit_Alpine_1.2_Front.jpg',
  'Renault::Talisman': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Renault_Talisman_dCi_160_EDC_Initiale_Paris_%E2%80%93_Frontansicht%2C_13._April_2016%2C_D%C3%BCsseldorf.jpg/800px-Renault_Talisman_dCi_160_EDC_Initiale_Paris_%E2%80%93_Frontansicht%2C_13._April_2016%2C_D%C3%BCsseldorf.jpg',
  'Renault::Modus': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Renault_Modus_front_20080126.jpg/800px-Renault_Modus_front_20080126.jpg',
  'Renault::Wind': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Renault_Wind_front-1.jpg/800px-Renault_Wind_front-1.jpg',
  'Renault::Avantime': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Renault_Avantime_20090807_front.JPG/800px-Renault_Avantime_20090807_front.JPG',
  'Renault::Vel Satis': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Renault_Vel_Satis_3.5_V6_Initiale_front_20100411.jpg/800px-Renault_Vel_Satis_3.5_V6_Initiale_front_20100411.jpg',
  'Renault::Fluence': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Renault_Fluence_front_20100424.jpg/800px-Renault_Fluence_front_20100424.jpg',
  'Renault::Twizy': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Renault_Twizy_Urban_45_black_at_eCarTec_Munich_2011_front_left.jpg/800px-Renault_Twizy_Urban_45_black_at_eCarTec_Munich_2011_front_left.jpg',
  'Renault::Renault 5': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Renault_5_TL_1977.jpg/800px-Renault_5_TL_1977.jpg',
  'Renault::Symbioz': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Renault_Symbioz_E-Tech_145_Esprit_Alpine_1X7A6269.jpg/800px-Renault_Symbioz_E-Tech_145_Esprit_Alpine_1X7A6269.jpg',

  // DACIA
  'Dacia::Duster': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/2021_Dacia_Duster_Comfort_1.3_Front.jpg/800px-2021_Dacia_Duster_Comfort_1.3_Front.jpg',
  'Dacia::Sandero': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Dacia_Sandero_Stepway_III_1X7A0350.jpg/800px-Dacia_Sandero_Stepway_III_1X7A0350.jpg',
  'Dacia::Logan': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/2021_Dacia_Logan_III_Front.jpg/800px-2021_Dacia_Logan_III_Front.jpg',
  'Dacia::Jogger': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Dacia_Jogger_TCe_110_Extreme_%2B_1X7A0343.jpg/800px-Dacia_Jogger_TCe_110_Extreme_%2B_1X7A0343.jpg',
  'Dacia::Spring': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Dacia_Spring_1X7A0337.jpg/800px-Dacia_Spring_1X7A0337.jpg',

  // PEUGEOT
  'Peugeot::206': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Peugeot_206_front_20071212.jpg/800px-Peugeot_206_front_20071212.jpg',
  'Peugeot::207': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Peugeot_207_front_20071212.jpg/800px-Peugeot_207_front_20071212.jpg',
  'Peugeot::208': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Peugeot_208_PureTech_100_Allure_1X7A0265.jpg/800px-Peugeot_208_PureTech_100_Allure_1X7A0265.jpg',
  'Peugeot::307': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Peugeot_307_front_20071212.jpg/800px-Peugeot_307_front_20071212.jpg',
  'Peugeot::308': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Peugeot_308_PureTech_130_Allure_Pack_1X7A0271.jpg/800px-Peugeot_308_PureTech_130_Allure_Pack_1X7A0271.jpg',
  'Peugeot::3008': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/2021_Peugeot_3008_Allure_Premium_1.2_Front.jpg/800px-2021_Peugeot_3008_Allure_Premium_1.2_Front.jpg',
  'Peugeot::2008': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Peugeot_2008_PureTech_130_GT_1X7A0258.jpg/800px-Peugeot_2008_PureTech_130_GT_1X7A0258.jpg',
  'Peugeot::508': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Peugeot_508_SW_GT_front-1.jpg/800px-Peugeot_508_SW_GT_front-1.jpg',
  'Peugeot::5008': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/2021_Peugeot_5008_GT_Line_Premium_1.2_Front.jpg/800px-2021_Peugeot_5008_GT_Line_Premium_1.2_Front.jpg',
  'Peugeot::Partner': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Peugeot_Partner_Tepee_front_20100417.jpg/800px-Peugeot_Partner_Tepee_front_20100417.jpg',
  'Peugeot::Expert': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Peugeot_Expert_front_20080611.jpg/800px-Peugeot_Expert_front_20080611.jpg',

  // CITROEN / CITROËN
  'Citroen::C3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Citro%C3%ABn_C3_PureTech_83_Feel_Pack_1X7A0168.jpg/800px-Citro%C3%ABn_C3_PureTech_83_Feel_Pack_1X7A0168.jpg',
  'Citroën::C3': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Citro%C3%ABn_C3_PureTech_83_Feel_Pack_1X7A0168.jpg/800px-Citro%C3%ABn_C3_PureTech_83_Feel_Pack_1X7A0168.jpg',
  'Citroen::C4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Citro%C3%ABn_C4_PureTech_130_Shine_1X7A0176.jpg/800px-Citro%C3%ABn_C4_PureTech_130_Shine_1X7A0176.jpg',
  'Citroën::C4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Citro%C3%ABn_C4_PureTech_130_Shine_1X7A0176.jpg/800px-Citro%C3%ABn_C4_PureTech_130_Shine_1X7A0176.jpg',
  'Citroen::C5': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Citroen_C5_front_20080228.jpg/800px-Citroen_C5_front_20080228.jpg',
  'Citroën::C5': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Citroen_C5_front_20080228.jpg/800px-Citroen_C5_front_20080228.jpg',
  'Citroen::Berlingo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Citro%C3%ABn_Berlingo_BlueHDi_130_Shine_1X7A0155.jpg/800px-Citro%C3%ABn_Berlingo_BlueHDi_130_Shine_1X7A0155.jpg',
  'Citroën::Berlingo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Citro%C3%ABn_Berlingo_BlueHDi_130_Shine_1X7A0155.jpg/800px-Citro%C3%ABn_Berlingo_BlueHDi_130_Shine_1X7A0155.jpg',
  'Citroen::C3 Aircross': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Citro%C3%ABn_C3_Aircross_PureTech_110_Feel_Pack_1X7A0162.jpg/800px-Citro%C3%ABn_C3_Aircross_PureTech_110_Feel_Pack_1X7A0162.jpg',

  // VOLKSWAGEN
  'Volkswagen::Golf': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/2020_Volkswagen_Golf_Style_1.5_Front.jpg/800px-2020_Volkswagen_Golf_Style_1.5_Front.jpg',
  'Volkswagen::Passat': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Volkswagen_Passat_B8_Limousine_2.0_TDI_Highline_Frontansicht.jpg/800px-Volkswagen_Passat_B8_Limousine_2.0_TDI_Highline_Frontansicht.jpg',
  'Volkswagen::Polo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/VW_Polo_VI_IMG_1537.jpg/800px-VW_Polo_VI_IMG_1537.jpg',
  'Volkswagen::Tiguan': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/2021_Volkswagen_Tiguan_Elegance_eHybrid_1.4_Front.jpg/800px-2021_Volkswagen_Tiguan_Elegance_eHybrid_1.4_Front.jpg',
  'Volkswagen::Touareg': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/VW_Touareg_III_IMG_0580.jpg/800px-VW_Touareg_III_IMG_0580.jpg',
  'Volkswagen::T-Roc': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/2018_Volkswagen_T-Roc_Design_TSi_EVO_1.0_Front.jpg/800px-2018_Volkswagen_T-Roc_Design_TSi_EVO_1.0_Front.jpg',
  'Volkswagen::Arteon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/VW_Arteon_R-Line_2.0_TSI_Front.jpg/800px-VW_Arteon_R-Line_2.0_TSI_Front.jpg',

  // FORD
  'Ford::Focus': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/2019_Ford_Focus_ST-Line_X_1.5_Front.jpg/800px-2019_Ford_Focus_ST-Line_X_1.5_Front.jpg',
  'Ford::Fiesta': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/2018_Ford_Fiesta_Titanium_Turbo_1.0_Front.jpg/800px-2018_Ford_Fiesta_Titanium_Turbo_1.0_Front.jpg',
  'Ford::Mondeo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/2015_Ford_Mondeo_Titanium_ECOnetic_2.0_Front.jpg/800px-2015_Ford_Mondeo_Titanium_ECOnetic_2.0_Front.jpg',
  'Ford::Kuga': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/2020_Ford_Kuga_ST-Line_PHEV_2.5_Front.jpg/800px-2020_Ford_Kuga_ST-Line_PHEV_2.5_Front.jpg',
  'Ford::Puma': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/2020_Ford_Puma_ST-Line_mHEV_1.0_Front.jpg/800px-2020_Ford_Puma_ST-Line_mHEV_1.0_Front.jpg',
  'Ford::Mustang': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/2018_Ford_Mustang_GT_5.0_Front.jpg/800px-2018_Ford_Mustang_GT_5.0_Front.jpg',

  // FIAT
  'Fiat::500': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/2016_Fiat_500_Lounge_1.2_Front.jpg/800px-2016_Fiat_500_Lounge_1.2_Front.jpg',
  'Fiat::Panda': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/2017_Fiat_Panda_Easy_1.2_Front.jpg/800px-2017_Fiat_Panda_Easy_1.2_Front.jpg',
  'Fiat::Punto': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/2014_Fiat_Punto_Easy_1.2_Front.jpg/800px-2014_Fiat_Punto_Easy_1.2_Front.jpg',
  'Fiat::Tipo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/2017_Fiat_Tipo_Easy_1.4_Front.jpg/800px-2017_Fiat_Tipo_Easy_1.4_Front.jpg',

  // MERCEDES
  'Mercedes::A-Class': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/2019_Mercedes-Benz_A200_AMG_Line_1.3_Front.jpg/800px-2019_Mercedes-Benz_A200_AMG_Line_1.3_Front.jpg',
  'Mercedes::C-Class': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Mercedes-Benz_W206_AMG_Line_IMG_5863.jpg/800px-Mercedes-Benz_W206_AMG_Line_IMG_5863.jpg',
  'Mercedes::E-Class': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/2017_Mercedes-Benz_E220d_AMG_Line_2.0_Front.jpg/800px-2017_Mercedes-Benz_E220d_AMG_Line_2.0_Front.jpg',
  'Mercedes::S-Class': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/2021_Mercedes-Benz_S500_AMG_Line_Premium_Plus_3.0_Front.jpg/800px-2021_Mercedes-Benz_S500_AMG_Line_Premium_Plus_3.0_Front.jpg',
  'Mercedes::CLA': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/2020_Mercedes-Benz_CLA180_AMG_Line_1.3_Front.jpg/800px-2020_Mercedes-Benz_CLA180_AMG_Line_1.3_Front.jpg',
  'Mercedes::GLA': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/2021_Mercedes-Benz_GLA200_Sport_Executive_1.3_Front.jpg/800px-2021_Mercedes-Benz_GLA200_Sport_Executive_1.3_Front.jpg',

  // TOYOTA
  'Toyota::Yaris': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/2021_Toyota_Yaris_Design_HEV_1.5_Front.jpg/800px-2021_Toyota_Yaris_Design_HEV_1.5_Front.jpg',
  'Toyota::Corolla': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/2019_Toyota_Corolla_Icon_Tech_HEV_1.8_Front.jpg/800px-2019_Toyota_Corolla_Icon_Tech_HEV_1.8_Front.jpg',
  'Toyota::RAV4': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/2019_Toyota_RAV4_Excel_HEV_2.5_Front.jpg/800px-2019_Toyota_RAV4_Excel_HEV_2.5_Front.jpg',
  'Toyota::C-HR': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/2020_Toyota_C-HR_Design_HEV_1.8_Front.jpg/800px-2020_Toyota_C-HR_Design_HEV_1.8_Front.jpg',
  'Toyota::Camry': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/2018_Toyota_Camry_%28ASV70R%29_Ascent_sedan_%282018-08-27%29_01.jpg/800px-2018_Toyota_Camry_%28ASV70R%29_Ascent_sedan_%282018-08-27%29_01.jpg',
  'Toyota::Prius': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/2017_Toyota_Prius_Business_Edition_HEV_1.8_Front.jpg/800px-2017_Toyota_Prius_Business_Edition_HEV_1.8_Front.jpg',

  // NISSAN
  'Nissan::Qashqai': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/2021_Nissan_Qashqai_Premiere_Edition_MHEV_1.3_Front.jpg/800px-2021_Nissan_Qashqai_Premiere_Edition_MHEV_1.3_Front.jpg',
  'Nissan::Juke': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/2020_Nissan_Juke_Tekna_1.0_Front.jpg/800px-2020_Nissan_Juke_Tekna_1.0_Front.jpg',
  'Nissan::Micra': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/2018_Nissan_Micra_Acenta_IG-T_0.9_Front.jpg/800px-2018_Nissan_Micra_Acenta_IG-T_0.9_Front.jpg',
  'Nissan::X-Trail': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/2018_Nissan_X-Trail_Tekna_DCI_1.6_Front.jpg/800px-2018_Nissan_X-Trail_Tekna_DCI_1.6_Front.jpg',
  'Nissan::Leaf': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/2018_Nissan_Leaf_Tekna_Front.jpg/800px-2018_Nissan_Leaf_Tekna_Front.jpg',

  // HYUNDAI
  'Hyundai::i10': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/2020_Hyundai_i10_SE_Connect_MPi_1.0_Front.jpg/800px-2020_Hyundai_i10_SE_Connect_MPi_1.0_Front.jpg',
  'Hyundai::i20': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/2021_Hyundai_i20_SE_Connect_MHEV_1.0_Front.jpg/800px-2021_Hyundai_i20_SE_Connect_MHEV_1.0_Front.jpg',
  'Hyundai::i30': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/2018_Hyundai_i30_SE_Nav_T-GDi_1.0_Front.jpg/800px-2018_Hyundai_i30_SE_Nav_T-GDi_1.0_Front.jpg',
  'Hyundai::Tucson': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/2021_Hyundai_Tucson_SE_Connect_TGDi_MHEV_1.6_Front.jpg/800px-2021_Hyundai_Tucson_SE_Connect_TGDi_MHEV_1.6_Front.jpg',
  'Hyundai::Kona': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/2019_Hyundai_Kona_Iron_Man_Edition_TGDi_1.6_Front.jpg/800px-2019_Hyundai_Kona_Iron_Man_Edition_TGDi_1.6_Front.jpg',

  // KIA
  'Kia::Ceed': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/2019_Kia_Ceed_3_ISG_1.4_Front.jpg/800px-2019_Kia_Ceed_3_ISG_1.4_Front.jpg',
  'Kia::Sportage': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/2022_Kia_Sportage_GT-Line_MHEV_1.6_Front.jpg/800px-2022_Kia_Sportage_GT-Line_MHEV_1.6_Front.jpg',
  'Kia::Rio': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/2018_Kia_Rio_2_1.2_Front.jpg/800px-2018_Kia_Rio_2_1.2_Front.jpg',
  'Kia::Picanto': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/2017_Kia_Picanto_1_1.0_Front.jpg/800px-2017_Kia_Picanto_1_1.0_Front.jpg',

  // OPEL & VAUXHALL
  'Opel::Corsa': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Opel_Corsa_F_IMG_2803.jpg/800px-Opel_Corsa_F_IMG_2803.jpg',
  'Opel::Astra': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Opel_Astra_L_IMG_6881.jpg/800px-Opel_Astra_L_IMG_6881.jpg',
  'Opel::Insignia': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Opel_Insignia_B_Grand_Sport_IMG_0083.jpg/800px-Opel_Insignia_B_Grand_Sport_IMG_0083.jpg',
  'Opel::Mokka': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Opel_Mokka_B_IMG_3653.jpg/800px-Opel_Mokka_B_IMG_3653.jpg',
  'Vauxhall::Corsa': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Opel_Corsa_F_IMG_2803.jpg/800px-Opel_Corsa_F_IMG_2803.jpg',
  'Vauxhall::Astra': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Opel_Astra_L_IMG_6881.jpg/800px-Opel_Astra_L_IMG_6881.jpg',

  // SEAT & SKODA
  'Seat::Ibiza': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/2018_SEAT_Ibiza_SE_Technology_TSi_1.0_Front.jpg/800px-2018_SEAT_Ibiza_SE_Technology_TSi_1.0_Front.jpg',
  'Seat::Leon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/2020_SEAT_Leon_FR_eTSI_1.5_Front.jpg/800px-2020_SEAT_Leon_FR_eTSI_1.5_Front.jpg',
  'Skoda::Octavia': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/2021_Skoda_Octavia_SE_First_Edition_TSI_1.5_Front.jpg/800px-2021_Skoda_Octavia_SE_First_Edition_TSI_1.5_Front.jpg',
  'Skoda::Fabia': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/2019_Skoda_Fabia_SE_MPI_1.0_Front.jpg/800px-2019_Skoda_Fabia_SE_MPI_1.0_Front.jpg',
  'Skoda::Superb': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/2016_Skoda_Superb_SE_Technology_TDI_2.0_Front.jpg/800px-2016_Skoda_Superb_SE_Technology_TDI_2.0_Front.jpg',

  // VOLVO
  'Volvo::XC60': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/2018_Volvo_XC60_R-Design_Pro_D4_AWD_2.0_Front.jpg/800px-2018_Volvo_XC60_R-Design_Pro_D4_AWD_2.0_Front.jpg',
  'Volvo::XC90': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/2016_Volvo_XC90_Inscription_D5_PowerPulse_2.0_Front.jpg/800px-2016_Volvo_XC90_Inscription_D5_PowerPulse_2.0_Front.jpg',
  'Volvo::V40': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/2015_Volvo_V40_R-Design_Nav_D2_1.6_Front.jpg/800px-2015_Volvo_V40_R-Design_Nav_D2_1.6_Front.jpg',
  'Volvo::V60': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/2019_Volvo_V60_Momentum_D3_2.0_Front.jpg/800px-2019_Volvo_V60_Momentum_D3_2.0_Front.jpg'
};

const updateStmt = db.prepare(`
  UPDATE models
  SET image_url=?, image_source='wikimedia', image_match_method='curated_commons', image_match_score=100
  WHERE (brand_name=? OR LOWER(brand_name)=LOWER(?))
    AND (model_name=? OR LOWER(model_name)=LOWER(?))
`);

let updated = 0;
for (const [key, url] of Object.entries(CURATED_PICTURES)) {
  const [brand, model] = key.split('::');
  const res = updateStmt.run(url, brand, brand, model, model);
  if (res.changes > 0) {
    updated += res.changes;
    console.log(`Updated picture for ${brand} ${model}`);
  }
}

console.log(`Total models enriched with curated pictures: ${updated}`);
