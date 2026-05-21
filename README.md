# PRAE — Protocol-Driven Research & Experimentation

> I run real projects across quantitative trading, marine systems, flight log automation, and DEX research — all managed with this toolchain. PRAE is the methodology + tools I extracted. Open-sourced because the discipline of public docs makes it better.

**Status**: `v0.1.0-alpha` · single maintainer · in production use by the author · English documentation is in progress — the methodology source-of-truth is currently Chinese (see [`methodology/`](methodology/)).

**Quickstart**: see [Quick Start](#快速开始) (works in Claude Code or Codex CLI). **Concepts**: see [Core Model](#核心概念). **What is PDAE**: see [与 PDAE 的关系](#与-pdae-的关系).

---

AI 辅助科研方法论框架。管"哪条研究路线值得走"的决策过程，与 **PDAE**（管"怎么把代码做好"）配套使用。

如果你是大模型，第一次进入本仓库时，先读 `LLM_ENTRYPOINT.md`。
## 入口定义

- `LLM_ENTRYPOINT.md`：模型上下文入口
- `prae bootstrap` / `/prae-bootstrap`：项目安装入口
- `prae init` / `/prae-init`：项目状态初始化入口

---

## 什么是 PRAE

研究型项目（量化策略、目标检测、机器人控制）的核心挑战不是写代码——是决定**跑哪个实验、相信哪个结果、何时放弃一条路线**。

PRAE 通过两类轨道、四个阶段、四层门控，让 AI 辅助这一决策过程，同时保证：
- 实验可复现（参数记录 + 随机种子）
- 决策有据可查（TRACK_LOG + PHASE_GATE）
- 基础设施稳定后才开始算法探索（Phase 0 门控）
- 毕业到生产前经过完整工程化（PDAE M1-M3）

---

## 快速开始

### 在现有研究项目里安装 PRAE

这里说的是**项目操作入口**，也就是一个新研究项目第一次接入 PRAE 时的第一条命令。

**Claude Code 用户：**
```
/prae-bootstrap
```
（Claude 会自动检测项目类型并部署 PRAE 文件）

**Codex 用户：**
```
codex exec --task /path/to/PRAE/runtime/codex/tasks/prae-bootstrap.md
```

或手动：
```bash
python3 /path/to/PRAE/tools/prae_bootstrap.py \
  --target /path/to/your/project \
  --client claude-code   # 或 codex
```

### 初始化研究项目

1. 打开 `prae/PRAE_INIT.md`，填写研究问题和轨道分类
2. 运行 `/prae-init`（Claude Code）或 `prae init`（Codex CLI）
   该步骤会生成 `prae/track_registry.yaml`、`prae/phases/phase_00_infra/PHASE_BRIEF.md` 和基础设施 `TRACK_LOG.md`
3. 先完成 Phase 0：为基础设施轨道记录选型实验，PDAE M3 通过后用 `/prae-lock-infra` 或 `prae lock-infra` 正式锁定
4. 所有基础设施轨道都 `LOCKED` 后，先运行 `/prae-advance-phase` 或 `prae advance-phase` 生成 gate；人工批准后再次运行同一命令进入 Phase 1
5. 进入 Phase 1 后，已在 `track_registry.yaml` 中登记的研究轨道运行 `/prae-new-track`、`/prae-new-exp`；若是全新假设，先 `/prae-add-track`，再 `/prae-new-track`
6. 实验跑完后，用 `/prae-record-result` 记录结果；若用户批准状态变更，再用 `/prae-update-track-state` 或 `prae update-track-state`

---

## 核心概念

### 两类轨道

| 类型 | 生命周期 | 说明 |
|------|----------|------|
| 基础设施轨道 | `EXPLORING → LOCKED` | 数据管道、特征工程等支撑组件；LOCKED 后只读，变更开 v2 |
| 研究轨道 | `EXPLORING → ACTIVE → KILLED/MERGED/GRADUATED` | 算法假设；每次实验记录在 EXP_NNN.md |

### 四个阶段

```
Phase 0  基础设施就绪期   所有基础设施轨道 LOCKED 后进入 Phase 1
Phase 1  算法探索期       并行实验，AI 分析，人批准
Phase 2  算法验证期       聚焦验证，严格参数记录
Phase 3  结论期           归档 or 毕业进 PDAE
```

### AI 角色

- **分析者**（Analyst）：轨道 EXPLORING/ACTIVE 时激活。设计实验、检索文献、解读结果。
- **执行者**（Executor）：轨道 LOCKED/实现期激活。写代码、跑 PDAE 单元门控。

---

## 仓库结构

```
PRAE/
├── methodology/           ← 方法论 SSOT（LLM 读，人也可读）
│   ├── PRAE_QUICKSTART.md ← 从这里开始
│   ├── PRAE_CORE_MODEL.md ← 轨道/阶段/状态机权威定义
│   ├── PRAE_ROLES.md      ← 分析者/执行者 SOP
│   ├── PRAE_PHASE_GATES.md
│   ├── PRAE_RESEARCH_GATE.md
│   └── PRAE_ARTIFACTS.md
│
├── runtime/
│   ├── abstract/          ← 平台无关模板（TRACK_LOG、EXP_NNN 等）
│   ├── claude-code/       ← Claude Code：skills + agents + commands
│   └── codex/             ← Codex：prompts + tasks + bin/prae CLI
│
├── project-pack/          ← 部署包（bootstrap 自动复制到研究项目）
├── tools/                 ← 门控脚本（check_phase_gate.py 等）
└── tests/                 ← 单元 + 集成测试
```

---

## 门控工具

所有工具输出 JSON，exit code 0=通过 / 1=不通过 / 2=文件缺失。

```bash
# 检查阶段门控（Phase 0→1）
python3 tools/check_phase_gate.py --project-dir . --phase 0

# 检查研究轨道门控
python3 tools/check_research_gate.py --project-dir . --track-id research_strategy_momentum

# 检查轨道状态一致性
python3 tools/check_track_status.py --project-dir .

# 契约检查（复用 PDAE）
python3 tools/check_contracts.py --contracts src/infra_data_v1/contracts.yaml --src src/
```

---

## 与 PDAE 的关系

| 场景 | PRAE | PDAE |
|------|------|------|
| 决定跑哪个实验 | ✓ | — |
| 基础设施代码工程化 | 触发 → | ✓ |
| 单元门控 / 契约检查 | 复用工具 | ✓ |
| 毕业到生产 | 触发 → | ✓ |

PDAE 仓库：`${PDAE_HOME}/`

---

## 开发与测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行集成测试（完整生命周期）
pytest tests/integration/test_end_to_end.py -v

# 手工冒烟测试
mkdir /tmp/prae-smoke && touch /tmp/prae-smoke/.claude
python3 tools/prae_bootstrap.py --target /tmp/prae-smoke --client claude-code
python3 tools/init_project.py --name smoke --output-dir /tmp/prae-smoke
```
