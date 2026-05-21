# PRAE Core Model

> **用途**: PRAE 方法论的权威定义文档；轨道、状态、阶段、门控的精确规格
> **读者**: LLM（你）
> **状态**: Active（PRAE v1.0）
> **最后更新**: 2026-04-19

本文档是**定义层**，不是教程。遇到概念不一致时，以本文档为准。

---

## 1. 两类轨道的完整定义

PRAE 把一个研究项目拆成若干条**轨道（Track）**。任何轨道必须严格属于以下两类之一：

### 1.1 基础设施轨道（Infrastructure Track）

**定义**：为研究提供可靠的数据 / 环境 / 工具底座的轨道。

**字段**（`track_registry.yaml` 中必填）：
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 必须以 `infra_` 前缀开头，含版本号（`infra_data_v1`） |
| `type` | `"infrastructure"` | 固定值 |
| `state` | enum | `EXPLORING` 或 `LOCKED`，无其他合法值 |
| `src` | path | 源码目录路径，格式 `src/infra_{name}_v{N}/` |
| `module_spec` | path | 指向 PDAE MODULE_SPEC.md |
| `contracts` | path | 指向 contracts.yaml |
| `locked_at` | date | state=LOCKED 时必填；state=EXPLORING 时必须为空或不存在 |

**生命周期**：
```
EXPLORING ──[选型确认 + PDAE M1-M3 通过]──▶ LOCKED
LOCKED    ──[需求变更]────────────────────▶ 新建 infra_{name}_v2（v1 保持 LOCKED）
```

**约束（硬性规则）**：
- 一旦 `state = LOCKED`，该轨道源码目录 `src/infra_{name}_v{N}/` 变为只读
- LOCKED 轨道的 `contracts.yaml` 变为合同，所有下游必须遵守
- LOCKED 轨道需要变更时，**永远不解锁**，而是新建 v2 轨道
- v1 和 v2 可以并存。迁移完成前，v1 继续为尚未迁移的研究轨道提供服务

### 1.2 研究轨道（Research Track）

**定义**：承载一条研究假设的并行实验空间。

**字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 必须以 `research_` 前缀开头（`research_strategy_momentum`） |
| `type` | `"research"` | 固定值 |
| `state` | enum | `EXPLORING` / `ACTIVE` / `KILLED` / `MERGED` / `GRADUATED` |
| `src` | path | 源码目录路径，格式 `src/tracks/{track_id}/` |
| `hypothesis` | string | 明确的可证伪假设 |
| `depends_on` | list[string] | 依赖的基础设施轨道 ID 列表 |
| `experiments` | int | 已执行实验次数 |
| `evidence_summary` | string | 当前证据的一句话概括 |
| `concluded_at` | date | state ∈ {KILLED, MERGED, GRADUATED} 时必填 |

**生命周期**：
```
EXPLORING ──[有正向信号]──▶ ACTIVE
ACTIVE ──[明显失败]────────▶ KILLED    （终态）
ACTIVE ──[与其他轨道互补]──▶ MERGED    （终态）
ACTIVE ──[结论确定，值得工程化]──▶ GRADUATED  （终态，触发 PDAE）
```

**约束**：
- `KILLED` / `MERGED` / `GRADUATED` 是终态，不可回退到 `ACTIVE` 或 `EXPLORING`
- 一条研究轨道只能有一条假设。同时探索两条假设时，必须拆成两条研究轨道
- 研究轨道的 `depends_on` 只能是 state=LOCKED 的基础设施轨道

---

## 2. 状态机（合法与非法转移）

### 2.1 基础设施轨道状态转移

| 当前状态 | 允许转到 | 禁止转到 | 备注 |
|----------|----------|----------|------|
| EXPLORING | LOCKED | 任何其他 | 必须经 PDAE M1-M3 全部通过 |
| LOCKED | （无） | 任何状态 | LOCKED 是终态；变更请开 v2 |

**非法转移**：
- `LOCKED → EXPLORING`：禁止。任何"解锁修改"意图都要改为开 v2 新轨道
- `EXPLORING → 任何其他名字`：不存在其他状态

### 2.2 研究轨道状态转移

| 当前状态 | 允许转到 | 禁止转到 | 备注 |
|----------|----------|----------|------|
| EXPLORING | ACTIVE | KILLED, MERGED, GRADUATED | 必须先有正向信号才能 ACTIVE |
| ACTIVE | KILLED, MERGED, GRADUATED | EXPLORING | 前进，不回退 |
| KILLED | （无） | 任何状态 | 终态 |
| MERGED | （无） | 任何状态 | 终态 |
| GRADUATED | （无） | 任何状态 | 终态，会触发 PDAE 工程项目 |

