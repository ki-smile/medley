#!/bin/bash

echo "Running remaining cases..."

# Case 4
echo "========== Case 4 =========="
python general_medical_pipeline.py "Case_4" "usecases/case_004_rare_genetic.txt" 2>&1 | tail -8

# Case 5
echo "========== Case 5 =========="
python general_medical_pipeline.py "Case_5" "usecases/case_005_environmental.txt" 2>&1 | tail -8

# Case 6
echo "========== Case 6 =========="
python general_medical_pipeline.py "Case_6" "usecases/case_006_disability_communication.txt" 2>&1 | tail -8

# Case 7
echo "========== Case 7 =========="
python general_medical_pipeline.py "Case_7" "usecases/case_007_gender_identity.txt" 2>&1 | tail -8

# Case 8
echo "========== Case 8 =========="
python general_medical_pipeline.py "Case_8" "usecases/case_008_rural_healthcare.txt" 2>&1 | tail -8

# Case 9
echo "========== Case 9 =========="
python general_medical_pipeline.py "Case_9" "usecases/case_009_weight_bias.txt" 2>&1 | tail -8

# Case 10
echo "========== Case 10 =========="
python general_medical_pipeline.py "Case_10" "usecases/case_010_migration_trauma.txt" 2>&1 | tail -8

# Case 11
echo "========== Case 11 =========="
python general_medical_pipeline.py "Case_11" "usecases/case_011_ethnic_medication.txt" 2>&1 | tail -8

echo "All cases completed!"