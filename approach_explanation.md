# Approach Explanation — Adobe India Hackathon Round 1B

## Objective

To build a robust system that, for any set of input PDFs and a specified persona/job, extracts and ranks the most relevant document sections and provides granular subsection details, suitable for generically analyzing a diverse range of documents.

---

## Solution Pipeline

**1. Section & Heading Extraction**
- Each PDF is parsed with `pdfplumber` to extract all lines of text as well as typographic and positional features (font size, boldness, position, etc).
- Headings (Title, H1-H3) are detected using a combination of:
  - Font size clustering
  - Capitalization heuristics (ALL CAPS/Title case/short length)
  - Section numbering patterns (e.g., `1.`, `1.1`, `A.`)
  - Keyword match against common academic headings (e.g., "Introduction", "Methods", "Results", etc)
- Text within each section heading is grouped by capturing all following lines until the next detected heading.

**2. Semantic Embedding & Relevance Scoring**
- The section title+content and the persona/job string are embedded using the compact, CPU-friendly `sentence-transformers` MiniLM model (`all-MiniLM-L6-v2`).
- Each section is scored for relevance (cosine similarity) to the combined persona/job description.
- Sections with job-critical keywords (e.g., methodology, data, evaluation) are favored.

**3. Ranking & Subsection Analysis**
- All sections across PDFs are stack-ranked by similarity.
- Top N (e.g., 5 or 10) most relevant sections are reported as `"extracted_sections"`, with corresponding "importance_rank".
- For each, a concise content snippet is produced by taking the start of the grouped section text and cleaning out footers/artifacts.

**4. Output Formatting**
- Results are serialized to JSON per the hackathon sample, including full metadata, ranked sections, and cleaned subsection details.
- The system is fully automated, with one result JSON per input PDF.

---

## Design Choices

- **Generalization:** No hardcoded document logic; headings are detected using layered heuristics that work across a wide variety of PDFs.
- **Efficiency:** All operations (including the ML model) are CPU-only and offline, fulfilling the hackathon’s runtime/environment constraints.
- **Pragmatism:** The modular design allows easy future extension (multi-language, more advanced summarization) and is simple to debug/test.

---

## Challenges & Solutions

- Noisy heading detection: Solved with combined visual/lexical rules along with keyword matching to avoid mid-paragraph junk or footers.
- Subsection noise: Output is limited to the first meaningful paragraph, truncated and cleaned.
- Diverse PDF formats: Method is tested on research articles and general documents, with options for further keyword or contextual boosting.

---

## Extensibility and Compliance

- Strict no-internet operation
- Model is <1GB; all dependencies and logic included
- Ready-to-run in Docker, with all required documentation for reproducibility


