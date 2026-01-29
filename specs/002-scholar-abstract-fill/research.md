# Research: Scholar API Abstract Retrieval

**Branch**: `002-scholar-abstract-fill` | **Date**: 2026-01-29

## Overview

This document captures research findings and technical decisions for implementing Scholar API integration to retrieve missing publication abstracts. All decisions align with the existing feature 001 (publication ingestion) technology stack.

## R1: HTTP Client Library Choice

**Decision**: Use `requests` library (version 2.31+)

**Rationale**:
- Industry-standard HTTP client for Python with stable API
- Simpler synchronous API suitable for batch processing with rate limiting
- Extensive documentation and community support
- Compatible with existing pytest ecosystem via `responses` mocking library
- No need for async/await complexity given sequential API calls with 1-second delays
- Already familiar to most Python developers

**Alternatives Considered**:
- `httpx`: Modern alternative with async support, but async unnecessary for rate-limited batch processing (1 req/sec)
- `urllib3`: Lower-level, more complex API, no significant benefit
- Built-in `urllib`: Too low-level, verbose error handling, no session management

**Testing Approach**: Use `responses` library to mock HTTP requests in pytest fixtures

---

## R2: Scholar API Integration Pattern

**Decision**: Query/keyword-based search using DOI or title+year in `keywords` and `query` parameters

**Rationale**:
- Scholar API is designed for AI agents and uses a natural language `query` parameter plus structured `keywords`
- Examination of `example_request.txt` shows the pattern: `keywords=<DOI>&query=Find the abstract of the manuscript with this doi: <DOI>`
- API returns `paper_data` array containing `answer` field (the abstract text), `doi`, `title`, `creators`, `publicationDate`
- Single endpoint (`/api/abstracts`) handles both DOI-based and title+year searches
- Response includes author matching data (`creators` field) for ambiguous result resolution

**API Request Format** (from example):
```
GET https://api.scholarai.io/api/abstracts
?sort=relevance
&peer_reviewed_only=true
&generative_mode=true
&keywords=<DOI or title>
&query=<natural language query>

Headers:
  x-scholarai-api-key: <API_KEY>
```

**Response Structure**:
```json
{
  "paper_data": [
    {
      "answer": "<abstract text>",
      "creators": ["Author1", "Author2", ...],
      "doi": "10.xxxx/xxxxx",
      "title": "Paper title",
      "publicationDate": "YYYY"
    }
  ],
  "total_num_results": 1
}
```

**DOI Search Query Template**:
- `keywords`: URL-encoded DOI (e.g., `10.1029%2F2002jd002448`)
- `query`: `Find the abstract of the manuscript with this doi: <DOI>`

**Title+Year Search Query Template** (for publications without DOI):
- `keywords`: URL-encoded title
- `query`: `Find the abstract of the publication titled "<title>" published in <year>`

**Alternatives Considered**:
- Direct DOI resolution via CrossRef or DOI.org: Scholar API provides generative abstracts and unified interface
- Multiple API integrations (PubMed, CrossRef): Spec explicitly scopes to Scholar API only

---

## R3: Abstract Detection Logic

**Decision**: Detect missing abstracts by searching for `**Abstract**:` text in markdown body

**Rationale**:
- Existing publications use consistent format: `**Abstract**: {text}` positioned after citation blockquote
- Regex pattern `r'\*\*Abstract\*\*:'` is reliable and fast
- Avoids false positives from abstract mentions in citation text
- Compatible with feature 001's markdown structure

**Implementation**: Use `re.search(r'\*\*Abstract\*\*:', body_content)` to determine if abstract exists

**Alternatives Considered**:
- Parse abstract section from markdown AST: Overcomplicated for simple text search
- Check abstract length threshold: Unreliable for short abstracts or malformed entries

---

## R4: CV.numbers Matching Strategy

**Decision**: Reuse feature 001's DOI/title+year matching logic

**Rationale**:
- Consistency with existing publication ingestion workflow
- DOI is primary unique identifier (normalize to lowercase, strip `https://doi.org/` prefix)
- Title+year fallback for older publications without DOIs
- Title normalization: lowercase, collapse whitespace via `re.sub(r'\s+', ' ', title.strip().lower())`
- Already tested and proven in feature 001

**Implementation**: Extract matching functions from feature 001 or duplicate the logic

**Alternatives Considered**:
- Match by publication ID from filename: Not present in CV.numbers, would require reverse lookup
- Match by author+year only: Too ambiguous (multiple papers per author per year)

---

## R5: Retry Strategy Implementation

**Decision**: Exponential backoff with jitter using `tenacity` library or manual implementation

**Rationale**:
- 3 retries with 2s, 4s, 8s delays (from clarification session)
- Handles transient network errors and temporary API unavailability
- Exponential backoff reduces server load during outages
- Small jitter (+/- 0.5s) prevents thundering herd if multiple instances run

**Manual Implementation** (if avoiding extra dependency):
```python
for attempt in range(1, 4):  # 3 retries
    try:
        response = make_api_call()
        break
    except TransientError:
        if attempt < 3:
            delay = 2 ** attempt  # 2s, 4s, 8s
            time.sleep(delay + random.uniform(-0.5, 0.5))
        else:
            raise
```

