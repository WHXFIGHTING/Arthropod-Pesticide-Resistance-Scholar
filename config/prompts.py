                      
                       


STEP03_PAIR_PROMPT = """You are an expert in insect and arthropod pesticide resistance mechanisms.

Your task is to read one Results or Results and discussion section and identify new species-pesticide association pairs.

Extraction scope:
- Use only the current section text.
- Candidate species and candidate pesticides are provided; use only names from the candidate lists.
- An association may involve resistance, toxicity change, treatment, exposure, selection, functional validation, or a table-defined relationship.
- Output a pair only when the current section clearly links the candidate species and candidate pesticide.

Decision rules:
- For HTML tables, read the whole table and use the title, headers, row labels, column labels, cells, and footnotes to infer valid pairs.
- Existing pairs are provided; do not repeat them.
- Do not infer beyond the text. Every output pair must be supported by the current section.

Output rules:
- Output JSON only.
- Do not output explanations.
- Do not show reasoning.

Paper ID:
{paper_id}

Section path:
{section_path}

Candidate species:
{species_json}

Candidate pesticides:
{pesticides_json}

Existing pairs:
{existing_pairs_json}

Current section text:
{section_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "section_path": "{section_path}",
  "pairs": [
    {{
      "species": "species name",
      "pesticide": "pesticide name"
    }}
  ]
}}
"""


STEP03_GENE_PROMPT = """You are an expert in insect and arthropod pesticide resistance mechanisms.

Your task is to read one Results or Results and discussion section and add specific single genes to confirmed species-pesticide mechanism pairs.

Extraction scope:
- Use only the current section text.
- Confirmed species-pesticide pairs are provided; add genes only to these pairs.
- Output a case only when the current section clearly links a confirmed pair to a specific single gene.
- Do not infer beyond the text. Every output case must be supported by the current section.

Gene rules:
- `gene` must be one specific single gene, such as a standard gene name, a unique locus ID, a unique transcript ID, or a numbered gene name.
- Do not output gene lists, gene families, enzyme systems, or protein classes, such as `P450 genes`, `CYP450`, `GST`, `UGT`, `ABC transporter`, `esterase`, or `detoxification enzyme`.
- The same gene may be linked to multiple confirmed pesticides; split each `species + pesticide + gene` into a separate case.
- Omics or expression evidence is valid only when a specific single gene is explicitly reported as upregulated or overexpressed.
- Do not output cases based only on differential expression without direction, tissue enrichment, downregulation, or low expression.

Decision rules:
- Output only when the current section clearly links the specific gene to the resistance mechanism of the species-pesticide pair.
- For HTML tables, read the whole table and use the title, headers, row labels, column labels, cells, and footnotes to judge gene links.
- Do not output if the pair and the gene merely appear in the same section without an explicit relationship.
- Do not repeat existing species-pesticide-gene cases.
- Prefer missing a weak case over guessing.

Output rules:
- Output JSON only.
- Return an empty list when no new gene is found.
- Do not output explanations.
- Do not show reasoning.

Paper ID:
{paper_id}

Section path:
{section_path}

Confirmed pairs:
{confirmed_pairs_json}

Existing gene cases:
{existing_cases_json}

Current section text:
{section_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "section_path": "{section_path}",
  "pairs": [
    {{
      "species": "species name",
      "pesticide": "pesticide name",
      "gene": "gene name"
    }}
  ]
}}
"""


