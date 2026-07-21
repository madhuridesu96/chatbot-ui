import sqlite3
import pandas as pd

# Load both CSVs into DataFrames (a DataFrame is just pandas' term for a table)
plans = pd.read_csv("data/plans.csv")
claims = pd.read_csv("data/claims.csv")

# Inspect plans
print("=== PLANS INFO ===")
print(plans.info())
print("\n=== PLANS HEAD ===")
print(plans.head())

# Inspect claims
print("\n=== CLAIMS INFO ===")
print(claims.info())
print("\n=== CLAIMS HEAD ===")
print(claims.head())
# --- Cleaning ---

# Drop exact duplicate rows, if any
plans = plans.drop_duplicates()
claims = claims.drop_duplicates()

# Fill or drop nulls (since we saw 0 nulls, this is precautionary/defensive)
plans = plans.dropna()
claims = claims.dropna()

# Convert date_filed from text to an actual datetime type
claims["date_filed"] = pd.to_datetime(claims["date_filed"])

# Confirm the cleaning worked
print("\n=== CLEANED CLAIMS INFO ===")
print(claims.info())
print("\n=== CLEANED CLAIMS HEAD ===")
print(claims.head())
# --- Load into SQLite database ---

# Create (or connect to) the database file
conn = sqlite3.connect("coverage.db")

# Write each cleaned DataFrame into its own table
plans.to_sql("plans", conn, if_exists="replace", index=False)
claims.to_sql("claims", conn, if_exists="replace", index=False)

conn.close()

print("\n✅ coverage.db created with 'plans' and 'claims' tables")