**Alternatives Considered**:
- `tenacity` library: Clean API but adds dependency; manual implementation is simple enough
- Fixed delay retries: Less respectful of API during issues
- No retries: Lower success rate for transient failures

---

## R6: Rate Limiting Implementation

**Decision**: Fixed 1-second `time.sleep()` between API calls

**Rationale**:
- Simple, predictable, meets clarification requirement
- Ensures ~170 publications complete in ~3 minutes of API time plus processing overhead
- No need for token bucket or sliding window complexity
- Easy to test (mock `time.sleep` in tests)

**Implementation**: Call `time.sleep(1.0)` after each successful or failed API request (but not during retries within the same publication)

**Alternatives Considered**:
- Adaptive rate limiting based on response headers: Overengineered for fixed 1-second requirement
- No rate limiting: Would violate API terms and risk throttling/blocking

---

## R7: Environment Variable Loading

**Decision**: Use `python-dotenv` to load `.env` file at script startup

**Rationale**:
- User has already created `.env` file with `SCHOLAR_API_KEY`
- `python-dotenv` is lightweight, standard library for .env handling
- Loads environment variables into `os.environ` seamlessly
- Fails fast if API key missing

**Implementation**:
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env from current directory or parent
api_key = os.getenv("SCHOLAR_API_KEY")
if not api_key:
    print("Error: SCHOLAR_API_KEY not found in environment")
    sys.exit(1)
```

**Alternatives Considered**:
- Manual .env parsing: Reinventing the wheel
- Direct `os.getenv()` without dotenv: Requires user to manually export variables

---

## R8: Abstract Insertion Position

**Decision**: Insert abstract after citation blockquote (`> ...`) and before article link button (`[Go to the Article]`)

**Rationale**:
- Matches existing publication format from feature 001
- Citation blockquote is always first body element
- Abstract comes before article link in existing entries
- Preserves markdown structure and readability

**Implementation**:
1. Split body content on `\n\n` to get paragraphs
2. Find citation blockquote (starts with `> `)
3. Insert `\n\n**Abstract**: {abstract_text}\n\n` after blockquote
4. Preserve remaining content (article link, etc.)

**Alternatives Considered**:
- Append at end of body: Inconsistent with existing format
- Replace entire body: Destructive, violates non-destructive principle

---

## R9: Testing Strategy

**Decision**: Use pytest with `responses` for API mocking, file fixtures for publications

**Rationale**:
- Consistent with feature 001 testing approach
- `responses` library provides clean API request/response mocking
- File fixtures (`sample_pub_no_abstract.md`, `sample_pub_with_abstract.md`) test real markdown parsing
- `tmpdir` pytest fixture for CV.numbers file mocking

**Test Coverage**:
- API call success/failure scenarios
- Retry logic with transient errors
- Rate limiting enforcement
- Abstract detection (present/absent)
- Abstract insertion formatting
- CV.numbers write-back matching
- Dry-run mode (no files written)
- Ambiguous result resolution (multiple API results)

**Alternatives Considered**:
- Live API integration tests: Expensive, slow, brittle; mocking is sufficient
- Manual testing only: Insufficient for retry logic and edge cases

---

## R10: Ambiguous Match Resolution Logic

**Decision**: Compare surname extraction from publication author list against API response `creators` field

**Rationale**:
- Title+year search may return multiple results
- Match by author surname increases precision
- Extract surname from publication frontmatter `author` field (e.g., "Kelly Caylor" → "caylor")
- Check if any surname appears in API response `creators` array
- Use first result with matching surname and year

**Implementation**:
```python
def extract_surnames(author_name):
    # "Kelly Caylor" → ["caylor"]
    # Handle multi-author frontmatter if present
    return [name.split()[-1].lower() for name in author_names]

def match_result(api_results, pub_year, pub_surnames):
    for result in api_results:
        if result['publicationDate'] != str(pub_year):
            continue
        result_surnames = [c.split()[-1].lower() for c in result['creators']]
        if any(s in result_surnames for s in pub_surnames):
            return result
    return None  # No match
```

**Alternatives Considered**:
- First result only: Less precise, may return wrong paper
- Manual user review: Not idempotent, breaks automation goal

---

## Summary of Technology Stack

| Component | Choice | Version/Details |
|-----------|--------|-----------------|
| Language | Python | 3.9+ (existing) |
| HTTP Client | requests | 2.31+ |
| API Mocking | responses | For pytest |
| Markdown Parsing | python-frontmatter | (existing from 001) |
| Numbers File | numbers-parser | (existing from 001) |
| YAML | PyYAML | (existing from 001) |
| Environment | python-dotenv | For .env loading |
| Testing | pytest | (existing from 001) |
| Rate Limiting | time.sleep() | Built-in |
| Retry Logic | Manual | Exponential backoff |

**Dependencies to Add** to `requirements.txt`:
```
requests>=2.31.0
python-dotenv>=1.0.0
responses>=0.24.0  # Test dependency
```

**No New Platform Requirements**: Reuses macOS, iCloud, Homebrew snappy from feature 001
