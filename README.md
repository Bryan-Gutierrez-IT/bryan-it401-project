# BryghtCentral

**Student:** Bryan Gutierrez  
**Course:** IT401 — Web Intelligence  
**Assignment:** A5 — Expanding the Web Intelligence Application with Intelligence Generation

---

## Project Overview

BryghtCentral is an IT operations intelligence application built with Flask. The project is designed as a centralized interface for viewing organizational assets, checking software lifecycle information, storing externally acquired information, and retrieving relevant records from a persistent database.

The application has grown across the IT401 assignments:

- **A1:** Established the BryghtCentral application and Asset Directory.
- **A2:** Added external information acquisition using an API and web scraping.
- **A3:** Added MySQL persistence, SQLAlchemy models, database migrations, and CRUD functionality.
- **A4:** Added information retrieval through keyword search, Boolean filtering, relevance ranking, sorting, pagination, search telemetry, and retrieval evaluation.
- **A5:** Adds retrieval-augmented lifecycle recommendations using Gemini, structured output, validation, generated-result persistence, and intelligence history.

BryghtCentral is intended for IT support technicians, administrators, and other technical staff who need to quickly determine software lifecycle status and locate useful support information.

The A5 intelligence system builds on A4 retrieval by using retrieved lifecycle records as bounded context for a validated lifecycle recommendation. BryghtCentral now moves beyond finding information and generates new, grounded intelligence from retrieved evidence.

---

# Current Application Features

BryghtCentral currently includes:

- Homepage and application navigation
- Asset Directory
- Asset searching and filtering
- External API integration
- Web scraping
- Support Intelligence interface
- Software lifecycle recommendations
- MySQL database persistence
- SQLAlchemy ORM models
- Flask-Migrate database migrations
- Create, Read, Update, and Delete operations
- Duplicate prevention
- Data validation
- Stored-record browsing
- Keyword search
- Multi-field retrieval
- Product filtering
- Lifecycle-status filtering
- Relevance ranking
- Multiple sorting options
- Pagination
- Search-state preservation
- Search telemetry
- Search-history interface
- Helpful no-results states
- Database and search error handling
- Retrieval-augmented intelligence generation
- Gemini Developer API integration through REST
- Lifecycle recommendations: KEEP, UPGRADE, REPLACE, or INVESTIGATE
- Structured JSON output
- Pydantic validation
- Supporting-record ID validation
- Bounded model context
- Generated-intelligence persistence
- Intelligence History interface
- Empty-context and AI-service error handling

---

# Information Sources

BryghtCentral currently acquires external information from two primary sources.

## endoflife.date API

Lifecycle information for:

- Apple macOS
- Google Chrome

is retrieved from the endoflife.date API.

This information includes fields such as:

- Product
- Version
- Codename
- Release date
- Maintenance status
- End-of-life status
- End-of-life date
- Latest version
- Latest release date

The lifecycle information acquired through the API is permanently stored in MySQL.

## Apple Security Releases

BryghtCentral also scrapes Apple's public security-release page to obtain information related to Apple software security updates.

This scraped information is used by the Support Intelligence feature and is currently retrieved when needed rather than permanently stored.

---

# Information Persistence

A3 introduced permanent information storage using MySQL and Flask-SQLAlchemy.

Lifecycle information from endoflife.date is stored in the `lifecycle_records` table.

The current database contains approximately:

- **23 Apple macOS lifecycle records**
- **148 Google Chrome lifecycle records**
- **171 lifecycle records total**

Persisting this information allows BryghtCentral to search and retrieve lifecycle data without calling the external API for every user search.

This creates the following flow:

```text
External API
     ↓
Data Acquisition
     ↓
Validation
     ↓
MySQL Persistence
     ↓
Search and Retrieval
     ↓
User Interface
```

The search functionality introduced in A4 operates on the information already stored in MySQL.

---

# Database Integration

BryghtCentral uses the following persistence stack:

```text
Flask
  ↓
Flask-SQLAlchemy
  ↓
SQLAlchemy ORM
  ↓
PyMySQL
  ↓
MySQL / MariaDB-Compatible CI Keys Database
```

During local development, the application connects to the remote CI Keys database through an SSH tunnel.

```text
Local Flask Application
        ↓
127.0.0.1:3307
        ↓
SSH Tunnel
        ↓
CI Keys Server
        ↓
MySQL :3306
```

Database credentials are stored in a local `.env` file and are not committed to Git.

---

# Database Schema

A5 uses three primary SQLAlchemy models.

---

## LifecycleRecord

**Table:** `lifecycle_records`

**Purpose:**  
Stores lifecycle information acquired from endoflife.date.

| Attribute | Purpose |
|---|---|
| `id` | Internal primary key |
| `title` | Human-readable record title |
| `description` | Description of the lifecycle record |
| `source` | Information source |
| `source_url` | Original source URL |
| `retrieved_date` | Date and time information was retrieved |
| `created_date` | Date and time database record was created |
| `product` | Product name |
| `version` | Product version |
| `codename` | Optional product codename |
| `release_date` | Product release date |
| `is_maintained` | Whether the release is actively maintained |
| `is_eol` | Whether the release has reached end of life |
| `eol_date` | Known end-of-life date |
| `latest_version` | Latest available version |
| `latest_release_date` | Date of latest available release |
| `external_id` | Identifier derived from the external source |

