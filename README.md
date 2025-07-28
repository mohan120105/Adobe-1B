# Adobe India Hackathon – Round 1B Submission

**Author:** GMRIT
**Date:** 28-07-2025

## Overview

This repository presents my solution for Adobe India Hackathon Round 1B ("Connecting the Dots" – Persona-Driven Document Intelligence). The system intelligently extracts and ranks the most relevant sections and subsections from a set of input PDFs, given a user persona and a concrete job-to-be-done, outputting results in Adobe's required JSON schema.

---

## Directory Structure
```
project/
├── main.py
├── requirements.txt
├── Dockerfile
├── README.md
├── approach_explanation.md
└── app/
    ├── input/     # Place input PDF files here
    └── output/    # Output JSONs will be written here

```
---

## Build & Run Instructions

1. **Build the Docker Image**

```bash
docker build --platform linux/amd64 -t my_hackathon_solution .
```

2. **Run the Container**

Put your PDFs in an `input` folder.

```bash
docker run --rm \
-v $(pwd)/app/input:/app/input \
-v $(pwd)/app/output:/app/output \
--network none \
my_hackathon_solution
```

This will process all PDFs in `/app/input` and write results as `.json` files to `/app/output`.

---

## Detailed Instructions

* Place 3–10 PDFs into `app/input/`.
* The program automatically processes all PDFs and outputs one JSON results file per input PDF.
* No internet connection is required/run-time downloading.

---

## Dependencies

All dependencies are in `requirements.txt`.
Main libraries: `pdfplumber`, `sentence-transformers`, `torch`, `numpy`.

---

## Output

Example top-level keys in the output JSON:

* `"metadata"`
* `"extracted_sections"`
* `"subsection_analysis"`

See `approach_explanation.md` for methodology and further details.



