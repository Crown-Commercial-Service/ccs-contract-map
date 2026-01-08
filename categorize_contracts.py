import pandas as pd
from contract_mapping_v2 import contract_mapper_v2
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import argparse
import functools

def process_contract(args, title_col, desc_col):
    """Helper function to process a single contract row."""
    index, row = args
    title = str(row[title_col]).strip()
    description = str(row[desc_col]).strip()

    user_contract_description = title
    if description and description.lower() != 'na':  # Assuming 'NA' is used for no description
        user_contract_description = f"{title}. {description}"
    
    category = contract_mapper_v2(user_contract_description=user_contract_description)
    return index, category

def categorize_contracts(
    input_csv_path: str, 
    output_csv_path: str,
    status_col: str = 'Is it inflight',
    status_val: str = 'Inflight',
    title_col: str = 'Contract Name',
    desc_col: str = 'Contract Description'
):
    """
    Categorizes contracts from a dataset based on their title and description using parallel processing.
    Only contracts with a specific status are categorized; others are marked 'Not Categorised'.
    """
    
    # Load the dataset, suppressing the DtypeWarning
    df = pd.read_csv(input_csv_path, low_memory=False)
    
    # Clean up column names by stripping whitespace
    df.columns = df.columns.str.strip()

    # Initialize a new 'Category' column
    df['Category'] = 'Not Categorised'

    # Filter for contracts to process
    if status_col in df.columns:
        contracts_to_process = df[df[status_col] == status_val]
    else:
        print(f"Warning: Status column '{status_col}' not found. Processing all rows.")
        contracts_to_process = df

    # Use ThreadPoolExecutor to parallelize API calls
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of arguments for the process_contract function
        tasks = contracts_to_process.iterrows()
        
        # Create a partial function to pass column names
        worker_func = functools.partial(process_contract, title_col=title_col, desc_col=desc_col)

        # Map the function to the tasks and get results
        desc = "Categorizing Contracts"
        results = list(tqdm(executor.map(worker_func, tasks), total=len(contracts_to_process), desc=desc))

    # Update the DataFrame with the categorized results
    for index, category in results:
        df.loc[index, 'Category'] = category
        
    # Save the categorized DataFrame to a new CSV file
    df.to_csv(output_csv_path, index=False)
    print(f"Categorization complete. Results saved to {output_csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categorize contracts from a CSV file.")
    parser.add_argument("input_file", help="The path to the input CSV file.")
    parser.add_argument("output_file", help="The path to save the output CSV file.")
    parser.add_argument("--status_col", default="Is it inflight", help="Name of the column indicating contract status.")
    parser.add_argument("--status_val", default="Inflight", help="Value in status_col that indicates a contract should be processed.")
    parser.add_argument("--title_col", default="Contract Name", help="Name of the column with the contract title.")
    parser.add_argument("--desc_col", default="Contract Description", help="Name of the column with the contract description.")
    
    args = parser.parse_args()

    input_path = Path(args.input_file)
    
    # Ensure the input file exists before proceeding
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found.")
    else:
        categorize_contracts(
            str(input_path), 
            args.output_file,
            args.status_col,
            args.status_val,
            args.title_col,
            args.desc_col
        )
