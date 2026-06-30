                      
                       

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from config.settings import (
    DASHSCOPE_MODEL,
    DASHSCOPE_VLM_MODEL,
    DEFAULT_COMMON_SPECIES_TSV,
    DEFAULT_PESTICIDE_TSV,
    DEFAULT_PUBLISHER_XML_DIR,
    DEFAULT_SPECIES_TSV,
)
from pipeline.step01_split_sections import split_sections
from pipeline.step02_candidates import extract_candidates, write_candidates
from pipeline.step03_mechanism import extract_mechanism_cases, write_mechanism_cases
from pipeline.step04_monitoring import extract_monitoring_cases, write_monitoring_cases
from pipeline.step05_figure_notes import extract_figure_notes, write_figure_notes


def parse_args():
    parser = argparse.ArgumentParser(description="运行单篇文献知识抽取总流程")
    parser.add_argument("--input-md", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--species-tsv", default=str(DEFAULT_SPECIES_TSV))
    parser.add_argument("--common-species-tsv", default=str(DEFAULT_COMMON_SPECIES_TSV))
    parser.add_argument("--pesticide-tsv", default=str(DEFAULT_PESTICIDE_TSV))
    parser.add_argument("--publisher-xml-dir", default=str(DEFAULT_PUBLISHER_XML_DIR))
    parser.add_argument("--llm-model", default=DASHSCOPE_MODEL)
    parser.add_argument("--vlm-model", default=DASHSCOPE_VLM_MODEL)
    parser.add_argument("--skip-step03", action="store_true")
    parser.add_argument("--skip-step05", action="store_true")
    return parser.parse_args()


def print_json(label, data):
    print(label)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run_pipeline(args):
    step01_summary = split_sections(
        args.input_md,
        args.output_dir,
        args.species_tsv,
        args.common_species_tsv,
        args.publisher_xml_dir,
    )
    paper_id = step01_summary["paper_id"]
    print_json("step01_done", step01_summary)

    step02_record = extract_candidates(
        paper_id,
        args.output_dir,
        args.species_tsv,
        args.common_species_tsv,
        args.pesticide_tsv,
    )
    step02_output = write_candidates(step02_record, args.output_dir)
    print_json(
        "step02_done",
        {
            "paper_id": paper_id,
            "species": len(step02_record["species"]),
            "pesticides": len(step02_record["pesticides"]),
            "output": str(step02_output),
        },
    )

    if not args.skip_step03:
        step03_record = extract_mechanism_cases(paper_id, args.output_dir, model=args.llm_model)
        step03_output = write_mechanism_cases(step03_record, args.output_dir)
        print_json(
            "step03_done",
            {
                "paper_id": paper_id,
                "mechanism_cases": len(step03_record["pairs"]),
                "output": str(step03_output),
            },
        )

    step04_record = extract_monitoring_cases(paper_id, args.output_dir, model=args.llm_model)
    step04_output = write_monitoring_cases(step04_record, args.output_dir)
    print_json(
        "step04_done",
        {
            "paper_id": paper_id,
            "monitoring_cases": len(step04_record["pairs"]),
            "step_summary": step04_record.get("step_summary", {}),
            "output": str(step04_output),
        },
    )

    if not args.skip_step05:
        step05_record = extract_figure_notes(paper_id, args.output_dir, model=args.vlm_model)
        step05_output = write_figure_notes(step05_record, args.output_dir)
        print_json(
            "step05_done",
            {
                "paper_id": paper_id,
                "step_summary": step05_record.get("step_summary", {}),
                "output": str(step05_output),
            },
        )

    return paper_id


def main():
    args = parse_args()
    paper_id = run_pipeline(args)
    print(f"pipeline_done: {paper_id}")


if __name__ == "__main__":
    main()