### Duplicate Prevention

Lifecycle records use a unique constraint based on:

```text
source + external_id
```

This prevents synchronization from creating duplicate records.

When lifecycle data is synchronized again, existing records are updated rather than duplicated.

---

## SearchEvent

**Table:** `search_events`

**Purpose:**  
Stores basic telemetry for completed searches.

| Attribute | Purpose |
|---|---|
| `id` | Primary key |
| `query` | Original query entered by the user |
| `normalized_query` | Processed lowercase query |
| `product_filter` | Product filter used |
| `status_filter` | Status filter used |
| `sort_option` | Selected result ordering |
| `result_count` | Number of records matching the search |
| `no_results` | Indicates whether the search returned zero results |
| `searched_at` | Date and time the search occurred |

## IntelligenceResult

**Table:** `intelligence_results`

**Purpose:**
Stores successfully validated lifecycle intelligence generated from retrieved BryghtCentral records.

| Attribute | Purpose |
|---|---|
| `id` | Primary key |
| `user_request` | User question or request |
| `capability` | Intelligent capability; currently `recommendation` |
| `summary` | Generated lifecycle summary |
| `recommendation` | KEEP, UPGRADE, REPLACE, or INVESTIGATE |
| `confidence` | high, medium, or low |
| `rationale_json` | JSON list of evidence-based reasons |
| `supporting_items_json` | JSON list of supporting records and evidence |
| `limitations_json` | JSON list of limitations |
| `source_record_ids_json` | JSON list of lifecycle record IDs used as context |
| `prompt_version` | Version identifier for the prompt |
| `model_name` | Gemini model used for generation |
| `generated_at` | Generation timestamp |
| `created_at` | Database creation timestamp |

Only successful, validated generations are stored. Failed or empty-context requests are not persisted.

---

The current schema can be summarized as:

```text
LifecycleRecord
────────────────────────────
PK  id
    title
    description
    source
    source_url
    retrieved_date
    created_date
    product
    version
    codename
    release_date
    is_maintained
    is_eol
    eol_date
    latest_version
    latest_release_date
    external_id


SearchEvent
────────────────────────────
PK  id
    query
    normalized_query
    product_filter
    status_filter
    sort_option
    result_count
    no_results
    searched_at
```

The two tables currently do not require a direct foreign-key relationship. Search telemetry describes retrieval activity across the lifecycle collection rather than an individual record.

---

# Search and Retrieval Features

A4 transforms BryghtCentral from a database browsing application into a searchable information system.

The primary search interface is available at:

```text
/search
```

Searches use HTTP GET requests.

Example:

```text
/search?q=Ventura&product=&status=&sort=relevance
```

Using GET requests allows searches to:

- Remain visible in the URL
- Be bookmarked
- Be shared
- Preserve search state during navigation
- Preserve filters and sorting during pagination

---

# Searchable Information

The primary searchable model is:

```text
LifecycleRecord
```

The following fields are searched:

- `title`
- `description`
- `product`
- `version`
- `codename`

These fields were selected because they contain information a technician is likely to know when looking for a lifecycle record.

For example, a technician may search for:

```text
Ventura
```

without knowing that Ventura corresponds to macOS 13.

Likewise:

```text
Chrome 153
```

can match both the product and version information.

Fields such as dates and lifecycle Boolean values are not treated as free-text search fields because they work better as sorting criteria or structured filters.

---

# Query Processing

Before database retrieval occurs, the user's query is processed.

BryghtCentral currently performs the following steps:

1. Preserves the original query for display.
2. Removes unnecessary leading and trailing whitespace.
3. Collapses repeated internal whitespace.
4. Converts the normalized query to lowercase.
5. Breaks the query into whitespace-separated tokens.
6. Rejects empty queries.
7. Rejects queries longer than 200 characters.
8. Uses SQLAlchemy expressions rather than manually inserting raw input into SQL.

Example:

```text
Original Query:
   Chrome   153

Normalized Query:
chrome 153

Tokens:
chrome
153
```

This represents a basic form of tokenization and normalization.

The original user query is still displayed in the interface while the normalized form is used for consistent comparison.

---

# Multi-Field Retrieval

Search queries are matched against multiple fields using SQLAlchemy.

Conceptually:

```text
Query
  ↓
title
OR description
OR product
OR version
OR codename
```

For multi-token queries, each query term must appear somewhere within the searchable fields.

For example:

```text
Chrome 153
```

requires both:

```text
Chrome
AND
153
```

to appear within the searchable lifecycle record.

This improves retrieval precision compared with searching only one database field.

---

# Boolean Filtering

BryghtCentral provides two optional structured filters.

## Product Filter

Users may select:

```text
All Products
Apple macOS
Google Chrome
```

The available product values are read from the stored database records.

## Status Filter

Users may select:

```text
All Statuses
Active
Ended
Unknown
```

The filters are combined with the keyword query.

Conceptually:

```text
keyword
AND product
AND lifecycle status
```

Example:

```text
Chrome
AND Google Chrome
AND Ended
```

Filters can be removed or changed directly from the interface.

---

# Sorting Options

BryghtCentral provides four result-ordering options.

## Relevance

Orders results according to the application's custom relevance score.

## Newest First

Orders results using release date in descending order.

## Oldest First

