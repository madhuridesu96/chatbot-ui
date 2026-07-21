# Structured Queries — Coverage Chatbot Data

Five SQL queries written and tested against `coverage.db`, mapped to realistic member questions.

## 1. What's the deductible on the Gold PPO plan?

```sql
SELECT plan_name, annual_deductible FROM plans WHERE plan_name = 'Gold PPO';
```

**Result:** Gold PPO — $2000 deductible

## 2. How many claims are pending for member M1001?

```sql
SELECT COUNT(*) FROM claims
WHERE member_id = 'M1001' AND status = 'Pending';
```

**Result:** 1 pending claim

## 3. Which plans have a monthly premium under $400?

```sql
SELECT plan_name, monthly_premium FROM plans WHERE monthly_premium < 400;
```

**Result:** Silver HMO ($300), Bronze HMO ($150)

## 4. JOIN — Claims with their plan details

```sql
SELECT claims.claim_id, claims.member_id, claims.procedure,
       claims.claim_amount, plans.plan_name
FROM claims
JOIN plans ON claims.plan_id = plans.plan_id;
```

**Result:** All 5 claims correctly matched to their plan names (e.g. C1001 → Gold PPO, C1003 → Silver HMO)

## 5. Top-N — Most claimed procedures by total amount

```sql
SELECT procedure, SUM(claim_amount) as total_amount
FROM claims
GROUP BY procedure
ORDER BY total_amount DESC
LIMIT 3;
```

**Result:** Surgery ($2100), X-ray ($450)