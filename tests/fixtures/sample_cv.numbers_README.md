# Sample CV.numbers Mock File

**Purpose**: Mock CV.numbers file for testing Feature 003 (People Profile Sync)

**Note**: This is a placeholder. The actual `sample_cv.numbers` file should be created using Apple Numbers with the following structure:

## Required Sheets

1. **Graduate PhD**
   - Columns: Name, Years, Degree, Institution, Research
   - Sample entries: 3-5 PhD students with complete data

2. **Postdoc**
   - Columns: Name, Years, Institution, Research
   - Sample entries: 2-3 postdocs

3. **Graduate MA_MS**
   - Columns: Name, Years, Degree, Institution
   - Sample entries: 1-2 Master's students

4. **Undergrad**
   - Columns: Name, Years
   - Sample entries: 2-3 undergraduates

5. **Visitors**
   - Columns: Name, Years, Institution, Visitor Type
   - Sample entries: 1-2 visitors

## Test Cases to Include

- **Duplicate person**: Same person appearing in multiple sheets (e.g., "John Doe" in both Postdoc and Visitor sheets)
- **Missing data**: Entries with empty Institution or Research fields
- **Special characters**: Names with apostrophes (O'Donnell), hyphens (Smith-Jones)
- **Invalid years**: Entries like "TBD", "N/A" to test error handling

## Creating the File

1. Open Apple Numbers
2. Create new spreadsheet
3. Add 5 sheets with names matching above
4. Populate with sample data following patterns in contracts/cv-sheet-schema.yml
5. Save as `sample_cv.numbers`
6. Place in `tests/fixtures/` directory

For automated testing without Numbers app, use numbers-parser to create programmatically or mock the Document object.
