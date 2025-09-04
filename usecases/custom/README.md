# Custom Cases Folder

This folder contains user-submitted custom medical cases analyzed through the MEDLEY web interface.

## Purpose
- Keeps custom cases separate from predefined use cases
- Maintains organization between system cases and user cases
- Allows easy identification of user-generated content

## File Naming Convention
Custom case files are automatically named with the format:
- `custom_YYYYMMDD_HHMMSS.txt`

Example: `custom_20250812_143025.txt`

## Privacy Note
These files may contain sensitive medical information. Please ensure:
- Do not commit real patient data to version control
- Use anonymized or fictional cases for testing
- Add this folder to `.gitignore` if using version control

## Usage
Files in this folder are automatically created when users:
1. Navigate to the `/analyze` page in the web interface
2. Enter a custom case description
3. Submit for analysis

The analysis results are stored in:
- JSON: `/reports/custom_YYYYMMDD_HHMMSS_ensemble_data.json`
- PDF: `/reports/FINAL_custom_YYYYMMDD_HHMMSS_comprehensive.pdf`

## Cleanup
Periodically review and clean up old custom cases to manage disk space.
Consider implementing automatic cleanup for cases older than a certain period.