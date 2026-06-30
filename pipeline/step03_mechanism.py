                      
                       

import json
import os
from pathlib import Path

import requests

from config.prompts import STEP03_GENE_PROMPT, STEP03_METHOD_PROMPT, STEP03_PAIR_PROMPT
from config.settings import DASHSCOPE_API_URL, DASHSCOPE_ENABLE_THINKING, DASHSCOPE_MODEL, DASHSCOPE_TIMEOUT


METHOD_OPTIONS = [
    "omics upregulation",
    "resistant overexpression",
    "in vitro validation",
    "Drosophila validation",
    "RNAi validation",
    "CRISPR validation",
]


METHOD_OPTION_DEFINITIONS = {
    "omics upregulation": "组学证据显示具体单基因上调",
    "resistant overexpression": "抗性种群中过表达",
    "in vitro validation": "体外表达系统验证",
    "Drosophila validation": "果蝇异源表达系统验证",
    "RNAi validation": "RNAi 策略验证",
    "CRISPR validation": "CRISPR 策略验证",
}


def load_candidates(input_json):
    return json.loads(Path(input_json).read_text(encoding="utf-8"))


def list_result_md_files(section_root, paper_id):
    paper_dir = Path(section_root) / paper_id
    result_files = []
    result_files.extend(sorted((paper_dir / "02_results").glob("*.md")))
    result_files.extend(sorted((paper_dir / "04_results_and_discussion").glob("*.md")))
    return result_files


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
        if "resistance_pairs" in parsed:
            return {"pairs": parsed["resistance_pairs"]}

    return {"pairs": []}


def ask_pair_llm(record, section_path, section_text, existing_pairs, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP03_PAIR_PROMPT.format(
        paper_id=record["paper_id"],
        section_path=str(section_path),
        species_json=json.dumps(record["species"], ensure_ascii=False),
        pesticides_json=json.dumps(record["pesticides"], ensure_ascii=False),
        existing_pairs_json=json.dumps(existing_pairs, ensure_ascii=False),
        section_text=section_text,
    )
    return parse_pairs_result(call_dashscope(prompt, api_key=api_key, model=model))


def ask_gene_llm(record, section_path, section_text, confirmed_pairs, existing_cases, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP03_GENE_PROMPT.format(
        paper_id=record["paper_id"],
        section_path=str(section_path),
        confirmed_pairs_json=json.dumps(confirmed_pairs, ensure_ascii=False),
        existing_cases_json=json.dumps(existing_cases, ensure_ascii=False),
        section_text=section_text,
    )
    return parse_pairs_result(call_dashscope(prompt, api_key=api_key, model=model))


def ask_method_llm(record, section_path, section_text, confirmed_cases, existing_method_cases, api_key=None, model=DASHSCOPE_MODEL):
    prompt = STEP03_METHOD_PROMPT.format(
        paper_id=record["paper_id"],
        section_path=str(section_path),
        method_options_json=json.dumps(METHOD_OPTIONS, ensure_ascii=False),
        method_option_definitions_json=json.dumps(METHOD_OPTION_DEFINITIONS, ensure_ascii=False),
        confirmed_cases_json=json.dumps(confirmed_cases, ensure_ascii=False),
        existing_method_cases_json=json.dumps(existing_method_cases, ensure_ascii=False),
        section_text=section_text,
    )
    return parse_pairs_result(call_dashscope(prompt, api_key=api_key, model=model))


def merge_pair_set(pair_set, new_pairs):
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        if species and pesticide:
            pair_set.add((species, pesticide))


def export_pair_list(pair_set):
    return [{"species": species, "pesticide": pesticide} for species, pesticide in sorted(pair_set)]


def merge_gene_cases(case_map, new_pairs):
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        gene = pair.get("gene", "").strip()
        if not species or not pesticide or not gene:
            continue
        case_map.setdefault((species, pesticide), set()).add(gene)


def export_gene_cases(case_map):
    output_pairs = []
    for (species, pesticide), genes in sorted(case_map.items()):
        for gene in sorted(genes):
            output_pairs.append({"species": species, "pesticide": pesticide, "gene": gene})
    return output_pairs


def flatten_gene_cases(case_map):
    return export_gene_cases(case_map)


def merge_method_cases(method_map, new_pairs):
    method_options = set(METHOD_OPTIONS)
    for pair in new_pairs:
        species = pair.get("species", "").strip()
        pesticide = pair.get("pesticide", "").strip()
        gene = pair.get("gene", "").strip()
        methods = [method.strip() for method in pair.get("methods", []) if method.strip() in method_options]
        if not species or not pesticide or not gene or not methods:
            continue
        method_map.setdefault((species, pesticide, gene), set()).update(methods)


def export_method_cases(method_map):
    output_pairs = []
    for (species, pesticide, gene), methods in sorted(method_map.items()):
        output_pairs.append(
            {
                "species": species,
                "pesticide": pesticide,
                "gene": gene,
                "methods": sorted(methods),
            }
        )
    return output_pairs


def export_gene_cases_with_methods(case_map, method_map):
    output_pairs = []
    for (species, pesticide), genes in sorted(case_map.items()):
        for gene in sorted(genes):
            methods = method_map.get((species, pesticide, gene), set())
            output_pairs.append(
                {
                    "species": species,
                    "pesticide": pesticide,
                    "gene": gene,
                    "methods": sorted(methods),
                }
            )
    return output_pairs


def extract_mechanism_cases(paper_id, section_root, api_key=None, model=DASHSCOPE_MODEL):
    input_json = Path(section_root) / paper_id / "03_species_pesticide_candidates.json"
    record = load_candidates(input_json)
    result_md_files = list_result_md_files(section_root, record["paper_id"])
    pair_set = set()
    case_map = {}
    method_map = {}

    if not record["species"] or not record["pesticides"] or not result_md_files:
        return {"paper_id": record["paper_id"], "pairs": []}

    for result_md in result_md_files:
        section_text = result_md.read_text(encoding="utf-8")
        existing_pairs = export_pair_list(pair_set)
        llm_result = ask_pair_llm(record, result_md, section_text, existing_pairs, api_key=api_key, model=model)
        merge_pair_set(pair_set, llm_result.get("pairs", []))

    confirmed_pairs = export_pair_list(pair_set)
    if not confirmed_pairs:
        return {"paper_id": record["paper_id"], "pairs": []}

    for result_md in result_md_files:
        section_text = result_md.read_text(encoding="utf-8")
        existing_cases = export_gene_cases(case_map)
        llm_result = ask_gene_llm(record, result_md, section_text, confirmed_pairs, existing_cases, api_key=api_key, model=model)
        merge_gene_cases(case_map, llm_result.get("pairs", []))

    confirmed_cases = flatten_gene_cases(case_map)
    for result_md in result_md_files:
        section_text = result_md.read_text(encoding="utf-8")
        existing_method_cases = export_method_cases(method_map)
        llm_result = ask_method_llm(record, result_md, section_text, confirmed_cases, existing_method_cases, api_key=api_key, model=model)
        merge_method_cases(method_map, llm_result.get("pairs", []))

    return {
        "paper_id": record["paper_id"],
        "pairs": export_gene_cases_with_methods(case_map, method_map),
    }


def write_mechanism_cases(record, section_root):
    output_json = Path(section_root) / record["paper_id"] / "04_species_pesticide_gene_pairs.json"
    output_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_json