STEP03_METHOD_PROMPT = """You are an expert in insect and arthropod pesticide resistance mechanisms.

Your task is to read one Results or Results and discussion section and add mechanism evidence types to confirmed species-pesticide-gene cases.

Extraction scope:
- Use only the current section text.
- Confirmed species-pesticide-gene cases are provided; add `methods` only to these cases.
- Output only when the current section clearly supports one or more mechanism evidence types for a confirmed case.
- Do not infer beyond the text. Every output case must be supported by the current section.

Allowed evidence types:
- `omics upregulation`: Transcriptomic, proteomic, heatmap, expression matrix, or other omics evidence showing upregulation or overexpression of a specific single gene.
- `resistant overexpression`: qPCR, RT-qPCR, targeted expression assay, protein expression assay, or similar single-gene validation showing overexpression in a resistant population, resistant strain, or selected resistant line.
- `in vitro validation`: In vitro expression, recombinant protein, cell expression, microsome, enzyme activity, or similar assays directly validating metabolism, binding, toxicity change, or resistance relevance.
- `Drosophila validation`: Drosophila heterologous expression system showing altered pesticide susceptibility or resistance.
- `RNAi validation`: RNAi, dsRNA, silencing, or knockdown of the gene followed by pesticide susceptibility, mortality, LC50, or resistance testing.
- `CRISPR validation`: CRISPR, genome editing, knockout, knock-in, or mutation editing showing altered pesticide susceptibility or resistance.

Decision rules:
- `methods` must be selected only from the allowed list. A case may have multiple methods.
- Check each confirmed case independently and add only methods supported by the current section.
- Add `omics upregulation` only when a specific single gene is explicitly upregulated or overexpressed.
- For HTML tables, read the whole table and use the title, headers, rows, columns, cells, and footnotes to judge methods.

Output rules:
- Output JSON only.
- Return an empty list when no new methods are found.
- Do not output explanations.
- Do not show reasoning.

Paper ID:
{paper_id}

Section path:
{section_path}

Allowed methods:
{method_options_json}

Method definitions:
{method_option_definitions_json}

Confirmed gene cases:
{confirmed_cases_json}

Existing method cases:
{existing_method_cases_json}

Current section text:
{section_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "section_path": "{section_path}",
  "pairs": [
    {{
      "species": "species name",
      "pesticide": "pesticide name",
      "gene": "gene name",
      "methods": [
        "omics upregulation",
        "resistant overexpression",
        "RNAi validation"
      ]
    }}
  ]
}}
"""


STEP04_PAIR_PROMPT = """You are an expert in insect and arthropod pesticide resistance monitoring extraction.

Your task is to read the current section and identify new species-pesticide pairs.

Extraction scope:
- Use only the current section text.
- Candidate species and candidate pesticides are provided; use only names from the candidate lists.
- Determine only whether a candidate species and a candidate pesticide are explicitly associated.
- Valid associations include monitoring, bioassay, toxicity test, exposure, selection, resistance comparison, mutation detection, or table-defined relationships.

Decision rules:
- Existing pairs are provided; do not repeat them.
- Every output pair must be supported by the current section.
- Prefer missing a weak case over guessing.

Table rules:
- For HTML tables, read the whole table and use the title, headers, row labels, column labels, cells, and footnotes to extract pairs.

Output rules:
- Output JSON only.
- Do not output explanations.
- Do not show reasoning.

Paper ID:
{paper_id}

Section path:
{section_path}

Candidate species:
{species_json}

Candidate pesticides:
{pesticides_json}

Existing pairs:
{existing_pairs_json}

Current section text:
{section_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "section_path": "{section_path}",
  "pairs": [
    {{
      "species": "species name",
      "pesticide": "pesticide name"
    }}
  ]
}}
"""


