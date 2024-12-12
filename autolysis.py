# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "matplotlib",
#   "requests",
# ]
# ///

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import requests

# AI Proxy configuration
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
API_TOKEN = os.environ.get("AIPROXY_TOKEN")

if not API_TOKEN:
    print("Error: AIPROXY_TOKEN environment variable not set.")
    exit(1)

def query_ai_proxy(prompt):
    """Query the AI Proxy with a prompt and return the response."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a data analysis assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Error querying AI Proxy: {e}")
        return None

# Function to load the dataset
def load_dataset(file_path):
    try:
        # Attempt to read the file with UTF-8 encoding
        data = pd.read_csv(file_path)
        return data
    except UnicodeDecodeError:
        print("UTF-8 decoding failed. Trying ISO-8859-1 encoding...")
        try:
            # Try with ISO-8859-1 encoding as a fallback
            data = pd.read_csv(file_path, encoding="ISO-8859-1")
            return data
        except Exception as e:
            print(f"Error loading dataset with fallback encoding: {e}")
            exit(1)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        exit(1)

# Function to perform generic analysis
def analyze_data(data):
    analysis = {}
    analysis['summary'] = data.describe(include='all').to_dict()
    analysis['missing_values'] = data.isnull().sum().to_dict()
    
    # Select only numeric columns for correlation matrix
    numeric_data = data.select_dtypes(include=['float64', 'int64'])
    if not numeric_data.empty:
        analysis['correlation'] = numeric_data.corr().to_dict()
    else:
        analysis['correlation'] = "No numeric columns available for correlation analysis."
    
    return analysis

# Function to visualize data
def create_visualizations(data, output_prefix):
    # Filter for numeric columns only
    numeric_data = data.select_dtypes(include=['float64', 'int64'])
    
    if not numeric_data.empty:
        # Correlation heatmap
        plt.figure(figsize=(10, 8))
        corr_matrix = numeric_data.corr()
        plt.imshow(corr_matrix, cmap="coolwarm", interpolation="none")
        plt.colorbar(label="Correlation")
        plt.title("Correlation Heatmap")
        plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns, rotation=45, ha="right")
        plt.yticks(range(len(corr_matrix.columns)), corr_matrix.columns)
        heatmap_file = f"{output_prefix}_heatmap.png"
        plt.savefig(heatmap_file, bbox_inches="tight")
        plt.close()
    else:
        print("No numeric columns available for correlation heatmap.")
        heatmap_file = None

    # Example scatter plot for numerical columns
    if len(numeric_data.columns) >= 2:
        plt.figure(figsize=(8, 6))
        plt.scatter(numeric_data.iloc[:, 0], numeric_data.iloc[:, 1], alpha=0.6)
        plt.xlabel(numeric_data.columns[0])
        plt.ylabel(numeric_data.columns[1])
        plt.title(f"Scatter Plot of {numeric_data.columns[0]} vs {numeric_data.columns[1]}")
        scatter_file = f"{output_prefix}_scatter.png"
        plt.savefig(scatter_file, bbox_inches="tight")
        plt.close()
    else:
        print("Not enough numeric columns for scatter plot.")
        scatter_file = None

    return [heatmap_file, scatter_file]

# Function to generate narrative
def create_narrative(data, analysis, charts):
    prompt = (
        f"The dataset has the following columns: {list(data.columns)}.\n"
        f"Summary statistics: {analysis['summary']}\n"
        f"Missing values: {analysis['missing_values']}\n"
        f"Correlation matrix: {analysis['correlation']}\n"
        f"Charts available: {charts}.\n"
        "Generate a story summarizing these findings and their implications."
    )
    return query_ai_proxy(prompt)

# Main function
def main():
    parser = argparse.ArgumentParser(description="Automated data analysis and storytelling.")
    parser.add_argument("csv_file", help="Path to the CSV file to analyze")
    args = parser.parse_args()

    # Load the dataset
    data = load_dataset(args.csv_file)

    # Perform analysis
    analysis = analyze_data(data)

    # Create visualizations
    output_prefix = os.path.splitext(os.path.basename(args.csv_file))[0]
    charts = create_visualizations(data, output_prefix)

    # Generate narrative
    narrative = create_narrative(data, analysis, charts)

    # Save narrative and embed images in README.md
    readme_content = f"""# Analysis of {args.csv_file}

## Key Findings
{narrative}

## Visualizations
"""
    for chart in charts:
        if chart:
            readme_content += f"![{chart}]({chart})\n"

    with open("README.md", "w") as f:
        f.write(readme_content)

    print("Analysis complete. Results saved to README.md and charts.")

if __name__ == "__main__":
    main()