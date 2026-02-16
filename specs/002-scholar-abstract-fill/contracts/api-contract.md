# API Contract: Scholar API Integration

**Branch**: `002-scholar-abstract-fill` | **Date**: 2026-01-29

## Base URL

```
https://api.scholarai.io/api
```

## Authentication

**Method**: API Key in HTTP Header

**Header Name**: `x-scholarai-api-key`

**Header Value**: Value from `SCHOLAR_API_KEY` environment variable

**Example**:
```
x-scholarai-api-key: D2zYycr6uO0I3A829REWveNUXyDYanBi2J2mrPdbfi1zUCr27ohWKSNpHxwD7GE3
```

## Endpoint: Get Abstracts

### Request

**Method**: `GET`

**Path**: `/abstracts`

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `keywords` | string | yes | URL-encoded DOI or publication title for structured search | `10.1029%2F2002jd002448` or `Soil%20moisture%20dynamics` |
| `query` | string | yes | Natural language query describing what to search for | `Find the abstract of the manuscript with this doi: 10.1029/2002jd002448` |
| `sort` | string | yes | Sort order for results (fixed: `relevance`) | `relevance` |
| `peer_reviewed_only` | boolean | yes | Filter for peer-reviewed papers only (fixed: `true`) | `true` |
| `generative_mode` | boolean | yes | Enable generative abstract summaries (fixed: `true`) | `true` |

**Request Example (DOI-based)**:
```http
GET /api/abstracts?sort=relevance&peer_reviewed_only=true&generative_mode=true&keywords=10.1029%2F2002jd002448&query=Find%20the%20abstract%20of%20the%20manuscript%20with%20this%20doi%3A%2010.1029%2F2002jd002448 HTTP/1.1
Host: api.scholarai.io
x-scholarai-api-key: D2zYycr6uO0I3A829REWveNUXyDYanBi2J2mrPdbfi1zUCr27ohWKSNpHxwD7GE3
```

**Request Example (Title+Year)**:
```http
GET /api/abstracts?sort=relevance&peer_reviewed_only=true&generative_mode=true&keywords=Soil%20moisture%20and%20plant%20stress%20dynamics&query=Find%20the%20abstract%20of%20the%20publication%20titled%20%22Soil%20moisture%20and%20plant%20stress%20dynamics%22%20published%20in%202003 HTTP/1.1
Host: api.scholarai.io
x-scholarai-api-key: D2zYycr6uO0I3A829REWveNUXyDYanBi2J2mrPdbfi1zUCr27ohWKSNpHxwD7GE3
```

### Response

**Success Status Code**: `200 OK`

**Content-Type**: `application/json`

**Response Schema**:

```json
{
  "hint": "string (informational message, can be ignored)",
  "next_offset": "integer (pagination offset, can be ignored for single-result queries)",
  "paper_data": [
    {
      "answer": "string (abstract text, may be multiple paragraphs)",
      "creators": ["string (author name in citation format)", "..."],
      "doi": "string (DOI, e.g., '10.1029/2002JD002448') or empty",
      "landing_page_url": "string (URL to publisher page)",
      "pdf_id": "string (internal PDF identifier)",
      "publicationDate": "string (year as YYYY)",
      "ss_id": "string (Semantic Scholar ID, may be empty)",
      "title": "string (publication title)"
    }
  ],
  "suggestion": "string (promotional message, can be ignored)",
  "total_num_results": "integer (number of results in paper_data array)"
}
```

**Response Example** (from `example_request.txt`):

```json
{
  "hint": "Unless asked otherwise, aggregate these answers into a cohesive multi-paragraph answer, creating in-line citations for every answer referenced.",
  "next_offset": 1,
  "paper_data": [
    {
      "answer": "We present an analysis of water balance and plant water stress along the Kalahari precipitation gradient using a probabilistic model of soil moisture. The rainfall statistical characteristics, obtained from daily data of four stations along the transect, show that the rainfall gradient (from 950 to 300 mm/year) is mostly due to a decrease in the mean rate of storm arrivals (from 0.38 to 0.09 1/day) rather than to a change in the mean storm depth (practically constant at 10 mm). Using this information and typical vegetation and soil parameters, the analysis relates the vegetation properties along the transect with those of climate and soil. It is shown that differences in water balance and plant water stress between trees and grasses generate varying preferences for vegetation types along the transect, with deeper‐rooted trees favored in the more mesic regions of the northern Kalahari and grasses favored in the drier zones of the southern Kalahari. The point of equal plant water stress is found at about 420 mm of rainfall during the growing season (October–April), indicating the possibility of tree‐grass coexistence in the central sector of the Kalahari. These findings are consistent with patterns of vegetation distribution across the Kalahari transect.",
      "creators": [
        "A Porporato",
        "F Laio",
        "L Ridolfi",
        "KK Caylor"
      ],
      "doi": "10.1029/2002JD002448",
      "landing_page_url": "https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2002JD002448",
      "pdf_id": "PDF_URL:https://agupubs.onlinelibrary.wiley.com/doi/pdfdirect/10.1029/2002JD002448",
      "publicationDate": "2003",
      "ss_id": "",
      "title": "Soil moisture and plant stress dynamics along the Kalahari precipitation gradient"
    }
  ],
  "suggestion": "If you are a plugin user, check out the ScholarAI GPT at the following link: https://chat.openai.com/g/g-L2HknCZTC-scholarai, where you can access new features!",
  "total_num_results": 1
}
```

### Error Responses

**400 Bad Request** - Invalid query parameters:
```json
{
  "error": "Invalid query parameters",
  "message": "keywords parameter is required"
}
```

