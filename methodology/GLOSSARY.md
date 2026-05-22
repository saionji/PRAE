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

## Artifact Section Headings & Field Labels (CN → EN)

> **Authoritative mapping for the full-i18n effort.** Templates, the tool
> writer/parser code, test fixtures, and test assertions MUST all use the
> exact English strings below. Any layer that diverges breaks the
> write → read → assert chain.

### Document titles (`#`)

| Chinese | English |
|---|---|
| `# 分析者角色提示词（抽象基础版）` | `# Analyst Role Prompt (Abstract Base)` |
| `# 执行者角色提示词（抽象基础版）` | `# Executor Role Prompt (Abstract Base)` |
| `# Phase {{NN}}_{{name}} 阶段简报` | `# Phase {{NN}}_{{name}} Brief` |
| `# EXP_{{NNN}}：{{实验标题}}` | `# EXP_{{NNN}}: {{experiment_title}}` |
| `# Phase {{from}} → Phase {{to}} 门控分析` | `# Phase {{from}} → Phase {{to}} Gate Analysis` |
| `# PRAE 项目初始化文档` | `# PRAE Project Initialization Document` |
| `# 轨道日志：{{track_id}}` | `# Track Log: {{track_id}}` |

### Section headings (`##`)

| Chinese | English |
|---|---|
| `## 你的当前角色` | `## Your Current Role` |
| `## 你能做什么（输入）` | `## What You Can Do (Inputs)` |
| `## 你要产出什么（输出）` | `## What You Must Produce (Outputs)` |
| `## 你不能做什么（硬性约束）` | `## What You Must Not Do (Hard Constraints)` |
| `## 实验版轻量 PDAE 协议` | `## Lightweight PDAE Protocol (Experiment Variant)` |
| `## 角色切换信号` | `## Role-Switch Signal` |
| `## 典型动作序列（Phase 1 研究探索）` | `## Typical Action Sequence (Phase 1 Research Exploration)` |
| `## PDAE 集成流程（基础设施轨道 EXPLORING → LOCKED）` | `## PDAE Integration Flow (Infrastructure Track EXPLORING → LOCKED)` |
| `## shared 代码迁移流程` | `## Shared Code Migration Flow` |
| `## 项目结论` | `## Project Conclusion` |
| `## 各轨道去向` | `## Disposition of Each Track` |
| `## 毕业轨道的 PDAE 项目链接` | `## PDAE Project Links for Graduated Tracks` |
| `## 未解决问题` | `## Unresolved Issues` |
| `## 最终决定` | `## Final Decision` |
| `## 最终结论` | `## Final Conclusion` |
| `## 阶段目标` | `## Phase Goal` |
| `## 成功标准` | `## Success Criteria` |
| `## 本阶段在场的轨道` | `## Tracks Present in This Phase` |
| `## 关键时间节点（可选）` | `## Key Time Milestones (Optional)` |
| `## 关联文件` | `## Related Files` |
| `## 1. 当前阶段状态` | `## 1. Current Phase State` |
| `## 2. 门控条件逐项检查` | `## 2. Gate Conditions — Item-by-Item Check` |
| `## 3. 证据摘要` | `## 3. Evidence Summary` |
| `## 4. 风险与未决项` | `## 4. Risks and Open Items` |
| `## 5. 建议` | `## 5. Recommendation` |
| `## 6. 待人工批准` | `## 6. Pending Human Approval` |
| `## 问题陈述` | `## Problem Statement` |
| `## 组件分类 → 基础设施轨道` | `## Component Classification → Infrastructure Tracks` |
| `## 组件分类 → 研究轨道` | `## Component Classification → Research Tracks` |
| `## Phase 0 成功标准` | `## Phase 0 Success Criteria` |
| `## Hypothesis（仅研究轨道填写）` | `## Hypothesis (research tracks only)` |
| `## 选型目标（仅基础设施轨道填写）` | `## Selection Goal (infrastructure tracks only)` |
| `## 选型目标` | `## Selection Goal` |
| `## PDAE 毕业记录` | `## PDAE Graduation Record` |

Already-English headings stay verbatim: `## Goal`, `## Method`, `## Preflight Check`, `## Expected Signal`, `## Result`, `## Conclusion`, `## State`, `## Experiments`, `## Evidence Summary`, `## Decision Log`, `## CHANGE_LOG`.

### Bold field labels (`**...**`)

| Chinese | English |
|---|---|
| `**研究轮次**` | `**Research Cycle**` |
| `**激活条件**` | `**Activation Condition**` |
| `**轨道 ID**` | `**Track ID**` |
| `**实验 ID**` | `**Experiment ID**` |
| `**日期**` | `**Date**` |
| `**状态**` | `**State**` |
| `**类型**` | `**Type**` |
| `**当前阶段**` | `**Current Phase**` |
| `**当前状态**` | `**Current State**` |
| `**依赖的轨道**` | `**Depends On**` |
| `**创建者**` | `**Creator**` |
| `**创建日期**` | `**Created**` |
| `**生成者**` | `**Generated by**` |
| `**生成日期**` | `**Generated**` |
| `**阶段**` | `**Phase**` |
| `**目标阶段**` | `**Target Phase**` |
| `**推荐动作**` | `**Recommended Action**` |
| `**数据源**` | `**Data Source**` |
| `**标的 / 数据集**` | `**Target / Dataset**` |
| `**时间窗**` | `**Time Window**` |
| `**随机种子**` | `**Random Seed**` |
| `**关键超参数**` | `**Key Hyperparameters**` |
| `**对照组**` | `**Control Group**` |
| `**代码路径**` | `**Code Path**` |
| `**最小冒烟检查**` | `**Minimal Smoke Check**` |
| `**输出契约**` | `**Output Contract**` |
| `**本次不做**` | `**Out of Scope This Time**` |
| `**成功判据**` | `**Success Criterion**` |
| `**失败判据**` | `**Failure Criterion**` |
| `**中性信号**` | `**Neutral Signal**` |
| `**关键数值**` | `**Key Values**` |
| `**输出位置**` | `**Output Location**` |
| `**原始输出**` | `**Raw Output**` |
| `**结论**` | `**Conclusion**` |
| `**理由**` | `**Rationale**` |
| `**对轨道状态的影响建议**` | `**Recommended Impact on Track State**` |
| `**研究问题**` | `**Research Question**` |
| `**背景**` | `**Background**` |
| `**成功标准**` | `**Success Criteria**` |
| `**基础设施轨道**` | `**Infrastructure Track**` |
| `**研究轨道**` | `**Research Track**` |
| `**PDAE 工具路径**` | `**PDAE Tool Path**` |
| `**毕业日期**` | `**Graduation Date**` |
| `**PDAE 项目路径**` | `**PDAE Project Path**` |
| `**移交状态**` | `**Handoff Status**` |

---

## Versioning

This file ships as `v0.1.0-alpha` alongside the rest of PRAE. As the methodology evolves, append new terms here in alphabetic order within the table; preserve old rows even if usage shifts (annotate deprecation in the Notes column).
