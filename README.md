# Arthropod Pesticide Resistance Scholar (APRS)

Arthropod Pesticide Resistance Scholar (APRS) is a Natural Language Processing (NLP) toolkit dedicated to the study of arthropod pesticide resistance. This release provides the literature case-extraction pipeline, which uses mapping tables, prompt engineering, Large Language Models (LLMs), and Vision-Language Models (VLMs) to extract structured resistance-related information from full-text academic papers.

The pipeline processes one full-text Markdown paper at a time and generates structured outputs for species, pesticides, resistance mechanisms, monitoring phenotypes, and figure-based evidence.

## Directory Structure

```text
APRS/
├── bin/
│   └── run_pipeline.py
├── config/
│   ├── prompts.py
│   └── settings.py
├── mapping_tables/
│   ├── arthropoda_binomial_species_dictionary.tsv
│   ├── species_common_name_registry_v0.2.tsv
│   └── pesticide_name_registry_clean.tsv
└── pipeline/
    ├── step01_split_sections.py
    ├── step02_candidates.py
    ├── step03_mechanism.py
    ├── step04_monitoring.py
    └── step05_figure_notes.py
```

## Core Resources

### config/prompts.py

This file stores all LLM and VLM prompts used by APRS.

The prompts are responsible for:

- species-pesticide association extraction
- gene-level resistance mechanism extraction
- resistance evidence type assignment
- strain or population extraction
- location and year extraction
- resistance factor, LC50/LD50, and mutation extraction
- resistance status, cross-resistance, and study context assignment
- figure-based evidence note extraction

### mapping_tables/arthropoda_binomial_species_dictionary.tsv

This table stores arthropod Latin binomial species names.

It is used to:

- detect valid arthropod species names
- normalize Latin species-name abbreviations
- reduce false species extraction

### mapping_tables/species_common_name_registry_v0.2.tsv

This table stores strict common-name to Latin-name mappings.

It is used to:

- identify high-confidence pest common names
- add corresponding Latin names when common names are detected

### mapping_tables/pesticide_name_registry_clean.tsv

This table stores normalized pesticide names.

It is used to:

- detect candidate pesticide names
- provide controlled pesticide candidates for downstream LLM extraction

## Workflow

```text
Step 1  Split full-text Markdown into sections and figure blocks
Step 2  Detect candidate arthropod species and pesticides
Step 3  Extract gene-level resistance mechanism cases
Step 4  Extract monitoring and phenotype cases
Step 5  Add figure-based evidence notes
```

## Input

The input is one full-text Markdown paper:

```text
paper.md
```

Recommended section headings:

```markdown
## Materials and Methods
## Results
## Results and Discussion
## Discussion
```

Supported image formats:

```markdown
![Figure 1](relative/path/to/image.jpg)
```

```html
<img src="relative/path/to/image.jpg" alt="Figure 1">
```

## Usage

Set the API key:

```bash
export DASHSCOPE_API_KEY=your_api_key
```

Run APRS:

```bash
python bin/run_pipeline.py \
  --input-md paper.md \
  --output-dir output
```

If figures need to be searched from an external publisher image directory:

```bash
python bin/run_pipeline.py \
  --input-md paper.md \
  --output-dir output \
  --publisher-xml-dir /path/to/publisher_xml_root
```

## Output

For an input file named `paper.md`, APRS writes results to:

```text
output/paper/
```

Main output files:

```text
00_normalized_fulltext.md
00_manifest.csv
03_species_pesticide_candidates.json
04_species_pesticide_gene_pairs.json
05_1_species_pesticide_strain_monitoring_cases.json
06_1_monitoring_cases_with_figure_notes.json
```

## Author

Wu Hongxin  
College of Plant Protection, South China Agricultural University  
wuhongxinscau@foxmail.com
