# How to Add New Medical Cases to MEDLEY

This guide explains how to add new pre-analyzed medical cases to the MEDLEY system that will appear in the "Explore Medical Cases" section of the web interface.

## Overview

New cases are generated using the same pipeline as Cases 1-12 to ensure:
- Consistent green theme (#16a34a) in reports
- Same comprehensive report structure
- Proper caching and model responses
- Integration with web interface

## Step-by-Step Instructions

### 1. Create the Case File

Create a new text file in the `usecases/` directory following the naming convention:
```
case_XXX_description.txt
```

Example: `case_013_complex_urology.txt`

The case file should contain:
- Patient demographics
- Chief complaint
- History of present illness
- Past medical history
- Physical examination
- Laboratory results
- Imaging findings

### 2. Generate the Case Reports

Use the `add_new_case.py` script to generate reports:

```bash
# Basic usage with free models
python add_new_case.py 13 usecases/case_013_complex_urology.txt

# With premium models for better quality
python add_new_case.py 13 usecases/case_013_complex_urology.txt --paid

# With full metadata for web interface
python add_new_case.py 13 usecases/case_013_complex_urology.txt \
  --title "Case 13: Complex Glomerulonephritis" \
  --specialty "Nephrology/Rheumatology" \
  --description "Young male with recurrent hematuria and renal dysfunction" \
  --bias "Ethnic and age-related diagnostic bias" \
  --paid
```

### 3. Verify Generated Files

After running the script, verify these files were created:

**Reports Directory:**
- `reports/FINAL_Case_13_comprehensive_[timestamp].pdf` - Main PDF report
- `reports/FINAL_Case_13_comprehensive_[timestamp].html` - HTML version

**Cache Directory:**
- `cache/responses/Case_13/*.json` - Individual model responses
- `cache/orchestrator/Case_13/*.json` - Orchestrator synthesis

### 4. Add to Web Interface

Edit `web_app.py` and add the new case to the `MEDICAL_CASES` list:

```python
MEDICAL_CASES = [
    # ... existing cases ...
    {
        'id': 'case_013',
        'title': 'Case 13: Complex Glomerulonephritis',
        'specialty': 'Nephrology/Rheumatology',
        'description': 'Young male with recurrent hematuria and renal dysfunction',
        'bias_focus': 'Ethnic and age-related diagnostic bias',
        'file': 'usecases/case_013_complex_urology.txt'
    }
]
```

### 5. Restart Web Server

Restart the web application to load the new case:

```bash
# Stop current server (Ctrl+C)
# Restart
python web_app.py
```

## Example: Adding Case 13 (Complex Urology)

### Step 1: Case file already created
`usecases/case_013_complex_urology.txt` contains the full medical case

### Step 2: Generate reports
```bash
python add_new_case.py 13 usecases/case_013_complex_urology.txt \
  --title "Case 13: Complex Glomerulonephritis" \
  --specialty "Nephrology/Rheumatology" \
  --description "Young male with recurrent hematuria and renal dysfunction" \
  --bias "Ethnic and age-related diagnostic bias"
```

### Step 3: Add to web interface
The script will output the exact configuration to add to `web_app.py`

## Important Notes

1. **Consistency**: Always use `general_medical_pipeline.py` through the `add_new_case.py` script to ensure consistent formatting

2. **Model Selection**: 
   - Free models: Faster but lower quality analysis
   - Paid models: Better diagnostic accuracy and bias detection

3. **Cache Management**: Cases are cached to avoid redundant API calls. To regenerate, delete the cache folder for that case

4. **Report Theme**: Reports automatically use the green theme (#16a34a) matching Cases 1-12

5. **Naming Convention**: Follow the pattern `case_XXX_description.txt` where XXX is the zero-padded case number

## Troubleshooting

### Reports not generating
- Check API keys are configured
- Verify case file exists and is readable
- Check console output for specific errors

### Wrong theme or format
- Ensure using `add_new_case.py` script, not direct CLI
- Verify `general_medical_pipeline.py` hasn't been modified

### Case not appearing in web interface
- Verify case was added to `MEDICAL_CASES` list
- Restart web server after changes
- Check browser cache (force refresh with Ctrl+F5)

## Pipeline Architecture

The case generation pipeline:
1. Reads case file from `usecases/`
2. Queries all configured AI models for diagnoses
3. Uses orchestrator to synthesize consensus
4. Generates comprehensive bias analysis
5. Creates PDF and HTML reports with consistent formatting
6. Caches all responses for future use

## Adding Multiple Cases

To add multiple cases efficiently:

```bash
# Create a batch script
for i in {13..20}; do
    python add_new_case.py $i usecases/case_${i}*.txt
done
```

## Contact

For questions or issues with case generation:
- Author: Farhad Abtahi
- Institution: SMAILE at Karolinska Institutet
- Website: smile.ki.se