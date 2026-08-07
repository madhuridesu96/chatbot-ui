from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

from tool_calling_chatbot import get_claim_status, check_coverage, get_plan_details

# ---------- Step 3: LLM setup (pointing at local Ollama) ----------

llm = ChatOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="llama3.1",
    temperature=0,
    stop=["\nObservation"],
)

# ---------- Step 2: Wrap Day 13 tools as LangChain Tool objects ----------

def check_coverage_wrapper(input_str):
    """Input format: 'plan_id, procedure' e.g. 'PLN-005, Physical Therapy'"""
    try:
        cleaned = input_str.strip().strip("'\"")
        plan_id, procedure = [x.strip().strip("'\"") for x in input_str.split(",", 1)]
        result = check_coverage(plan_id, procedure)
        return f"{result.model_dump()} [This is the complete answer. Do not call this tool again. Proceed directly to Final Answer.]"
    
    except Exception as e:
        return f"Error: {e}"

def get_claim_status_wrapper(claim_id):
    """Input format: a claim ID, e.g. 'C-2003'"""
    try:
        cleaned_id = claim_id.strip().strip("'\"")
        result = get_claim_status(cleaned_id)
        return f"{result.model_dump()}[This is the complete answer. Do not call this tool again. Proceed directly to Final Answer.]"

    except Exception as e:
        return f"Error: {e}"

def get_plan_details_wrapper(plan_id):
    """Input format: a plan ID, e.g. 'PLN-003'"""
    try:
        cleaned_id = plan_id.strip().strip("'\"")
        result = get_plan_details(plan_id.strip())
        return f"{result.model_dump()} [This is the complete answer. Do not call this tool again. Proceed directly to Final Answer.]"

    except Exception as e:
        return f"Error: {e}"

tools = [
    Tool(
        name="check_coverage",
        func=check_coverage_wrapper,
        description="Check whether a specific procedure is covered under a specific plan. Input must be exactly: 'plan_id, procedure' (e.g. 'PLN-005, Physical Therapy'). Use this when a member asks if something is covered."
    ),
    Tool(
        name="get_claim_status",
        func=get_claim_status_wrapper,
        description="Get the status, procedure, and amount for a specific claim. Input must be exactly a claim ID (e.g. 'C-2003'). Use this when a member asks about the status of a specific claim."
    ),
    Tool(
        name="get_plan_details",
        func=get_plan_details_wrapper,
        description="Get premium, deductible, and network details for a specific plan. Input must be exactly a plan ID (e.g. 'PLN-003'). Use this when a member asks about their plan's cost or deductible."
    ),
]

# ---------- Step 3: Create the ReAct agent (manual prompt, no hub dependency) ----------

react_prompt_template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
Thought: I know the final answer
Final Answer: the final answer to the original input question
Example:
Question: What's the status of claim C-1001?
Thought: I need to look up this claim's status.
Action: get_claim_status
Action Input: C-1001
Observation: {{'status': 'Approved', 'claim_amount': 200.0}}
Thought: I now know the final answer
Final Answer: Claim C-1001 is Approved with an amount of $200.00.

IMPORTANT: After receiving ONE Observation with the data you need, immediately write "Thought: I now know the final answer" followed by "Final Answer:". Do NOT repeat the same Action twice.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
prompt = PromptTemplate.from_template(react_prompt_template)
agent = create_react_agent(llm, tools, prompt)  

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3,

)

if __name__ == "__main__":
    test_questions = [
        "What's the status of claim C-2003?",
        "Is physical therapy covered under plan PLN-005?",
        "What's the deductible on plan PLN-003?",
        "What medication should I take for a headache?",
        "Is dental coverage included under plan PLN-009?",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {question}")
        print(f"{'='*70}")
        try:
            result = agent_executor.invoke({"input": question})
            print(f"\nFINAL ANSWER: {result['output']}")
        except Exception as e:
            print(f"\nERROR: {e}")