STEP04_STRAIN_PROMPT = """You are an expert in insect and arthropod pesticide resistance monitoring extraction.

Your task is to read the current section and attach monitoring objects, strains, populations, selected lines, or experimental lines to confirmed species-pesticide pairs.

Extraction scope:
- Use only the current section text.
- Confirmed species-pesticide pairs are provided; select only from these pairs.
- In this step, output only species + pesticide + strain.
- `strain` is the label that distinguishes the monitored object. It may be a strain, population, line, colony, field population, selected strain, susceptible line, generation, or mutant line.
- If no explicit strain, population, line, colony, or generation is given, but a location is used as the sampling population label, use the location as `strain`.
- `strain` must be an explicit object label appearing in the text, table row, table column, figure legend, or section. Do not output generic or explanatory phrases.

Decision rules:
- Resistant strains, susceptible strains, field populations, laboratory-selected generations, and mutant lines may be extracted.
- Output only when the current section clearly supports that the strain is linked to a confirmed species-pesticide pair through monitoring, bioassay, toxicity test, selection, resistance comparison, mutation detection, or table relationship.
- Existing monitoring objects are provided; do not repeat them.
- Every output object must be supported by the current section.

Table rules:
- For HTML tables, read the title, headers, row labels, column labels, cells, and footnotes, and attach strains to the correct species-pesticide pairs using the true row-column relationship.

Output rules:
- Output JSON only.
- Do not output explanations.
- Do not show reasoning.

Paper ID:
{paper_id}

Section path:
{section_path}

Confirmed species-pesticide pairs:
{confirmed_pairs_json}

Existing monitoring objects:
{existing_strains_json}

Current section text:
{section_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "section_path": "{section_path}",
  "strains": [
    {{
      "species": "species name",
      "pesticide": "pesticide name",
      "strain": "strain or population name"
    }}
  ]
}}
"""


STEP04_LOCATION_PROMPT = """You are an expert in insect and arthropod pesticide resistance monitoring extraction.

Your task is to read the current input and add location and year to confirmed monitoring case frames.

Extraction scope:
- The current input is used only to add `location` and `year` to confirmed species + pesticide + strain cases.
- Do not add new species, pesticides, strains, or cases.
- Do not infer beyond the text. Every output row must be supported by the current input.

Field rules:
- Copy species, pesticide, and strain exactly from the confirmed case frames.
- `location` should be the location described in the source text.
- `year` should be a four-digit year; use an empty string when unavailable.

Table rules:
- For HTML tables, read the whole table and use the title, headers, row labels, column labels, cells, and footnotes.

Output rules:
- Output JSON only.
- Do not output explanations.
- Do not show reasoning.

Paper ID:
{paper_id}

Section path:
{section_path}

Confirmed case frames:
{confirmed_frames_json}

Existing location-year cases:
{existing_cases_json}

Current section text:
{section_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "section_path": "{section_path}",
  "pairs": [
    {{
      "species": "species name",
      "pesticide": "pesticide name",
      "strain": "strain or population name",
      "location": "location name, or empty string",
      "year": "2019, or empty string"
    }}
  ]
}}
"""


STEP04_EVIDENCE_PROMPT = """You are an expert in insect and arthropod pesticide resistance monitoring extraction.

Task:
Read the current section and add only the following fields to confirmed species + pesticide + strain monitoring cases:
- resistance_factor
- LC50_LD50
- mutation

Extraction scope:
- Use only the current section text.
- Do not create new cases and do not repeat existing results.
- Output only when the information can be matched to an existing case; otherwise return an empty list.

Field rules:
- `resistance_factor` should contain only the numeric resistance fold explicitly reported in the text, such as RF, RR, resistance ratio, resistance factor, or fold resistance. Do not include units.
- `LC50_LD50` should contain only LC50 or LD50 values with units. Do not output KC50, LT50, KT50, LC90, LD90, or similar endpoints.
- `mutation` should contain only target-site resistance mutations such as kdr/vgsc/sodium channel, ace-1, or rdl. If both gene and site are given, write `gene(site)`. If only a generic marker is mentioned without a specific site, leave it empty.

Table rules:
- Table titles, headers, row labels, column labels, cells, and footnotes may all be evidence.
- Check resistance_factor, LC50_LD50, and mutation by the true row-column relationship. Evidence in tables must be captured completely.

Output rules:
- Output JSON only.
- Return an empty list when no new evidence is found.
- Do not output explanations.
- Do not show reasoning.

Candidate monitoring cases:
{confirmed_cases_json}

Existing results:
{existing_evidence_json}

Current section:
{section_path}

Current section text:
{section_text}

Output JSON format:
[
  {{
    "species": "species name",
    "pesticide": "pesticide name",
    "strain": "strain name",
    "location": "location name, or empty string",
    "year": "2019, or empty string",
    "resistance_factor": "resistance factor, or empty string",
    "LC50_LD50": "LC50 or LD50 value with unit, or empty string",
    "mutation": "marker gene or marker name(mutation site), mutation site, or empty string"
  }}
]
"""


