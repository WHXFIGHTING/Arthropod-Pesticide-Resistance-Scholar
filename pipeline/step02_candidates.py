                      
                       

import csv
import json
import re
from collections import Counter
from pathlib import Path


BINOMIAL_RE = re.compile(r"\b([A-Z][A-Za-z-]+ [a-z][a-z-]+)\b")


def list_methods_md_files(section_root, paper_id):
    return sorted((Path(section_root) / paper_id / "01_materials_and_methods").glob("*.md"))


def list_pesticide_md_files(section_root, paper_id):
    paper_dir = Path(section_root) / paper_id
    md_files = []
    md_files.extend(sorted((paper_dir / "01_materials_and_methods").glob("*.md")))
    md_files.extend(sorted((paper_dir / "02_results").glob("*.md")))
    md_files.extend(sorted((paper_dir / "04_results_and_discussion").glob("*.md")))
    return md_files


def load_species_dict(species_tsv):
    species_dict = {}
    with open(species_tsv, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            species_dict[row["name_txt"]] = row
    return species_dict


def load_common_species_dict(common_species_tsv):
    common_species_dict = {}
    with open(common_species_tsv, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            common_species_dict[row["common_name"].lower()] = row["species_name"]
    return common_species_dict


def load_pesticide_dict(pesticide_tsv):
    pesticide_rows = []
    with open(pesticide_tsv, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            pattern = re.compile(
                r"(?<![A-Za-z0-9-])" + re.escape(row["normalized_name"]) + r"(?![A-Za-z0-9-])"
            )
            row["pattern"] = pattern
            pesticide_rows.append(row)
    return pesticide_rows


def extract_species_mentions(text, species_dict, common_species_dict):
    species_counter = Counter()
    text_lower = text.lower()

    for match in BINOMIAL_RE.finditer(text):
        species_name = match.group(1).strip()
        if species_name in species_dict:
            species_counter[species_name] += 1

    for common_name, species_name in common_species_dict.items():
        if species_name not in species_dict:
            continue
        match_count = len(re.findall(r"(?<![a-z0-9-])" + re.escape(common_name) + r"(?![a-z0-9-])", text_lower))
        if match_count:
            species_counter[species_name] += match_count

    return species_counter


def extract_pesticide_mentions(text, pesticide_rows):
    text_lower = text.lower()
    pesticide_counter = Counter()

    for row in pesticide_rows:
        match_count = len(row["pattern"].findall(text_lower))
        if match_count:
            pesticide_counter[row["compound_name"]] = match_count

    return pesticide_counter


def extract_candidates(paper_id, section_root, species_tsv, common_species_tsv, pesticide_tsv):
    methods_md_files = list_methods_md_files(section_root, paper_id)
    pesticide_md_files = list_pesticide_md_files(section_root, paper_id)
    species_dict = load_species_dict(species_tsv)
    common_species_dict = load_common_species_dict(common_species_tsv)
    pesticide_rows = load_pesticide_dict(pesticide_tsv)

    species_set = set()
    pesticide_set = set()

    for md_file in methods_md_files:
        text = md_file.read_text(encoding="utf-8")
        species_set.update(extract_species_mentions(text, species_dict, common_species_dict).keys())

    for md_file in pesticide_md_files:
        text = md_file.read_text(encoding="utf-8")
        pesticide_set.update(extract_pesticide_mentions(text, pesticide_rows).keys())

    return {
        "paper_id": paper_id,
        "species": sorted(species_set),
        "pesticides": sorted(pesticide_set),
    }


def write_candidates(record, section_root):
    output_json = Path(section_root) / record["paper_id"] / "03_species_pesticide_candidates.json"
    output_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_json
