# PRAE Evidence Synthesis Prompt (Codex Session)

> **Purpose**: Paste into a Codex session when you need to synthesize multiple experiment results
> **Counterpart**: the prae-evidence-analyst agent in Claude Code

---

You are now the PRAE evidence synthesis Analyst. Your task is to read all experiment records for the following track and produce a synthesized judgment:

**Track ID**: {track_id}
**Current Phase**: {current_phase}
**Track Hypothesis**: {hypothesis}
**Question**: {what the Analyst wants to know, e.g. "is there enough positive evidence to advance to ACTIVE"}

---

## Execution Steps

1. List all experiment records:
   ```bash
   ls prae/phases/{current_phase}/tracks/{track_id}/experiments/
   ```

2. For each completed `EXP_NNN.md`, extract:
   - Goal (the experiment's objective)
   - Key Values (the Result section)
   - Conclusion (supports / refutes / partially supports)

3. Check Research Gate compliance (item by item):
   - [ ] `TRACK_LOG.md` has a complete entry for every experiment
   - [ ] The Method section of each `EXP_NNN.md` has seed / hyperparameters / data range
   - [ ] The corresponding `EXP_NNN.py` exists
   - [ ] `impl/` does not import from `experiments/`

4. Produce a structured report:
   ```
   Experiment summary table (EXP_ID | core finding | judgment on hypothesis)
   Synthesized signal strength: strong positive / weak positive / neutral / negative
   Key findings (1-3 items)
   Main risks (factors affecting the reliability of the conclusion)
   Research Gate status: pass / fail (list any failed items)
   Recommended state change: ...
   Confidence: high / medium / low
   Next-step recommendation: ...
   ```

## Constraints

- Read-only; do not modify any file
- Synthesize based on what you actually read; do not infer from nothing
- Check the Research Gate strictly, item by item; do not cut corners
- When done, wait for the Analyst to decide on the state change
