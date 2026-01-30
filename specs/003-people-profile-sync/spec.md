# Feature Specification: People Profile Management and Enrichment

**Feature Branch**: `003-people-profile-sync`
**Created**: 2026-01-29
**Status**: Draft
**Input**: User description: "Let's continue to extract information from the CV.numbers file. I have additional Sheets in the file - Graduate PhD, Postdoc, Graduate MA_MS, Undergrad, and Visitors - that we could use to try to keep current on the People page. Developing some tooling to use web searches, LinkedIn, + LLM/semantic searching to get updates for People (especially lab alums) would also be nice. Generally looking for ways to leverage my CV file and web resources to make management of group profiles at little easier (okay if we still need to make changes directly; looking for directional improvement, not a turn-key set-and-forget solution)."

## Clarifications

### Session 2026-01-29

- Q: What happens when someone appears in multiple CV.numbers sheets (e.g., Graduate PhD → Postdoc → Visitor)? → A: Merge into single profile with all roles - consolidate entries into one profile showing role history/progression
- Q: How should the system distinguish between CV-sourced fields and manually-added content in profile markdown files? → A: Frontmatter field tagging - tag each frontmatter field with source metadata (cv_sourced: true/false)
- Q: How long should web enrichment cache results before re-fetching for the same person? → A: Until manually cleared - cache indefinitely unless user forces refresh (future enhancement may add scheduled refresh)
- Q: What happens when CV.numbers data conflicts with manually customized content in a profile markdown file (e.g., different position title)? → A: Preserve manual, log warning - keep manual customization, report conflict for review
- Q: What minimum confidence score should web enrichment require before presenting a suggestion for manual review? → A: 0.6 (60% confidence) - moderate threshold balancing recall and precision

## User Scenarios & Testing

### User Story 1 - Extract People from CV.numbers Sheets (Priority: P1)

As a site maintainer, I want to extract people information from the five CV.numbers sheets (Graduate PhD, Postdoc, Graduate MA_MS, Undergrad, Visitors) so that I can populate and update the website's People page without manual re-entry of data I've already maintained in my CV.

**Why this priority**: This is the foundation - extracting structured data from the existing CV source of truth. Without this, no enrichment or syncing is possible. It provides immediate value by reducing duplicate data entry and ensures the CV remains the authoritative source.

**Independent Test**: Can be fully tested by running the extraction tool against CV.numbers and verifying that people data from all five sheets is correctly parsed and ready for use, without requiring any web enrichment features.

**Acceptance Scenarios**:

1. **Given** CV.numbers file contains Graduate PhD sheet with 10 alumni entries, **When** extraction tool runs, **Then** all 10 entries are extracted with name, years, degree information
2. **Given** CV.numbers contains entries across all five sheets (PhD, Postdoc, MA/MS, Undergrad, Visitors), **When** extraction runs, **Then** people are categorized by their sheet type for appropriate role assignment
3. **Given** same person appears in both Postdoc and Visitor sheets, **When** extraction runs, **Then** entries are merged into single profile with both roles listed chronologically
4. **Given** an entry has missing or incomplete data fields, **When** extraction runs, **Then** entry is still extracted with available fields and missing fields are noted
5. **Given** CV.numbers file is locked or being edited, **When** extraction runs, **Then** tool waits or provides clear error message without data corruption

---

### User Story 2 - Update People Page Profiles (Priority: P2)

As a site maintainer, I want to update existing people profile markdown files with freshly extracted CV.numbers data so that alumni information stays current without manual file editing.

**Why this priority**: Once data is extracted (P1), updating the website files is the next logical step. This delivers the core value of keeping the People page synchronized with the CV. It's independent from web enrichment.

**Independent Test**: Run the update tool after extraction completes, then verify that people markdown files in `_people/` directory reflect the latest CV.numbers data, preserving any existing content not sourced from the CV.

**Acceptance Scenarios**:

