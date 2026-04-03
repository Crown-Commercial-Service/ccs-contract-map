import pandas as pd
import asyncio
import ast
from pathlib import Path
from src.core.classification_v2_mix_v5 import keywords_and_llm

# --- Configuration & Data Loading ---
file_path = "AI Catrgorisation Testing Notes2.xlsx"
data = pd.read_excel(file_path)

# Cleaning logic based on your specific row indices
drop_1 = data.iloc[0:8].index
drop_2 = data.iloc[170:181].index
all_to_drop = drop_1.union(drop_2)
new_data = data.drop(all_to_drop)

# Filter for labeled data and take a sample for testing
data_to_analyse = new_data[new_data["Correct Match "].notna()].iloc[0:30].copy()


async def run_classification_test(df):
    """
    Async loop to process each row through the Hybrid Classifier.
    """
    output_labels = []
    output_reasons = []

    print(f"Starting analysis on {len(df)} rows...")

    for index, row in df.iterrows():
        print(f"--- Processing Row: {index} ---")

        # 1. Safely parse the ContractDescription dictionary string
        try:
            description_raw = row["ContractDescription"]
            # Handle cases where it might already be a dict or needs parsing
            if isinstance(description_raw, str):
                description_dict = ast.literal_eval(description_raw)
            else:
                description_dict = description_raw

            clean_desc = description_dict.get("description", "")
        except (ValueError, SyntaxError, AttributeError) as e:
            print(f"Warning: Could not parse description at index {index}: {e}")
            clean_desc = str(row["ContractDescription"])

        # 2. Build the combined text for the classifier
        # We combine title and description for maximum keyword context
        contract_text = f"{row['contract_title']} : {clean_desc}"

        # 3. Call the Hybrid Classifier (AWAIT required for the LLM fallback)
        # result = category label, reason = "Heuristic Match" or "LLM Categorization"
        result, reason = await keywords_and_llm(contract_text)

        output_labels.append(result)
        output_reasons.append(reason)

        print(f"AI Prediction: {result}")
        print(f"Actual Label:  {row['Correct Match ']}")
        print(f"Method:        {reason}\n")

    # 4. Update the DataFrame and save
    df["AI_CategoryMatchV3"] = output_labels
    df["Classification_Method"] = output_reasons

    # Accuracy Calculations
    accuracy_series = df["AI_CategoryMatchV3"] == df["Correct Match "]
    correct_count = accuracy_series.sum()
    total_count = len(df)
    accuracy_pct = (correct_count / total_count) * 100
    old_model_correct_df = df[df["AI_CategoryMatch"] == df["Correct Match "]]
    print(f"--- Test Results ---")
    print(f"Total Analyzed: {total_count}")
    print(f"Correct Matches: {correct_count}")
    print(f"Accuracy: {accuracy_pct:.2f}%")
    print(f"Old model total correct matches: {len(old_model_correct_df)}")
    print(f"Old model total correct accuracy%: {len(old_model_correct_df)/total_count*100}%")

    # Save to Excel
    output_file = "new_AI_results.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    # This entry point starts the asyncio event loop
    asyncio.run(run_classification_test(data_to_analyse))