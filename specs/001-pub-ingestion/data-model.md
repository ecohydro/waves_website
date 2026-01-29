# Data Model: Publication Ingestion

**Branch**: `001-pub-ingestion` | **Date**: 2026-01-29

## Entities

### SpreadsheetRow (input, read-only)

Represents a single row from the Publications sheet in `CV.numbers`.

| Field | Source Column | Type | Required | Notes |
|-------|--------------|------|----------|-------|
| `num` | `NUM` (col 0) | int | yes | Sequential row number (1-159), not used as website ID |
| `year` | `YEAR` (col 1) | int | yes | Publication year (2000-2026) |
| `pub_type` | `Type` (col 2) | str | yes | `P`, `R`, or `D`. Only `P` rows are ingested |
| `title` | `TITLE` (col 3) | str | yes | Full publication title |
| `doi` | `DOI` (col 4) | str | no | DOI string or `-` if absent |
| `journal` | `PUBLISHER` (col 5) | str | yes | Journal or publisher name |
| `kind` | `Kind` (col 10) | str | no | `RA`, `BC`, `CP`, `EC` |
| `authors` | `A1`-`A31` (cols 20-50) | list[str] | yes | Ordered author names (up to 31) |
| `volume` | `VOL` (col 55) | str | no | Volume string (e.g., `98(3-4)`) |
| `pages` | `PAGES` (col 56) | str | no | Page range (e.g., `376-388`) |
| `abstract` | `Abstract` (col 86) | str | no | Full abstract text |
| `undergrad_author` | `Undergrad Author` (col 14) | str | no | Author position (e.g., `A1`) |
| `visitor_author` | `Visitor Author` (col 15) | str | no | Author position |
| `phd_committee` | `PhD Committee Member` (col 16) | str | no | Author position |
| `graduate_advisee` | `Graduate Advisee` (col 17) | str | no | Author position |
| `postdoc_advisee` | `Postdoctoral Advisee` (col 18) | str | no | Author position |
| `pi_author` | `PI Author` (col 19) | str | no | Author position |

### PublicationEntry (output, written to disk)

Represents a Jekyll collection markdown file in `_publications/`.

**Filename**: `{PrimaryAuthorLastName}{Year}_{id}.md`

#### YAML Frontmatter

| Field | Type | Required | Derivation |
|-------|------|----------|------------|
| `author` | str | yes | Group member with earliest author position per FR-014 |
| `date` | datetime | yes | `{year}-01-01 00:00:00` |
| `id` | int | yes | Random 4-digit (1000-9999), collision-checked |
| `year` | str | yes | Quoted string from `YEAR` column |
| `title` | str | yes | Direct from `TITLE` column |
| `doi` | str | conditional | From `DOI` column; omitted if `-` or empty |
| `excerpt` | str | yes | Formatted citation (see Citation Format below) |
| `header.teaser` | str | yes | `assets/images/publications/{LastName}{Year}_{id}.png` |
| `portfolio-item-category` | list[str] | yes | Always `["publications"]` |
| `portfolio-item-tag` | list[str] | yes | `["{year}", "{journal}"]` |
| `author-tags` | list[str] | yes | All group members found in A1-A31 |

#### Markdown Body

```markdown
![ first page ]( {{ "assets/images/publications/{LastName}{Year}_{id}_figure.png" | absolute_url }} ){:class="img-responsive" width="50%" .align-right}

> {FullCitation}

**Abstract**: {abstract text}

[Go to the Article](https://www.doi.org/{doi}){: .btn .btn--success}
```

### AuthorRegistry (reference, read-only)

Represents the `_data/authors.yml` file.

| Field | Type | Notes |
|-------|------|-------|
| YAML key | str | Top-level key, used for matching (e.g., `Natasha Krell`) |
| `name` | str | Display name (usually identical to key) |

**Special case**: "Kelly Caylor" is the site owner defined in `_config.yml`, not in `authors.yml`, but is treated as a valid group member for matching.

## Relationships

```text
SpreadsheetRow (1) --[ingests to]--> (0..1) PublicationEntry
  - Only rows with pub_type = "P" and no existing DOI/title match

SpreadsheetRow.authors (many) --[cross-ref]--> AuthorRegistry
  - Produces author-tags list and determines primary author

PublicationEntry.id --[unique across]--> all existing PublicationEntry files
  - Validated at generation time; no filesystem collisions allowed
```

## Citation Format

The `excerpt` field and body blockquote follow the existing citation pattern:

**Excerpt** (short form for listings):
```
"LastName, F. et al. (Year). Title. _Journal_, doi:DOI."
```

**Body blockquote** (full form with all authors):
```
> LastName1, F.M., LastName2, G., ... & LastNameN, H. (Year). Title. _Journal_, Vol(Issue), Pages, doi:DOI.
```

### Author Name Formatting in Citations

- Spreadsheet stores full names: `Kelly Caylor`, `Natasha Krell`
- Citation format uses: `Caylor, K.K.`, `Krell, N.`
- Transformation: split name into parts, use last part as surname, initial(s) from remaining parts
- Handle multi-part surnames and suffixes as edge cases

## Validation Rules

| Rule | Source | Enforcement |
|------|--------|-------------|
| `pub_type` must be `P` | FR-002 | Skip row if not `P` |
| `title` must be non-empty | FR-011 | Skip row; report as error |
| `year` must be valid integer | FR-011 | Skip row; report as error |
| `doi` uniqueness across existing files | FR-004 | Skip row if DOI already exists |
| `id` uniqueness across all entries | FR-005 | Re-generate if collision |
| At least one author (A1) present | FR-015 | Alert user; create entry with warning |
| Abstract present | FR-015 | Alert user; create entry without abstract |
| DOI present | FR-015 | Alert user; create entry without DOI link |

## State Transitions

Publications in this system have a simple one-way lifecycle:

```text
[Not on website] --> (ingestion) --> [Published on website]
```

There is no update or delete flow. Existing entries are never modified by this tool.
