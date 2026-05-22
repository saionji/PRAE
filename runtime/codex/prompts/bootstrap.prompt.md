# PRAE Bootstrap Prompt (Codex Session Startup)

> **Purpose**: paste when starting a Codex session for the first time in a research project, to automatically deploy the PRAE framework
> **Where to paste**: the Codex session input box (as the first message)

This is the **project installation entry-point prompt**, not the model-context entry-point prompt.
If the model needs to establish context first, it should read the project's `AGENTS.md` / `CLAUDE.md`; project-state initialization is handled later by `prae init`.

---

You are the execution assistant for the PRAE research methodology framework. I need you to deploy the PRAE framework into the current project.

**PRAE repository location**: ${PRAE_HOME} (or specified via --prae-path)

Please perform the following operations:

1. **Detect the current environment**:
   - Check whether there is an `AGENTS.md` (Codex project)
   - Check whether there is a `.claude/` or `CLAUDE.md` (Claude Code project)
   - If neither exists: ask me which one to choose

2. **Run the bootstrap script**:
   ```bash
   python3 ${PRAE_HOME}/tools/prae_bootstrap.py \
     --target $(pwd) \
     --client codex
   ```
   The script copies the minimal project-pack skeleton, Codex tasks, and templates.
   Note: `track_registry.yaml` and the Phase 0 artifacts are not created by bootstrap; they are generated later by `prae init`.

3. **Check the PDAE installation status**:
   ```bash
   ls ${PDAE_HOME}/tools/check_contracts.py
   ```
   If it does not exist, tell me "PRAE's infrastructure graduation feature depends on PDAE; should we install it now?"

4. **Merge the contents of AGENTS_SNIPPET.md into AGENTS.md**:
   - If AGENTS.md already exists: append the PRAE section to the end of the file
   - If it does not exist: create a new AGENTS.md containing only the PRAE section

5. **Verify the installation**:
   ```bash
   ls prae/templates/
   ls .prae/tasks/ 2>/dev/null || ls prae/tasks/ 2>/dev/null
   ```

6. **Output the next-step guidance**:
   ```
   ✓ PRAE has been deployed
   Next step: fill in prae/PRAE_INIT.md, then run:
     prae init   # generates track_registry.yaml and the Phase 0 artifacts
   ```

After all operations are complete, wait for my further instructions.
