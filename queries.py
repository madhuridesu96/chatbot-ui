import sqlite3

conn = sqlite3.connect("coverage.db")
cursor = conn.cursor()

# Question 1: What's the deductible on the Gold PPO plan?
print("=== Q1: Deductible on Gold PPO plan ===")
cursor.execute("SELECT plan_name, annual_deductible FROM plans WHERE plan_name = 'Gold PPO'")
print(cursor.fetchall())

# Question 2: How many claims are pending for member M1001?
print("\n=== Q2: Pending claims for member M1001 ===")
cursor.execute("""
    SELECT COUNT(*) FROM claims
    WHERE member_id = 'M1001' AND status = 'Pending'
""")
print(cursor.fetchall())

# Question 3: Which plans have a monthly premium under $400?
print("\n=== Q3: Plans with monthly premium under $400 ===")
cursor.execute("SELECT plan_name, monthly_premium FROM plans WHERE monthly_premium < 400")
print(cursor.fetchall())

# Question 4: A JOIN between claims and plans
print("\n=== Q4: Claims joined with plan details ===")
cursor.execute("""
    SELECT claims.claim_id, claims.member_id, claims.procedure,
           claims.claim_amount, plans.plan_name
    FROM claims
    JOIN plans ON claims.plan_id = plans.plan_id
""")
print(cursor.fetchall())

# Question 5: A top-N query (most claimed procedures)
print("\n=== Q5: Most claimed procedures (by total amount) ===")
cursor.execute("""
    SELECT procedure, SUM(claim_amount) as total_amount
    FROM claims
    GROUP BY procedure
    ORDER BY total_amount DESC
    LIMIT 3
""")
print(cursor.fetchall())

conn.close()