Orders results using release date in ascending order.

## Alphabetical

Orders results by product and version.

---

# Relevance Ranking

BryghtCentral uses a transparent rule-based relevance score.

The ranking strategy gives stronger weight to matches in fields that more directly identify a release.

Conceptual weighting:

```text
Exact title match        +10
Exact product match       +9
Exact codename match      +8
Exact version match       +7

Partial title match       +5
Partial product match     +4
Partial codename match    +4
Partial version match     +4
Description match         +1
```

Individual query tokens may also contribute additional relevance points.

A small boost is also given to currently maintained releases.

This strategy is appropriate for BryghtCentral because lifecycle records have clearly structured identifying fields.

A match in:

```text
product
version
codename
```

is generally more useful than the same word appearing only in a longer description.

For example:

```text
Search: Ventura
```

returns:

```text
Apple macOS
Version 13
Codename Ventura
```

as the highest and only result.

---

# Retrieval Workflow

The complete A4 search workflow is:

```text
User enters search query
          ↓
Flask receives GET request
          ↓
Query is normalized
          ↓
Query is tokenized
          ↓
SQLAlchemy builds retrieval statement
          ↓
Search multiple LifecycleRecord fields
          ↓
Apply product filter
          ↓
Apply lifecycle-status filter
          ↓
Calculate relevance score
          ↓
Apply selected sorting strategy
          ↓
Paginate results
          ↓
Render Jinja results template
          ↓
Record SearchEvent telemetry
```

The retrieval sequence follows:

```text
Retrieve
   ↓
Filter
   ↓
Rank
   ↓
Paginate
   ↓
Display
```

---

# Pagination

Search results are limited to:

```text
15 results per page
```

This prevents the application from rendering the entire result collection at once.

Pagination displays:

- Previous navigation
- Next navigation
- Current page
- Total pages
- Current result range
- Total result count

Example:

```text
Showing 16–30 of 148 results
Page 2 of 10
```

Pagination links preserve:

```text
query
product filter
status filter
sort selection
page
```

Example:

```text
/search?q=Chrome&product=&status=&sort=relevance&page=2
```

This prevents the user's search state from being lost while navigating between pages.

---

# Results Presentation

Each search result displays information intended to help a technician quickly determine whether the record is useful.

Displayed fields include:

- Product
- Version
- Codename when available
- Lifecycle status
- Record title
- Description
- Source
- Release date
- Relevance score
- Link to the original source

BryghtCentral distinguishes among several retrieval states.

## Before Searching

```text
Enter a keyword or phrase to begin.
```

## Results Found

Example:

```text
Results for "Chrome"

Showing 1–15 of 148 results.
```

## No Results

Example:

```text
No Results Found

No matching records were found for "potato123xyz".

Try a broader term or remove one of the filters.
```

## Search Error

If database retrieval fails, the application displays a user-friendly message instead of exposing a full traceback.

---

# Search Telemetry

A4 adds search telemetry using the `SearchEvent` model.

Each completed first-page search records:

- Original query
- Normalized query
- Product filter
- Status filter
- Sorting option
- Total result count
- Whether zero results were returned
- Search date and time

Pagination requests do not create additional telemetry events for the same search.

This prevents a user clicking:

```text
Page 1
Page 2
Page 3
```

from being counted as three separate searches.

The telemetry interface is available at:

```text
/search-history
```

The Search History page displays up to the 50 most recent events.

Telemetry could later help BryghtCentral identify:

- Common search terms
- Frequently used filters
- Searches that return no results
- Searches that may need synonyms
- Popular product families
- Search behavior that could improve recommendations
- Opportunities for better relevance ranking

BryghtCentral currently does not store sensitive personal information in search telemetry.

---

# Search Evaluation

Five test queries were used to evaluate BryghtCentral's retrieval quality.

| Query | Expected Relevant Records | Results Returned | Ranking Observation |
|---|---|---:|---|
| `Ventura` | Apple macOS 13 Ventura | 1 | Expected record ranked first |
| `Chrome 153` | Google Chrome 153 | 1 | Exact version returned as the only result |
| `Sequoia` | Apple macOS 15 Sequoia | 1 | Expected record ranked first |
| `macOS` | Stored Apple macOS lifecycle records | 23 | Current and recent macOS releases appeared near the top |
| `Chrome` | Stored Google Chrome lifecycle records | 148 | Chrome 155 appeared first followed by recent versions |

## Detailed Results

### Query 1 — Ventura

Expected:

```text
Apple macOS 13
Codename: Ventura
```

Actual:

```text
1 result
Relevance score: 14
Apple macOS 13 — Ventura
```

No obvious false positives were returned.

The expected relevant record was not missed.

**Precision observation:** Excellent. The only returned result was useful.

**Recall observation:** Strong. The expected record was successfully retrieved.

---

### Query 2 — Chrome 153

Expected:

```text
Google Chrome 153
```

Actual:

```text
1 result
Relevance score: 18
Google Chrome 153
```

No obvious false positives were returned.

The expected record was not missed.

**Precision observation:** Excellent.

**Recall observation:** Strong.

---

### Query 3 — Sequoia

Expected:

```text
Apple macOS 15
Codename: Sequoia
```

Actual:

```text
1 result
Relevance score: 15
Apple macOS 15 — Sequoia
```

No obvious false positives were returned.

