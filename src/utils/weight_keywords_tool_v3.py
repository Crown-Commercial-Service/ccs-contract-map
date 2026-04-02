import  pandas as pd
from pathlib import Path
import ast
from src.utils.llm_keywords_finder import keywords_finder_llm
import json

corpus_location = Path(__file__).parents[2] / "AI Catrgorisation Testing Notes.xlsx"
registry_path = Path(__file__).parents[2] / "semantic_anchors3.json"

data = pd.read_excel(str(corpus_location))
data_to_analyse = data[data["Correct Match "].notna()]
data_to_analyse["Correct Match "] = (
    data_to_analyse["Correct Match "]
    .astype(str)
    .str.replace(r"\s*&\s*", " and ", regex=True)
    .str.strip()
)

data_to_analyse["Correct Match "] = data_to_analyse["Correct Match "].replace({
    "Network Service": "Network Services"
})

def extract_description(val):
    try:
        # Convert string representation of dict to actual dict
        # ast.literal_eval is safer than eval() for strings like "{'key': 'val'}"
        d = ast.literal_eval(val)
        return d.get('description', '')
    except (ValueError, SyntaxError, AttributeError):
        return ""
data_to_analyse['clean_description'] = data_to_analyse['ContractDescription'].apply(extract_description)


grouped_data = data_to_analyse.groupby("Correct Match ")

registry = {}

for category, group in grouped_data:
    print(f"Processing category: {category}")

    # Combine all descriptions into one large text block for the LLM
    primary_store = []
    secondary_store = []
    for text in group['clean_description'].tolist():
        print(f" text: {text}")
        primary, secondary = keywords_finder_llm(text)
        primary_store.extend(primary)
        secondary_store.extend(secondary)


    registry[category] = {"primary": primary_store, "secondary": secondary_store}

# --- GLOBAL DE-DUPLICATION (The Change) ---

# 1. Map every primary word to the categories that claim it
word_ownership = {}
for cat, content in registry.items():
    for word in content["primary"]:
        word_clean = word.lower().strip()
        if word_clean not in word_ownership:
            word_ownership[word_clean] = []
        word_ownership[word_clean].append(cat)

# 2. Identify and resolve conflicts
for cat in list(registry.keys()):
    orig_primary = registry[cat]["primary"]
    orig_secondary = registry[cat]["secondary"]

    final_primary = []
    final_secondary = list(orig_secondary)  # Start with existing secondary

    for word in orig_primary:
        word_clean = word.lower().strip()
        # If more than one category claimed this word, demote it
        if len(word_ownership[word_clean]) > 1:
            if word not in final_secondary:
                final_secondary.append(word)
            print(f"Demoting contested word '{word}' from Primary to Secondary in {cat}")
        else:
            final_primary.append(word)

    # Update registry with cleaned lists
    registry[cat] = [final_primary, final_secondary]

# --- FINAL SAVE ---
with open(registry_path, "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=4, ensure_ascii=False)

    print(f"Successfully saved {len(registry)} deduplicated categories to {registry_path}")