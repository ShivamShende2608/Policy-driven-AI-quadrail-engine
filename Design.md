# Design Decisions

## Architecture

### Policy Resolution Strategy
- **Choice:** Most restrictive action wins
- **Rationale:** Prioritizes safety in ambiguous cases
- **Trade-off:** May be overly cautious

### Confidence Handling
- Below threshold → Escalate to more restrictive action
- Above threshold → Use least restrictive allowed action

### Default Behavior
- Unknown risk types → Block by default
- Missing policies → Fail-safe approach

## Alternative Approaches Considered

1. **Weighted voting**: Could assign weights to policies
   - Rejected: Adds complexity, reduces determinism

2. **Confidence-based priority**: Higher confidence wins
   - Rejected: Safety should not depend on confidence alone

3. **First-match-wins**: Apply first matching policy only
   - Rejected: Misses important safety constraints