The expected record was not missed.

**Precision observation:** Excellent.

**Recall observation:** Strong.

---

### Query 4 — macOS

Expected:

```text
Apple macOS lifecycle records
```

Actual:

```text
23 results
```

Top results included:

```text
macOS 27 — Golden Gate
macOS 26 — Tahoe
macOS 15 — Sequoia
macOS 14 — Sonoma
macOS 13 — Ventura
```

The returned records belonged to the expected macOS product family.

**Precision observation:** High because the results were relevant to the requested product.

**Recall observation:** Strong within the current lifecycle dataset because the stored macOS collection was retrieved.

---

### Query 5 — Chrome

Expected:

```text
Google Chrome lifecycle records
```

Actual:

```text
148 results
```

Top results included:

```text
Chrome 155
Chrome 154
Chrome 153
Chrome 152
Chrome 151
```

The most current Chrome release appeared first.

**Precision observation:** High because returned records belonged to Google Chrome.

**Recall observation:** Strong within the current stored Chrome collection.

---

# Evaluation Summary

The five test queries demonstrated strong retrieval quality for the current dataset.

Specific queries such as:

```text
Ventura
Chrome 153
Sequoia
```

returned exactly one highly relevant record.

Broader product queries such as:

```text
macOS
Chrome
```

returned their expected product collections without obvious false positives.

The rule-based relevance strategy successfully placed current or recent records near the top when several records had similar textual relevance.

Formal mathematical precision and recall calculations were not required for this evaluation, so they are discussed qualitatively.

One future improvement would be adding synonym-aware or semantic retrieval. The current system depends primarily on stored text matching and does not understand that two different words may represent related concepts.

---

# Intelligence Generation

A5 adds one intelligent capability to BryghtCentral:

```text
Lifecycle Recommendation
```

The recommendation capability was selected because lifecycle data naturally supports operational questions such as whether a release should be kept, upgraded, replaced, or investigated.

Supported recommendation values are:

```text
KEEP
UPGRADE
REPLACE
INVESTIGATE
```

Supported confidence labels are:

```text
high
medium
low
```

The purpose is to help an IT support professional interpret retrieved lifecycle evidence while still showing the underlying records, rationale, limitations, and provenance.

---

# Retrieval-Augmented Workflow

A5 continues using the existing A4 application and retrieval layer. It does not create a separate AI demo.

```text
User Request
    ↓
Retrieve Relevant Records
    ↓
Build Bounded Context
    ↓
Generate Structured Intelligence
    ↓
Validate Output
    ↓
Persist Valid Result
    ↓
Display Recommendation
```

The interface summarizes the same process as:

```text
Retrieve → Analyze → Validate → Recommend
```

The `/intelligence` route reuses `search_lifecycle_records()` from `services/search_service.py`.

A maximum of five retrieved lifecycle records are supplied to the intelligence component. If no records are retrieved, generation is blocked.

Example empty-context behavior:

```text
Search: potato123xyz

No lifecycle records matched that search.
Intelligence was not generated because there was no retrieved context.
```

This prevents BryghtCentral from asking the model to invent an answer without application evidence.

---

# Context Design

The context builder sends only lifecycle fields that are useful for the recommendation task.

Included information may contain:

- Record ID
- Title
- Product
- Version
- Codename
- Description
- Release date
- Maintenance status
- End-of-life status
- End-of-life date
- Latest known version
- Latest release date
- Source
- Source URL
- Retrieval date

The context excludes:

- Database credentials
- Gemini API key
- `.env` contents
- SSH configuration
- Unrelated records
- Unrelated search history
- Arbitrary external information not retrieved by BryghtCentral

Keeping the context bounded improves grounding, reduces irrelevant information, and makes the final recommendation easier to verify.

---

# Prompt Design

Prompt construction is isolated in:

```text
services/prompts.py
```

The current prompt version is:

```text
a5-lifecycle-recommendation-v1
```

## System Prompt

The system instructions define Gemini as BryghtCentral's lifecycle intelligence component and require it to:

- Analyze only the supplied lifecycle context
- Avoid outside knowledge
- Avoid inventing versions, dates, lifecycle status, or product details
- Return a supported recommendation value
- Return a supported confidence label
- Ground factual claims in retrieved records
- State limitations when evidence is incomplete
- Return structured output

## User Prompt

The user prompt is organized into separate sections:

```text
USER REQUEST
<user question>

RETRIEVED LIFECYCLE CONTEXT
<retrieved records>

TASK
Generate a lifecycle recommendation from the supplied evidence.
```

Separating instructions, user intent, and retrieved context makes the prompt easier to maintain and reduces ambiguity.

---

# AI Component

BryghtCentral uses the Gemini Developer API for A5.

Configured model:

```text
gemini-3.6-flash
```

The application calls Google's REST `generateContent` endpoint with Python `requests`.

Environment variables:

```text
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
```

The actual API key is stored only in `.env` and is never committed to Git.

The generation request includes:

- System instructions
- User request
- Retrieved lifecycle context
- Temperature set to 0
- JSON response MIME type
- A JSON response schema

---

# Structured Output

Gemini is asked to return a structured result similar to:

