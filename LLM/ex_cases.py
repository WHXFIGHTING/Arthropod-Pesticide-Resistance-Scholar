#author:whx


#=========================================================
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator,ValidationInfo, model_validator
from typing import List,Dict
import pandas as pd
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import ast
from langchain_core.exceptions import OutputParserException
import networkx as nx
import matplotlib.pyplot as plt
from retrying import retry
from tqdm import tqdm
from joblib import Parallel, delayed




#=========================================================

from pydantic import BaseModel, model_validator, ConfigDict, PydanticSchemaGenerationError
from typing import Dict, List, Optional
from pydantic import ValidationError
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI  


class ResistanceEvent(BaseModel):
    Pesticides: str
    Species: str
    Resistance_factor_value: List[str] = []
    location: List[str] = []
    Genes: List[str] = []
    Year: List[str] = []
    Research_level: List[str] = []
    LC_LD: List[str] = [] 
    Resistance_mechanism: List[str] = []
    Population_type: Optional[str] = ""

    model_config = ConfigDict(extra='allow')  

    _entities: Dict[str, List[str]] = {
        "Pesticides": [],
        "Species": [],
        "Resistance_factor_value": [],
        "location": [],
        "Genes": [],     
        "Year": [],
        "Research_level": [],
        "Resistance_mechanism": [],
        "LC_LD": [],
        "Population_type": []  
    }

    @classmethod
    def set_entities(cls, entities: Dict[str, List[str]]):
        if not entities:
            raise ValueError("The provided entity dictionary cannot be empty.")
        cls._entities = entities


    @model_validator(mode="after")
    def validate_entities_and_combinations(self):
        entities = self.__class__._entities

        if not any(entities.values()):
            raise ValueError("The content of the entity list dictionary cannot be empty. Please call set_entities first to set valid values.")


        for field_name, allowed_values in entities.items():
            if not allowed_values:  
                continue
                
            current_value = getattr(self, field_name, None)

        return self

class ResistanceEventList(BaseModel):
    records: List[ResistanceEvent]


#==================================================================================================

