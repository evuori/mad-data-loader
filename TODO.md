# Data Ingestion App TODOs

> **IMPORTANT**: Review and update this TODO file regularly. Use it to track progress, prioritize work, and ensure no requirements are missed. Mark items as [x] when completed.

## Core Requirements

### Confluence Integration
- [x] Research Confluence API options
- [x] Set up authentication to Confluence API
- [x] Build functionality to fetch specific page by ID
- [x] Extend to support fetching multiple pages
- [x] Consider migrating document metadata to table format in Confluence for better structure
- [x] Create template for consistent metadata table format across pages
- [x] Template exists at docs/templates/business-requirements-template.md

### Document Type Handling
- [x] Implement document type detection based on Document ID prefix:
  - [x] ABRD-* prefix indicates Application Business Requirements
  - [x] FBRD-* prefix indicates Feature Business Requirements
- [x] Extract project/application code from Document ID (e.g., "HRMS" from "ABRD-HRMS-2025-1.0")
- [x] Extract year from Document ID (e.g., "2025" from "ABRD-HRMS-2025-1.0")
- [x] Extract version from Document ID (e.g., "1.0" from "ABRD-HRMS-2025-1.0")
- [x] Create document type-specific parsing logic for each type
- [x] Map document type to metadata field in Azure Search
- [x] Add document type as a filterable field for search

### Content Processing
- [x] Parse Confluence content (likely HTML or XHTML)
- [x] Support extraction of document data from both list and table formats
- [x] Extract shared "Document Control" table data across all document types:
  - [x] Document ID
  - [x] Version
  - [x] Status
  - [x] Author
  - [x] Date Created
  - [x] Last Updated
  - [x] Approved By
  - [x] Approval Date
- [x] Also extract "Document History" table data
- [x] Develop type-specific content extraction for ABRD documents
- [x] Develop type-specific content extraction for FBRD documents
- [x] Convert Confluence content to well-structured Markdown format matching template
- [x] Identify and extract numbered sections based on headings (e.g., "1. Executive Summary")
- [x] Handle nested subsections (e.g., "2.1 Project Background")
- [x] Extract requirements with specific IDs from tables (e.g., FR-001, PR-001)
- [x] Maintain proper table formatting in Markdown output
- [x] Preserve list structures (numbered and bulleted)
- [x] Develop logic to split Markdown content by sections
- [x] Handle images and attachments appropriately
- [x] Preserve relevant formatting
- [x] Implement caching system to track processed document versions
- [x] Add logic to avoid sending duplicate content to Azure Search
- [x] Only update Azure Search when document version changes

### Azure Search Integration
- [x] Azure Search service is already set up and running
- [x] Create schema for the search index with appropriate fields:
  - [x] Document control metadata fields from template
  - [x] Document type field (ABRD or FBRD)
  - [x] Section content fields (in Markdown format)
  - [x] Full document content field (in Markdown format)
  - [x] Document summary field
- [x] Create specific fields for different requirement types (FR, PR, SR, etc.)
- [x] Index each section as a separate searchable document with parent document reference
- [x] Include requirement IDs as searchable fields with boosted relevance
- [x] Implement semantic search capabilities
- [x] Support hybrid queries (combining vector and keyword search)
- [x] Optimize document structure for search relevance

### AI Integration
- [x] Implement summarization via Azure OpenAI
- [x] Update summarization to use chat completion API
- [x] Configure proper API version for Azure OpenAI
- [x] Implement vector embeddings for semantic search
- [ ] Add ability to generate answers from document content
- [ ] Implement cross-document summarization
- [ ] Add relevance scoring to search results

## Technical Implementation

### Project Setup
- [x] Initialize project structure
- [x] Set up dependency management
- [x] Create .env file template with required variables
- [x] Document environment setup process
- [x] Add gitignore for sensitive files

### Architecture & Code Quality
- [x] Design modular architecture with separation of concerns
- [x] Implement clean interfaces between components
- [x] Add type definitions/interfaces for data structures
- [x] Follow consistent coding standards
- [x] Create reusable utilities for common operations

### Logging & Monitoring
- [x] Set up structured logging framework
- [x] Implement different log levels (info, debug, error)
- [x] Add performance metrics collection
- [x] Create detailed error reporting
- [x] Design informative console output format

### Caching
- [x] Implement SQLite-based persistent caching system
- [x] Track document versions to avoid duplicate processing
- [x] Add cache status reporting functionality
- [x] Provide cache clearing capabilities

### Configuration Management
- [x] Implement page configuration management system
- [x] Support for enabling/disabling specific pages
- [x] CLI interface for configuration management

## Additional Recommendations

### Testing Strategy
- [ ] Write unit tests for core functions
- [ ] Implement integration tests for external services
- [ ] Create mock data for testing
- [ ] Set up CI pipeline for automated testing
- [ ] Add load/performance testing for production readiness

### Error Handling & Resilience
- [x] Implement comprehensive error handling
- [x] Add retry mechanisms for transient failures
- [ ] Create circuit breakers for external dependencies
- [ ] Design graceful degradation strategies
- [x] Validate input data before processing

### Security & Compliance
- [x] Secure handling of credentials and secrets
- [x] Implement proper authentication for all services
- [ ] Add input sanitization to prevent injection attacks
- [ ] Follow principle of least privilege for service accounts
- [ ] Consider data residency and compliance requirements

### Performance Optimization
- [x] Implement batching for Azure Search operations
- [x] Add caching where appropriate
- [ ] Consider parallel processing for multiple pages
- [ ] Optimize memory usage for large documents
- [x] Add rate limiting to respect API quotas
- [x] Optimize AI request parameters for better performance

### Deployment & Operations
- [ ] Set up monitoring and alerting
- [ ] Document operational procedures and troubleshooting
- [ ] Create deployment scripts or containers
- [ ] Add health check endpoints
- [ ] Implement logging to external systems
- [x] Add detailed logging for AI operations

## Next Steps (Prioritized)
1. [ ] Implement question answering capabilities from document content
2. [ ] Add parallel processing for improved performance
3. [ ] Optimize AI model configuration and prompts
4. [ ] Build a simple web UI for searching indexed documents
5. [ ] Implement scheduled document updates
6. [ ] Set up automated testing infrastructure
7. [ ] Add visualization for document relationships
8. [ ] Create a document dashboard with statistics
9. [ ] Add support for other document sources beyond Confluence 