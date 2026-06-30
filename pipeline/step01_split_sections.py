                      
                       

import csv
import re
import shutil
import unicodedata
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
TAG_RE = re.compile(r"<[^>]+>")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_IMAGE_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
HTML_ALT_RE = re.compile(r"\balt=[\"']([^\"']*)[\"']", re.IGNORECASE)
FIGURE_CAPTION_RE = re.compile(r"^(?:>\s*)?(?:Figure|Fig\.?)\s*[A-Za-z]*\d+", re.IGNORECASE)
BINOMIAL_RE = re.compile(r"\b([A-Z][A-Za-z-]+ [a-z][a-z-]+)\b")
ABBREVIATION_RE = re.compile(r"\b([A-Z][a-z]{0,20})\.\s+([a-z][a-z-]+)\b")


FORCED_ABBREVIATION_MAP = {
    "An. stephensi": "Anopheles stephensi",
    "Cx. quinquefasciatus": "Culex quinquefasciatus",
    "Cx. tarsalis": "Culex tarsalis",
}


EXCLUDED_MAJOR_HEADINGS = {
    "abstract",
    "resume",
    "resumen",
    "introduction",
    "introduccion",
    "acknowledgments",
    "acknowledgements",
    "remerciements",
    "agradecimientos",
    "reference",
    "references",
    "referencias",
    "literature cited",
    "supplemental material",
    "supplementary material",
    "supplementary information",
    "supporting information",
}


STRICT_MAJOR_HEADING_KEYS = {
    "abstract",
    "resume",
    "resumen",
    "introduction",
    "introduccion",
    "materials and methods",
    "material and methods",
    "materials methods",
    "methods",
    "method",
    "materiel et methodes",
    "materiel methodes",
    "metodologia",
    "experimental procedure",
    "experimental procedures",
    "experimental section",
    "experimental design",
    "experimental design materials and methods",
    "protocol",
    "results",
    "result",
    "resultats",
    "resultados",
    "representative results",
    "results and discussion",
    "results discussion",
    "discussion",
    "discusion",
    "discussion and conclusion",
    "conclusion",
    "conclusions",
    "conclusiones",
    "summary and conclusion",
    "summary and conclusions",
    "acknowledgments",
    "acknowledgements",
    "remerciements",
    "agradecimientos",
    "references",
    "referencias",
    "literature cited",
}


STICKY_MAJOR_PREFIXES = (
    "materials and methods ",
    "material and methods ",
    "materials methods ",
    "materiel et methodes ",
    "materiel methodes ",
    "experimental design materials and methods ",
    "results ",
    "resultats ",
    "resultados ",
    "results and discussion ",
)


def clean_heading_text(text):
    text = TAG_RE.sub("", text)
    text = text.replace("*", "")
    return " ".join(text.split()).strip()


def strip_accents(text):
    normalized_text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized_text if not unicodedata.combining(char))


def slugify(text):
    text = clean_heading_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "section"


def normalize_major_heading(text):
    return clean_heading_text(text).lower().rstrip(".")


def normalize_heading_key(text):
    heading_key = strip_accents(normalize_major_heading(text))
    heading_key = re.sub(r"[^a-z0-9]+", " ", heading_key).strip()
    heading_key = re.sub(r"^(?:\d+\s+)+", "", heading_key).strip()
    return heading_key


def get_heading_number_depth(text):
    heading_text = clean_heading_text(text)
    match = re.match(r"^\s*(\d+(?:\.\d+)*)(?:\.|\s)", heading_text)
    if not match:
        return 0
    return len(match.group(1).split("."))


def has_prefix_word(words, prefix):
    return any(word.startswith(prefix) for word in words)


def is_strict_major_heading_text(text):
    heading_key = normalize_heading_key(text)
    return heading_key in STRICT_MAJOR_HEADING_KEYS or heading_key.startswith(STICKY_MAJOR_PREFIXES)


