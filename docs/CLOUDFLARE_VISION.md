# Humanizer Platform Expansion - Cloudflare Workers Architecture & Multi-Format Archive System

## Vision Summary

Transform Humanizer into a dual-deployment platform:
1. **Cloud (humanizer.com)** - Cloudflare Workers serverless with global scalability
2. **Local (Mac/Node.js)** - Personal archive with MCP server for any compatible UI

## Key Requirements

### Architecture Goals
- **Cloudflare Workers deployment** for public frontend (serverless, globally distributed)
- **Cloudflare Containers** for transformation engine (Docker containers on Workers, available June 2025)
- **Cloudflare R2** for media/document storage (zero egress fees, S3-compatible)
- **Cloudflare D1** for metadata/indexes (SQLite-based, 10GB per database, horizontal scaling)
- **Local Node.js app** for personal archives (PostgreSQL + pgvector)
- **MCP Server** implementation for local archive API access from any compatible app

### Data Processing Expansion

Support rich metadata extraction and indexing for:
- **ChatGPT archives** (JSON exports)
- **Claude conversation exports** (JSON)
- **Facebook archive** (photos, posts, messages, metadata)
- **X/Twitter archive** (tweets, media, interactions)
- **Images** (EXIF metadata, OCR text extraction, visual embeddings)
- **Documents** (PDF, DOCX, XLSX with full text + metadata)
- **Audio/Video** (transcription, scene detection, temporal indexing)
- **Email archives** (MBOX, PST with threading/metadata)

### Storage Strategy Decision

**Option A: Database-centric** (Recommended for Cloudflare)
- Store all content in D1/PostgreSQL with rich metadata
- Files stored in R2/filesystem, referenced by hash
- Advantages: Fast queries, vector search, relational integrity
- Disadvantages: Migration complexity, storage duplication

**Option B: Filesystem-centric**
- Files in filesystem/R2 with sidecar metadata
- Database only stores indexes and embeddings
- Advantages: Simpler migration, lower DB costs
- Disadvantages: Slower queries, harder to maintain consistency

**Hybrid Approach** (Best of both):
- Small content (<100KB): Store in database with embeddings
- Large media: R2/filesystem with hash reference + metadata in DB
- All searchable via vector embeddings regardless of storage location

### Authentication & Privacy Architecture

- **Robust user accounts** with OAuth2/WebAuthn
- **Sub-accounts/personas** - pseudonymous identities per context
- **Sophisticated privacy masks** - control what's shared per transformation
- **Zero-knowledge encryption** option for private archives
- **Granular sharing controls** - share specific transformations, not full archive
- **Anti-doxing protection** - metadata stripping, identity separation

### Chunking & Embedding Strategy

**Intelligent chunking**:
- Semantic boundaries (paragraphs, sections, turns in conversation)
- Overlapping windows for context preservation
- Size-adaptive: 512 tokens for dense content, 2048 for sparse
- Preserve document structure in metadata

**Embedding approach**:
- Source content embeddings (Voyage-3 or OpenAI ada-003)
- Transformed content embeddings
- Multi-level: document, chunk, and sentence embeddings
- Metadata embeddings for multi-modal search

## Implementation Roadmap

### Phase 1: Cloudflare Workers MVP (8 weeks)
1. **Worker deployment** - Transform API on Cloudflare Workers
2. **R2 integration** - File upload/storage with zero egress
3. **D1 database** - Metadata and transformation history
4. **Container setup** - Transformation engine in Docker on Workers (June 2025+)
5. **Vector search** - Implement pgvector equivalent or Pinecone integration

### Phase 2: Multi-Format Ingestion (6 weeks)
1. **ChatGPT/Claude importers** - Parse conversation JSON, extract metadata
2. **Social media archives** - Facebook/X parsers with media extraction
3. **Document processors** - PDF/DOCX text extraction + OCR
4. **Media processors** - Image EXIF, audio transcription, video scene detection
5. **Email importers** - MBOX/PST parsing with threading

### Phase 3: Local MCP Server (4 weeks)
1. **Node.js MCP server** - Expose local archive via Model Context Protocol
2. **PostgreSQL + pgvector** - Local database with vector search
3. **Ollama integration** - Local transformations with open models
4. **Cloud sync option** - Selectively sync to cloud via R2
5. **Compatible with any MCP client** - Claude Desktop, VS Code, etc.

### Phase 4: Privacy & Security (6 weeks)
1. **User account system** - OAuth2, WebAuthn, magic links
2. **Pseudonymous sub-accounts** - Create masked identities per context
3. **Granular sharing** - Share specific transformations, not full archive
4. **Metadata stripping** - Remove identifying info before sharing
5. **Zero-knowledge encryption** - Optional E2E encryption for archives

### Phase 5: Advanced Features (8 weeks)
1. **Belief pattern network** - Visualize evolution across all archives
2. **Temporal analysis** - Track framework changes over time
3. **Cross-archive search** - Semantic search across all imported content
4. **Collaborative transformations** - Shared sessions with privacy controls
5. **API marketplace** - Share transformation frameworks securely

## Technical Architecture

### Cloudflare Stack
```
Frontend (Workers) → API (Workers) → Containers (Transform Engine)
                          ↓
                    R2 (Media/Files)
                          ↓
                    D1 (Metadata/Index)
                          ↓
                    Vectorize (Embeddings) OR Pinecone
```

### Local Stack
```
MCP Server (Node.js) → PostgreSQL + pgvector
                            ↓
                    Local filesystem OR Cloud storage
                            ↓
                    Ollama (Local LLM transforms)
```

### Data Flow
1. User uploads archive (ChatGPT, Facebook, etc.)
2. Extract content → chunk intelligently
3. Generate embeddings for all chunks
4. Store: Large files in R2, metadata + embeddings in D1
5. Index for vector search
6. Transform on-demand using Workers/Containers
7. Results stored with provenance chain

## Cloudflare Services Overview (2025)

### Cloudflare Workers
- Serverless platform for building, deploying, and scaling apps
- Global network deployment with single command
- No infrastructure to manage

### Cloudflare Containers (June 2025 Beta)
- Run Docker containers on Workers
- Built on Durable Objects for state management
- Supports resource-intensive apps requiring parallel CPU cores
- Full filesystem and specific runtime environments
- Autoscaling and sleep instances

### Cloudflare R2
- Zero-egress-fee object storage
- S3-compatible API
- Native integration with Workers (330+ data centers)
- Apache Iceberg integration for data warehouse functionality

### Cloudflare D1
- Managed serverless SQLite database
- Horizontal scale-out across multiple 10GB databases
- Time Travel: restore to any minute within last 30 days
- Pricing based only on query and storage costs
- Ideal for per-user, per-tenant, or per-entity databases

### Cloudflare Durable Objects
- Building block for stateful applications
- Distributed systems support
- Manages container lifecycle

## Next Steps (Immediate)
1. Test ChatGPT/Claude archive import with current PostgreSQL system
2. Design D1 schema for Cloudflare deployment
3. Prototype Workers deployment of transformation API
4. Build MCP server for local archive access
5. Implement privacy mask system

## Notes
- Cloudflare Containers enable running transformation engines globally
- R2 zero-egress makes media storage economically viable
- D1 horizontal scaling supports massive user growth
- MCP server enables any compatible app to access local archives
- Hybrid storage strategy balances performance and cost

---

**Status**: Vision documented, awaiting implementation
**Last Updated**: 2025-01-04
**Next Review**: After Phase 1 completion
