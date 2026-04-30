import pandas as pd
import asyncio
import ast
from src.core.classification_v2_mix_v5 import keywords_and_llm


# --- Configuration & Data Loading ---
file_path = "new_AI_results_for_Jasmine.xlsx"
data = pd.read_excel(file_path)

# 1. Clean the 'Correct Match' column
# This converts '&' to 'and' and removes extra trailing spaces
data["Correct Match "] = (
    data["Correct Match "]
    .astype(str)
    .str.replace(r"\s*&\s*", " and ", regex=True)
    .str.replace(r"\s+", " ", regex=True)  # Remove double spaces
    .str.strip()
)

# 2. Fix specific singular/plural or inconsistent names
# Based on your failure list, standardise these specific strings
normalization_map = {
    "Network Service": "Network Services",
    "Cloud & Hosting": "Cloud and Hosting",
    "HR & Workforce Services": "HR and Workforce Services",
    "Digital & Technology Services": "Digital and Technology Services",
}

data["Correct Match "] = data["Correct Match "].replace(normalization_map)
data["AI_CategoryMatch"] = data["AI_CategoryMatch"].replace(normalization_map)


async def run_classification_test(df):
    """
    Async loop to process each row through the Hybrid Classifier.
    """
    output_labels = []
    wrong_results = {}

    print(f"Starting analysis on {len(df)} rows...")

    for index, row in df.iterrows():
        print(f"--- Processing Row: {index} ---")

        # Safely parse the ContractDescription dictionary string
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

        # Build the combined text for the classifier
        # Combine title and description for maximum keyword context
        contract_text = f"{row['contract_title']} : {clean_desc}"

        result, reason = await keywords_and_llm(
            description=contract_text, threshold=10, margin=0
        )

        if result != row["Correct Match "]:
            wrong_results[str(index)] = {
                "description": row["ContractDescription"],
                "AI_label": result,
                "Actual_label": row["Correct Match "],
            }

        output_labels.append(result)

        print(f"AI Prediction: {result}")
        print(f"Actual Label:  {row['Correct Match ']}")

    # Update the DataFrame and save
    df["AI_CategoryMatchV3"] = output_labels

    # Accuracy Calculations
    accuracy_series = df["AI_CategoryMatchV3"] == df["Correct Match "]
    correct_count = accuracy_series.sum()
    total_count = len(df)
    accuracy_pct = (correct_count / total_count) * 100
    old_model_correct_df = df[df["AI_CategoryMatch"] == df["Correct Match "]]
    print("--- Test Results ---")
    print(f"Total Analyzed: {total_count}")
    print(f"Correct Matches: {correct_count}")
    print(f"Accuracy: {accuracy_pct:.2f}%")
    print(f"Old model total correct matches: {len(old_model_correct_df)}")
    print(
        f"Old model total correct accuracy%: {len(old_model_correct_df)/total_count*100}%"
    )

    output_file = "new_AI_results_keywords_llm.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")
    print(wrong_results)
    print()
    print(len(wrong_results))


if __name__ == "__main__":
    asyncio.run(run_classification_test(data))
