LAB M2.04 Different Ways to Chunk Podcast and PDF
Cindy Lund

# Chunking Strategy Analysis and Recommendations
Overview
This lab evaluated multiple chunking strategies for two different content types:
A structured PDF document (Ethics Guidelines for Trustworthy AI)
A conversational podcast transcript
The goal was to compare chunk quality, boundary preservation, and alignment with LLM context constraints.

# Strategy Comparison
## 1. Fixed-Size Chunking (Character-Based)
Chunk size: 1000 characters
Overlap: 50 characters

# Observations:
High mid-word split rate (PDF: 0.95)
Very high sentence break rate (PDF: 0.98)
Ignores paragraph and structural boundaries
Character count does not align with token count
1000 characters ≈ 272 tokens (PDF average)

# Conclusion
Fixed-size chunking is simple and predictable but damages semantic coherence. It is suitable only as a baseline approach.

## 2. Recursive Character Chunking
Chunk size: 1000 characters
Overlap: 200 characters
Separator priority: ["\n\n", "\n", ". ", " ", ""]
Observations (PDF)
Sentence break rate reduced from 0.98 → 0.69
Mid-word split rate reduced from 0.95 → 0.62
Preserves paragraph and header structure
Slightly smaller average chunk size due to structure-aware splitting

Observations (Podcast)
Minimal improvement over fixed-size
Conversational text lacks strong structural markers
Sentence break rate remains high due to spoken phrasing

Conclusion
Recursive chunking significantly improves structural preservation for structured documents like PDFs. It is the best strategy for documents with clear formatting and paragraph boundaries.

## 3. Token-Based Chunking
Chunk size: 500 tokens
Overlap: 50 tokens

Observations (PDF)
162 chunks (fewer than character-based methods)
Average ≈ 363 tokens per chunk
Character lengths vary significantly (~1337 avg chars)
Better alignment with model context windows
Observations (Podcast)
Only 5 chunks (vs 11 for character-based)
Average ≈ 464 tokens per chunk
Efficient use of context window
No structural awareness

Conclusion
Token-based chunking aligns directly with LLM context limits and embedding cost planning. It is the most production-aligned approach, especially for conversational transcripts.

Sentence Break Rate:
Fixed: 0.98
Recursive: 0.69
Token: 0.93
Mid-Word Split Rate:
Fixed: 0.95
Recursive: 0.62
Token: 0.82

Recursive chunking clearly preserves semantic boundaries best for structured documents.

Podcast Transcript
Sentence Break Rate:
Fixed: 1.0
Recursive: 1.0
Token: 1.0

Due to conversational structure, differences between strategies are less pronounced. Structural preservation is limited by the nature of spoken language rather than the algorithm itself.

### Trade-Off Summary
### Fixed-Size
- Pros: Simple, predictable
- Cons: Breaks sentences and words, ignores structure
- Best for: Quick baselines, uniform content

### Recursive
- Pros: Preserves structure, reduces destructive splits
- Cons: Slightly variable chunk sizes
- Best for: Structured documents (PDFs, reports)

### Token-Based
- Pros: Accurate for LLM context windows, efficient chunk count
- Cons: Not structure-aware
- Best for: Production RAG systems, conversational transcripts

### Semantic
- Pros: Meaning-based splitting
- Cons: Computationally expensive
- Best for: Complex long-form documents

# Key Insight
Structured documents benefit most from structure-aware recursive chunking.
Conversational transcripts benefit most from token-based chunking aligned with model constraints.
Fixed-size chunking serves only as a baseline.
Token-based chunking is the most practical for real-world LLM systems.

# Recommended Strategy: Recursive Character Chunking
Chunk Size: 1000 characters
Overlap: 200 characters

# Reasoning:
Best sentence boundary preservation
Lowest mid-word split rate
Maintains structural integrity of headings and paragraphs
Most semantically coherent for structured content
For Podcast Transcripts

# Recommended Strategy: Token-Based Chunking
Chunk Size: 500 tokens
Overlap: 50 tokens

# Reasoning:
Maximizes LLM context window utilization
Efficient embedding cost
Produces fewer, larger, context-rich chunks
Structural preservation differences are minimal for conversational text


