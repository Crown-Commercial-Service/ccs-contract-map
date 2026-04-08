import pandas as pd
from pathlib import Path
import ast
from src.utils.llm_keywords_finder import keywords_finder_llm
import json

# --- CONFIGURATION ---
corpus_location = Path(__file__).parents[2] / "AI Catrgorisation Testing Notes.xlsx"
registry_path = Path(__file__).parents[2] / "semantic_anchors4.json"

# --- DATA PREPARATION ---
data = pd.read_excel(str(corpus_location))
data_to_analyse = data[data["Correct Match "].notna()].copy()

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
        d = ast.literal_eval(val)
        return d.get('description', '')
    except (ValueError, SyntaxError, AttributeError):
        return ""


data_to_analyse['clean_description'] = data_to_analyse['ContractDescription'].apply(extract_description)

# --- KEYWORD EXTRACTION LOOP ---
grouped_data = data_to_analyse.groupby("Correct Match ")
registry = {}

for category, group in grouped_data:
    print(f"Processing category: {category}")
    primary_store = set()
    secondary_store = set()

    for text in group['clean_description'].tolist():
        # Using the LLM to find keywords for each individual contract
        primary, secondary = keywords_finder_llm(text)
        primary_store.update(primary)
        secondary_store.update(secondary)

    registry[category] = {"primary": list(primary_store), "secondary": list(secondary_store)}

# --- 1. GLOBAL DE-DUPLICATION ---
word_ownership = {}
for cat, content in registry.items():
    for word in content["primary"]:
        word_clean = word.lower().strip()
        if word_clean not in word_ownership:
            word_ownership[word_clean] = []
        word_ownership[word_clean].append(cat)

for cat in list(registry.keys()):
    orig_primary = registry[cat]["primary"]
    orig_secondary = registry[cat]["secondary"]
    final_primary = []
    final_secondary = list(orig_secondary)

    for word in orig_primary:
        word_clean = word.lower().strip()
        if len(word_ownership[word_clean]) > 1:
            if word not in final_secondary:
                final_secondary.append(word)
        else:
            final_primary.append(word)

    registry[cat] = [final_primary, final_secondary]

# --- 2. OUTSIDE TAXONOMY PURGE ---
# Ensures "Outside New Taxonomy" doesn't claim words belonging to real categories
if "Outside New Taxonomy" in registry:
    real_category_words = set()
    for cat, content in registry.items():
        if cat != "Outside New Taxonomy":
            real_category_words.update([w.lower().strip() for w in content[0]])  # Primary
            real_category_words.update([w.lower().strip() for w in content[1]])  # Secondary

    o_primary, o_secondary = registry["Outside New Taxonomy"]

    # Remove words from 'Outside' if they exist anywhere else in the real taxonomy
    registry["Outside New Taxonomy"] = [
        [w for w in o_primary if w.lower().strip() not in real_category_words],
        [w for w in o_secondary if w.lower().strip() not in real_category_words]
    ]
    print("Purged overlapping keywords from 'Outside New Taxonomy'.")

# --- 3. GLOBAL FREQUENCY FILTER (NOISE CANCELLATION) ---
# If a word appears in more than 3 categories total, it's generic noise and should be deleted
global_word_frequency = {}
for cat, content in registry.items():
    all_words = set(content[0] + content[1])
    for word in all_words:
        w_clean = word.lower().strip()
        global_word_frequency[w_clean] = global_word_frequency.get(w_clean, 0) + 1

MAX_CATEGORIES = 3
final_cleaned_registry = {}

for cat, (primary, secondary) in registry.items():
    clean_p = [w for w in primary if global_word_frequency[w.lower().strip()] <= MAX_CATEGORIES]
    clean_s = [w for w in secondary if global_word_frequency[w.lower().strip()] <= MAX_CATEGORIES]
    final_cleaned_registry[cat] = [clean_p, clean_s]

# --- FINAL SAVE ---
with open(registry_path, "w", encoding="utf-8") as f:
    json.dump(final_cleaned_registry, f, indent=4, ensure_ascii=False)

print(f"Successfully saved {len(final_cleaned_registry)} cleaned categories to {registry_path}")
# import  pandas as pd
# from pathlib import Path
# import ast
# from src.utils.llm_keywords_finder import keywords_finder_llm
# import json
#
# corpus_location = Path(__file__).parents[2] / "AI Catrgorisation Testing Notes.xlsx"
# registry_path = Path(__file__).parents[2] / "semantic_anchors3.json"
#
# data = pd.read_excel(str(corpus_location))
# data_to_analyse = data[data["Correct Match "].notna()]
# data_to_analyse["Correct Match "] = (
#     data_to_analyse["Correct Match "]
#     .astype(str)
#     .str.replace(r"\s*&\s*", " and ", regex=True)
#     .str.strip()
# )
#
# data_to_analyse["Correct Match "] = data_to_analyse["Correct Match "].replace({
#     "Network Service": "Network Services"
# })
#
# def extract_description(val):
#     try:
#         # Convert string representation of dict to actual dict
#         # ast.literal_eval is safer than eval() for strings like "{'key': 'val'}"
#         d = ast.literal_eval(val)
#         return d.get('description', '')
#     except (ValueError, SyntaxError, AttributeError):
#         return ""
# data_to_analyse['clean_description'] = data_to_analyse['ContractDescription'].apply(extract_description)
#
#
# grouped_data = data_to_analyse.groupby("Correct Match ")
#
# registry = {}
#
# for category, group in grouped_data:
#     print(f"Processing category: {category}")
#
#     # Combine all descriptions into one large text block for the LLM
#     primary_store = []
#     secondary_store = []
#     for text in group['clean_description'].tolist():
#         print(f" text: {text}")
#         primary, secondary = keywords_finder_llm(text)
#         primary_store.extend(primary)
#         secondary_store.extend(secondary)
#
#
#     registry[category] = {"primary": primary_store, "secondary": secondary_store}
#
# # --- GLOBAL DE-DUPLICATION (The Change) ---
#
# # 1. Map every primary word to the categories that claim it
# word_ownership = {}
# for cat, content in registry.items():
#     for word in content["primary"]:
#         word_clean = word.lower().strip()
#         if word_clean not in word_ownership:
#             word_ownership[word_clean] = []
#         word_ownership[word_clean].append(cat)
#
# # 2. Identify and resolve conflicts
# for cat in list(registry.keys()):
#     orig_primary = registry[cat]["primary"]
#     orig_secondary = registry[cat]["secondary"]
#
#     final_primary = []
#     final_secondary = list(orig_secondary)  # Start with existing secondary
#
#     for word in orig_primary:
#         word_clean = word.lower().strip()
#         # If more than one category claimed this word, demote it
#         if len(word_ownership[word_clean]) > 1:
#             if word not in final_secondary:
#                 final_secondary.append(word)
#             print(f"Demoting contested word '{word}' from Primary to Secondary in {cat}")
#         else:
#             final_primary.append(word)
#
#     # Update registry with cleaned lists
#     registry[cat] = [final_primary, final_secondary]
#
# # --- FINAL SAVE ---
# with open(registry_path, "w", encoding="utf-8") as f:
#     json.dump(registry, f, indent=4, ensure_ascii=False)
#
#     print(f"Successfully saved {len(registry)} deduplicated categories to {registry_path}")