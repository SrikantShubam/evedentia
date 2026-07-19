import json

p = json.load(open("outputs/tournament_live.json"))
total_gates = 0
total_cost = p.get("total_llm_cost_usd", 0)

for s in p.get("ideas", []):
    gates = [g for g in s.get("gate_results", []) if g.get("status") == "COMPLETED"]
    total_gates += len(gates)
    for g in gates:
        print(f"  {s['idea']['id'][:45]}: {g['gate_name']} cost={g.get('llm_cost_usd')} conf={g.get('confidence')}")

print(f"\nTotal LLM gate calls: {total_gates}")
print(f"Total cost: ${total_cost}")
print(f"Avg cost per gate: ${total_cost / total_gates:.4f}" if total_gates else "N/A")

# Estimate tokens per gate call
# Each gate call uses a classifier prompt with source text + gate rubric
# Rough estimate: ~2000 prompt tokens + ~300 completion tokens per gate
est_prompt_tokens = total_gates * 2000
est_completion_tokens = total_gates * 300
print(f"\nEstimated tokens (for cost comparison):")
print(f"  Prompt tokens: ~{est_prompt_tokens}")
print(f"  Completion tokens: ~{est_completion_tokens}")

# DeepSeek V4 Flash pricing (approximate, based on market rates)
# Using typical Flash-tier pricing: ~$0.15/M input, ~$0.60/M output
DS_V4_INPUT = 0.15 / 1_000_000
DS_V4_OUTPUT = 0.60 / 1_000_000

ds_cost = (est_prompt_tokens * DS_V4_INPUT) + (est_completion_tokens * DS_V4_OUTPUT)
print(f"\nDeepSeek V4 Flash estimated cost: ${ds_cost:.6f}")
print(f"Comparison: NVIDIA cost was ${total_cost:.2f}")
print(f"Ratio: {total_cost / ds_cost:.0f}x cheaper/more expensive with DeepSeek V4 Flash" if ds_cost > 0 else "")