**特殊情况**：
- 若判定失误想"恢复"一个 KILLED 轨道：**不允许**修改 state 字段，应新建一个 `research_{新ID}`，在其 `TRACK_LOG.md` 说明继承自哪个 KILLED 轨道
- `EXPLORING → KILLED` 跳过 ACTIVE：不允许。既然要杀，也得进 ACTIVE 留下至少一次实验记录，否则无证据可审

---

## 3. 四个阶段的完整定义

### 3.1 Phase 0 — 基础设施就绪期

- **目标**：把所有在 `PRAE_INIT.md` 中声明的基础设施轨道推到 `LOCKED`
- **进入前提**：项目完成 `PRAE_INIT.md` 和 `track_registry.yaml` 初始化
- **退出门控**：所有 `type=infrastructure` 的轨道 `state=LOCKED`
- **AI 角色**：分析者（选型研究）→ 执行者（PDAE M1-M3 实现）
- **典型工件**：各 `infra_*` 轨道的选型实验记录、MODULE_SPEC.md、contracts.yaml
- **允许同时存在多个基础设施轨道并行推进**

### 3.2 Phase 1 — 算法探索期

- **目标**：并行启动多条研究轨道，快速积累信号
- **进入前提**：Phase 0 PHASE_GATE.md 经人工批准
- **退出门控**：≥1 条研究轨道 `state=ACTIVE` 且 PHASE_GATE.md 经人工批准
- **AI 角色**：分析者为主（文献检索、实验设计、结果解读）
- **典型工件**：每条研究轨道的首批 EXP 记录、正向信号汇总

### 3.3 Phase 2 — 算法验证期

- **目标**：收敛到主方案，淘汰或合并轨道
- **进入前提**：Phase 1 PHASE_GATE.md 经人工批准
- **退出门控**：所有 `ACTIVE` 研究轨道都有明确结论（KILLED / MERGED / GRADUATED）且 PHASE_GATE.md 经人工批准
- **AI 角色**：分析者（严格验证实验设计、结果解读）+ 执行者（对 GRADUATED 轨道启动 PDAE 准备）
- **典型工件**：验证实验记录、轨道结论决策表

### 3.4 Phase 3 — 结论期

- **目标**：形成最终结论；归档或毕业到 PDAE
- **进入前提**：Phase 2 PHASE_GATE.md 经人工批准
- **退出门控**：人工决定（无 AI 自动判定）
- **AI 角色**：文档整理；对 GRADUATED 轨道执行 PDAE 路由
- **典型工件**：`CONCLUSION.md`、PDAE 工程项目的初始化材料

---

## 4. 四层门控体系（权威表）

| # | 门控名称 | 管什么 | 工具 | 谁触发 | 是否阻塞 |
|---|----------|--------|------|--------|----------|
| 1 | PRAE Phase Gate | 阶段 N → 阶段 N+1 转换决策 | `tools/check_phase_gate.py` | AI 生成 + 人工批准 | 是（阻塞下一阶段） |
| 2 | Research Gate | 研究轨道最低质量（实验日志、冒烟测试、参数记录） | `tools/check_research_gate.py` | 自动，研究轨道提交前 | 是（阻塞研究轨道提交） |
| 3 | Contracts Gate | 基础设施轨道边界合规（研究代码不违反契约） | `tools/check_contracts.py`（复用 PDAE，可用） | 自动，所有涉及基础设施调用的提交前 | 是 |
| 4 | PDAE M1-M3 Gate | 基础设施轨道和 shared 代码的工程质量 | PDAE 完整流程（可用） | 显式触发 | 是（阻塞 `EXPLORING → LOCKED`） |

**调用顺序建议**：
- 研究轨道提交：Research Gate → Contracts Gate
- 基础设施轨道 LOCKED：PDAE M3 Gate → Contracts Gate
- 阶段转换：Phase Gate（各轨道自身的门控应已在此之前通过）

**Research Gate 的 5 条检查项**：
```
✓ TRACK_LOG.md 有本次实验记录（目标、方法、结果、结论）
✓ 至少一个冒烟测试（能跑通、输出格式正确）
✓ 实验参数已记录（随机种子、超参数、数据时间范围）
✓ check_contracts 通过（不违反基础设施契约）
✓ 实验脚本在 experiments/ 下（不被其他代码 import）
✗ 不要求覆盖率
✗ 不要求设计评审
```