```json
{
  "summary": "...",
  "recommendation": "UPGRADE",
  "confidence": "high",
  "rationale": ["..."],
  "supporting_items": [
    {
      "record_id": 25,
      "product": "Google Chrome",
      "version": "154",
      "source": "endoflife.date",
      "evidence": "..."
    }
  ],
  "limitations": ["..."]
}
```

Structured output allows the application to validate and display each field independently.

---

# Validation

Generated intelligence is validated before it is displayed or persisted.

## Pydantic Validation

`SupportingItem` and `IntelligenceOutput` models validate field presence and data types.

## Application Validation

`validate_intelligence_output()` also verifies:

- Summary is present
- Recommendation is KEEP, UPGRADE, REPLACE, or INVESTIGATE
- Confidence is high, medium, or low
- Rationale contains usable strings
- Supporting items are present
- Every supporting `record_id` was actually supplied in the retrieved context
- Required supporting-item fields are present
- Limitations use the expected list format

A direct validation test used an allowed record ID of `10` while the generated supporting item referenced `999`. The validator correctly rejected the output.

This additional record-ID check helps prevent unsupported or hallucinated citations.

---

# Generated Intelligence Example

A tested web request used:

```text
Lifecycle search:
Chrome 154

Intelligence request:
Should an organization still using this release upgrade?
```

The existing A4 search service retrieved:

```text
Record #25
Google Chrome 154
Maintained: False
End of Life: True
EOL Date: 2026-10-06
```

The generated result was:

```text
Recommendation: UPGRADE
Confidence: high
```

Summary:

```text
Google Chrome version 154 has reached End of Life and is no longer maintained, requiring an upgrade.
```

The rationale referenced the retrieved lifecycle status and EOL date. The model also stated a limitation because the retrieved record did not identify the latest version or latest release date.

The generated result adds value beyond simple retrieval by converting several lifecycle fields into a concise operational interpretation while preserving evidence and uncertainty.

---

# Storage of Generated Intelligence

Successful validated intelligence is persisted through:

```text
services/intelligence_persistence.py
```

into:

```text
intelligence_results
```

Stored information includes:

- User request
- Capability
- Summary
- Recommendation
- Confidence
- Rationale
- Supporting items
- Limitations
- Source record IDs
- Prompt version
- Model name
- Generation timestamp

Two successful tests produced:

```text
Result #1
Source IDs: [24, 25]

Result #2
Source IDs: [25]
```

The empty-context `potato123xyz` test did not create another database record.

Therefore:

```text
Valid retrieved context
    ↓
Generate
    ↓
Validate
    ↓
Store

No retrieved context
    ↓
Block generation
    ↓
Store nothing
```

---

# A5 Reliability and Fallback Behavior

The intelligence layer gracefully handles:

- Missing Gemini API key
- Rate limiting
- Timeouts
- Connection failures
- Temporary provider errors
- Authentication or permission errors
- Empty retrieval context
- Invalid JSON
- Invalid structured output
- Unsupported recommendation or confidence values
- Supporting record IDs outside the retrieved context
- Failed database persistence

Temporary provider failures may be retried a limited number of times.

If generation fails, the user receives a clear error rather than a raw traceback. Failed or ungrounded generations are not stored.

---

# A5 Application Organization

A5 separates responsibilities instead of placing all AI logic inside one route.

```text
routes/intelligence.py
    Request handling and rendering

services/search_service.py
    Existing A4 retrieval

services/context_builder.py
    Bounded retrieved context

services/prompts.py
    Versioned system and user prompts

services/intelligence_service.py
    Gemini REST request and provider-error handling

services/intelligence_validator.py
    Pydantic and application-level validation

services/intelligence_persistence.py
    Storage of validated output

models/intelligence_result.py
    Generated-intelligence database model

templates/intelligence.html
    Generation interface and structured result display

templates/intelligence_history.html
    Stored generated-result history
```

---

# Reliability and Error Handling

BryghtCentral handles common search and intelligence-generation failures gracefully.

## Empty Query

An empty query does not execute a normal search.

The user receives:

```text
Enter a keyword or phrase to begin searching.
```

## Very Long Query

Queries longer than 200 characters are rejected.

## Invalid Product Filter

Product values are validated against products stored in the database.

Invalid product filters are rejected.

## Invalid Status Filter

Only supported lifecycle states are accepted.

## Invalid Sorting Option

Unsupported sorting values are rejected.

## Invalid Page Number

Invalid or negative page values are normalized to a valid page.

If a requested page is beyond the available result set, BryghtCentral displays the final valid page.

## No Results

A zero-result search produces a helpful user-facing message with suggestions to broaden the query or remove filters.

## Database Failure

Database exceptions are caught and the SQLAlchemy session is rolled back where appropriate.

Users receive a helpful search-unavailable message rather than a raw database traceback.

## Telemetry Failure

Search telemetry is intentionally separated from retrieval.

If saving a `SearchEvent` fails:

- The database transaction is rolled back.
- Search results may still be displayed.
- The user receives a telemetry warning instead of losing the search results.

---

# CRUD Functionality

A3 CRUD functionality remains available in A4.

Users can:

## Create

Manually create a lifecycle record.

Required values are validated before insertion.

## Read

View persisted lifecycle records through the Stored Records interface.

## Update

Modify an existing lifecycle record.

## Delete

Remove a stored lifecycle record.

Duplicate protection continues to use:

```text
source + external_id
```

---

# Lifecycle Synchronization

