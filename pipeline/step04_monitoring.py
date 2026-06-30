                      
                       

import json
import os
from pathlib import Path

import requests

from config.prompts import (
    STEP04_EVIDENCE_PROMPT,
    STEP04_LOCATION_PROMPT,
    STEP04_PAIR_PROMPT,
    STEP04_STATUS_CONTEXT_PROMPT,
    STEP04_STRAIN_PROMPT,
)
from config.settings import DASHSCOPE_API_URL, DASHSCOPE_ENABLE_THINKING, DASHSCOPE_MODEL, DASHSCOPE_TIMEOUT


def load_candidates(input_json):
    return json.loads(Path(input_json).read_text(encoding="utf-8"))


def list_result_md_files(section_root, paper_id):
    paper_dir = Path(section_root) / paper_id
    md_files = []
    md_files.extend(sorted((paper_dir / "02_results").glob("*.md")))
    md_files.extend(sorted((paper_dir / "04_results_and_discussion").glob("*.md")))
    return md_files


def list_methods_md_files(section_root, paper_id):
    return sorted((Path(section_root) / paper_id / "01_materials_and_methods").glob("*.md"))


def short_section_path(section_root, paper_id, md_file):
    return str(Path(md_file).relative_to(Path(section_root) / paper_id))


def build_paper_text(section_root, paper_id, md_files):
    chunks = []
    for md_file in md_files:
        section_path = short_section_path(section_root, paper_id, md_file)
        section_text = md_file.read_text(encoding="utf-8")
        chunks.append(f"## {section_path}\n\n{section_text}")
    return "\n\n".join(chunks)


def strip_code_fence(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def call_dashscope(prompt_text, api_key=None, model=DASHSCOPE_MODEL):
    api_key = api_key or os.environ["DASHSCOPE_API_KEY"]
    response = requests.post(
        f"{DASHSCOPE_API_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0,
            "enable_thinking": DASHSCOPE_ENABLE_THINKING,
        },
        timeout=DASHSCOPE_TIMEOUT,
    )
    data = response.json()
    if response.status_code != 200 or "choices" not in data:
        raise RuntimeError(json.dumps(data, ensure_ascii=False))
    return data["choices"][0]["message"]["content"].strip()


def parse_pairs_result(result):
    clean_result = strip_code_fence(result)
    if clean_result == "":
        return {"pairs": []}
    try:
        parsed = json.loads(clean_result)
    except json.JSONDecodeError:
        return {"pairs": []}
    if isinstance(parsed, list):
        return {"pairs": parsed}
    if isinstance(parsed, dict):
        if "pairs" in parsed:
            return parsed
        if "monitoring_pairs" in parsed:
            return {"pairs": parsed["monitoring_pairs"]}
    return {"pairs": []}


def parse_strains_result(result):
    clean_result = strip_code_fence(result)
    if clean_result == "":
        return {"strains": []}
    try:
        parsed = json.loads(clean_result)
    except json.JSONDecodeError:
        return {"strains": []}
    if isinstance(parsed, list):
        return {"strains": parsed}
    if isinstance(parsed, dict):
        if "strains" in parsed:
            return parsed
        if "pairs" in parsed:
            return {"strains": parsed["pairs"]}
    return {"strains": []}


