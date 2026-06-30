                      
                       

import os
from pathlib import Path


REFACTOR_ROOT = Path(__file__).resolve().parents[1]
MAPPING_TABLE_DIR = REFACTOR_ROOT / "mapping_tables"

DEFAULT_SPECIES_TSV = MAPPING_TABLE_DIR / "arthropoda_binomial_species_dictionary.tsv"
DEFAULT_COMMON_SPECIES_TSV = MAPPING_TABLE_DIR / "species_common_name_registry_v0.2.tsv"
DEFAULT_PESTICIDE_TSV = MAPPING_TABLE_DIR / "pesticide_name_registry_clean.tsv"
DEFAULT_PUBLISHER_XML_DIR = os.environ.get("LOOM_PUBLISHER_XML_DIR", "")


DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_MODEL = "qwen3.5-27b"
DASHSCOPE_VLM_MODEL = "qwen3.5-plus"
DASHSCOPE_ENABLE_THINKING = False
DASHSCOPE_TIMEOUT = 1800

MIN_IMAGE_EDGE = 10
MAX_IMAGE_PIXELS = 178956970
