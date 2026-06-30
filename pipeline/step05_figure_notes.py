                      
                       

import base64
import json
import mimetypes
import os
import re
from pathlib import Path

import requests
from PIL import Image, ImageFile, UnidentifiedImageError
from PIL.Image import DecompressionBombError

from config.prompts import STEP05_FIGURE_PROMPT
from config.settings import (
    DASHSCOPE_API_URL,
    DASHSCOPE_ENABLE_THINKING,
    DASHSCOPE_TIMEOUT,
    DASHSCOPE_VLM_MODEL,
    MAX_IMAGE_PIXELS,
    MIN_IMAGE_EDGE,
)


ImageFile.LOAD_TRUNCATED_IMAGES = True


def load_json(input_json, default_record):
    input_path = Path(input_json)
    if not input_path.exists():
        return default_record
    return json.loads(input_path.read_text(encoding="utf-8"))


def build_existing_cases(monitoring_record):
    existing_cases = []
    for pair in monitoring_record.get("pairs", []):
        existing_cases.append(
            {
                "case_type": "monitoring",
                "species": pair.get("species", "").strip(),
                "pesticide": pair.get("pesticide", "").strip(),
                "strain": pair.get("strain", "").strip(),
                "location": pair.get("location", "").strip(),
                "year": pair.get("year", "").strip(),
                "resistance_status": pair.get("resistance_status", "").strip(),
                "cross": pair.get("cross", "").strip(),
                "study_context": pair.get("study_context", "").strip(),
                "resistance_factor": pair.get("resistance_factor", "").strip(),
                "LC50_LD50": pair.get("LC50_LD50", "").strip(),
                "mutation": pair.get("mutation", "").strip(),
            }
        )
    return existing_cases


def extract_image_paths(md_file, text):
    image_paths = []
    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        raw_path = match.group(1).strip()
        if raw_path.startswith("http://") or raw_path.startswith("https://"):
            continue
        if " " in raw_path:
            raw_path = raw_path.split(" ", 1)[0]
        image_path = (Path(md_file).parent / raw_path).resolve()
        if image_path.exists():
            image_paths.append(image_path)
    return image_paths


