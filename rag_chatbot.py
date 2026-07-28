from openai import OpenAI
from retrieval_engine import retrieve

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

GROUNDING_PROMPT = """Answer using ONLY the context below.
If the answer isn't in the context, say you don't know and suggest the member contact support.
This is not medical advice.

Context: {context}

Question: {question}
"""

def generate_answer(question, context):
    """Generate a grounded answer using ONLY the provided context."""
    context_text = "\n".join(context) if isinstance(context, list) else str(context)
    prompt = GROUNDING_PROMPT.format(context=context_text, question=question)

    response = client.chat.completions.create(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
def generate_answer_streaming(question, context):
    """Same as generate_answer, but streams tokens as they arrive."""
    context_text = "\n".join(context) if isinstance(context, list) else str(context)
    prompt = GROUNDING_PROMPT.format(context=context_text, question=question)

    stream = client.chat.completions.create(
        model="llama3.1",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    full_answer = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
            full_answer += delta
    print()
    return full_answer

def retrieve_and_answer(question):
    """Full RAG pipeline: retrieve context, then generate a grounded answer."""
    result = retrieve(question)
    answer = generate_answer(question, result["context"])
    return {
        "question": question,
        "classification": result["classification"],
        "context": result["context"],
        "answer": answer,
    }

if __name__ == "__main__":
    test = retrieve_and_answer("What's the deductible on the Gold Complete PPO plan?")
    print("Question:", test["question"])
    print("Classification:", test["classification"])
    print("\nAnswer:", test["answer"])
    print("\n\n=== STREAMING TEST ===")
    question2 = "What's the claims appeal process?"
    result = retrieve(question2)
    print(f"Question: {question2}\n")
    generate_answer_streaming(question2, result["context"])