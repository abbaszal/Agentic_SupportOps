import json
import os
from agt.agent1 import run_agent

def main():
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("Set GEMINI_API_KEY in your environment or .env before running.")

    # Run on an existing ticket
    res = run_agent(ticket_id=1, model="gemini-2.5-flash-lite")
    print("AGENT_RUN_ID:", res.agent_run_id)
    print(json.dumps(res.result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()