STEP04_STATUS_CONTEXT_PROMPT = """You are an expert reviewer of insect and arthropod pesticide resistance monitoring cases.

Your task is to read the current Methods, Results, and Results and discussion text and add the following fields to confirmed monitoring cases:
- resistance_status
- cross
- study_context

Extraction scope:
- Use only the provided text.
- Do not create cases, delete cases, or modify species, pesticide, strain, location, or year.
- Return one output row for every input case.
- `resistance_status`, `cross`, and `study_context` are independent fields. Do not use one field as a substitute for another.

Field rules:
- `resistance_status` must be either `resistant` or an empty string. Use `resistant` only when the text explicitly describes the current species + pesticide + strain as resistant or as a resistance result.
- `cross` must be either `cross` or an empty string. Use `cross` only when the text or table explicitly states that the current species + pesticide + strain is part of cross-resistance, cross resistant, cross-tolerance, or cross-susceptibility between pesticides.
- `study_context` must be one of the following three values:
  - `field_monitoring`: field-collected population, regional population, field monitoring, hut trial, ULV, IRS, LLIN, or field efficacy.
  - `laboratory_research`: laboratory-selected strain, susceptible reference strain, laboratory-maintained strain, F1/F2, hybrid, cross, selected line, transgenic line, heterologous expression, or mechanism-validation object.
  - `unclear`: Methods/Results do not support a clear source classification.

Table rules:
- For HTML tables, read the whole table. The title, headers, row labels, column labels, cells, and footnotes may all be evidence.

Output rules:
- Output JSON only.
- Do not output explanations.
- Do not show reasoning.

Paper ID:
{paper_id}

Confirmed monitoring cases:
{confirmed_cases_json}

Existing results:
{existing_status_context_json}

Current paper text:
{paper_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "pairs": [
    {{
      "species": "species name",
      "pesticide": "pesticide name",
      "strain": "strain or population name",
      "location": "location name, or empty string",
      "year": "2019, or empty string",
      "resistance_status": "resistant, or empty string",
      "cross": "cross, or empty string",
      "study_context": "field_monitoring"
    }}
  ]
}}
"""


STEP05_FIGURE_PROMPT = """You are an expert in extracting image-based evidence for insect and arthropod pesticide resistance.

Your task is to read all image panels and the title/caption of one Results Figure and determine which existing monitoring cases can receive image-based supporting notes.

Rules:
- Use only the current Figure images, title, and caption.
- If one Figure is split into multiple image blocks, interpret all image blocks together.
- Add `figure_note` only when the current Figure directly supports an existing monitoring case.
- The image evidence must be linkable to the species, pesticide, and strain/population of an existing case.
- Relevant image evidence may include target-site result, resistance status, resistance strength, mortality, LC50/LD50, resistance fold, or mutation.
- Do not attach sampling maps, species composition figures, location figures, or background figures to monitoring cases unless the image also shows pesticide exposure or resistance results for the case.
- `figure_note` must be one English sentence describing what the image adds. Prefer starting with `Figure X:`.
- `figure_note` should describe values or patterns shown in the image. Do not independently judge resistant, susceptible, or resistance level beyond the figure.
- If uncertain, do not add a note.

Output rules:
- Output JSON only.
- Do not output explanations.
- Do not show reasoning.
- Return an empty list when there is no image support.
- Prefer missing a weak case over guessing.

Paper ID:
{paper_id}

Figure md path:
{figure_md_path}

Image path list:
{image_paths_json}

Existing monitoring cases:
{existing_cases_json}

Current figure title and caption md:
{figure_md_text}

Output JSON format:
{{
  "paper_id": "{paper_id}",
  "monitoring_cases": [
    {{
      "species": "species name copied from existing case",
      "pesticide": "pesticide name copied from existing case",
      "strain": "strain copied from existing case",
      "figure_note": "Figure X: one English sentence describing the figure evidence"
    }}
  ]
}}
"""
