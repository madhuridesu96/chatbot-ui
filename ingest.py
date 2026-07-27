import pandas as pd
import sqlite3

# --- Load ---
plans = pd.read_csv("data/plans.csv")
claims = pd.read_csv("data/claims.csv")
members = pd.read_csv("data/members.csv")

print("=== PLANS ===")
print(plans.info())
print(plans.head())
print("\n=== CLAIMS ===")
print(claims.info())
print(claims.head())
print("\n=== MEMBERS ===")
print(members.info())
print(members.head())

# --- Clean ---
plans = plans.drop_duplicates().dropna(subset=["plan_id"])
claims = claims.drop_duplicates()
members = members.drop_duplicates()


claims["date_filed"] = pd.to_datetime(claims["date_filed"])
claims["date_processed"] = pd.to_datetime(claims["date_processed"], errors="coerce")
members["enrollment_date"] = pd.to_datetime(members["enrollment_date"])
members["date_of_birth"] = pd.to_datetime(members["date_of_birth"])

# --- Load into SQLite ---
conn = sqlite3.connect("coverage.db")
plans.to_sql("plans", conn, if_exists="replace", index=False)
claims.to_sql("claims", conn, if_exists="replace", index=False)
conn.close()

print("\n✅ coverage.db rebuilt with plans, claims")