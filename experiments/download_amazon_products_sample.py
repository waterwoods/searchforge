#!/usr/bin/env python3
"""
Download and sample Amazon Products Dataset from Kaggle.

This script downloads the Amazon Products Dataset from Kaggle, filters for Electronics
products, samples 500-1000 records, and saves them in a standardized format.

Usage:
    1. Install dependencies:
       pip install kaggle pandas

    2. Configure Kaggle credentials (choose one):
       - Option A: Place credentials in ~/.kaggle/kaggle.json:
         {
           "username": "your_username",
           "key": "your_api_key"
         }
       - Option B: Set environment variables:
         export KAGGLE_USERNAME=your_username
         export KAGGLE_KEY=your_api_key

    3. Run the script:
       cd /home/andy/searchforge
       python -m experiments.download_amazon_products_sample

Output:
    - data/amazon/products_sample_2023.csv
      Contains 500-1000 Electronics products with columns:
      product_id, title, brand, category, price, rating, ratings_count,
      image_url, product_url
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        load_dotenv()  # Try default locations
except ImportError:
    pass  # python-dotenv not available, rely on system env vars

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas")
    sys.exit(1)

try:
    from kaggle.api.kaggle_api_extended import KaggleApi
except ImportError:
    print("Error: kaggle package is required. Install with: pip install kaggle")
    print("If kaggle is not available, please download the dataset manually and place")
    print("the CSV file in a temporary directory, then update this script.")
    sys.exit(1)

# Constants
KAGGLE_DATASET = "subbubana/amazon-products-dataset"
TEMP_DIR = Path(tempfile.gettempdir()) / "amazon_products_download"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "amazon"
OUTPUT_FILE = OUTPUT_DIR / "products_sample_2023.csv"
SAMPLE_SIZE = 1000
MIN_SAMPLE_SIZE = 500
RANDOM_STATE = 42

# Expected columns in the output CSV
OUTPUT_COLUMNS = [
    "product_id",
    "title",
    "brand",
    "category",
    "price",
    "rating",
    "ratings_count",
    "image_url",
    "product_url",
]

# Mapping from potential original column names to standardized names
# This will be populated based on actual dataset structure
COLUMN_MAPPING = {
    # Common variations
    "asin": "product_id",
    "product_id": "product_id",
    "id": "product_id",
    "product_name": "title",
    "name": "title",
    "title": "title",
    "brand": "brand",
    "main_category": "category",
    "category": "category",
    "categories": "category",
    "product_price": "price",
    "price": "price",
    "list_price": "price",
    "product_rating": "rating",
    "rating": "rating",
    "average_rating": "rating",
    "ratings_count": "ratings_count",
    "rating_count": "ratings_count",
    "number_of_reviews": "ratings_count",
    "reviews": "ratings_count",
    "image_url": "image_url",
    "image": "image_url",
    "imageURL": "image_url",
    "product_url": "product_url",
    "url": "product_url",
    "productURL": "product_url",
    "link": "product_url",
}


def is_electronics(row: pd.Series, category_col: Optional[str] = None) -> bool:
    """
    Check if a product belongs to Electronics category.

    Args:
        row: A pandas Series representing a product row
        category_col: Name of the category column (if None, will try to detect)

    Returns:
        True if the product is Electronics-related, False otherwise
    """
    if category_col is None:
        # Try common category column names (case-insensitive)
        for col_name in row.index:
            col_lower = col_name.lower()
            if "category" in col_lower:
                category_col = col_name
                break

    if category_col and category_col in row.index:
        category_value = str(row[category_col]).lower().strip()
        # Check for exact match or partial match
        if category_value == "electronics" or "electronic" in category_value:
            return True

    # If no category column found or no match, check title or other text fields
    title_col = None
    for col in ["title", "product_name", "name", "product name"]:
        if col in row.index:
            title_col = col
            break
    
    if title_col:
        title = str(row[title_col]).lower()
        electronics_keywords = [
            "headphone", "earphone", "speaker", "charger", "cable", "adapter",
            "keyboard", "mouse", "monitor", "laptop", "tablet", "phone",
            "camera", "tv", "television", "router", "modem", "processor",
            "memory", "storage", "usb", "bluetooth", "wireless", "battery",
            "electronic", "electronics", "samsung galaxy", "iphone", "pixel"
        ]
        return any(keyword in title for keyword in electronics_keywords)

    return False


def download_dataset() -> Path:
    """
    Download the Amazon Products Dataset from Kaggle.

    Returns:
        Path to the downloaded CSV file

    Raises:
        SystemExit: If download fails
    """
    print(f"Downloading dataset '{KAGGLE_DATASET}' from Kaggle...")

    # Check for Kaggle credentials
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    
    if not username or not key:
        print("Error: KAGGLE_USERNAME and KAGGLE_KEY environment variables not set.")
        print("Please set them in .env file or as environment variables.")
        sys.exit(1)
    
    # Set environment variables for Kaggle API (if not already set)
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = key

    # Create temporary directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        api = KaggleApi()
        api.authenticate()

        # Download dataset files
        api.dataset_download_files(
            KAGGLE_DATASET,
            path=str(TEMP_DIR),
            unzip=True
        )

        # Find the main CSV file
        csv_files = list(TEMP_DIR.glob("*.csv"))
        if not csv_files:
            print(f"Error: No CSV files found in {TEMP_DIR}")
            print(f"Files in temp directory: {list(TEMP_DIR.iterdir())}")
            sys.exit(1)

        # Use the largest CSV file (likely the main dataset)
        main_csv = max(csv_files, key=lambda p: p.stat().st_size)
        print(f"Found dataset file: {main_csv.name} ({main_csv.stat().st_size / 1024 / 1024:.2f} MB)")

        return main_csv

    except Exception as e:
        print(f"Error downloading dataset: {e}")
        print("\nPlease check your Kaggle credentials:")
        print("  - Ensure ~/.kaggle/kaggle.json exists with username and key")
        print("  - Or set KAGGLE_USERNAME and KAGGLE_KEY environment variables")
        print(f"\nYou can also manually download from: https://www.kaggle.com/datasets/{KAGGLE_DATASET}")
        sys.exit(1)


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse price string to float.

    Args:
        price_str: Price as string (may contain currency symbols, commas, etc.)

    Returns:
        Float price or None if parsing fails
    """
    if pd.isna(price_str) or price_str == "":
        return None

    try:
        # Remove currency symbols and commas
        price_clean = str(price_str).replace("$", "").replace(",", "").strip()
        # Try to extract first number
        import re
        match = re.search(r"(\d+\.?\d*)", price_clean)
        if match:
            return float(match.group(1))
    except (ValueError, AttributeError):
        pass

    return None