BryghtCentral can synchronize lifecycle information from endoflife.date.

The synchronization system:

1. Retrieves external lifecycle information.
2. Converts external values into application fields.
3. Checks for an existing record using `source + external_id`.
4. Creates missing records.
5. Updates existing records.
6. Commits the transaction.

A repeated synchronization demonstrated duplicate-safe behavior:

```text
Created: 0
Updated: 171
```

This confirms that synchronization updates existing records rather than creating duplicate lifecycle entries.

---

# Application Architecture

BryghtCentral separates major responsibilities across routes, models, services, templates, and static files.

```text
Browser
   ↓
Flask Route
   ↓
Search Service
   ↓
SQLAlchemy ORM
   ↓
MySQL
   ↓
Search Results
   ↓
Jinja Template
   ↓
Browser
```

Search telemetry follows a second path:

```text
Completed Search
      ↓
SearchEvent Model
      ↓
SQLAlchemy
      ↓
MySQL
      ↓
Search History
```

Separating retrieval logic from Flask routing keeps the application easier to maintain and prepares the project for later intelligent-system features.

---

## A5 Intelligence Architecture

```text
Browser
   ↓
/intelligence Flask Route
   ↓
A4 Search Service
   ↓
LifecycleRecord Results
   ↓
Context Builder
   ↓
Prompt Builder
   ↓
Gemini REST API
   ↓
Structured JSON
   ↓
Pydantic + Application Validation
   ↓
Intelligence Persistence
   ↓
MySQL intelligence_results
   ↓
Jinja Intelligence Interface
```

---

# Project Structure

```text
bryan-it401-project/
│
├── app.py
├── extensions.py
├── requirements.txt
├── README.md
├── .env
├── .env.example
├── .gitignore
├── sync_lifecycle.py
│
├── data/
│   └── assets.json
│
├── migrations/
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0772cbdf46e6_create_lifecycle_records_table.py
│       └── 4dece5aa8ef5_create_search_events_table.py
│
├── models/
│   ├── __init__.py
│   ├── lifecycle.py
│   └── search_event.py
│
├── routes/
│   ├── main.py
│   ├── lifecycle_records.py
│   └── search.py
│
├── services/
│   ├── lifecycle_api.py
│   ├── apple_scraper.py
│   ├── lifecycle_persistence.py
│   └── search_service.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── assets.html
│   ├── support_intelligence.html
│   ├── stored_releases.html
│   ├── lifecycle_form.html
│   ├── search.html
│   └── search_history.html
│
└── static/
    ├── style.css
    │
    └── screenshots/
        ├── homepage.png
        ├── asset-directory.png
        ├── filtered-assets.png
        │
        ├── a2-homepage.png
        ├── a2-api-results.png
        ├── a2-scraped-results.png
        ├── a2-combined-interface.png
        ├── a2-error-handling.png
        │
        ├── a3-homepage.png
        ├── a3-stored-records.png
        ├── a3-crud-interface.png
        ├── a3-sync-success.png
        ├── a3-validation.png
        │
        ├── a4-search-form.png
        ├── a4-ranked-results.png
        ├── a4-pagination.png
        ├── a4-filtered-results.png
        ├── a4-active-filter.png
        ├── a4-no-results.png
        └── a4-search-history.png
```

---

# Important File Responsibilities

## `app.py`

Creates and configures the Flask application.

Responsibilities include:

- Loading environment variables
- Configuring the database connection
- Initializing SQLAlchemy
- Initializing Flask-Migrate
- Registering application routes

## `extensions.py`

Creates reusable SQLAlchemy and Flask-Migrate extension instances.

## `models/lifecycle.py`

Defines the persisted lifecycle information model.

## `models/search_event.py`

Defines the A4 search telemetry model.

## `routes/main.py`

Handles the original BryghtCentral pages and support-intelligence routes.

## `routes/lifecycle_records.py`

Handles stored lifecycle record browsing and CRUD functionality.

## `routes/search.py`

Handles:

- Search HTTP requests
- Search form state
- Search-result rendering
- Telemetry recording
- Search-history display

## `services/lifecycle_api.py`

Retrieves lifecycle information from endoflife.date.

## `services/apple_scraper.py`

Retrieves Apple security-release information from Apple's website.

## `services/lifecycle_persistence.py`

Synchronizes external lifecycle information into MySQL.

## `services/search_service.py`

Contains A4 information-retrieval logic, including:

- Query normalization
- Tokenization
- Multi-field searching
- Boolean filtering
- Relevance scoring
- Sorting
- Pagination
- Search telemetry storage

## `templates/search.html`

Displays:

- Search controls
- Keyword field
- Filters
- Sorting controls
- Search results
- Relevance scores
- Pagination
- Empty-query state
- No-results state
- Error messages

## `templates/search_history.html`

Displays recorded search telemetry.

---

# Installation Instructions

## 1. Clone the Repository

```bash
git clone <repository-url>
cd bryan-it401-project
```

Switch to the A5 branch if necessary:

```bash
git switch bryan-it401-a5
```

---

## 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```text
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Major dependencies include:

- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- SQLAlchemy
- PyMySQL
- python-dotenv
- requests
- BeautifulSoup
- Pydantic

---

# Environment Variables

Create:

```text
.env
```

from:

```text
.env.example
```

Required variables:

