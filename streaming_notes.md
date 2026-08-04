# Streaming Notes — Day 18

## UX Confirmation

Directly tested and confirmed: the assistant's response visibly "types out" word by word in the browser, using st.empty() updated in a loop as each SSE token arrives. A "▌" cursor character is appended during active streaming to indicate the response is still in progress, and removed once the stream completes. A brief st.spinner("Thinking...") shows before the first token arrives, so the user isn't staring at a blank screen while the backend performs retrieval and starts generation.

## Timeout Handling

requests.post(..., timeout=30) is used on the frontend. If no response arrives within 30 seconds, a requests.exceptions.Timeout is raised and caught, displaying a friendly message: "The response took too long. Please try again." This prevents the UI from hanging indefinitely if the backend or LLM becomes unresponsive.

## Dropped Connection / Mid-Stream Error Handling

Backend side: The entire retrieval and generation process is wrapped in a try/except inside the streaming generator function. On failure, instead of crashing the stream ungracefully, it yields a properly formatted SSE error payload: data: {"error": "..."}, allowing the frontend to receive a clean, parseable error even mid-stream.

Frontend side: Each parsed SSE payload is checked for an "error" key. If present, the partial response is replaced with the error message, displayed in the chat bubble, and the streaming loop breaks cleanly rather than continuing to wait for more data that will never arrive.

General connection failures (e.g., backend server not running at all) are caught separately via requests.exceptions.RequestException, showing "Could not reach the backend."

## Real Testing Observations

Successfully tested multiple structured questions (deductible, claim status) and unstructured questions (claims appeal process, coverage questions) - both streamed correctly with visible token-by-token output.

One question ("Can you explain what a deductible, copay, and coinsurance each mean?") returned an honest "I don't know" despite the knowledge base likely containing relevant general definitions - noted as a retrieval quality observation for potential future improvement, separate from the streaming mechanics themselves, which functioned correctly throughout.

A backend bug was found and fixed during implementation: an initial NameError: name 'json' is not defined occurred because the json import was missing from main.py. This caused the stream to fail mid-response, closing the connection unexpectedly (curl: (18) transfer closed with outstanding read data remaining) - a real, first-hand example of the exact kind of mid-stream failure this step's error handling is designed to gracefully catch. Adding import json resolved it.