# GeneCLI - Gene Information Lookup Tool

A Python CLI tool that fetches gene information from NCBI persistent local caching.
I built this tool because I once tried to classify genes based on their functionality and I think that a tool like this would have really speed my job (I tried to filter unrelevant genes, and find relevant ones to a group of cells, based on their behavior), I used visual studio code with Claude Haiku 4.5 and it worked amazingly.

## Features

- **Persistent Caching**: Local JSON cache in the project directory (`cache.json`) to avoid re-downloading
- **Separation of Concerns**: `business.py` (business logic + cache) and `cli.py` (user interaction)
- **Interactive & One-shot Modes**: Run interactively or pass genes as arguments
- **Rich Output**: Multi-field display including Entrez ID, chromosome, location, descriptions, and direct links
- **Smart Fallback System**: GeneALaCart → ClinicalTables NCBI → NCBI Entrez (for robust gene lookups)
- **Error Handling**: Clear feedback for invalid genes, network errors, and edge cases
- **Comprehensive Testing**: 16 unit tests, all passing, with mocked API responses
- **No API Keys Required**: All public APIs, no credentials needed


### Quick Fetch (one or more genes)

```bash
# Fetch BRCA1 and TP53 info
python3 cli.py BRCA1 TP53

# Output:
# BRCA1 | Entrez:672 | Chr:17 | Loc:17q21.31
# Summary: This gene encodes a 190 kD nuclear...
# Description: BRCA1 DNA repair associated
# NCBI: https://www.ncbi.nlm.nih.gov/gene/672
# GeneCards: https://www.genecards.org/cgi-bin/carddisp.pl?gene=BRCA1
```

### Interactive Mode

```bash
python3 cli.py

# Then type:
genes> BRCA1 TP53
# [shows results]

genes> CFTR
# [shows results]

genes> help
# [shows usage]

genes> exit
# [closes program]
```

### Show Help

```bash
python3 cli.py --help
# or
python3 cli.py -h
```

### Run Tests

```bash
python3 -m pytest test_genecli.py -v
# or short output:
python3 -m pytest test_genecli.py -q
```


## How It Works

### Business Logic (`business.py`)

- **GeneCache**: Persistent JSON-based cache (`cache.json` in the project directory)
  - Case-insensitive lookups
  - Legacy cache cleanup (removes old format entries)
  - Automatic directory creation
- **Gene Data Fetching** (Multi-source fallback strategy):
  1. Check local cache first
  2. Try GeneCards GeneALaCart (detects auth requirement)
  3. Fall back to ClinicalTables NCBI Genes API
  4. Fall back to NCBI Entrez esearch + esummary for exact symbol matching
- **Data Enrichment**:
  - NCBI Entrez esummary for detailed gene descriptions
  - Direct links to NCBI Gene pages and GeneCards
- **Error Handling**:
  - `GeneNotFoundError` exception for non-existent genes
  - Invalid genes are NOT cached
  - Network errors propagate with clear messages

### Output Format

```
SYMBOL | Entrez:ID | Chr:X | Loc:Xp00.0
Summary: [One-line condensed summary, max 300 chars]
Description: [Full multi-line description]
NCBI: https://www.ncbi.nlm.nih.gov/gene/ID
GeneCards: https://www.genecards.org/cgi-bin/carddisp.pl?gene=SYMBOL
```

### CLI Interface (`cli.py`)

- **Argument Parsing**:
  - `python cli.py --help` or `-h`: Show help
  - `python cli.py GENE1 GENE2 ...`: Fetch genes and exit
  - `python cli.py`: Enter interactive mode
- **Interactive Mode Commands**:

  - Type gene symbols separated by spaces
  - `help` or `--help`: Display help
  - `exit` or `quit`: Exit program
  - `Ctrl-C`: Exit program

- **Error Indicators**:
  - ❌ Gene not found (invalid gene)
  - ⚠️ Error fetching (network or API error)

## Cache

Data is automatically cached in:

```
cache.json
```

**What Gets Cached?**

- ✅ Valid gene symbols (found in NCBI)
- ✅ Gene info (ID, chromosome, location, descriptions, summaries)
- ❌ Invalid genes are NOT cached

**First Run vs. Subsequent Runs:**

```bash
# First run (fetches from NCBI, caches result)
$ python3 cli.py BRCA1
[network request to NCBI]
BRCA1 | Entrez:672 | Chr:17 | Loc:17q21.31
...

# Second run (instant, from cache - no network needed!)
$ python3 cli.py BRCA1
[reads from cache.json]
BRCA1 | Entrez:672 | Chr:17 | Loc:17q21.31
...
```

## Testing

The project includes 16 comprehensive unit tests covering:

- **Cache Operations**: Persistence, case-insensitivity, legacy cleanup
- **API Fetching**: Success cases, not-found scenarios, error handling
- **Integration**: Full gene data retrieval, caching validation
- **URL Generation**: NCBI and GeneCards URL correctness
- **Edge Cases**: Empty input, whitespace, invalid IDs

All tests use mocked API responses (no network dependency):

```bash
python3 -m pytest test_genecli.py -v
# Expected: 16 passed
```

## API Integration

### ClinicalTables NCBI Genes (Tier 1)

- Public API endpoint
- Search genes by symbol with exact matching
- Fetch GeneID, chromosome, map_location
- Returns multiple fields in one request

### NCBI Entrez (Tier 2 & 3)

- **esearch**: Find genes by symbol, returns GeneID
- **esummary**: Fetch detailed summaries, descriptions
- Used as fallback when ClinicalTables doesn't have exact match

### GeneCards GeneALaCart (Tier 0)

- Attempted first if available
- Detects when auth is required (returns HTML) and falls back gracefully

## Implementation Highlights

### Separation of Concerns

- `business.py`: API calls, caching, data normalization (no user I/O)
- `cli.py`: User interaction, output formatting (no business logic)
- Clean interfaces, easy to test and extend

### Robust Multi-Source Fallback

Handles API limitations gracefully:

- ClinicalTables fuzzy matching issue resolved with Entrez exact match fallback
- GeneALaCart auth requirement detected and handled

### Smart Caching

- Case-insensitive, normalized keys (always uppercase)
- Legacy format detection and cleanup
- Separates one-line and full summaries

### Comprehensive Testing

- 16 unit tests covering all major functions
- Mock API responses to avoid network dependency
- Temporary directories for cache testing
- 100% pass rate

---

## Development History & Interaction Summary

This project was developed through an iterative conversation with GitHub Copilot using the **Claude 3.5 Sonnet** model.

### Key Milestones

1. **Initial Request**: Create a CLI script that takes space-separated gene list, checks local cache, fetches from NCBI via API, outputs results, and loops. Requirements: separation of business logic/UI, persistent storage, no sensitive data in git.

2. **Core Implementation** (Messages 1-4):

   - Created `business.py` with `GeneCache` class and API integration
   - Created `cli.py` for user interaction
   - Generated supporting files (requirements.txt, .gitignore, README.md, **init**.py)
   - Initial API: GeneALaCart, fallback to MyGene.info

3. **API Pivot to NCBI** (Message 5):

   - User requested NCBI instead of MyGene.info
   - Implemented ClinicalTables NCBI Genes API as primary fallback
   - Endpoint: `https://clinicaltables.nlm.nih.gov/api/ncbi_genes/v3/search`

4. **Feature Enhancements** (Messages 6-9):

   - Added multi-field output (GeneID, chromosome, map location)
   - Added links (NCBI Gene pages, GeneCards URLs)
   - Added one-line summary using NCBI Entrez esummary API
   - Added `--help` option, error handling for non-existent genes
   - Implemented 16 comprehensive unit tests (all passing)

5. **Bug Fix - Fuzzy Match Issue** (Message 10):

   - User reported searching for "ex" returned unrelated GPR84
   - Root cause: ClinicalTables uses fuzzy search (partial matches)
   - Fix: Removed fallback to first result; now requires exact match

6. **Regression & Secondary Fallback** (Message 11-Current):
   - Strict exact matching broke TP53 lookup (ClinicalTables missing)
   - Root cause: ClinicalTables returns related genes (TP53TG3, TP53RK) but not TP53
   - Solution: Implemented NCBI Entrez esearch + esummary as secondary fallback
   - Result: TP53 now works; all 16 tests still passing

### Evolution of Requirements

- **Output Format**: Simple summary → Rich multi-field with links
- **API Sources**: GeneALaCart only → Multi-source with detection & fallbacks
- **Error Handling**: Basic → Comprehensive with test coverage
- **Gene Matching**: Accept any result → Strict exact matching with intelligent fallbacks

### Key Technical Decisions

1. **Persistent Cache in Home Directory**: Prevents git pollution, survives program restarts
2. **Case-Insensitive Lookups**: User convenience, normalized storage
3. **Multiple API Layers**: Resilience against API limitations
4. **Mock Testing**: Comprehensive tests without network dependency
5. **Clean Separation**: Business logic entirely separate from CLI concerns

### Tools & Technologies

- **Language**: Python 3
- **HTTP Requests**: `requests` library
- **Testing**: `pytest` with mocking
- **APIs**: ClinicalTables, NCBI Entrez (esearch, esummary), GeneALaCart
- **Data Storage**: JSON cache in `cache.json` (project directory)

---

## Notes

- The cache file is stored in the local directory
- No API keys are required for basic queries. The script uses only public APIs
- For very large gene lists, consider processing in batches to avoid rate limiting


## Links

- https://genealacart.genecards.org
- https://clinicaltables.nlm.nih.gov