```text
DB_USERNAME=
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3307
DB_NAME=
SECRET_KEY=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
```

Actual credentials must never be committed to Git.

The endoflife.date and Apple security-release sources do not require API keys for the current project. A5 requires a Gemini Developer API key for intelligence generation. The real key is stored only in `.env`; `.env.example` contains only placeholders.

---

# Generating a Secret Key

A development secret key can be generated with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Store the result only in:

```text
.env
```

---

# CI Keys Database Connection

When running the application locally, create the SSH tunnel before starting Flask.

Example:

```bash
ssh -N -T \
-o IdentitiesOnly=yes \
-o ExitOnForwardFailure=yes \
-L 127.0.0.1:3307:127.0.0.1:3306 \
-i ~/.ssh/cikeys \
-p 22 \
YOUR_CPANEL_USERNAME@csuci.dooo.host.reclaimhosting.com
```

Keep that Terminal session open while using the application.

The Flask application then connects through:

```text
DB_HOST=127.0.0.1
DB_PORT=3307
```

---

# Database Migrations

Apply all existing migrations with:

```bash
flask db upgrade
```

When a model changes, create a migration using:

```bash
flask db migrate -m "Describe migration"
```

Then apply it:

```bash
flask db upgrade
```

A4 added the `search_events` table through a migration. A5 adds the `intelligence_results` table through `73081e72c1ee_create_intelligence_results_table.py`.

---

# Running the Application

Start BryghtCentral with:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

Primary routes include:

```text
/
 /assets
 /support-intelligence
 /stored-releases
 /stored-releases/create
 /search
 /search-history
 /intelligence
 /intelligence-history
```

---

# Screenshots

## A4 Search Interface

![A4 Search Form](static/screenshots/a4-search-form.png)

The dedicated information-retrieval interface provides a keyword field, product filter, lifecycle-status filter, sorting control, and search button.

---

## A4 Ranked Search Results

![A4 Ranked Results](static/screenshots/a4-ranked-results.png)

A broad search for Chrome demonstrates keyword retrieval and relevance ordering.

---

## A4 Pagination

![A4 Pagination](static/screenshots/a4-pagination.png)

The Chrome search returns 148 records. Results are limited to 15 per page while the query, filters, and sorting state remain preserved.

---

## A4 Filtered and Sorted Results

![A4 Filtered Results](static/screenshots/a4-filtered-results.png)

The interface demonstrates combined:

```text
Keyword: Chrome
Product: Google Chrome
Status: Ended
Sort: Newest First
```

---

## A4 Active Lifecycle Filter

![A4 Active Filter](static/screenshots/a4-active-filter.png)

Applying the Active lifecycle filter reduces the Chrome result set to the currently maintained release.

---

## A4 No-Results State

![A4 No Results](static/screenshots/a4-no-results.png)

The application provides a helpful message when no matching records are found.

---

## A4 Search Telemetry

![A4 Search History](static/screenshots/a4-search-history.png)

The Search History interface shows recorded queries, filters, sort selections, result counts, no-result status, and timestamps.

---

## A5 Lifecycle Intelligence Interface

![A5 Intelligence Form](static/screenshots/a5-intelligence-form.png)

The A5 interface separates lifecycle retrieval from the intelligence request and explains the Retrieve → Analyze → Validate → Recommend workflow.

---

## A5 Retrieved Context

![A5 Retrieved Context](static/screenshots/a5-retrieved-context.png)

The interface shows the lifecycle records that were actually supplied as model context.

---

## A5 Generated Intelligence

![A5 Generated Intelligence](static/screenshots/a5-generated-intelligence.png)

The generated result displays recommendation, confidence, summary, rationale, supporting records, and limitations.

---

## A5 Error Handling

![A5 Error Handling](static/screenshots/a5-error-handling.png)

A zero-result retrieval blocks generation and explains that no context was available.

---

## A5 Stored Generated Results

![A5 Intelligence History](static/screenshots/a5-intelligence-history.png)

The Intelligence History interface displays persisted generated results and supporting evidence.

---

# Design Decisions

## Why These Fields Are Searchable

The following fields were selected:

```text
title
description
product
version
codename
```

because they represent the information users are most likely to know when attempting to identify a software release.

For example, a technician might know:

```text
Ventura
```

without knowing:

```text
macOS 13
```

Searching the codename makes that information discoverable.

---

## Why Product and Status Are Filters

Product and lifecycle state are structured attributes with a limited set of possible values.

They are therefore more appropriate as Boolean-style filters than as free-text search fields.

---

## Why Relevance Uses a Custom Score

BryghtCentral currently contains a relatively small and highly structured lifecycle dataset.

A rule-based relevance model provides several advantages:

- Easy to explain
- Easy to debug
- Predictable behavior
- No additional search infrastructure
- Strong matches in important fields can be weighted more heavily

This approach is appropriate for the current scale of the project.

---

## Why Pagination Uses 15 Results

A page size of:

```text
15
```

was selected as a balance between:

- Displaying enough information to browse efficiently
- Keeping pages manageable
- Avoiding rendering the full result collection
- Providing meaningful pagination for large searches such as Chrome

---

## Why Search Telemetry Is Stored

Search telemetry prepares BryghtCentral for later intelligent-system functionality.

Future versions could use search activity to identify:

