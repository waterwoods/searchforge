# Add-Car C+ scenario library run

- Generated: 2026-04-25T02:10:36.693463+00:00
- Scenarios: 150
- Pass: 134  Fail: 16
- Elapsed: 29.899s

## By category

- **adversarial**: 2/2 pass
- **cross_intent**: 3/4 pass
- **destruction_billing_tease**: 16/18 pass
- **destruction_drip**: 16/18 pass
- **destruction_flip**: 16/18 pass
- **destruction_mixed**: 16/18 pass
- **destruction_ocrish**: 15/17 pass
- **destruction_restate**: 17/18 pass
- **destruction_silent_zip**: 16/17 pass
- **identity_collapse**: 3/4 pass
- **long_drift**: 3/3 pass
- **multi_entity_chaos**: 0/2 pass
- **noisy_real_world**: 2/2 pass
- **self_contradiction**: 3/3 pass
- **silent_correction**: 1/1 pass
- **system_challenge**: 2/2 pass
- **temporal_confusion**: 3/3 pass

## Top failure patterns

- summary_or_substring_mismatch: 17

## Failed scenarios (sample)

### dest_id_01

- turn 7: primary_vehicle_summary: missing substring 'Camry' in '2020 Tesla'
- turn 7: primary_vehicle_summary: should not contain 'Tesla'

### dest_me_01

- turn 7: primary_vehicle_summary: missing substring 'Camry' in '2019 Honda CR-V'

### dest_me_02

- turn 7: primary_vehicle_summary: missing substring 'Camry' in '2020 Honda CR-V'

### dest_ex_05

- turn 7: primary_vehicle_summary: missing substring 'WRX' in '2019 Subaru'

### dest_p_001

- turn 7: primary_vehicle_summary: missing substring 'Camry' in '2020'

### dest_p_012

- turn 10: primary_vehicle_summary: missing substring 'Telluride' in '2021'

### dest_p_023

- turn 13: primary_vehicle_summary: missing substring 'Outback' in '2022'

### dest_p_034

- turn 8: primary_vehicle_summary: missing substring 'Civic' in '2019'

### dest_p_045

- turn 11: primary_vehicle_summary: missing substring 'Accord' in '2021'

### dest_p_056

- turn 14: primary_vehicle_summary: missing substring 'Accord' in '2022'

### dest_p_067

- turn 9: primary_vehicle_summary: missing substring '4Runner' in '2022'

### dest_p_078

- turn 12: primary_vehicle_summary: missing substring 'F-150' in '2021'

### dest_p_089

- turn 7: primary_vehicle_summary: missing substring 'RAV4' in '2021'

### dest_p_100

- turn 10: primary_vehicle_summary: missing substring 'Model Y' in '2022'

### dest_p_111

- turn 13: primary_vehicle_summary: missing substring 'Model 3' in '2023'

### dest_p_122

- turn 8: primary_vehicle_summary: missing substring 'Highlander' in '2023'
