# LLM Context Entry Point

本文件是 **PRAE 仓库的模型上下文入口**。  
如果你是大模型，第一次进入本仓库时，先读本文件，再按这里给出的顺序继续读。

## 入口定义

- `LLM_ENTRYPOINT.md`：模型上下文入口
- `prae bootstrap` / `/prae-bootstrap`：项目安装入口
- `prae init` / `/prae-init`：项目状态初始化入口

---

## 1. 先判断你身处哪种场景

### 场景 A：你正在这个仓库里工作

也就是你当前目录就是 `PRAE/` 本身。  
此时你面对的是 **PRAE 框架仓库**，不是某个具体研究项目。

你的目标通常是以下几类之一：
- 理解 PRAE 方法论本身
- 修改 `tools/`、`runtime/`、`methodology/`
- 解释这个框架怎么用
- 修复 gate / CLI / 模板 / 测试

### 场景 B：你在一个“使用了 PRAE 的研究项目”里工作

也就是你当前目录不是 PRAE 仓库，而是某个业务 / 研究项目，里面有：
- `prae/`
- `tools/`
- `AGENTS.md` 或 `CLAUDE.md`

此时你面对的是 **PRAE 的使用方项目**。  
你的目标通常是：
- 初始化研究项目
- 开新轨道 / 新实验
- 记录实验结果
- 推进 phase
- 做最终结论 / reopen

---

## 2. 如果你在 PRAE 框架仓库里，按这个顺序读

### 最小必读顺序

1. `README.md`
2. `methodology/PRAE_QUICKSTART.md`
3. `methodology/PRAE_CORE_MODEL.md`
4. `methodology/PRAE_ROLES.md`

### 如果你要改框架实现，再继续读

5. `CLAUDE.md`
6. `runtime/codex/bin/prae`
7. `tools/` 里与你任务直接相关的脚本
8. `tests/` 里对应的单测 / 集成测试

### 目录职责速记

- `methodology/`：规则 SSOT
- `tools/`：正式执行逻辑
- `runtime/`：给 Claude / Codex 的命令、prompt、skill 外壳
- `project-pack/`：bootstrap 时投放到研究项目里的部署包
- `tests/`：行为回归

---

## 3. 如果你在 PRAE 使用方项目里，按这个顺序读

1. 项目根目录的 `AGENTS.md` 或 `CLAUDE.md`
2. `prae/PRAE_INIT.md`
3. `prae/track_registry.yaml`
4. 当前 phase 的 `PHASE_BRIEF.md`
5. 目标轨道的 `TRACK_LOG.md`
6. 最近的 `EXP_NNN.md`

如果 `prae/track_registry.yaml` 不存在，说明项目可能只做了 bootstrap、还没 init。  
此时先完成 `prae/PRAE_INIT.md`，再运行初始化。

---

## 4. PRAE 的最短使用路径

从这一节开始，说的是 **项目操作入口**，不是模型文件入口。  
也就是说：模型第一次进入仓库先读本文件；真正开始在项目里安装 PRAE 的第一条命令仍然是 `bootstrap`。

如果你是人在一个研究项目里用 PRAE，最短路径是：

1. `bootstrap`
2. 填 `prae/PRAE_INIT.md`
3. `init`
4. Phase 0：`new-track` / `new-exp`（基础设施选型实验）→ `record-result` → `lock-infra`
5. 所有基础设施轨道 `LOCKED` 后 `advance-phase`
6. Phase 1：已登记研究轨道用 `new-track` → `new-exp` → `record-result`；若是全新假设，先 `add-track`
7. 用户批准后 `update-track-state`
8. `advance-phase`
9. `graduate / finalize / reopen`

### Codex CLI 入口

主入口文件：
- `runtime/codex/bin/prae`

典型命令：