- Common user needs
- Frequently searched products
- Poor-performing queries
- Missing terminology
- Failed searches
- Useful ranking improvements
- Recommendation opportunities

---

## A5 Intelligence Design Decisions

### Why Recommendation Was Selected

Recommendation fits BryghtCentral's IT operations domain because lifecycle records already contain evidence that can help a technician decide whether a release should be kept, upgraded, replaced, or investigated.

### Why the Prompt Is Restrictive

The prompt tells Gemini to use only retrieved context and to avoid inventing lifecycle facts. This keeps the output tied to BryghtCentral evidence rather than arbitrary outside knowledge.

### Why Context Is Bounded

At most five retrieved records are supplied. This reduces irrelevant context, latency, and opportunities for unsupported claims.

### How Hallucinations and Invalid Output Are Handled

Gemini receives a JSON schema, Pydantic validates the structure, and the application rejects supporting record IDs that were not included in the retrieved context. Failed validation prevents display and persistence.

### Current A5 Limitations

- The intelligent capability currently focuses on lifecycle recommendations.
- Gemini availability and free-tier limits may affect response reliability.
- An exact search can retrieve only one release, so comparison data may be unavailable.
- Confidence is categorical rather than a statistical probability.
- Natural-language reasoning still requires human review even after structural validation.

---

# Ethical and Privacy Considerations

Search telemetry can potentially reveal user interests or behavior.

BryghtCentral currently avoids collecting sensitive personal information.

The telemetry model stores retrieval activity rather than identity information.

If authentication or personalized search is added later, additional privacy controls would be necessary.

For A5, Gemini receives only bounded lifecycle context needed for the current request. Database credentials, API keys, SSH details, and unrelated records are excluded from the prompt.

Potential improvements could include:

- Retention limits
- User consent
- Anonymization
- Administrative access controls
- Telemetry deletion policies

---

# Known Limitations

The current retrieval system intentionally remains understandable and relatively simple.

Known limitations include:

- Search is primarily keyword-based.
- Synonyms are not understood automatically.
- Singular and plural forms may produce different results.
- Stemming and lemmatization are not implemented.
- Typographical errors are not automatically corrected.
- Ranking is rule-based.
- MySQL full-text indexing is not currently used.
- Search is not personalized.
- Search results do not currently learn from previous user selections.
- Result clicks and selected-result rank are not yet recorded.
- Search suggestions are not implemented.
- Autocomplete is not implemented.
- Semantic similarity is not implemented.
- The current stored lifecycle collection is limited mainly to macOS and Google Chrome.
- Search relevance is optimized for the current structured lifecycle dataset rather than general unstructured documents.

---

# Future Work

A6 will evolve the A5 recommendation feature into decision support. The current system explains what the retrieved lifecycle evidence suggests; A6 can add alternatives, tradeoffs, user override, feedback, and decision-oriented presentation.

Potential A6 improvements include:

- Compare KEEP, UPGRADE, REPLACE, and INVESTIGATE alternatives
- Show tradeoffs and missing evidence
- Allow the user to accept, reject, or override a recommendation
- Record recommendation usefulness feedback
- Improve evaluation of generated intelligence
- Use broader retrieval when an exact-version search lacks comparison records


Future modules can build intelligent behavior on top of the A4 retrieval foundation.

Potential improvements include:

## Semantic Search

Use embeddings or another semantic representation so conceptually related queries can match even when they do not use the same words.

## Search Suggestions

Recommend alternate queries when a search produces few or no results.

## Autocomplete

Use existing stored products, versions, and search-history terms to suggest queries while the user types.

## Typo Tolerance

Handle small misspellings and spelling variations.

## Full-Text Indexing

Use MySQL full-text indexes if the database grows large enough that wildcard matching becomes inefficient.

## Personalized Ranking

Use user role, device environment, or previous interactions to prioritize relevant records.

## Search Interaction Telemetry

Record:

- Result selected
- Selected result rank
- Time to selection
- Query reformulation
- Abandoned searches

## Recommendations

Use stored information, search context, lifecycle status, and telemetry to recommend:

- Software upgrades
- Devices requiring attention
- Unsupported products
- Replacement priorities
- Appropriate software versions

## Retrieval-Augmented Intelligence

A5 now implements retrieval-augmented lifecycle recommendations using retrieved BryghtCentral records as grounded context. A6 can extend this foundation into explicit decision support.

---

# Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Flask-Migrate
- Alembic
- PyMySQL
- MySQL / MariaDB
- python-dotenv
- Requests
- BeautifulSoup
- Pydantic
- HTML
- CSS
- Jinja
- Git
- GitHub
- CI Keys
- SSH tunneling
- Gemini Developer API
- Gemini REST `generateContent` endpoint
- Pydantic

---

# Assignment Progress

```text
A1 — Application Foundation                 Complete
A2 — Information Acquisition                Complete
A3 — Information Persistence                Complete
A4 — Search and Information Retrieval       Complete
A5 — Intelligence Generation                Complete
```

BryghtCentral now supports the full information flow developed through the first five application assignments:

```text
Acquire
   ↓
Persist
   ↓
Retrieve
   ↓
Rank
   ↓
Build Context
   ↓
Generate Intelligence
   ↓
Validate
   ↓
Persist Generated Result
   ↓
Present
```

This A5 intelligence foundation prepares BryghtCentral for A6 decision support.