**401 Unauthorized** - Missing or invalid API key:
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "error": "Rate limit exceeded",
  "message": "Please wait before making additional requests"
}
```

**500 Internal Server Error** - API server error:
```json
{
  "error": "Internal server error",
  "message": "An error occurred processing your request"
}
```

## Query Construction Patterns

### Pattern 1: DOI-based Query (Primary)

**Use When**: Publication has a DOI in frontmatter

**Keywords**: URL-encoded DOI (replace `/` with `%2F`, `:` with `%3A`)

**Query Template**:
```
Find the abstract of the manuscript with this doi: {DOI}
```

**Example**:
- DOI: `10.1029/2002jd002448`
- Keywords: `10.1029%2F2002jd002448`
- Query: `Find the abstract of the manuscript with this doi: 10.1029/2002jd002448`

### Pattern 2: Title+Year Query (Fallback)

**Use When**: Publication has no DOI

**Keywords**: URL-encoded publication title (first 100 chars to avoid URL length limits)

**Query Template**:
```
Find the abstract of the publication titled "{TITLE}" published in {YEAR}
```

**Example**:
- Title: `Soil moisture and plant stress dynamics along the Kalahari precipitation gradient`
- Year: `2003`
- Keywords: `Soil%20moisture%20and%20plant%20stress%20dynamics%20along%20the%20Kalahari%20precipitation%20gradient`
- Query: `Find the abstract of the publication titled "Soil moisture and plant stress dynamics along the Kalahari precipitation gradient" published in 2003`

## Response Parsing

### Extract Abstract Text

**Field**: `paper_data[0].answer`

**Validation**:
1. Check `total_num_results > 0`
2. Check `paper_data` array is non-empty
3. Extract `paper_data[0].answer`
4. Validate: non-empty string, length > 50 characters

**Pseudocode**:
```python
if response['total_num_results'] == 0:
    return None, "No results found"

if not response['paper_data']:
    return None, "Empty results array"

abstract = response['paper_data'][0]['answer']

if not abstract or len(abstract) < 50:
    return None, f"Invalid abstract (length: {len(abstract)})"

return abstract, None
```

### Resolve Ambiguous Results (Title+Year Search)

**Use When**: `total_num_results > 1` for title+year query

**Logic**:
1. Extract publication year and author surnames from frontmatter
2. For each result in `paper_data`:
   - Check if `publicationDate` matches year
   - Extract surnames from `creators` array
   - Check if any publication surname matches any result surname
3. Use first result that matches both year and author

**Pseudocode**:
```python
pub_year = str(publication['year'])
pub_surnames = extract_surnames(publication['author'], publication.get('author-tags', []))

for result in response['paper_data']:
    if result['publicationDate'] != pub_year:
        continue

    result_surnames = [creator.split()[-1].lower() for creator in result['creators']]

    if any(surname in result_surnames for surname in pub_surnames):
        return result['answer']

return None, "No matching result found"
```

## Rate Limiting

**Policy**: 1-second delay between consecutive API requests

**Implementation**: Call `time.sleep(1.0)` after each API request (successful or failed) before processing next publication

**Does NOT apply**: During retries within the same publication (retries use exponential backoff delays: 2s, 4s, 8s)

## Retry Strategy

**Policy**: Up to 3 retries with exponential backoff for transient errors

**Transient Errors** (retry):
- HTTP 500 (Internal Server Error)
- HTTP 429 (Rate Limit Exceeded)
- Network timeouts
- Connection errors

**Permanent Errors** (do not retry):
- HTTP 400 (Bad Request)
- HTTP 401 (Unauthorized)
- HTTP 404 (Not Found)
- `total_num_results == 0` (no results found)

**Retry Delays**:
- Attempt 1 → Attempt 2: 2 seconds
- Attempt 2 → Attempt 3: 4 seconds
- Attempt 3 → fail: 8 seconds (not used, gives up after attempt 3)

**Pseudocode**:
```python
for attempt in range(1, 4):  # 3 total attempts
    try:
        response = make_api_request()
        return response
    except TransientError as e:
        if attempt < 3:
            delay = 2 ** attempt  # 2s, 4s
            time.sleep(delay + random.uniform(-0.5, 0.5))  # jitter
        else:
            raise  # Exhausted retries

    except PermanentError as e:
        raise  # Don't retry
```

## Testing Strategy

### Mock Response Patterns

Use `responses` library to mock HTTP requests in tests:

**Success Response**:
```python
responses.add(
    responses.GET,
    "https://api.scholarai.io/api/abstracts",
    json={
        "paper_data": [{
            "answer": "Test abstract text with sufficient length...",
            "creators": ["Caylor, KK"],
            "doi": "10.1234/test",
            "publicationDate": "2023",
            "title": "Test Paper"
        }],
        "total_num_results": 1
    },
    status=200
)
```

**No Results Response**:
```python
responses.add(
    responses.GET,
    "https://api.scholarai.io/api/abstracts",
    json={"paper_data": [], "total_num_results": 0},
    status=200
)
```

**Rate Limit Error**:
```python
responses.add(
    responses.GET,
    "https://api.scholarai.io/api/abstracts",
    json={"error": "Rate limit exceeded"},
    status=429
)
```

**Multiple Results** (for ambiguous match testing):
```python
responses.add(
    responses.GET,
    "https://api.scholarai.io/api/abstracts",
    json={
        "paper_data": [
            {"answer": "Abstract 1", "creators": ["Smith, J"], "publicationDate": "2023"},
            {"answer": "Abstract 2", "creators": ["Caylor, KK"], "publicationDate": "2023"}
        ],
        "total_num_results": 2
    },
    status=200
)
```
