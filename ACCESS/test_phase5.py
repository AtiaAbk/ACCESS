from ACCESS.ai.decision_engine import AIDecisionEngine

engine = AIDecisionEngine()

tests = [
    "Could you open the calculator for me?",
    "Prepare my development workspace.",
    "close the terminal now",
    "delete the file report.txt",
    "shut down",
    "restart",
    "take a screenshot",
    "find the file budget.xlsx",
    "random gibberish text",
]

print("=" * 60)
for t in tests:
    result = engine.interpret(t)
    print(f"Input: {t}")
    print(f"  -> intent={result.intent}, target={result.target}, confidence={result.confidence}")
    print(f"  -> multi_step={result.is_multi_step()}, steps={len(result.steps)}")
    print("-" * 60)

memory = [("open chrome", "opened chrome", "2026-08-12T10:00:00")]
result = engine.interpret("do that again", recent_memory=memory)
print(f"Memory fallback test: {result}")
print("=" * 60)