def get_major_section_info(text):
    normalized_text = normalize_major_heading(text)
    heading_key = normalize_heading_key(text)
    words = heading_key.split()

    if (
        normalized_text in EXCLUDED_MAJOR_HEADINGS
        or heading_key in EXCLUDED_MAJOR_HEADINGS
        or "abstract" in words
        or "introduction" in words
        or "introduccion" in words
        or "acknowledgment" in words
        or "acknowledgments" in words
        or "acknowledgement" in words
        or "acknowledgements" in words
        or "remerciements" in words
        or "agradecimientos" in words
        or "references" in words
        or "referencias" in words
        or "supplementary" in words
        or "supporting" in words
    ):
        return {"excluded": True, "dir_name": "", "section_key": ""}

    if has_prefix_word(words, "result") and has_prefix_word(words, "discussion"):
        return {"excluded": False, "dir_name": "04_results_and_discussion", "section_key": "results_and_discussion"}

    if (
        has_prefix_word(words, "method")
        or has_prefix_word(words, "material")
        or "materiel" in words
        or "methode" in words
        or "methodes" in words
        or "metodologia" in words
        or heading_key in {
            "experimental procedure",
            "experimental procedures",
            "experimental section",
            "experimental design",
            "protocol",
        }
    ):
        return {"excluded": False, "dir_name": "01_materials_and_methods", "section_key": "materials_and_methods"}

    if (
        has_prefix_word(words, "result")
        or "resultat" in words
        or "resultats" in words
        or "resultado" in words
        or "resultados" in words
        or "findings" in words
    ):
        return {"excluded": False, "dir_name": "02_results", "section_key": "results"}

    if has_prefix_word(words, "discussion") or "discusion" in words:
        return {"excluded": False, "dir_name": "03_discussion", "section_key": "discussion"}

    if has_prefix_word(words, "conclusion") or "conclusiones" in words or heading_key in {
        "summary and conclusion",
        "summary and conclusions",
    }:
        return {"excluded": False, "dir_name": "05_conclusion", "section_key": "conclusion"}

    return {"excluded": False, "dir_name": "99_other_kept", "section_key": "other_kept"}


def is_major_heading(level, heading_text, major_section_info):
    if level == 2:
        return True
    if level != 3:
        return False
    if major_section_info["section_key"] == "other_kept" and not major_section_info["excluded"]:
        return False
    if get_heading_number_depth(heading_text) > 1:
        return False
    return is_strict_major_heading_text(heading_text)


def is_inherited_subsection(current_major, heading_text, major_section_info):
    if current_major is None or current_major["excluded"]:
        return False
    if major_section_info["excluded"] or is_strict_major_heading_text(heading_text):
        return False
    return current_major["section_key"] in {"materials_and_methods", "results", "results_and_discussion"}


