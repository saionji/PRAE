# PRAE Glossary & Style Guide

> Status: v0.1.0-alpha — established 2026-05-22 (during `infra_doc_translation_v1`)
> Use this file as the **mandatory glossary reference** for any AI-assisted translation of PRAE methodology documents.

---

## Why this exists

PRAE methodology documents originated in Chinese. As we translate them incrementally, we need a stable English vocabulary so that:
1. Multiple translators (humans or LLM sessions) converge on the same terms.
2. Cross-document references stay accurate.
3. Newcomers reading the English docs see a coherent vocabulary rather than synonyms drift.

If you are an LLM doing translation work: **read this file before any translation prompt and refer to it explicitly**.

---

## Core term mapping (CN ↔ EN)

| Chinese | English (preferred) | Avoid | Notes |
|---|---|---|---|
| 协议 | protocol | system | Used in the project name "Protocol-Driven Research & Experimentation". Refers to a set of conventions and gating rules, not a network protocol. |
| 方法论 | methodology | framework | "framework" sounds like software; methodology is closer to the discipline-of-thought sense. |
| 工具链 | toolchain | tools / pipeline | The 27 Python CLI scripts collectively. |
| 轨道 | track | lane / line | Both infrastructure and research carry the same word; preserve consistency. |
| 基础设施轨道 | infrastructure track | infra track (informal OK) | Always hyphenate adjectivally: *infrastructure-track artifacts*. |
| 研究轨道 | research track | hypothesis track | "research track" is the established term. |
| 阶段 | phase | stage | "Phase 0/1/2/3" is the canonical numbering. |
| 门控 | gate | gating / check (these are OK when used as verbs) | Noun: "gate". Verb: "to gate", "gating". |
| 状态机 | state machine | finite state machine | Plain "state machine" is sufficient — no FSM acronym. |
| 实验 | experiment | trial / run | Each `EXP_NNN.md` is one experiment. |
| 实验日志 | experiment record | log entry | Each experiment is a record, not a log entry. |
| 假设 | hypothesis | assumption / conjecture | Research tracks are organized around hypotheses. |
| 证据 | evidence | data | Use "evidence" for the qualitative judgment ("does the evidence support the hypothesis"), reserve "data" for numerical/dataset references. |
| 决策 | decision | call / verdict | Particularly: "phase-gate decision", "lock decision". |
| 收敛 | converge | wrap up | "Phase 2 converges to the leading hypothesis." |
| 毕业 | graduate | promote / ship | A research track that gets promoted to production is "graduated" — terminology matches `GRADUATED` state. |
| 锁定 | lock / LOCKED | freeze / commit | "LOCKED" is the literal state name; "lock" is the verb. |
| 探索中 | EXPLORING | exploring (lowercase) | When referring to the *state*, capitalize as `EXPLORING` in code-style monospace. |
| 活跃中 | ACTIVE | active (lowercase) | Same convention. |
| 已击杀 | KILLED | killed (lowercase) | Same convention. |
| 已并入 | MERGED | merged (lowercase) | Same convention. |
| 已毕业 | GRADUATED | graduated (lowercase) | Same convention. |
| 契约 | contract | spec / interface | `contracts.yaml` is a single concrete artifact; "contract" is the discipline. |
| 模块规格 | module spec | module specification | `MODULE_SPEC.md` is the file. "Module spec" suffices in prose. |
| 角色 | role | persona / agent | Analyst and Executor are *roles*, not personas. |
| 分析者 | Analyst | analyst (lowercase OK in prose) | Capitalize when referring to the named role. |
| 执行者 | Executor | executor (lowercase OK in prose) | Same convention. |
| 人审 | human approval | manual review / sign-off | The act of a human writing `APPROVED: yes` in `PHASE_GATE.md`. |

---

## Avoid these patterns

- **Don't say "the framework"** when you mean "PRAE the methodology". Say "PRAE" or "the methodology".
- **Don't translate `EXP_001` etc. literally**. Keep them as filenames / identifiers in monospace.
- **Don't say "phase one" in prose**. Use "Phase 1" with an uppercase P and a numeral.
- **Don't dilute state names**. `EXPLORING` is a state; "in EXPLORING" is fine, "in exploring mode" is wrong.
- **Don't introduce `system`** where Chinese said `协议`. PRAE is intentionally a *protocol* in the discipline sense, not a software system.

---

## Style notes for translations

1. **British vs American spelling**: prefer American (`color`, `analyze`, `organize`). Consistency matters more than choice — pick one and don't mix in the same paragraph.
2. **Tone**: instructive, second-person. "Run this command." not "The user should run this command."
3. **Codeblocks**: keep Chinese commit messages and example prompts translated as well — they are part of the document, not opaque data.
4. **Headings**: keep heading levels and structure identical to the source. Don't merge or split sections during translation.
5. **CJK content in command output examples**: leave the literal output as-is (it's an artifact), but add a one-line English summary above or below.

---

## Translation order recommendation

For the post-launch translation backlog (PRAE_INIT.md notes these are deferred to v2):

1. `methodology/PRAE_QUICKSTART.md` — highest impact for new external users.
2. `methodology/PRAE_CORE_MODEL.md` — authoritative state-machine definitions; downstream docs reference these.
3. `methodology/PRAE_ROLES.md` — Analyst/Executor SOPs that the Claude Code skills cite.
4. `methodology/PRAE_PHASE_GATES.md`
5. `methodology/PRAE_RESEARCH_GATE.md`
6. `methodology/PRAE_ARTIFACTS.md`

Each translation should preserve cross-references to the others — if doc N translates a term, the others should match what's in this glossary, not improvise.

---

## Versioning

This file ships as `v0.1.0-alpha` alongside the rest of PRAE. As the methodology evolves, append new terms here in alphabetic order within the table; preserve old rows even if usage shifts (annotate deprecation in the Notes column).