prompt_template = """

As a professional expert in pesticide resistance relationship extraction, strictly adhere to the following core task requirements: Using "pesticide" as the root entity, associate it with "species," and integrate elements from the provided entity list to construct resistance reporting events. Extract information precisely based on the text content; all event details must originate from the given entity list (allowing correction of entity boundary errors to enhance readability), with clear textual evidence required. Leave any unmentioned attributes blank, but ensure no fields are missing from the output structure.

Specifically for the "Population_type" attribute, make reasonable inferences: If the text explicitly mentions "field population" or similar phrases, mark it as "field"; if it refers to laboratory-selected strains (e.g., FLU-SEL), mark it as "laboratory".

1.During extraction, for the "Species" attribute, strictly use the species name forms provided in the entity list. If the entity list contains both abbreviations and full names for the same species, prioritize and use the full Latin scientific name as the unique standard representation for that species; retain and use the abbreviation only when it is the sole form provided in the entity list.
2.For the "Research_level" and "Resistance_mechanism" attributes, minimal corrections to entity boundary errors are permitted to enhance readability, such as removing redundant punctuation, correcting obvious spelling errors, or normalizing expression formats, while ensuring the core semantics of the terms remain unchanged.
3.Only extract pesticide entities from the entity list that are explicitly categorized as specific chemical compounds or biological toxins. General category names (such as "insecticides", "herbicides"), mode of action descriptions (such as "neonicotinoids"), and non-compound entities (such as resistance genes, metabolic enzyme names) should not be included as pesticide entities in case extraction.
4.Strictly prohibit any entity extraction beyond the scope of the provided entity list. All output entities must originate exclusively from the given entity list, only allowing boundary corrections (such as punctuation adjustment, format normalization) to existing entities. Do not add, infer, or create any entities not explicitly present in the list.
5.For the "Resistance_factor_value" attribute, standardize resistance factor expressions as follows:
 -Convert "times" uniformly to "fold"
 -Standardize "X- to Y-fold" format to "X-Y-fold"
 -Ensure all resistance factor values adopt the unified "numerical range-fold" format
 -Perform format standardization only, without modifying original numerical values and ranges
 -In the case records, the "Resistance_factor_value" field exclusively documents the resistance fold to pesticide compounds, specifically defined as the ratio of median lethal doses between resistant and susceptible strains (e.g., RR = LD50 resistant strain/LD50 susceptible strain). This field explicitly excludes gene expression folds, protein activity folds, or other molecular-level fold changes. Ensure that every extracted resistance factor value is directly linked to the quantitative assessment of pesticide resistance phenotypes.
 -Preserve specific dosage identifiers in resistance factors, including "RR(50)=", "RR(99)=" and other indicators representing different mortality levels. These identifiers are crucial for distinguishing resistance folds under different experimental conditions and should be retained as integral components of the resistance factor values.
6.In case construction, each extracted gene entity must have a clear resistance association with the corresponding pesticide entity. A gene should only be included in the "Genes" field of a pesticide event if the text explicitly states that the gene is involved in resistance to that specific pesticide. Do not include unrelated genes, genes with unclear associations, or misclassify species abbreviations, population names, chemical substances, Bt toxins, mutation sites, kdr types, incomplete gene fragments, or other uppercase abbreviations as gene entities.
7.For the "Year" field, extract only specific year values (e.g., "2000", "2010"), ignoring month, date, and time range descriptions. If the entity list contains complete time range strings, retain only the year portion.
 
Example Input：
"BACKGROUND: Bemisia tabaci is one of most notorious pests on various crops worldwide and many populations show high resistance to different types of insecticides. Flupyradifurone is a novel insecticide against sucking pests. B. tabaci resistance to flupyradifurone has been detected in the field, however the mechanism of flupyradifurone resistance has rarely been studied. RESULTS: The flupyradifurone-resistant strain (FLU-SEL) was selected from the susceptible strain of B. tabaci (MED-S) using flupyradifurone for 24 generations. The FLU-SEL strain exhibited 105.56-fold resistance to flupyradifurone, and moderate cross-resistance to imidacloprid, but no cross-resistance to other tested neonicotinoids. Synergism tests and metabolic enzyme assays suggested that FLU-SEL resistance can be attributed to enhanced detoxification mediated by glutathione S-transferase (GST) and P450 monooxygenase (P450). Compared with MED-S strain, CYP6CX4 and GSTs2 were significantly overexpressed in FLU-SEL, and silencing CYP6CX4 or GSTs2 increased the mortality of whiteflies to flupyradifurone challenge in FLU-SEL. In addition, silencing CYP6CX4 also increased the mortality of whiteflies exposed to imidacloprid. CONCLUSION: Overexpression of CYP6CX4 and GSTs2 was associated with flupyradifurone resistance, as confirmed by RNA interference. Our findings suggested that metabolic resistance to flupyradifurone might be mediated by P450s and GSTs."

Example Entities:
{{'Species': ['B. tabaci', 'Bemisia tabaci'], 'Pesticides': ['imidacloprid', 'Flupyradifurone', 'FLU-SEL', 'flupyradifurone', 'neonicotinoids'], 'Resistance_factor_value': ['105.56-fold'], 'Location': [], 'Gene': ['CYP6CX4', 'GSTs2', 'P450s', 'GSTs', 'P450 monooxygenase (P450)', 'glutathione S-transferase (GST)'], 'Year': [], 'Research_level': ['overexpressed', 'Overexpression', 'RNA interference'], 'Resistance_mechanism': ['metabolic resistance'], 'LC_LC': []}}


Example Result:

{{
"records": [
{{
"Pesticides": "flupyradifurone",
"Species": "Bemisia tabaci",
"Resistance_factor_value": ["105.56-fold"],
"location": [],
"Genes": ["CYP6CX4", "GSTs2"],
"Year": [],
"Research_level": ["overexpressed", "RNA interference"],
"LC_LC": [],
"Resistance mechanism": ["metabolic resistance"],
"Population_type": "laboratory"
}},
{{
"Pesticides": "imidacloprid",
"Species": "Bemisia tabaci",
"Resistance_factor_value": [],
"location": [],
"Genes": ["CYP6CX4"],
"Year": [],
"Research_level": ["RNA interference"],
"LC_LC": [],
"Resistance mechanism": [],
"Population_type": "laboratory"
}}
]
}}




Text to be extracted:
{text}

Entity List:
{ent}

Based on the above rules and example, please extract the combinations of events. The events must be combinations of the given entities, and output in JSON format.
{format_instructions}




"""



parser = PydanticOutputParser(pydantic_object=ResistanceEventList)
prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["text", "ent"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)



#==========================================================================================================


OPENAI_API_KEY = ""
API_BASE = ""


llm = ChatOpenAI(model="" , temperature=0.001, openai_api_key=OPENAI_API_KEY, base_url=API_BASE)
chain = prompt | llm | parser




#==========================================================================================================

import ast
@retry(stop_max_attempt_number=3, wait_fixed=1000)
def extract_relations(text,input_entities):
    entities = ast.literal_eval(input_entities)
    ResistanceEvent.set_entities(entities)
    result = chain.invoke({
        "text": text,
        "ent": entities
    })
    return result




#==========================================================================================================

chunk1 = pd.read_csv('')





def process_row(row):

    try:
        entities= row['entities'] 
        text = row['sentence']
        result = extract_relations(text, entities)
    except Exception as e:
        result = f"Error: {e}"
    return str(result)





chunk1['re'] = Parallel(n_jobs=10, backend='multiprocessing')(
    delayed(process_row)(row) for _, row in tqdm(chunk1.iterrows(), total=len(chunk1), desc="ROW")
)



chunk1.to_csv('', index=False)

print("All Done!")