import os
import re
import pdfplumber
import numpy as np
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# ==== HACKATHON-COMPLIANT AUTOMATION ====
# input_dir = "/app/input/"
# output_dir = "/app/output"
import os

if os.path.exists("/app/input"):
    input_dir = "/app/input"
    output_dir = "/app/output"
elif os.path.exists("app/input"):
    input_dir = "app/input"
    output_dir = "app/output"
elif os.path.exists("./input"):
    input_dir = "./input"
    output_dir = "./output"
else:
    raise Exception(
        "Could not find input directory. Please ensure you have an 'app/input' or './input' folder."
    )


# Define persona and job query here for the batch (can swap to env/os.environ/argparse if needed)
persona = "PhD Researcher in semantic plagiarism"
job = "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks"

def extract_sections_from_pdf(pdf_path):
    lines = []
    common_headings = set([
        "introduction", "abstract", "related work", "background", "methods", "methodology",
        "materials and methods", "system architecture", "literature review", "experiments",
        "dataset", "datasets", "experimental results", "analysis", "results", "evaluation",
        "discussion", "conclusion", "summary", "references"
    ])
    section_re = re.compile(r"^(\d+(\.\d+)*|[A-Z]|[IVXLC]+)\.?\s")
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            chars = page.chars
            if not chars:
                continue
            lines_by_y = {}
            for c in chars:
                y_key = round(c['top'])
                lines_by_y.setdefault(y_key, []).append(c)
            for y0 in sorted(lines_by_y.keys()):
                chars_in_line = lines_by_y[y0]
                text = ''.join(c['text'] for c in chars_in_line).strip()
                if not text:
                    continue
                fontsize = np.mean([c['size'] for c in chars_in_line])
                fontname = chars_in_line[0]['fontname']
                bold = "Bold" in fontname
                lines.append({
                    "text": text,
                    "font_size": fontsize,
                    "font": fontname,
                    "bold": bold,
                    "page": page_num,
                    "y": y0
                })
    all_sizes = sorted({line['font_size'] for line in lines}, reverse=True)
    while len(all_sizes) < 4:
        all_sizes.append(all_sizes[-1])
    title_font, h1_font, h2_font, h3_font = all_sizes[:4]
    heading_lines = []
    for line in lines:
        text = line['text']
        text_lc = text.lower().strip(": .")
        is_heading = (
            line['font_size'] in (title_font, h1_font, h2_font, h3_font)
            or (text.isupper() and 3 <= len(text.split()) <= 8)
            or section_re.match(text)
            or any(h in text_lc for h in common_headings)
        ) and (3 <= len(text.split()) <= 12)
        if is_heading:
            if line['font_size'] == title_font:
                level = "Title"
            elif line['font_size'] == h1_font:
                level = "H1"
            elif line['font_size'] == h2_font:
                level = "H2"
            elif line['font_size'] == h3_font:
                level = "H3"
            else:
                level = "H3"
            heading_lines.append({**line, "level": level})
    sections = []
    current = None
    for line in lines:
        matched_headings = [h for h in heading_lines if (
            h['text'] == line['text'] and h['page'] == line['page'] and h['y'] == line['y']
        )]
        if matched_headings:
            if current:
                sections.append(current)
            heading = matched_headings[0]
            if heading['level'] == "Title":
                current = None
                continue
            current = {
                "title": heading['text'],
                "level": heading['level'],
                "page": heading['page'],
                "content": ""
            }
        else:
            if current and line['font_size'] >= 7:
                if line['text'].strip():
                    current['content'] += line['text'].strip() + " "
    if current:
        sections.append(current)
    return sections

def clean_text_block(txt, maxlen=400):
    txt = re.sub(r'\s*\d+\s*$', '', txt)
    txt = re.sub(r'©.*$', '', txt)
    txt = txt.strip()
    return txt[:maxlen]

def process_pdf(pdf_path, persona, job, model):
    docname = os.path.basename(pdf_path)
    sections = extract_sections_from_pdf(pdf_path)
    all_sections = []
    for sec in sections:
        all_sections.append({
            "document": docname,
            "title": sec['title'],
            "level": sec['level'],
            "page": sec['page'],
            "content": sec['content'].strip()
        })
    section_texts = [sec['title'] + ". " + sec['content'] for sec in all_sections]
    if not section_texts:
        # Empty or failed PDF, return minimal output
        return {
            "metadata": {
                "input_documents": [pdf_path],
                "persona": persona,
                "job": job,
                "timestamp": datetime.utcnow().isoformat()
            },
            "extracted_sections": [],
            "subsection_analysis": []
        }
    persona_job = persona.strip() + ". " + job.strip()
    persona_job_emb = model.encode(persona_job)
    section_embs = model.encode(section_texts, batch_size=16)
    similarities = util.cos_sim(persona_job_emb, section_embs).cpu().numpy().flatten()
    for i, sec in enumerate(all_sections):
        sec['similarity'] = float(similarities[i])
    ordered_sections = sorted(all_sections, key=lambda s: s['similarity'], reverse=True)
    n_top_sections = min(5, len(ordered_sections))
    timestamp = datetime.utcnow().isoformat()
    output_json = {
        "metadata": {
            "input_documents": [pdf_path],
            "persona": persona,
            "job": job,
            "timestamp": timestamp
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }
    for i, sec in enumerate(ordered_sections[:n_top_sections]):
        output_json["extracted_sections"].append({
            "document": sec['document'],
            "page": int(sec['page']),
            "section_title": sec["title"],
            "importance_rank": i + 1
        })
        output_json["subsection_analysis"].append({
            "document": sec['document'],
            "page": int(sec['page']),
            "refined_text": clean_text_block(sec['content'])
        })
    return output_json

def main():
    # Load embedding model just once!
    model = SentenceTransformer('all-MiniLM-L6-v2')
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for fname in pdf_files:
        print(f"Processing PDF: {fname}")
        fpath = os.path.join(input_dir, fname)
        out_name = os.path.splitext(fname)[0] + ".json"
        outpath = os.path.join(output_dir, out_name)
        result = process_pdf(fpath, persona, job, model)
        with open(outpath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
