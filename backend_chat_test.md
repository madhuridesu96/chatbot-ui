# Backend Chat Test — Day 16

Testing /chat and /history/{session_id} with a 3-message sequential session using the same session_id.

## Test 1: First message

Request:
curl -X POST http://127.0.0.1:8001/chat -H "Content-Type: application/json" -d '{"session_id": "test-session-1", "member_id": "M-1004", "message": "What is the deductible on the Gold Complete PPO plan?"}'

Response:
{"session_id":"test-session-1","classification":"structured","answer":"$1,500","elapsed_seconds":3.786}

## Test 2: Second message (same session_id)

Request:
curl -X POST http://127.0.0.1:8001/chat -H "Content-Type: application/json" -d '{"session_id": "test-session-1", "member_id": "M-1004", "message": "Is physical therapy covered under plan PLN-005?"}'

Response:
{"session_id":"test-session-1","classification":"unstructured","answer":"I don't know. The context does mention Acupuncture (if prescribed for rehabilitation) and outpatient services. It's best to contact support for clarification.","elapsed_seconds":4.197}

## Test 3: Third message (same session_id)

Request:
curl -X POST http://127.0.0.1:8001/chat -H "Content-Type: application/json" -d '{"session_id": "test-session-1", "member_id": "M-1004", "message": "What is the claims appeal process?"}'

Response:
{"session_id":"test-session-1","classification":"unstructured","answer":"The claims appeal process is explained in Step 6: Filing an Appeal. Members have 180 days from the denial notice to submit a written appeal.","elapsed_seconds":2.523}

## Test 4: Confirm /history reflects all 3 messages

Request:
curl http://127.0.0.1:8001/history/test-session-1

Response:
{"session_id":"test-session-1","turns":[
  {"role":"user","content":"What is the deductible on the Gold Complete PPO plan?"},
  {"role":"assistant","content":"$1,500"},
  {"role":"user","content":"Is physical therapy covered under plan PLN-005?"},
  {"role":"assistant","content":"I don't know..."},
  {"role":"user","content":"What is the claims appeal process?"},
  {"role":"assistant","content":"The claims appeal process is explained in Step 6..."}
]}

Confirmed: all 3 user messages and all 3 assistant responses appear correctly, in order, under the same session_id.

## Error handling and timing logs (server-side)

[ERROR] session=test-session-1 elapsed=0.001s error=no such table: plans
[TIMING] session=test-session-1 elapsed=3.786s classification=structured
[TIMING] session=test-session-1 elapsed=4.197s classification=unstructured
[TIMING] session=test-session-1 elapsed=2.523s classification=unstructured

An initial request failed with a 500 error due to the server being started from the wrong working directory, causing coverage.db to not be found. The try/except block caught this cleanly and returned a graceful error message instead of crashing. The user's message was still saved to the session store despite the failure, confirming conversation state is preserved even when generation fails. The issue was fixed by restarting the server from the chatbot-ui root directory.