def load_species_dictionary(species_dictionary_path):
    species_name_set = set()
    with open(species_dictionary_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            species_name_set.add(row["name_txt"].strip())
    return species_name_set


def load_species_common_name_registry(registry_path, species_name_set):
    common_name_map = {}
    if not Path(registry_path).exists():
        return common_name_map

    with open(registry_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("confidence", "").strip() != "strict":
                continue
            common_name = row.get("common_name", "").strip()
            species_name = row.get("species_name", "").strip()
            if common_name and species_name in species_name_set:
                common_name_map[common_name] = species_name
    return common_name_map


def extract_paper_meta(lines, md_path):
    title = ""
    doi = ""
    journal = ""

    for line in lines:
        if line.startswith("# "):
            title = clean_heading_text(line[2:])
            break

    for line in lines:
        if line.startswith("- DOI:"):
            doi = line.split(":", 1)[1].strip()
        if line.startswith("- Journal:"):
            journal = line.split(":", 1)[1].strip()

    return {
        "paper_id": md_path.stem,
        "paper_title": title,
        "doi": doi,
        "journal": journal,
        "source_md": str(md_path),
    }


def normalize_latin_abbreviations(text, species_name_set):
    abbreviation_map = {}
    genus_species_map = {}

    for full_name in species_name_set:
        parts = full_name.split()
        if len(parts) != 2:
            continue
        genus, species = parts
        genus_species_map.setdefault((genus[0], species), set()).add(full_name)

    for match in BINOMIAL_RE.finditer(text):
        full_name = match.group(1).strip()
        if full_name not in species_name_set:
            continue
        genus, species = full_name.split()
        for prefix_len in range(1, len(genus)):
            abbreviation = f"{genus[:prefix_len]}. {species}"
            abbreviation_map.setdefault(abbreviation, set()).add(full_name)

    resolved_map = {}
    for abbreviation, candidates in abbreviation_map.items():
        if len(candidates) == 1:
            resolved_map[abbreviation] = next(iter(candidates))

    for abbreviation, full_name in FORCED_ABBREVIATION_MAP.items():
        if full_name in species_name_set:
            resolved_map[abbreviation] = full_name

    for match in ABBREVIATION_RE.finditer(text):
        abbreviation = f"{match.group(1)}. {match.group(2)}"
        if abbreviation in resolved_map:
            continue
        candidates = genus_species_map.get((match.group(1)[0], match.group(2)), set())
        if len(candidates) == 1:
            resolved_map[abbreviation] = next(iter(candidates))

    replacement_count = 0

    def replace_match(match):
        nonlocal replacement_count
        abbreviation = f"{match.group(1)}. {match.group(2)}"
        full_name = resolved_map.get(abbreviation)
        if not full_name:
            return match.group(0)
        replacement_count += 1
        return full_name

    normalized_text = ABBREVIATION_RE.sub(replace_match, text)
    return normalized_text, resolved_map, replacement_count


def normalize_common_species_names(text, common_name_map):
    if not common_name_map:
        return text, 0

    replacement_count = 0
    sorted_items = sorted(common_name_map.items(), key=lambda item: len(item[0]), reverse=True)
    species_lookup = {" ".join(common_name.lower().split()): species_name for common_name, species_name in common_name_map.items()}
    common_name_patterns = [re.escape(common_name).replace(r"\ ", r"\s+") for common_name, _ in sorted_items]
    pattern = re.compile(rf"(?<![A-Za-z0-9])({'|'.join(common_name_patterns)})(?![A-Za-z0-9])", re.IGNORECASE)

    def replace_match(match):
        nonlocal replacement_count
        matched_name = match.group(1)
        lookup_key = " ".join(matched_name.lower().split())
        species_name = species_lookup.get(lookup_key)
        if not species_name:
            return matched_name
        after_text = text[match.end(): match.end() + len(species_name) + 4]
        if species_name in after_text:
            return matched_name
        replacement_count += 1
        return f"{matched_name} ({species_name})"

    normalized_text = pattern.sub(replace_match, text)
    return normalized_text, replacement_count


def clean_caption_text(line):
    text = clean_heading_text(line)
    text = text.lstrip("> ").strip()
    return text


def is_figure_caption_line(line):
    return bool(FIGURE_CAPTION_RE.match(clean_caption_text(line)))


def extract_image_info(line):
    markdown_match = IMAGE_RE.search(line)
    if markdown_match:
        return {"alt_text": markdown_match.group(1).strip() or "Image", "raw_path": markdown_match.group(2).strip()}

    html_match = HTML_IMAGE_RE.search(line)
    if html_match:
        alt_match = HTML_ALT_RE.search(line)
        return {
            "alt_text": alt_match.group(1).strip() if alt_match else "Image",
            "raw_path": html_match.group(1).strip(),
        }

    return None


def extract_figure_title(lines, fallback_title):
    for line in lines:
        if is_figure_caption_line(line):
            return clean_caption_text(line)
    return fallback_title or "Figure"


def build_figure_slug(title, figure_order):
    figure_match = re.search(r"\b(?:Figure|Fig\.?)\s*([A-Za-z]*\d+[A-Za-z0-9]*)", title, re.IGNORECASE)
    if figure_match:
        return f"fig_{figure_match.group(1).lower()}"
    return f"fig_{figure_order}"


def collect_consecutive_image_lines(lines, start_index):
    figure_lines = []
    image_infos = []
    pending_blank_lines = []
    index = start_index

    while index < len(lines):
        image_info = extract_image_info(lines[index])
        if image_info:
            figure_lines.extend(pending_blank_lines)
            pending_blank_lines = []
            figure_lines.append(lines[index])
            image_infos.append(image_info)
            index += 1
            continue
        if image_infos and not lines[index].strip():
            pending_blank_lines.append(lines[index])
            index += 1
            continue
        break

    return figure_lines, image_infos, index


def extract_figure_blocks(lines, paper_meta):
    figure_blocks = []
    index = 0

    while index < len(lines):
        if not extract_image_info(lines[index]):
            index += 1
            continue

        figure_lines, image_infos, index = collect_consecutive_image_lines(lines, index)
        lookahead_lines = []
        lookahead_index = index
        caption_found = False

        while lookahead_index < len(lines) and len(lookahead_lines) < 12:
            next_line = lines[lookahead_index]
            if HEADING_RE.match(next_line) or extract_image_info(next_line):
                break
            lookahead_lines.append(next_line)
            lookahead_index += 1
            if is_figure_caption_line(next_line):
                caption_found = True
                break

        if not caption_found:
            continue

        figure_lines.extend(lookahead_lines)
        index = lookahead_index
        while index < len(lines) and lines[index].startswith(">") and not is_figure_caption_line(lines[index]):
            figure_lines.append(lines[index])
            index += 1

        figure_order = len(figure_blocks) + 1
        figure_title = extract_figure_title(figure_lines, image_infos[0]["alt_text"])
        figure_slug = build_figure_slug(figure_title, figure_order)
        figure_blocks.append(
            {
                "paper_id": paper_meta["paper_id"],
                "paper_title": paper_meta["paper_title"],
                "doi": paper_meta["doi"],
                "journal": paper_meta["journal"],
                "source_md": paper_meta["source_md"],
                "major_heading": "Figures",
                "major_dir_name": "06_figures",
                "major_section_key": "figures",
                "section_order": figure_order,
                "section_title": figure_title,
                "section_slug": figure_slug,
                "section_level": 2,
                "content": "\n".join(figure_lines).strip() + "\n",
            }
        )

    return figure_blocks


def merge_same_figure_blocks(figure_blocks):
    merged_blocks = []
    slug_block_map = {}

    for block in figure_blocks:
        figure_slug = block["section_slug"]
        if figure_slug not in slug_block_map:
            block["section_order"] = len(merged_blocks) + 1
            slug_block_map[figure_slug] = block
            merged_blocks.append(block)
            continue

        target_block = slug_block_map[figure_slug]
        target_block["content"] = target_block["content"].rstrip() + "\n\n" + block["content"].strip() + "\n"
        if len(block["section_title"]) > len(target_block["section_title"]):
            target_block["section_title"] = block["section_title"]

    return merged_blocks


def split_one_md(md_path, species_name_set, common_name_map):
    original_text = Path(md_path).read_text(encoding="utf-8")
    normalized_text, resolved_map, replacement_count = normalize_latin_abbreviations(original_text, species_name_set)
    normalized_text, common_name_replacement_count = normalize_common_species_names(normalized_text, common_name_map)
    lines = normalized_text.splitlines()
    paper_meta = extract_paper_meta(lines, Path(md_path))

    blocks = merge_same_figure_blocks(extract_figure_blocks(lines, paper_meta))
    current_major = None
    current_block = None
    section_counters = {}

    def flush_block():
        nonlocal current_block
        if current_major is None or current_major["excluded"] or current_block is None:
            current_block = None
            return

        content = "\n".join(current_block["lines"]).strip()
        if not content:
            current_block = None
            return

        current_major["block_count"] += 1
        section_counters.setdefault(current_major["dir_name"], 0)
        section_counters[current_major["dir_name"]] += 1
        blocks.append(
            {
                "paper_id": paper_meta["paper_id"],
                "paper_title": paper_meta["paper_title"],
                "doi": paper_meta["doi"],
                "journal": paper_meta["journal"],
                "source_md": paper_meta["source_md"],
                "major_heading": current_major["title"],
                "major_dir_name": current_major["dir_name"],
                "major_section_key": current_major["section_key"],
                "section_order": section_counters[current_major["dir_name"]],
                "section_title": current_block["title"],
                "section_slug": current_block["slug"],
                "section_level": current_block["level"],
                "content": content + "\n",
            }
        )
        current_block = None

    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = clean_heading_text(heading_match.group(2))
            major_section_info = get_major_section_info(heading_text)

            if is_major_heading(level, heading_text, major_section_info):
                flush_block()
                if is_inherited_subsection(current_major, heading_text, major_section_info):
                    current_block = {"title": heading_text, "slug": slugify(heading_text), "level": 2, "lines": [f"### {heading_text}", ""]}
                    continue
                current_major = {
                    "title": heading_text,
                    "excluded": major_section_info["excluded"],
                    "dir_name": major_section_info["dir_name"],
                    "section_key": major_section_info["section_key"],
                    "block_count": 0,
                }
                current_block = None
                continue

            if current_major is None or current_major["excluded"]:
                continue

            if level == 3:
                flush_block()
                current_block = {"title": heading_text, "slug": slugify(heading_text), "level": 3, "lines": [f"### {heading_text}", ""]}
                continue

            if level >= 4:
                if current_block is None:
                    current_block = {"title": current_major["title"], "slug": slugify(current_major["title"]), "level": 2, "lines": []}
                current_block["lines"].append(f"{'#' * level} {heading_text}")
                current_block["lines"].append("")
                continue

        if current_major is not None and current_major["excluded"]:
            continue
        if current_major is None:
            continue
        if current_block is None:
            current_block = {"title": current_major["title"], "slug": slugify(current_major["title"]), "level": 2, "lines": []}
        current_block["lines"].append(line)

    flush_block()
    return paper_meta, normalized_text, blocks, resolved_map, replacement_count, common_name_replacement_count


def get_asset_output_rel_path(raw_path):
    path_parts = [part for part in Path(raw_path).parts if part not in {".", ""}]
    if "images" in path_parts:
        image_index = path_parts.index("images")
        kept_parts = path_parts[image_index + 1:]
    else:
        kept_parts = [part for part in path_parts if part != ".."]
    if not kept_parts:
        kept_parts = [Path(raw_path).name]
    return Path("images").joinpath(*kept_parts)


def get_paper_id_from_image_path(raw_path):
    path_parts = [part for part in Path(raw_path).parts if part not in {".", ""}]
    if "images" in path_parts:
        image_index = path_parts.index("images")
        if image_index + 1 < len(path_parts):
            return path_parts[image_index + 1]
    return ""


def find_publisher_image_path(source_md, raw_path, publisher_xml_dir):
    raw_path_obj = Path(raw_path)
    candidate_paths = [(Path(source_md).parent / raw_path).resolve()]
    paper_id = get_paper_id_from_image_path(raw_path)

    if publisher_xml_dir and paper_id:
        for publisher_dir in sorted(Path(publisher_xml_dir).glob("*")):
            candidate_paths.append(publisher_dir / "images" / paper_id / raw_path_obj.name)

    return next((path for path in candidate_paths if path.exists()), None), candidate_paths[0]


def copy_image_and_build_markdown(raw_path, alt_text, source_md, paper_dir, relative_prefix, publisher_xml_dir):
    if raw_path.startswith("http://") or raw_path.startswith("https://") or raw_path.startswith("data:"):
        return ""

    source_image_path, default_source_image_path = find_publisher_image_path(source_md, raw_path, publisher_xml_dir)
    output_rel_path = get_asset_output_rel_path(raw_path)
    output_image_path = paper_dir / output_rel_path

    if source_image_path:
        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_image_path, output_image_path)
    else:
        print(f"图片不存在, 跳过复制: {default_source_image_path}")
        return ""

    new_rel_path = Path(relative_prefix) / output_rel_path if relative_prefix else output_rel_path
    return f"![{alt_text}]({new_rel_path.as_posix()})"


def rewrite_image_paths(content, source_md, paper_dir, relative_prefix, publisher_xml_dir):
    source_md = Path(source_md)

    def replace_markdown_match(match):
        alt_text = match.group(1)
        raw_path = match.group(2).strip()
        new_markdown = copy_image_and_build_markdown(raw_path, alt_text, source_md, paper_dir, relative_prefix, publisher_xml_dir)
        return new_markdown or match.group(0)

    def replace_html_match(match):
        raw_path = match.group(1).strip()
        alt_match = HTML_ALT_RE.search(match.group(0))
        alt_text = alt_match.group(1).strip() if alt_match else "Image"
        new_markdown = copy_image_and_build_markdown(raw_path, alt_text, source_md, paper_dir, relative_prefix, publisher_xml_dir)
        return new_markdown or match.group(0)

    content = IMAGE_RE.sub(replace_markdown_match, content)
    content = HTML_IMAGE_RE.sub(replace_html_match, content)
    return content


def build_section_md(block):
    content = block["content"].strip()
    if block["major_section_key"] == "figures":
        return content + "\n"
    if content.startswith("#"):
        return content + "\n"
    return f"### {block['section_title']}\n\n{content}\n"


def write_normalized_fulltext_md(paper_meta, normalized_text, output_dir, publisher_xml_dir):
    paper_dir = Path(output_dir) / paper_meta["paper_id"]
    paper_dir.mkdir(parents=True, exist_ok=True)
    normalized_text = rewrite_image_paths(normalized_text, paper_meta["source_md"], paper_dir, "", publisher_xml_dir)
    output_md = paper_dir / "00_normalized_fulltext.md"
    output_md.write_text(normalized_text.rstrip() + "\n", encoding="utf-8")
    return output_md


def build_manifest_row(block, normalized_fulltext_md, output_md):
    return {
        "paper_id": block["paper_id"],
        "paper_title": block["paper_title"],
        "doi": block["doi"],
        "journal": block["journal"],
        "major_heading": block["major_heading"],
        "major_dir_name": block["major_dir_name"],
        "major_section_key": block["major_section_key"],
        "section_order": block["section_order"],
        "section_title": block["section_title"],
        "section_level": block["section_level"],
        "source_md": block["source_md"],
        "normalized_fulltext_md": str(normalized_fulltext_md),
        "output_md": str(output_md),
    }


def write_blocks(paper_meta, blocks, output_dir, normalized_fulltext_md, publisher_xml_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    paper_dir = output_dir / paper_meta["paper_id"]
    paper_dir.mkdir(parents=True, exist_ok=True)

    for block in blocks:
        major_dir = paper_dir / block["major_dir_name"]
        output_md = major_dir / f"{block['section_order']:02d}_{block['section_slug']}.md"
        major_dir.mkdir(parents=True, exist_ok=True)
        block["content"] = rewrite_image_paths(block["content"], block["source_md"], paper_dir, "..", publisher_xml_dir)
        output_md.write_text(build_section_md(block), encoding="utf-8")
        manifest_rows.append(build_manifest_row(block, normalized_fulltext_md, output_md))

    manifest_path = paper_dir / "00_manifest.csv"
    fieldnames = [
        "paper_id",
        "paper_title",
        "doi",
        "journal",
        "major_heading",
        "major_dir_name",
        "major_section_key",
        "section_order",
        "section_title",
        "section_level",
        "source_md",
        "normalized_fulltext_md",
        "output_md",
    ]

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    return manifest_path


def split_sections(input_md, output_dir, species_tsv, common_species_tsv, publisher_xml_dir=""):
    species_name_set = load_species_dictionary(species_tsv)
    common_name_map = load_species_common_name_registry(common_species_tsv, species_name_set)
    paper_meta, normalized_text, blocks, resolved_map, replacement_count, common_name_replacement_count = split_one_md(
        Path(input_md),
        species_name_set,
        common_name_map,
    )
    normalized_fulltext_md = write_normalized_fulltext_md(paper_meta, normalized_text, output_dir, publisher_xml_dir)
    manifest_path = write_blocks(paper_meta, blocks, output_dir, normalized_fulltext_md, publisher_xml_dir)
    return {
        "paper_id": paper_meta["paper_id"],
        "manifest_path": str(manifest_path),
        "block_count": len(blocks),
        "abbreviation_count": len(resolved_map),
        "abbreviation_replacement_count": replacement_count,
        "common_name_count": len(common_name_map),
        "common_name_replacement_count": common_name_replacement_count,
    }
