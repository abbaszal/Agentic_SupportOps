import json
import os
from agt.agent import run_agent

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your environment or .env before running.")

    # Run on an existing ticket
    res = run_agent(ticket_id=1, model="gpt-5")
    print("AGENT_RUN_ID:", res.agent_run_id)
    print(json.dumps(res.result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