def ask_pair_llm(record, section_path, section_text, existing_pairs, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP04_PAIR_PROMPT.format(
        paper_id=record["paper_id"],
        section_path=str(section_path),
        species_json=json.dumps(record["species"], ensure_ascii=False),
        pesticides_json=json.dumps(record["pesticides"], ensure_ascii=False),
        existing_pairs_json=json.dumps(existing_pairs, ensure_ascii=False),
        section_text=section_text,
    )
    return parse_pairs_result(call_dashscope(prompt, api_key=api_key, model=model))


def ask_strain_llm(record, section_path, section_text, confirmed_pairs, existing_strains, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP04_STRAIN_PROMPT.format(
        paper_id=record["paper_id"],
        section_path=str(section_path),
        confirmed_pairs_json=json.dumps(confirmed_pairs, ensure_ascii=False),
        existing_strains_json=json.dumps(existing_strains, ensure_ascii=False),
        section_text=section_text,
    )
    return parse_strains_result(call_dashscope(prompt, api_key=api_key, model=model))


def ask_location_llm(record, section_path, section_text, confirmed_frames, existing_cases, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP04_LOCATION_PROMPT.format(
        paper_id=record["paper_id"],
        section_path=str(section_path),
        confirmed_frames_json=json.dumps(confirmed_frames, ensure_ascii=False),
        existing_cases_json=json.dumps(existing_cases, ensure_ascii=False),
        section_text=section_text,
    )
    return parse_pairs_result(call_dashscope(prompt, api_key=api_key, model=model))


def ask_evidence_llm(record, section_path, section_text, confirmed_cases, existing_evidence, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP04_EVIDENCE_PROMPT.format(
        confirmed_cases_json=json.dumps(confirmed_cases, ensure_ascii=False),
        existing_evidence_json=json.dumps(existing_evidence, ensure_ascii=False),
        section_path=str(section_path),
        section_text=section_text,
    )
    return parse_pairs_result(call_dashscope(prompt, api_key=api_key, model=model))


def ask_status_context_llm(record, paper_text, confirmed_cases, existing_status_context, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP04_STATUS_CONTEXT_PROMPT.format(
        paper_id=record["paper_id"],
        confirmed_cases_json=json.dumps(confirmed_cases, ensure_ascii=False, indent=2),
        existing_status_context_json=json.dumps(existing_status_context, ensure_ascii=False),
        paper_text=paper_text,
    )
    return parse_pairs_result(call_dashscope(prompt, api_key=api_key, model=model))


def merge_species_pesticide_pairs(pair_set, new_pairs):
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        if species and pesticide:
            pair_set.add((species, pesticide))


def export_species_pesticide_pairs(pair_set):
    return [{"species": species, "pesticide": pesticide} for species, pesticide in sorted(pair_set)]


def merge_species_strains(strain_set, new_strains):
    for item in new_strains:
        species = item.get("species", "").strip()
        pesticide = item.get("pesticide", "").strip()
        strain = item.get("strain", "").strip()
        if species and pesticide and strain:
            strain_set.add((species, pesticide, strain))


def export_species_strains(strain_set):
    return [
        {"species": species, "pesticide": pesticide, "strain": strain}
        for species, pesticide, strain in sorted(strain_set)
    ]


def merge_case_frames(frame_set, new_pairs):
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        strain = pair.get("strain", "").strip()
        if species and pesticide and strain:
            frame_set.add((species, pesticide, strain))


def export_case_frames(frame_set):
    return [
        {"species": species, "pesticide": pesticide, "strain": strain}
        for species, pesticide, strain in sorted(frame_set)
    ]


def merge_location_cases(case_map, new_pairs):
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        strain = pair.get("strain", "").strip()
        location = pair.get("location", "").strip()
        year = pair.get("year", "").strip()
        if not species or not pesticide or not strain:
            continue
        old_location, old_year = case_map.get((species, pesticide, strain), ("", ""))
        case_map[(species, pesticide, strain)] = (old_location or location, old_year or year)


def export_location_cases_from_frames(frame_set, case_map):
    output_pairs = []
    for species, pesticide, strain in sorted(frame_set):
        location, year = case_map.get((species, pesticide, strain), ("", ""))
        output_pairs.append(
            {
                "species": species,
                "pesticide": pesticide,
                "strain": strain,
                "location": location,
                "year": year,
            }
        )
    return output_pairs


def export_location_cases(case_map):
    output_pairs = []
    for (species, pesticide, strain), (location, year) in sorted(case_map.items()):
        output_pairs.append(
            {
                "species": species,
                "pesticide": pesticide,
                "strain": strain,
                "location": location,
                "year": year,
            }
        )
    return output_pairs


def merge_value(old_value, new_value):
    if not new_value:
        return old_value
    if not old_value:
        return new_value
    if new_value in old_value:
        return old_value
    if old_value in new_value:
        return new_value
    return old_value + "; " + new_value


def merge_evidence_cases(evidence_map, new_pairs):
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        strain = pair.get("strain", "").strip()
        location = pair.get("location", "").strip()
        year = pair.get("year", "").strip()
        resistance_factor = pair.get("resistance_factor", "").strip()
        LC50_LD50 = pair.get("LC50_LD50", "").strip()
        mutation = pair.get("mutation", "").strip()
        if not species or not pesticide or not strain:
            continue
        if not (resistance_factor or LC50_LD50 or mutation):
            continue
        case_key = (species, pesticide, strain, location, year)
        old_case = evidence_map.get(case_key, {"resistance_factor": "", "LC50_LD50": "", "mutation": ""})
        old_case["resistance_factor"] = merge_value(old_case["resistance_factor"], resistance_factor)
        old_case["LC50_LD50"] = merge_value(old_case["LC50_LD50"], LC50_LD50)
        old_case["mutation"] = merge_value(old_case["mutation"], mutation)
        evidence_map[case_key] = old_case


def export_evidence_cases(evidence_map):
    output_pairs = []
    for (species, pesticide, strain, location, year), evidence in sorted(evidence_map.items()):
        output_pairs.append(
            {
                "species": species,
                "pesticide": pesticide,
                "strain": strain,
                "location": location,
                "year": year,
                "resistance_factor": evidence["resistance_factor"],
                "LC50_LD50": evidence["LC50_LD50"],
                "mutation": evidence["mutation"],
            }
        )
    return output_pairs


def normalize_study_context(value):
    value = str(value or "").strip()
    if value in {"field_monitoring", "laboratory_research", "unclear"}:
        return value
    return "unclear"


def merge_status_context_cases(status_context_map, new_pairs):
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        strain = pair.get("strain", "").strip()
        location = pair.get("location", "").strip()
        year = pair.get("year", "").strip()
        resistance_status = pair.get("resistance_status", "").strip()
        cross = pair.get("cross", "").strip()
        study_context = normalize_study_context(pair.get("study_context", ""))
        if resistance_status != "resistant":
            resistance_status = ""
        if cross != "cross":
            cross = ""
        if not species or not pesticide or not strain:
            continue
        case_key = (species, pesticide, strain, location, year)
        old_case = status_context_map.get(case_key, {"resistance_status": "", "cross": "", "study_context": ""})
        old_case["resistance_status"] = old_case["resistance_status"] or resistance_status
        old_case["cross"] = old_case["cross"] or cross
        old_case["study_context"] = old_case["study_context"] or study_context
        status_context_map[case_key] = old_case


def export_status_context_cases(status_context_map):
    output_pairs = []
    for (species, pesticide, strain, location, year), status_context in sorted(status_context_map.items()):
        output_pairs.append(
            {
                "species": species,
                "pesticide": pesticide,
                "strain": strain,
                "location": location,
                "year": year,
                "resistance_status": status_context["resistance_status"],
                "cross": status_context["cross"],
                "study_context": normalize_study_context(status_context["study_context"]),
            }
        )
    return output_pairs


def export_monitoring_cases(location_cases, evidence_map, status_context_map):
    output_pairs = []
    for case in location_cases:
        species = case["species"]
        pesticide = case["pesticide"]
        strain = case["strain"]
        location = case["location"]
        year = case["year"]
        key = (species, pesticide, strain, location, year)
        evidence = evidence_map.get(key, {"resistance_factor": "", "LC50_LD50": "", "mutation": ""})
        status_context = status_context_map.get(key, {"resistance_status": "", "cross": "", "study_context": "unclear"})
        output_pairs.append(
            {
                "species": species,
                "pesticide": pesticide,
                "strain": strain,
                "location": location,
                "year": year,
                "resistance_status": status_context["resistance_status"],
                "cross": status_context["cross"],
                "study_context": normalize_study_context(status_context["study_context"]),
                "resistance_factor": evidence["resistance_factor"],
                "LC50_LD50": evidence["LC50_LD50"],
                "mutation": evidence["mutation"],
            }
        )
    return output_pairs


def build_step_summary(confirmed_pairs, confirmed_strains, confirmed_frames, location_cases, evidence_cases, status_context_cases):
    return {
        "species_pesticide_pairs": len(confirmed_pairs),
        "species_strains": len(confirmed_strains),
        "case_frames": len(confirmed_frames),
        "location_cases": len(location_cases),
        "evidence_cases": len(evidence_cases),
        "status_context_cases": len(status_context_cases),
    }


def extract_monitoring_cases(paper_id, section_root, api_key=None, model=DASHSCOPE_MODEL):
    input_json = Path(section_root) / paper_id / "03_species_pesticide_candidates.json"
    record = load_candidates(input_json)
    result_md_files = list_result_md_files(section_root, record["paper_id"])
    methods_md_files = list_methods_md_files(section_root, record["paper_id"])
    monitoring_md_files = methods_md_files + result_md_files

    pair_set = set()
    strain_set = set()
    frame_set = set()
    location_map = {}
    evidence_map = {}
    status_context_map = {}

    if not record["species"] or not record["pesticides"] or not result_md_files:
        return {"paper_id": record["paper_id"], "pairs": [], "step_summary": build_step_summary([], [], [], [], [], [])}

    for result_md in result_md_files:
        section_text = result_md.read_text(encoding="utf-8")
        existing_pairs = export_species_pesticide_pairs(pair_set)
        llm_result = ask_pair_llm(record, result_md, section_text, existing_pairs, api_key=api_key, model=model)
        merge_species_pesticide_pairs(pair_set, llm_result.get("pairs", []))
    confirmed_pairs = export_species_pesticide_pairs(pair_set)

    for md_file in monitoring_md_files:
        section_text = md_file.read_text(encoding="utf-8")
        existing_strains = export_species_strains(strain_set)
        llm_result = ask_strain_llm(record, md_file, section_text, confirmed_pairs, existing_strains, api_key=api_key, model=model)
        merge_species_strains(strain_set, llm_result.get("strains", []))
    confirmed_strains = export_species_strains(strain_set)

    for item in confirmed_strains:
        merge_case_frames(frame_set, [item])
    confirmed_frames = export_case_frames(frame_set)

    for md_file in monitoring_md_files:
        section_text = md_file.read_text(encoding="utf-8")
        existing_cases = export_location_cases(location_map)
        llm_result = ask_location_llm(record, md_file, section_text, confirmed_frames, existing_cases, api_key=api_key, model=model)
        merge_location_cases(location_map, llm_result.get("pairs", []))
    location_cases = export_location_cases_from_frames(frame_set, location_map)

    for result_md in result_md_files:
        section_text = result_md.read_text(encoding="utf-8")
        existing_evidence = export_evidence_cases(evidence_map)
        llm_result = ask_evidence_llm(record, result_md, section_text, location_cases, existing_evidence, api_key=api_key, model=model)
        merge_evidence_cases(evidence_map, llm_result.get("pairs", []))
    evidence_cases = export_evidence_cases(evidence_map)

    paper_text = build_paper_text(section_root, record["paper_id"], monitoring_md_files)
    existing_status_context = export_status_context_cases(status_context_map)
    llm_result = ask_status_context_llm(record, paper_text, location_cases, existing_status_context, api_key=api_key, model=model)
    merge_status_context_cases(status_context_map, llm_result.get("pairs", []))
    status_context_cases = export_status_context_cases(status_context_map)

    return {
        "paper_id": record["paper_id"],
        "pairs": export_monitoring_cases(location_cases, evidence_map, status_context_map),
        "step_summary": build_step_summary(
            confirmed_pairs,
            confirmed_strains,
            confirmed_frames,
            location_cases,
            evidence_cases,
            status_context_cases,
        ),
        "intermediate": {
            "species_pesticide_pairs": confirmed_pairs,
            "species_strains": confirmed_strains,
            "case_frames": confirmed_frames,
        },
    }


def write_monitoring_cases(record, section_root):
    output_json = Path(section_root) / record["paper_id"] / "05_1_species_pesticide_strain_monitoring_cases.json"
    output_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_json