1. **Given** extracted people data and existing person file with tagged frontmatter, **When** update runs, **Then** fields marked cv_sourced are updated while fields without cv_sourced tag (manually-added like bio, photo, research interests) are preserved
2. **Given** person appears in CV.numbers but has no website file, **When** update runs, **Then** new markdown file is created with extracted data
3. **Given** person no longer appears in CV.numbers, **When** update runs, **Then** file is marked as alumni or moved to appropriate status without deletion
4. **Given** multiple people with similar names, **When** update runs, **Then** correct profiles are matched using year and degree type as additional identifiers
5. **Given** cv_sourced field has been manually modified after initial sync, **When** update runs with conflicting CV.numbers data, **Then** manual modification is preserved and conflict is logged for review

---

### User Story 3 - Enrich Profiles via Web Search (Priority: P3)

As a site maintainer, I want to search the web for current information about alumni (position, affiliation, LinkedIn profile) so that I can enhance profile pages with up-to-date professional information beyond what's in the CV.

**Why this priority**: This is an enhancement that adds value but isn't required for basic CV synchronization. It provides "directional improvement" for keeping alumni data current, especially for people who have moved since leaving the lab.

**Independent Test**: Run enrichment tool on a specific person's profile and verify that it suggests current position/affiliation information from web sources, presenting these as proposed updates rather than automatically applying them.

**Acceptance Scenarios**:

1. **Given** alumni name and last known affiliation, **When** web search enrichment runs, **Then** system finds and presents current position, institution, and LinkedIn URL as suggested updates
2. **Given** web search returns multiple possible matches, **When** enrichment runs, **Then** system ranks matches by relevance and presents top 3 with confidence scores for manual review
3. **Given** person has common name with many web results, **When** enrichment runs, **Then** system uses contextual clues (research area, previous institution, publication co-authors) to disambiguate
4. **Given** web search finds matches below 0.6 confidence threshold, **When** enrichment runs, **Then** low-confidence matches are filtered out and not presented for review
5. **Given** enrichment has been run previously, **When** tool runs again, **Then** cached results are used unless explicitly forced to re-fetch via cache clear option

---

### Edge Cases

- How does the system handle entries with special characters or non-English names in CV.numbers?
- What happens when LinkedIn or web sources are unavailable or rate-limited?
- How does system handle people who have no digital footprint or have opted out of public profiles?
- What happens when web enrichment finds conflicting information across different sources?
- How does system handle CV.numbers format changes or missing expected columns?
- How does system handle very large CV.numbers files (100+ entries per sheet)?

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract people data from all five CV.numbers sheets: Graduate PhD, Postdoc, Graduate MA_MS, Undergrad, and Visitors
- **FR-002**: System MUST parse standard CV fields including name, years active, degree type, institution, and research focus from each sheet
- **FR-003**: System MUST detect when the same person appears in multiple CV.numbers sheets (matched by name) and merge their entries into a single profile with role history showing all affiliations chronologically
- **FR-004**: System MUST match extracted CV.numbers entries to existing people markdown files using name as primary key
- **FR-005**: System MUST tag frontmatter fields with source metadata (cv_sourced: true for CV.numbers fields, false/absent for manually-added fields) and preserve all manually-added content when updating CV-sourced data
- **FR-005a**: When CV.numbers data conflicts with manually modified content in a cv_sourced field, system MUST preserve the manual modification and log a warning for manual review rather than overwriting
- **FR-006**: System MUST create new people markdown files for entries in CV.numbers that don't have existing website profiles
- **FR-007**: System MUST handle missing or incomplete data in CV.numbers entries without failing entire extraction
- **FR-008**: System MUST provide web search functionality to find current professional information (position, affiliation) for alumni
- **FR-009**: Web enrichment MUST present suggested updates for manual review rather than automatically modifying profile files
- **FR-010**: System MUST support searching LinkedIn profiles by name and institution to gather professional updates
- **FR-011**: System MUST use contextual information (research area, previous institution, degree year) to disambiguate common names in web searches
- **FR-012**: System MUST cache web search results indefinitely to avoid redundant API calls and MUST provide option to force refresh (clear cache) for specific people or entire cache
- **FR-013**: System MUST rank multiple web search matches by relevance/confidence (0.0 to 1.0 scale) and only present suggestions with confidence score ≥ 0.6 for manual review
- **FR-014**: System MUST operate in preview/dry-run mode to show proposed changes before applying them
- **FR-015**: System MUST log all data extraction, matching, and update operations for troubleshooting
- **FR-016**: System MUST handle CV.numbers file locking gracefully (wait or retry if file is being edited in Numbers app)
- **FR-017**: System MUST maintain referential integrity between CV.numbers source data and website profile files
- **FR-018**: Web enrichment MUST respect privacy and only use publicly available information sources

