# Confluence to Azure Search Data Ingestion

A data ingestion application that fetches content from Confluence, processes it, and indexes it in Azure Search for advanced search capabilities.

## Features

- Fetch specific pages or entire spaces from Confluence
- Parse and extract document metadata from structured tables
- Handle different document types (ABRD, FBRD)
- Split content into searchable sections based on headings
- Convert HTML content to well-structured Markdown
- Extract and index requirement IDs (e.g., FR-001, PR-001)
- Index full documents and sections in Azure Search
- Support for semantic search and hybrid queries
- Vector search capabilities using Azure OpenAI embeddings
- AI-generated document summaries using Azure OpenAI chat models
- SQLite-based persistent caching to avoid re-processing unchanged content
- Version tracking with unique document IDs in the search index
- Page configuration management system

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Copy `env.template` to `.env`:
   ```
   cp env.template .env
   ```
2. Edit `.env` and fill in your Confluence and Azure Search credentials
3. For AI features, configure Azure OpenAI settings:
   - `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
   - `AZURE_OPENAI_DEPLOYMENT_NAME`: The deployment name of your chat model
   - `AZURE_OPENAI_API_VERSION`: Use "2024-12-01-preview" or later
   - `ENABLE_SUMMARIZATION`: Set to "true" to enable AI summaries
4. Configure pages to process in `config/pages.json` (see Page Configuration section)

## Usage

### Process a specific page

```
python src/main.py --page-id 123456
```

### Process all pages in a space

```
python src/main.py --space-key MYSPACE
```

### Process all configured pages

```
python src/main.py --process-all
```

### Enable AI Summarization

To process a page with AI-generated summaries:

```
ENABLE_SUMMARIZATION="true" python src/main.py --page-id 123456
```

Or set `ENABLE_SUMMARIZATION="true"` in your `.env` file.

### Page Configuration Management

```
# List all configured pages and spaces
python src/main.py --list-pages

# Add a page to configuration
python src/main.py --add-page 123456 --page-name "My Document"

# Remove a page from configuration
python src/main.py --remove-page 123456
```

### Cache Management

```
# Show cache statistics
python src/main.py --cache-status

# Clear the cache
python src/main.py --clear-cache

# Force reindex a page (ignores cache)
python src/main.py --page-id 123456 --force-reindex
```

### Additional options

- `--config-file`: Specify an alternate config file path (default: config/pages.json)
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--dry-run`: Process content but don't send to Azure Search
- `--force-reindex`: Force reprocessing even if the page version hasn't changed

## Project Structure

```
.
├── config/            # Configuration files
│   └── pages.json     # Page configuration
├── src/
│   ├── config/        # Configuration loading
│   ├── connectors/    # API clients for external services
│   │   ├── confluence/ # Confluence API client
│   │   └── azure_search/ # Azure Search client
│   ├── core/          # Core processing logic
│   ├── models/        # Data models
│   ├── services/      # External service integrations
│   └── utils/         # Utility functions
├── tests/             # Unit and integration tests
├── docs/              # Documentation
├── env.template       # Template for environment variables
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Azure Search Index Schema

The application expects an Azure Search index with the following fields:

- `id` (String): Unique identifier for the document (includes version info)
- `content` (String): The main content of the document or section
- `source_page_id` (String): The ID of the source page in Confluence
- `source_page_title` (String): The title of the source page
- `source_url` (String): URL to the source page
- `is_section` (Boolean): Whether this is a section or full document
- `section_id` (String): ID of the section (if applicable)
- `section_title` (String): Title of the section (if applicable)
- `section_level` (Integer): Heading level of the section
- `section_number` (String): Section number (e.g., "2.1.3")
- `document_type` (String): Type of document (ABRD, FBRD, UNKNOWN)
- `project_code` (String): Project code extracted from document ID
- `document_id` (String): Document ID from metadata
- `document_version` (String): Document version
- `document_status` (String): Document status (DRAFT, APPROVED, etc.)
- `created_date` (String): When the document was created
- `last_updated_date` (String): When the document was last updated
- `document_owner` (String): Owner of the document
- `summary` (String): AI-generated summary (if enabled)
- `requirement_ids` (Collection(String)): Requirements IDs found in the section
- `vector` (Collection(float)): Vector embedding of the content for vector search

## Page Configuration

The application uses a JSON configuration file to manage pages and spaces to process. Example:

```json
{
  "pages": {
    "5296685148": {
      "name": "Business Requirements for Project WSC",
      "enabled": true,
      "type": "ABRD",
      "project": "WSC"
    }
  },
  "spaces": {
    "AJODMS": {
      "name": "AJODMS",
      "enabled": true,
      "description": "Main documentation space"
    }
  }
}
``` 