def list_result_figure_files(section_root, paper_id):
    figure_files = []
    figure_dir = Path(section_root) / paper_id / "06_figures"
    if not figure_dir.exists():
        return figure_files

    for md_file in sorted(figure_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        image_paths = extract_image_paths(md_file, text)
        if image_paths:
            figure_files.append((md_file, image_paths))

    return figure_files


def get_image_size(image_path):
    with Image.open(image_path) as image:
        width, height = image.size
    pixels = width * height
    if width <= MIN_IMAGE_EDGE or height <= MIN_IMAGE_EDGE:
        raise ValueError(f"bad_image_size:{width}x{height}")
    if pixels >= MAX_IMAGE_PIXELS:
        raise ValueError(f"bad_image_pixels:{pixels}")
    return width, height


def encode_image(image_path):
    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
    image_base64 = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{image_base64}"


def strip_code_fence(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def call_dashscope_with_images(prompt_text, image_paths, api_key=None, model=DASHSCOPE_VLM_MODEL):
    api_key = api_key or os.environ["DASHSCOPE_API_KEY"]
    content = [{"type": "text", "text": prompt_text}]
    for image_path in image_paths:
        content.append({"type": "image_url", "image_url": {"url": encode_image(image_path)}})

    response = requests.post(
        f"{DASHSCOPE_API_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "enable_thinking": DASHSCOPE_ENABLE_THINKING,
        },
        timeout=DASHSCOPE_TIMEOUT,
    )
    data = response.json()
    if response.status_code != 200 or "choices" not in data:
        raise RuntimeError(json.dumps(data, ensure_ascii=False))
    return data["choices"][0]["message"]["content"].strip()


def parse_figure_result(result):
    clean_result = strip_code_fence(result)
    if clean_result == "":
        return {"monitoring_cases": []}

    try:
        parsed = json.loads(clean_result)
    except json.JSONDecodeError:
        return {"monitoring_cases": []}

    if isinstance(parsed, list):
        return {"monitoring_cases": parsed}

    if isinstance(parsed, dict):
        if "monitoring_cases" in parsed:
            return {"monitoring_cases": parsed.get("monitoring_cases", [])}
        if "pairs" in parsed:
            return {"monitoring_cases": parsed["pairs"]}

    return {"monitoring_cases": []}


def build_figure_prompt(paper_id, figure_md, image_paths, figure_md_text, existing_cases):
    return STEP05_FIGURE_PROMPT.format(
        paper_id=paper_id,
        figure_md_path=str(figure_md),
        image_paths_json=json.dumps([str(path) for path in image_paths], ensure_ascii=False),
        existing_cases_json=json.dumps(existing_cases, ensure_ascii=False),
        figure_md_text=figure_md_text,
    )


def ask_figure_llm(paper_id, figure_md, image_paths, figure_md_text, existing_cases, api_key=None, model=DASHSCOPE_VLM_MODEL):
    prompt = build_figure_prompt(paper_id, figure_md, image_paths, figure_md_text, existing_cases)
    result = call_dashscope_with_images(prompt, image_paths, api_key=api_key, model=model)
    return parse_figure_result(result)


def merge_note(old_note, new_note):
    if not new_note:
        return old_note
    if not old_note:
        return new_note
    if new_note in old_note:
        return old_note
    return old_note + "；" + new_note


def get_monitoring_key(pair):
    return (
        pair.get("species", "").strip(),
        pair.get("pesticide", "").strip(),
        pair.get("strain", "").strip(),
    )


def merge_case_notes(case_note_map, llm_result, monitoring_keys):
    for note in llm_result.get("monitoring_cases", []):
        case_key = ("monitoring",) + get_monitoring_key(note)
        figure_note = note.get("figure_note", "").strip()
        if not figure_note or case_key not in monitoring_keys:
            continue
        case_note_map[case_key] = merge_note(case_note_map.get(case_key, ""), figure_note)


def export_cases_with_figure_notes(monitoring_record, case_note_map):
    monitoring_cases = []
    for pair in monitoring_record.get("pairs", []):
        output_pair = dict(pair)
        output_pair["figure_note"] = case_note_map.get(("monitoring",) + get_monitoring_key(pair), "")
        monitoring_cases.append(output_pair)
    return monitoring_cases


def filter_valid_image_paths(paper_id, figure_index, figure_count, figure_md, image_paths):
    valid_image_paths = []
    image_infos = []
    skipped_images = []

    for image_path in image_paths:
        try:
            width, height = get_image_size(image_path)
        except (ValueError, UnidentifiedImageError, OSError, DecompressionBombError) as error:
            skipped_images.append(
                f"{paper_id}\tfigure\t{figure_index}/{figure_count}\t{figure_md.name}\tskip_image\t{image_path.name}\t{error}"
            )
            continue
        valid_image_paths.append(image_path)
        image_infos.append(f"{width}x{height}:{image_path.stat().st_size}")

    return valid_image_paths, image_infos, skipped_images


def extract_figure_notes(paper_id, section_root, api_key=None, model=DASHSCOPE_VLM_MODEL):
    paper_dir = Path(section_root) / paper_id
    monitoring_json = paper_dir / "05_1_species_pesticide_strain_monitoring_cases.json"
    monitoring_record = load_json(monitoring_json, {"paper_id": paper_id, "pairs": []})
    existing_cases = build_existing_cases(monitoring_record)
    monitoring_keys = {("monitoring",) + get_monitoring_key(pair) for pair in monitoring_record.get("pairs", [])}
    figure_files = list_result_figure_files(section_root, paper_id)
    case_note_map = {}
    run_messages = []

    if not figure_files or not existing_cases:
        return {
            "paper_id": paper_id,
            "monitoring_cases": export_cases_with_figure_notes(monitoring_record, case_note_map),
            "step_summary": {
                "figure_files": len(figure_files),
                "monitoring_cases": len(monitoring_record.get("pairs", [])),
                "figure_note_cases": 0,
            },
            "messages": run_messages,
        }

    for index, (figure_md, image_paths) in enumerate(figure_files, 1):
        valid_image_paths, image_infos, skipped_images = filter_valid_image_paths(
            paper_id,
            index,
            len(figure_files),
            figure_md,
            image_paths,
        )
        run_messages.extend(skipped_images)
        if not valid_image_paths:
            run_messages.append(f"{paper_id}\tfigure\t{index}/{len(figure_files)}\t{figure_md.name}\tskip_figure\tno_valid_image")
            continue

        run_messages.append(f"{paper_id}\tfigure\t{index}/{len(figure_files)}\t{figure_md.name}\timages:{len(valid_image_paths)}\t{','.join(image_infos)}")
        figure_md_text = figure_md.read_text(encoding="utf-8")
        try:
            llm_result = ask_figure_llm(
                paper_id,
                figure_md,
                valid_image_paths,
                figure_md_text,
                existing_cases,
                api_key=api_key,
                model=model,
            )
        except Exception as error:
            run_messages.append(f"{paper_id}\tfigure\t{index}/{len(figure_files)}\t{figure_md.name}\tskip_figure\t{error}")
            continue
        merge_case_notes(case_note_map, llm_result, monitoring_keys)

    monitoring_cases = export_cases_with_figure_notes(monitoring_record, case_note_map)
    return {
        "paper_id": paper_id,
        "monitoring_cases": monitoring_cases,
        "step_summary": {
            "figure_files": len(figure_files),
            "monitoring_cases": len(monitoring_cases),
            "figure_note_cases": sum(1 for case in monitoring_cases if case.get("figure_note")),
        },
        "messages": run_messages,
    }


def write_figure_notes(record, section_root):
    output_json = Path(section_root) / record["paper_id"] / "06_1_monitoring_cases_with_figure_notes.json"
    output_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_json