### Key Entities

- **Person**: Individual who has been affiliated with the research group. Attributes include name, role history (list of affiliations: grad student, postdoc, visitor, etc. with years for each), degree info, current position, current institution, LinkedIn profile, research interests, publications, photo filename, custom bio text, alumni status
- **CVSheet**: One of the five source sheets in CV.numbers file. Attributes include sheet name (Graduate PhD, Postdoc, etc.), expected column structure, mapping rules to Person attributes
- **ProfileFile**: Markdown file in `_people/` directory representing a Person. Attributes include file path, frontmatter fields tagged with cv_sourced metadata to distinguish CV.numbers data from manually-added fields, body content, last updated timestamp
- **EnrichmentSuggestion**: Proposed update from web sources. Attributes include person name, field to update (position, affiliation, LinkedIn), suggested value, source URL, confidence score (0.0-1.0, minimum 0.6 to be presented), timestamp
- **MatchCandidate**: Potential link between CVSheet entry and ProfileFile. Attributes include CV entry identifier, profile file path, match confidence, matching criteria used (name, year, degree)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Site maintainer can extract people from all five CV.numbers sheets and update corresponding website profiles in under 5 minutes for typical CV file (50-100 total entries)
- **SC-002**: At least 90% of CV.numbers entries successfully match to existing people profile files or create new files without manual intervention
- **SC-003**: Web enrichment finds current professional information for at least 60% of alumni with suggested updates requiring only approve/reject decision
- **SC-004**: Subsequent synchronization runs (after initial setup) complete in under 2 minutes by skipping unchanged entries
- **SC-005**: Manual data entry for maintaining People page reduces by at least 70% by leveraging CV.numbers as source of truth
- **SC-006**: System preserves 100% of manually-added profile content (photos, custom bios, research interests) when updating CV-sourced fields

## Dependencies

- Feature 001 (publication ingestion) - shares CV.numbers file access and numbers-parser library usage
- CV.numbers file must be accessible and contain the five specified sheets with expected column structure
- Web search capability requires internet connectivity and may need API keys for structured search services
- LinkedIn profile enrichment may require compliance with LinkedIn's usage policies and rate limits

## Assumptions

- CV.numbers file follows consistent column naming and structure across all five sheets
- Person names in CV.numbers are unique enough to match to profile files, or combination of name+year+degree provides sufficient uniqueness
- Frontmatter field tagging mechanism (cv_sourced metadata) is sufficient to distinguish CV-sourced fields from manually-added fields
- Web search results for common names can be disambiguated using available context (institution, research area, publication co-authors)
- Site maintainer will manually review and approve web enrichment suggestions rather than auto-applying all updates
- CV.numbers sheets may have varying column structures, but core fields (name, years, affiliation) are consistently present
- iCloud sync keeps CV.numbers file accessible at expected path (same as Feature 001)
- Rate limits and access restrictions for web searches and LinkedIn are manageable through caching and reasonable usage patterns
- People markdown files follow Jekyll frontmatter conventions established by the current site structure
- The tool aims for "directional improvement" - 60-80% automation with manual review, not 100% hands-free operation

## Out of Scope

- Automatic modification of profile files without manual review and approval
- Real-time synchronization or scheduled automatic updates (tool runs on-demand only)
- Scheduled automatic cache refresh for web enrichment (cache cleared manually only; scheduled refresh may be future enhancement)
- Bidirectional sync (changes in profile files do not write back to CV.numbers)
- Automated email outreach to alumni requesting profile updates
- Integration with university directory systems or other external databases
- Social media monitoring beyond LinkedIn (no Twitter, Facebook, Instagram scraping)
- Batch processing of publications or research output for each person (handled by Feature 001)
- Profile photo sourcing or management (photos remain manually added)
- Generation of alumni newsletters or automated communications
- Analytics or reporting on alumni career trajectories

