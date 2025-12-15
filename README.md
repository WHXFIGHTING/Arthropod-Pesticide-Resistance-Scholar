# Arthropod Pesticide Resistance Scholar (APRS)

**Arthropod Pesticide Resistance Scholar** is a Natural Language Processing (NLP) toolkit dedicated to the study of arthropod (pest) pesticide resistance. This project aims to build an automated pipeline that combines the reasoning capabilities of Large Language Models (LLMs) with the extraction precision of fine-tuned BERT models to automatically filter, identify, and structure resistance-related data from massive amounts of academic literature.

## 📂 Directory Structure

The project adopts a modular design consisting of four core components:

```text
Arthropod-Pesticide-Resistance-Scholar/
├── CLS/          # Text Classification Module (Classification BERT)
├── NER/          # Named Entity Recognition Module (NER BERT)
├── LLM/          # Case Extraction Module (LLM Case Extraction)
└── DATA/         # Core Data & Resources (Datasets)
```text

🚀 Module Details
1. DATA/ - Datasets & Resources
This folder serves as the core data repository, storing all resources required for model training and evaluation.

Training Data: Contains manually annotated text used for fine-tuning the CLS (Classification) and NER (Entity Recognition) models.

Few-shot Examples: Provides sample data for the LLM module

2. CLS/ - Classification
A BERT-based binary classification model acting as the system's "filter".

Core Task: Relevance Filtering.

Function: Automatically analyzes literature abstracts or full texts to accurately distinguish whether a document belongs to the "pesticide resistance" research domain.

Application: Rapidly filters out irrelevant non-resistance texts when processing massive literature streams, retaining only high-quality data for downstream modules.

3. NER/ - Named Entity Recognition
A BERT-based sequence labeling model designed specifically for the field of insect toxicology.

Core Task: Entity Extraction.

Function: Precisely locates and extracts key entities within the unstructured text (e.g., specific pest species, insecticide chemical names, target genes, mutation sites), providing structured anchors for the LLM.

4. LLM/ - Case Extraction
Leveraging the strong semantic understanding and logical reasoning capabilities of Large Language Models (LLMs), this module serves as the central hub for information synthesis.

Core Task: Event Structuring.

Function: Combines the filtering results from CLS and the entity information from NER. It uses Prompt Engineering to guide the LLM in extracting complete "Resistance Events."

Output Goal: Synthesizes scattered information into structured entries

🛠️ Workflow

Filter: The CLS module filters out non-resistance-related literature.

Extract: The NER module identifies key biological and chemical entities in the retained texts.

Synthesize: The LLM module integrates the context to generate the final structured resistance report.

👤 Author
Wu Hongxin College of Plant Protection, South China Agricultural University
wuhongxinscau@foxmail.com


