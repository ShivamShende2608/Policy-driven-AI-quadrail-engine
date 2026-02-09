# Policy-Driven AI Guardrail Engine

A deterministic guardrail system that evaluates AI-generated outputs against configurable policies to determine safe actions.

## Overview

This engine sits between an AI system and end users, enforcing safety policies based on:
- Risk type classification
- Confidence thresholds
- Allowed actions per policy

## How to Run

### Prerequisites
- Python 3.7+
- No external dependencies required

### Execution
```bash
python3 guardrail_engine.py
```

This will:
1. Load `policies.json` and `inputs.json`
2. Process each input against applicable policies
3. Generate `output.json` with decisions

### Run Tests
```bash
python3 test_guardrail.py
```

## File Structure
```
.
├── guardrail_engine.py    # Main engine implementation
├── test_guardrail.py      # Unit tests
├── policies.json          # Policy configuration
├── inputs.json            # AI outputs to evaluate
├── output.json            # Generated decisions
└── README.md              # This file
```

## How It Works

### 1. Policy Matching
- Each input is matched against policies by risk type
- Multiple policies can apply to the same input

### 2. Confidence Evaluation
- If confidence ≥ min_confidence: use least restrictive allowed action
- If confidence < min_confidence: escalate to more restrictive action

### 3. Multi-Policy Resolution
- When multiple policies match, the **most restrictive** action wins
- Restriction order: `block > escalate > sanitize > allow`

### 4. Actions

| Action | Description |
|--------|-------------|
| `allow` | Show output as-is |
| `sanitize` | Replace with safe fallback message |
| `escalate` | Send for human review |
| `block` | Suppress output entirely |

## Assumptions

1. **Policy Completeness**: If no policy matches an input's risk type, the default action (`block`) is applied
2. **Confidence Semantics**: Confidence represents the AI system's certainty, not correctness of content
3. **Sanitization**: Complete replacement (not partial editing) with generic safe message
4. **Determinism**: No randomness; same inputs always produce same outputs
5. **Risk Types**: Risk classification is provided by upstream AI system

## Design Tradeoffs

### Chosen: Most Restrictive Wins
- **Pro**: Maximizes safety when policies conflict
- **Con**: May be overly cautious in some scenarios
- **Alternative**: Could use "most specific" or "highest confidence" policy

### Chosen: Block by Default
- **Pro**: Fail-safe for unknown risk types
- **Con**: May block legitimate content if policies are incomplete
- **Alternative**: Could allow unknowns or require explicit coverage

### Chosen: Complete Sanitization
- **Pro**: Eliminates risk of partial leakage
- **Con**: Loss of potentially useful context
- **Alternative**: Could provide risk-specific fallback messages

## Example Decision Flow

For input R1 (medical, confidence 0.96):
1. Match policies: `MED_STRICT` (min 0.95), `MED_BLOCK` (min 0.0)
2. Evaluate: R1 confidence 0.96 ≥ 0.95 → `MED_STRICT` allows escalate
3. Evaluate: R1 confidence 0.96 ≥ 0.0 → `MED_BLOCK` allows block
4. Resolve: block > escalate → **Decision: block**

## Output Format
```json
{
  "id": "R1",
  "decision": "escalate",
  "applied_policies": ["MED_STRICT"],
  "final_output": "Sent for human review",
  "reason": "medical risk; confidence 0.96; requires human review"
}
```

## Extension Ideas

- Audit mode: Show all matched policies and their individual evaluations
- Rule trace: Log which confidence checks passed/failed
- CLI flags for custom file paths
- Policy validation on load
- Metrics/logging for production monitoring