def clean_and_normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize the raw dataset.

    Args:
        df: Raw DataFrame from Kaggle

    Returns:
        Cleaned DataFrame with standardized columns
    """
    print(f"\nCleaning data: {len(df)} rows, {len(df.columns)} columns")
    print(f"Available columns: {list(df.columns)}")

    # Detect column mappings with improved matching
    detected_mapping = {}
    used_orig_cols = set()
    
    # Explicit mappings for common patterns (ordered by priority)
    mapping_rules = {
        "product_id": ["asin", "product_id", "id"],
        "title": ["product name", "name", "title", "product_name"],
        "brand": ["brand"],
        "category": ["product category", "category", "main_category", "categories"],
        "price": ["product price", "price", "product_price", "list_price"],
        "rating": ["product rating", "rating", "product_rating", "average_rating"],
        "ratings_count": ["total ratings", "ratings_count", "rating_count", "number_of_reviews", "reviews"],
        "image_url": ["product image", "image_url", "image", "imageurl"],
        "product_url": ["product url", "product_url", "url", "producturl", "link"],
    }
    
    # First pass: exact matches
    for std_col, possible_names in mapping_rules.items():
        for orig_col in df.columns:
            if orig_col in used_orig_cols:
                continue
            orig_col_lower = orig_col.lower().strip()
            for possible_name in possible_names:
                if orig_col_lower == possible_name.lower():
                    detected_mapping[orig_col] = std_col
                    used_orig_cols.add(orig_col)
                    break
            if orig_col in detected_mapping:
                break
    
    # Second pass: partial matches (for columns not yet mapped)
    for std_col, possible_names in mapping_rules.items():
        if std_col in detected_mapping.values():
            continue  # Already mapped
        for orig_col in df.columns:
            if orig_col in used_orig_cols:
                continue
            orig_col_lower = orig_col.lower().strip()
            for possible_name in possible_names:
                if possible_name.lower() in orig_col_lower or orig_col_lower in possible_name.lower():
                    detected_mapping[orig_col] = std_col
                    used_orig_cols.add(orig_col)
                    break
            if orig_col in detected_mapping:
                break
    
    # Handle Unnamed: 0 as product_id if not already mapped
    if "Unnamed: 0" in df.columns and "Unnamed: 0" not in detected_mapping:
        if "product_id" not in detected_mapping.values():
            detected_mapping["Unnamed: 0"] = "product_id"
        used_orig_cols.add("Unnamed: 0")

    # Create new DataFrame with standardized columns
    result = pd.DataFrame()
    for orig_col, std_col in detected_mapping.items():
        result[std_col] = df[orig_col]
    
    print(f"Mapped columns: {detected_mapping}")
    print(f"Result columns after mapping: {list(result.columns)}")

    # If product_id is missing, create one from index
    if "product_id" not in result.columns:
        if "asin" in df.columns:
            result["product_id"] = df["asin"]
        else:
            result["product_id"] = df.index.astype(str)

    # Parse and clean price
    if "price" in result.columns:
        result["price"] = result["price"].apply(parse_price)
    elif "product_price" in df.columns or any("price" in col.lower() for col in df.columns):
        price_col = next((col for col in df.columns if "price" in col.lower()), None)
        if price_col:
            result["price"] = df[price_col].apply(parse_price)

    # Ensure numeric columns are properly typed
    if "rating" in result.columns:
        result["rating"] = pd.to_numeric(result["rating"], errors="coerce")
    if "ratings_count" in result.columns:
        result["ratings_count"] = pd.to_numeric(result["ratings_count"], errors="coerce").astype("Int64")

    # Fill missing optional columns
    for col in ["brand", "rating", "ratings_count"]:
        if col not in result.columns:
            result[col] = None

    # Drop rows with missing critical fields (only drop if columns exist)
    before_drop = len(result)
    required_cols = [col for col in ["title", "image_url", "price"] if col in result.columns]
    if required_cols:
        result = result.dropna(subset=required_cols)
        after_drop = len(result)
        if before_drop != after_drop:
            print(f"Dropped {before_drop - after_drop} rows with missing required fields: {required_cols}")
    else:
        print("Warning: No required columns found for filtering")

    # Fill empty strings with None for optional fields
    for col in ["brand"]:
        if col in result.columns:
            result[col] = result[col].replace("", None)

    return result


def filter_electronics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter DataFrame to only include Electronics products.

    Args:
        df: Cleaned DataFrame

    Returns:
        Filtered DataFrame with only Electronics products
    """
    print(f"\nFiltering for Electronics products...")

    # Detect category column (case-insensitive)
    category_col = None
    for col in df.columns:
        col_lower = col.lower()
        if "category" in col_lower or "subcategory" in col_lower:
            category_col = col
            break

    if category_col:
        print(f"Using category column: {category_col}")

    # Apply filter
    electronics_mask = df.apply(lambda row: is_electronics(row, category_col), axis=1)
    filtered_df = df[electronics_mask].copy()

    print(f"Filtered from {len(df)} to {len(filtered_df)} Electronics products")

    return filtered_df


