import json
import sqlite3
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from typing import Optional

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

SYSTEM_PROMPT = """You are a health plan coverage assistant. Answer using ONLY the exact plan terms provided in the context below. Cite specific numbers, percentages, and plan names precisely as they appear.

When a tool returns data, use ONLY the exact fields and values in that tool's result. NEVER add specific numbers, percentages, page references, copay amounts, visit limits, or any other detail that is not explicitly present in the tool's returned data. If the tool result only confirms yes/no coverage with no further detail, state only that yes/no fact and nothing more.

If the requested information is not explicitly present in the context or tool result, let the member know clearly and kindly that this specific detail isn't available in their plan documentation, and suggest contacting member support for a complete answer.

You must NEVER call check_coverage, get_claim_status, get_plan_details, or estimate_out_of_pocket_cost for questions about medications, symptoms, diagnosis, or treatment recommendations. These questions require no tool. Respond directly and only: "I'm not able to provide medical advice — a licensed healthcare provider is the right person to help with that."

This is not medical advice.Do not invent reasons, plan nicknames, section references, or per-unit breakdowns (such as "per session" or "per visit") unless those exact words appear in the tool's returned data."""

# ---------- STEP 4: Pydantic models for tool outputs ----------

class CoverageResult(BaseModel):
    plan_id: str
    procedure: str
    covered: bool
    notes: Optional[str] = None

class ClaimStatusResult(BaseModel):
    claim_id: str
    member_id: str
    status: str
    procedure_description: str
    claim_amount: float

class PlanDetailsResult(BaseModel):
    plan_id: str
    plan_name: str
    monthly_premium: float
    annual_deductible: int
    network_type: str

class CostEstimateResult(BaseModel):
    plan_id: str
    procedure: str
    estimated_member_cost: float
    basis: str

# ---------- STEP 1: Tool schemas ----------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_coverage",
            "description": "Check whether a specific procedure is covered under a specific plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string", "description": "The plan ID, e.g. PLN-003"},
                    "procedure": {"type": "string", "description": "The procedure or service name, e.g. Physical Therapy"},
                },
                "required": ["plan_id", "procedure"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_claim_status",
            "description": "Get the status and details of a specific claim by its claim ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "The claim ID, e.g. C-2003"},
                },
                "required": ["claim_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_plan_details",
            "description": "Get premium, deductible, and network details for a specific plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string", "description": "The plan ID, e.g. PLN-003"},
                },
                "required": ["plan_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_out_of_pocket_cost",
            "description": "Estimate the member's out-of-pocket cost for a procedure under a specific plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_id": {"type": "string", "description": "The plan ID, e.g. PLN-003"},
                    "procedure": {"type": "string", "description": "The procedure or service name"},
                },
                "required": ["plan_id", "procedure"],
            },
        },
    },
]

# ---------- Tool implementations (against Day 4 data) ----------

def check_coverage(plan_id, procedure):
    conn = sqlite3.connect("coverage.db")
    cursor = conn.cursor()
    cursor.execute("SELECT covers_physical_therapy, covers_maternity, covers_mental_health, covers_dental FROM plans WHERE plan_id = ?", (plan_id,))
    row = cursor.fetchone()
    conn.close()

    covered = False
    notes = "No matching plan found."
    if row:
        pt, mat, mh, dental = row
        proc_lower = procedure.lower()
        if "physical therapy" in proc_lower:
            covered = (pt == "Yes")
        elif "maternity" in proc_lower:
            covered = (mat == "Yes")
        elif "mental" in proc_lower:
            covered = (mh == "Yes")
        elif "dental" in proc_lower:
            covered = (dental == "Yes")
        else:
            notes = "Coverage flag not available for this procedure type."
        notes = notes if not row else f"Based on plan coverage flags for {plan_id}."

    result = CoverageResult(plan_id=plan_id, procedure=procedure, covered=covered, notes=notes)
    return result

def get_claim_status(claim_id):
    conn = sqlite3.connect("coverage.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT claim_id, member_id, status, procedure_description, claim_amount FROM claims WHERE claim_id = ?",
        (claim_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"No claim found with ID {claim_id}")

    result = ClaimStatusResult(
        claim_id=row[0], member_id=row[1], status=row[2],
        procedure_description=row[3], claim_amount=row[4],
    )
    return result

def get_plan_details(plan_id):
    conn = sqlite3.connect("coverage.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT plan_id, plan_name, monthly_premium, annual_deductible, network_type FROM plans WHERE plan_id = ?",
        (plan_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"No plan found with ID {plan_id}")

    result = PlanDetailsResult(
        plan_id=row[0], plan_name=row[1], monthly_premium=row[2],
        annual_deductible=row[3], network_type=row[4],
    )
    return result

def estimate_out_of_pocket_cost(plan_id, procedure):
    conn = sqlite3.connect("coverage.db")
    cursor = conn.cursor()
    cursor.execute("SELECT annual_deductible, coinsurance_pct FROM plans WHERE plan_id = ?", (plan_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"No plan found with ID {plan_id}")

    deductible, coinsurance = row
    estimated = round(deductible * (coinsurance / 100), 2)

    result = CostEstimateResult(
        plan_id=plan_id, procedure=procedure,
        estimated_member_cost=estimated,
        basis=f"Estimated as {coinsurance}% coinsurance applied to deductible (mock estimate)",
    )
    return result

TOOL_FUNCTIONS = {
    "check_coverage": check_coverage,
    "get_claim_status": get_claim_status,
    "get_plan_details": get_plan_details,
    "estimate_out_of_pocket_cost": estimate_out_of_pocket_cost,
}

# ---------- STEP 3: Tool execution loop ----------

def run_with_tools(question, log_entries=None):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model="llama3.1",
        messages=messages,
        tools=TOOLS,
    )

    message = response.choices[0].message

    if not message.tool_calls:
        return {"question": question, "tool_used": None, "args": None, "result": None, "answer": message.content}

    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    func = TOOL_FUNCTIONS[tool_name]
    try:
        validated_result = func(**tool_args)
    except (ValidationError, ValueError) as e:
        validated_result = {"error": str(e)}

    result_data = validated_result.model_dump() if hasattr(validated_result, "model_dump") else validated_result

    if log_entries is not None:
        log_entries.append({"question": question, "tool": tool_name, "args": tool_args, "result": result_data})

    messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result_data),
    })

    final_response = client.chat.completions.create(
        model="llama3.1",
        messages=messages,
    )

    return {
        "question": question,
        "tool_used": tool_name,
        "args": tool_args,
        "result": result_data,
        "answer": final_response.choices[0].message.content,
    }

if __name__ == "__main__":
    test = run_with_tools("What's the deductible on plan PLN-003?")
    print(test)