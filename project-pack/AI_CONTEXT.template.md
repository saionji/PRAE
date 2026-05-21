# {{project_name}} — 研究项目 AI 上下文

> **安装**: 将此文件重命名为 `CLAUDE.md`（Claude Code）或 `AGENTS.md`（Codex），填写项目信息后删除此行。

## 入口定义

- `CLAUDE.md` / `AGENTS.md`：模型上下文入口
- `/prae-bootstrap` 或 `prae bootstrap`：项目安装入口
- `/prae-init` 或 `prae init`：项目状态初始化入口

---

## 项目简介

**项目名称**: {{project_name}}
**研究问题**: {{research_question}}
**当前阶段**: phase_00_infra（初始，随进展更新）

---

## PRAE 方法论

此项目使用 PRAE（Protocol-Driven Research & Experimentation）管理研究决策过程。

**方法论文档**（PRAE 仓库）:
- `methodology/PRAE_QUICKSTART.md` — 操作手册
- `methodology/PRAE_CORE_MODEL.md` — 轨道/阶段/状态机定义
- `methodology/PRAE_ROLES.md` — 分析者/执行者 SOP
- `methodology/PRAE_PHASE_GATES.md` — 四阶段门控规则
- `methodology/PRAE_RESEARCH_GATE.md` — 研究轨道门控规则
- `methodology/PRAE_ARTIFACTS.md` — 所有工件规格

---

## PDAE 集成

基础设施轨道进入 LOCKED 状态时，调用 PDAE 工程化流程：
- PDAE 仓库: `${PDAE_HOME}/`
- 关键工具: `tools/check_contracts.py`、`tools/check_unit_gate.py`

---

## 项目结构

```
{{project_name}}/
├── CLAUDE.md / AGENTS.md    ← 本文件
├── prae/
│   ├── PRAE_INIT.md         ← 问题陈述和组件分类（只填一次）
│   ├── track_registry.yaml  ← 轨道状态总表（`/prae-init` 后创建）
│   └── phases/
│       ├── phase_00_infra/  ← 基础设施就绪期（`/prae-init` 后创建）
│       ├── phase_01_research/（Phase 0 通过后创建）
│       ├── phase_02_validation/
│       └── phase_03_conclusion/
└── src/
    ├── infra_{name}_v1/     ← LOCKED 基础设施（只读）
    ├── shared/              ← 多轨道共用（PDAE M3）
    └── tracks/{track_id}/  ← 研究代码
        ├── experiments/     ← 实验脚本（不被 import）
        └── impl/            ← 稳定实现（执行者创建）
```

---

## 常用命令

```bash
# 检查轨道状态
python3 tools/check_track_status.py --project-dir .

# 检查阶段门控
python3 tools/check_phase_gate.py --project-dir . --phase 0

# 检查研究门控
python3 tools/check_research_gate.py --track-id {track_id} --project-dir .

# 契约检查（需 PDAE）
python3 tools/check_contracts.py --contracts src/{infra_track}/contracts.yaml --src src/
```

---

## 当前状态

- 轨道总数: {{N}}
- 当前阶段: phase_00_infra
- 下一步:
  - 如果项目还没接入 PRAE：先运行 `/prae-bootstrap` 或 `prae bootstrap`
  - 如果已经 bootstrap 但还没有 `prae/track_registry.yaml`：填写 `prae/PRAE_INIT.md`，然后运行 `/prae-init`（Claude Code）或 `prae init`（Codex）