详见 `PRAE_RESEARCH_GATE.md`。

---

## 5. 代码目录的治理分级

| 目录 | 约束级别 | 谁管 | 允许的操作 |
|------|----------|------|-----------|
| `src/infra_{name}_v{N}/`（LOCKED） | 最严格 | PDAE + Contracts Gate | 只读；变更需开 v2 |
| `src/infra_{name}_v{N}/`（EXPLORING） | 严格 | 选型实验；LOCK 前必过 PDAE M1-M3 | 可修改，但目标是冻结 |
| `src/shared/` | 严格 | PDAE M3 单元门控 | 新增或修改均走 PDAE M3 |
| `src/tracks/{track_id}/impl/` | 中等 | Research Gate + Contracts Gate | 可修改，被二次 import 时必须迁移到 shared/ |
| `src/tracks/{track_id}/experiments/` | LOOSE | 仅 Research Gate | 自由修改、删除；**不可被其他代码 import** |

**关键约束**：
- `experiments/` 下的脚本**不能被 `impl/` 或其他轨道 import**。违反此规则会被 Contracts Gate / Research Gate 拦截
- 同一函数或模块被**第二处 import** 的瞬间，必须迁入 `shared/`，触发 PDAE M3
- 两条研究轨道**不允许直接相互 import**，只能通过 `shared/` 或基础设施轨道的公开接口交互

---

## 6. 关键约束汇总（硬性规则）

以下规则是 PRAE 方法论的硬约束，违反即视为破坏治理：

1. **LOCKED 不可修改规则**：基础设施轨道一旦 LOCKED，其 `src/infra_{name}_v{N}/` 目录只读
2. **v2 规则**：基础设施需求变更时，**新建 v2** 轨道而非解锁 v1
3. **单一真相来源规则**：轨道状态以 `track_registry.yaml` 为准；任何其他文件冲突时修正它们
4. **研究轨道不相互 import 规则**：共用代码必须进 `shared/`，禁止 `src/tracks/A/` import `src/tracks/B/`
5. **experiments/ 不可被 import 规则**：该目录下的脚本是丢弃型的，被 import 会破坏复现性
6. **终态不可回退规则**：KILLED / MERGED / GRADUATED / LOCKED 都是终态
7. **人工批准规则**：所有 Phase Gate 必须人工批准；AI 只生成建议，不直接推进阶段
8. **假设必须可证伪规则**：每条研究轨道的 `hypothesis` 必须是能被证据证伪的陈述，不能是"探索一下 X"这类开放句式
9. **依赖必须 LOCKED 规则**：研究轨道进入 `ACTIVE` 时，`depends_on` 中声明的基础设施轨道必须全部处于 `LOCKED` 状态。初始化（Phase 0）期间允许声明对尚未 LOCKED 的轨道的依赖，但该研究轨道不得激活（不可从 EXPLORING 进入 ACTIVE），直到所有依赖项 LOCKED

---

## 7. 与 PDAE 的边界

PRAE 管**决策**，PDAE 管**实现**。衔接点只有两个：

| 衔接事件 | PRAE 这边 | PDAE 这边 |
|---------|-----------|-----------|
| 基础设施轨道 `EXPLORING → LOCKED` | 产出 MODULE_SPEC.md 骨架、contracts.yaml 草稿 | 跑完 M1-M3，产出合格的实现 |
| 研究轨道 `ACTIVE → GRADUATED` | 冻结轨道代码，整理需求输入 | 从零或从研究代码启动新 M1-M3 流程 |

PRAE 不干涉 PDAE 内部流程，PDAE 不干涉 PRAE 的阶段推进。

---

## 8. 术语表（统一使用）

| 术语 | 含义 | 不要写成 |
|------|------|----------|
| 轨道（Track） | 一条独立研究或基础设施工作线 | 实验组、分支 |
| 阶段（Phase） | Phase 0/1/2/3 中的一个 | 里程碑、季度 |
| 实验（Experiment / EXP） | 一次带完整参数记录的可复现运行 | 跑一下、试试 |
| 证据（Evidence） | 实验结果中支持或证伪假设的部分 | 直觉、感觉 |
| 毕业（Graduate） | 研究轨道达到工程化条件，启动 PDAE | 上线、部署 |
| 基础设施（Infrastructure） | 数据管道、仿真器、数据库等非算法底座 | 底层、平台 |
