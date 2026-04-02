ACT AS A DATA CLASSIFIER.

CONTRACT DESCRIPTION:
{{contract_description}}


RULES TO FOLLOW:
{{relevant_rules}}

# EXTRACTION RULE
In the "RULES TO FOLLOW" section, each rule begins with a header formatted as:
"--- CATEGORY: [CATEGORY_NAME] ---"

# TASK
1. Analyze the CONTRACT DESCRIPTION against the provided RULES.
2. Identify the single best matching CATEGORY from the provided rules.
3. Extract ONLY the [CATEGORY_NAME] from that rule's header.
4. If the CONTRACT DESCRIPTION does not fit any of the provided CATEGORIES, or if it matches an 'Exclusion' for all provided categories, return "Outside New Taxonomy".

# CRITICAL CONSTRAINTS
- Return ONLY the clean [CATEGORY_NAME] (e.g., "Software", "Construction").
- DO NOT include the Framework Title, RM numbers, or any text appearing after the header (e.g., do NOT return "Software - Back Office Software 2 (RM6285)").
- Your response must be a single phrase/category name with no preamble or punctuation.