```bash
prae bootstrap
prae init
prae new-track infra_data_v1
prae new-exp infra_data_v1 --title "DuckDB 选型实验"
prae record-result infra_data_v1 EXP_001
prae lock-infra infra_data_v1 --approver saionji --reason "PDAE M3 通过"
prae advance-phase
prae add-track research_strategy_reversal --type research --hypothesis "反转因子在A股ETF上有效" --depends-on infra_data_v1
prae new-track research_strategy_momentum
prae new-exp research_strategy_momentum --title "首个动量实验"
prae record-result research_strategy_momentum EXP_001
prae update-track-state research_strategy_momentum ACTIVE --approver saionji --reason "EXP_001 正向信号"
prae advance-phase
```

### Claude Code 入口

主入口是 slash commands：
- `/prae-bootstrap`
- `/prae-init`
- `/prae-add-track`
- `/prae-new-track`
- `/prae-new-exp`
- `/prae-record-result`
- `/prae-lock-infra`
- `/prae-update-track-state`
- `/prae-advance-phase`
- `/prae-graduate`
- `/prae-finalize`
- `/prae-reopen`

---

## 5. 你必须记住的几条硬规则

1. 不跳过 gate。
2. 不手工修改研究轨道的 `state`，状态变更走 `update_track_state.py` / `prae update-track-state`。
3. 不手工修改基础设施轨道的 `LOCKED` 确认，锁定走 `lock_infra_track.py` / `prae lock-infra`。
4. `prae init` 之后默认仍在 `phase_00_infra`；在 Phase 0 批准通过前，不要直接创建研究轨道实验。
5. `new-track` 只为已登记轨道创建当前阶段目录；如果是全新轨道，先走 `add-track`。
6. 研究轨道不能 `EXPLORING → KILLED` 直接终止，必须先经过 `ACTIVE`。
7. `ACTIVE` 轨道进终态前必须通过 Research Gate。
8. `LOCKED` 基础设施不可直接改；要改就开 v2。
9. 实验代码采用“轻量 PDAE”顺序：先设计、先定义 Preflight、再实现、再验收。

---

## 6. 给大模型的最小启动指令

如果你想让另一个大模型快速进入状态，直接把下面这段发给它：

```text
先读仓库根目录的 LLM_ENTRYPOINT.md，并严格按其中的“文件读取顺序”和“硬规则”建立上下文。

如果你当前在 PRAE 框架仓库里：
- 先读 README.md
- 再读 methodology/PRAE_QUICKSTART.md、PRAE_CORE_MODEL.md、PRAE_ROLES.md
- 然后再读与你任务直接相关的 tools/、runtime/、tests/

如果你当前在某个使用 PRAE 的研究项目里：
- 先读 AGENTS.md/CLAUDE.md
- 再读 prae/PRAE_INIT.md、prae/track_registry.yaml、当前 phase 的 PHASE_BRIEF.md、目标轨道 TRACK_LOG.md 和最近的 EXP_NNN.md

严格遵守：
- 不跳过 gate
- 不手工改研究轨道 state
- 不手工把基础设施轨道改成 LOCKED，必须走 lock_infra_track.py / prae lock-infra
- prae init 之后默认仍在 phase_00_infra；在 Phase 0 批准前不要直接开研究实验
- 状态变更必须走 update_track_state.py / prae update-track-state
- EXPLORING 不能直接到 KILLED
- ACTIVE 进终态前必须通过 Research Gate
```

如果你想直接复制现成版本，也可以用根目录这两个文件：
- `CODEX_START_PROMPT.md`
- `CLAUDE_START_PROMPT.md`

---

## 7. 这一个文件的边界

这个文件只负责 **让你最快进入正确上下文**。  
它不是完整方法论文档，也不是执行规范的 SSOT。

如果本文件和以下文档冲突，以它们为准：
- `methodology/PRAE_CORE_MODEL.md`
- `methodology/PRAE_ROLES.md`
- `methodology/PRAE_PHASE_GATES.md`
- `methodology/PRAE_RESEARCH_GATE.md`