def sample_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sample 500-1000 records from the DataFrame.

    Args:
        df: Filtered DataFrame

    Returns:
        Sampled DataFrame
    """
    print(f"\nSampling data...")

    if len(df) > SAMPLE_SIZE:
        sampled = df.sample(n=SAMPLE_SIZE, random_state=RANDOM_STATE)
        print(f"Sampled {SAMPLE_SIZE} from {len(df)} products")
    elif len(df) >= MIN_SAMPLE_SIZE:
        sampled = df.copy()
        print(f"Using all {len(df)} products (within target range)")
    else:
        sampled = df.copy()
        print(f"Warning: Only {len(df)} products available (target: {MIN_SAMPLE_SIZE}-{SAMPLE_SIZE})")

    return sampled


def main():
    """Main execution function."""
    print("=" * 70)
    print("Amazon Products Dataset Download & Sample Script")
    print("=" * 70)

    # Step 1: Download dataset
    csv_path = download_dataset()

    # Step 2: Load raw data
    print(f"\nLoading data from {csv_path.name}...")
    try:
        df_raw = pd.read_csv(csv_path, low_memory=False)
        print(f"Loaded {len(df_raw)} raw rows")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Step 3: Clean and normalize
    df_clean = clean_and_normalize_data(df_raw)

    # Step 4: Filter Electronics
    df_electronics = filter_electronics(df_clean)

    if len(df_electronics) == 0:
        print("\nError: No Electronics products found after filtering.")
        print("The dataset structure may be different than expected.")
        print("Please check the column names and update the filtering logic.")
        sys.exit(1)

    # Step 5: Sample
    df_sample = sample_data(df_electronics)

    # Step 6: Ensure all required columns exist
    for col in OUTPUT_COLUMNS:
        if col not in df_sample.columns:
            df_sample[col] = None

    # Reorder columns
    df_sample = df_sample[OUTPUT_COLUMNS]

    # Step 7: Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df_sample.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(df_sample)} products to {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")

    # Step 8: Print summary
    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  - Loaded {len(df_raw)} raw rows")
    print(f"  - Filtered to {len(df_electronics)} Electronics products")
    print(f"  - Sampled {len(df_sample)} rows")
    print(f"  - Output: {OUTPUT_FILE}")
    print("=" * 70)

    # Cleanup temporary directory
    if TEMP_DIR.exists():
        try:
            shutil.rmtree(TEMP_DIR)
            print(f"\nCleaned up temporary directory: {TEMP_DIR}")
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory: {e}")


if __name__ == "__main__":
    main()
