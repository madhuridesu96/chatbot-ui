from pydantic import BaseModel
from typing import Optional

class ClaimStatusCard(BaseModel):
    claim_id: str
    status: str
    amount: float
    date: Optional[str] = None

class CoverageSummaryCard(BaseModel):
    plan_name: str
    deductible: float
    copay: float
    covered: bool