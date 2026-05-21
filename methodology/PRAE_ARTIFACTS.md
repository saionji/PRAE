# PRAE Artifacts

> **用途**: PRAE 所有工件的完整清单；谁创建、何时创建、如何更新、主要字段、相互关联
> **读者**: LLM（你）
> **状态**: Active（PRAE v1.0）
> **最后更新**: 2026-04-20

---

## 1. 工件总览

PRAE 工件分两大类：
- **方法论工件**：位于 `prae/` 下，描述研究过程和决策
- **代码工件**：位于 `src/` 下，研究代码和基础设施代码

下表按读取顺序列出。详细规格见后续章节。

| # | 文件 / 路径模式 | 创建者 | 何时创建 | 层次 |
|---|----------------|--------|----------|------|
| 1 | `CLAUDE.md` 或 `AGENTS.md` | 人工（初始化时） | 项目启动 | 项目级 |
| 2 | `prae/PRAE_INIT.md` | AI 分析者 + 人工确认 | 项目启动，只填一次 | 项目级 |
| 3 | `prae/track_registry.yaml` | AI 初始化，人工 + AI 共同维护 | 项目启动，持续更新 | 项目级 |
| 4 | `prae/phases/phase_NN_*/PHASE_BRIEF.md` | AI 分析者 | 阶段开始时 | 阶段级 |
| 5 | `prae/phases/phase_NN_*/PHASE_GATE.md` | AI 分析者 + 人工批准 | 阶段结束时 | 阶段级 |
| 6 | `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md` | AI 分析者 | 轨道进入阶段时 | 轨道级 |
| 7 | `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md` | AI 分析者 | 每次实验 | 实验级 |
| 8 | `src/tracks/{track_id}/experiments/EXP_NNN.py` | AI 分析者 | 每次实验（实验脚本代码） | 实验级 |
| 9 | `src/tracks/{track_id}/impl/*.py` | AI 分析者 / 执行者 | 成熟代码迁出 experiments 后 | 实现级 |
| 10 | `src/infra_{name}_v{N}/MODULE_SPEC.md` | AI 执行者（跑 PDAE） | 基础设施进入 PDAE M3 时 | 基础设施级 |
| 11 | `src/infra_{name}_v{N}/contracts.yaml` | AI 执行者 | 基础设施进入 PDAE M2 时 | 基础设施级 |
| 12 | `src/shared/{module}/MODULE_SPEC.md` | AI 执行者 | 代码迁入 shared 时 | 共享级 |
| 13 | `prae/phases/phase_03_conclusion/CONCLUSION.md` | AI 分析者 | Phase 3 | 项目级 |

---

## 2. 方法论工件详细规格

### 2.1 `CLAUDE.md` 或 `AGENTS.md`

- **作用**：LLM 进入项目时的首读上下文
- **创建者**：人工（部署 project-pack 时复制模板）
- **何时创建**：项目启动
- **更新规则**：每次项目重要结构变化时由人工更新
- **主要字段**：
  - 项目一句话描述
  - 与 PDAE 的关系
  - PRAE 核心模型快速参考
  - 仓库目录结构
  - 当前阶段和下一步
  - 常用命令
- **关联**：指向 `methodology/` 下所有方法论文档

### 2.2 `prae/PRAE_INIT.md`

- **作用**：项目启动时的问题陈述 + 组件分类
- **创建者**：AI 分析者起草，人工确认
- **何时创建**：项目启动期，只填一次
- **更新规则**：原则上不改。若项目中途发现组件分类错误，在 `CHANGE_LOG` 节追加记录，不删原内容
- **主要字段（必填）**：
  - `## 问题陈述`：研究要解决什么、成功标准是什么
  - `## 组件分类 → 基础设施轨道`：表格（轨道ID / 描述 / 依赖）
  - `## 组件分类 → 研究轨道`：表格（轨道ID / 假设 / 依赖的基础设施）
  - `## Phase 0 成功标准`：所有基础设施 LOCKED 的具体判断标准
- **关联**：
  - 所有轨道 ID 必须同步登记到 `track_registry.yaml`
  - 每条研究轨道的 `hypothesis` 必须与后续 `TRACK_LOG.md` 一致

### 2.3 `prae/track_registry.yaml`

- **作用**：所有轨道状态的**唯一真相来源**
- **创建者**：AI 从 `PRAE_INIT.md` 初始化
- **何时创建**：项目启动
- **更新规则**：
  - state 字段变更：AI 建议 → 人工批准 → 执行者在该文件落盘
  - experiments 计数、evidence_summary：AI 可直接更新
  - `current_phase` 字段：阶段门控批准后立即更新
  - 项目收尾字段：`ARCHIVED / GRADUATED_TO_PDAE` 由终态工具写入；`CONTINUE` 由 reopen 工具写入
- **主要字段**（项目级，可选）：
  - `project_decision`
  - `project_approver`
  - `project_decided_at`
  - `project_reopened_at`（仅 `CONTINUE`）
  - `project_finalized_at`（仅终态决定）
  - `archived_at`（仅 `ARCHIVED`）
- **主要字段**（每条 track）：
  - `id`（必填，前缀 `infra_` 或 `research_`）
  - `type`（`infrastructure` 或 `research`）
  - `state`（见 PRAE_CORE_MODEL.md § 2）
  - `src`（源码目录路径）
  - 基础设施专属：`module_spec`、`contracts`、`locked_at`
  - 研究专属：`hypothesis`、`depends_on`、`experiments`、`evidence_summary`、`concluded_at`、`merged_into`
- **关联**：
  - 所有轨道 ID 与 `PRAE_INIT.md` 一致
  - `src` 路径必须与真实目录匹配
  - 基础设施 `contracts` 必须对应真实存在的 contracts.yaml

**示例**：
```yaml
project: sonar-detection
current_cycle: 1
current_phase: phase_01_research
updated: 2026-04-22
project_decision: GRADUATED_TO_PDAE
project_approver: saionji
project_decided_at: 2026-04-22
project_finalized_at: 2026-04-22

tracks:
  - id: infra_data_v1
    type: infrastructure
    state: LOCKED
    src: src/infra_data_v1/
    module_spec: src/infra_data_v1/MODULE_SPEC.md
    contracts: src/infra_data_v1/contracts.yaml
    locked_at: 2026-04-18

  - id: research_detector_cnn
    type: research
    state: ACTIVE
    src: src/tracks/research_detector_cnn/
    hypothesis: "CNN 在低 SNR 场景下 recall ≥ 0.85"
    depends_on: [infra_data_v1]
    experiments: 3
    evidence_summary: "初步 recall 0.78，F1 0.72；需补短时段实验"
```

如项目在 `Phase 3` 被人工判定 `DECISION: CONTINUE`，则工具会把旧轮次的 `phase_01/02/03` 目录归档到 `prae/history/cycle_N/phases/`，并把 `current_cycle` 递增到下一轮。

### 2.4 `prae/phases/phase_NN_{name}/PHASE_BRIEF.md`

- **作用**：本阶段目标和成功标准
- **创建者**：AI 分析者
- **何时创建**：上一阶段 PHASE_GATE 批准后立即创建本阶段目录时
- **更新规则**：阶段内可微调（例如新增一条研究轨道），不能改变阶段整体目标
- **主要字段**：
  - `## 阶段目标`
  - `## 成功标准`（对应退出门控）
  - `## 本阶段在场的轨道`
  - `## 关键时间节点`（可选）
- **关联**：指向所属阶段的 PHASE_GATE.md（未生成前留空）

### 2.5 `prae/phases/phase_NN_{name}/PHASE_GATE.md`

- **作用**：阶段转换的决策记录和批准留痕
- **创建者**：AI 分析者生成；人工批准
- **何时创建**：认为可以进入下一阶段时，由 AI 主动生成（或 `/prae-advance-phase` 触发）
- **更新规则**：固定文件名为 `PHASE_GATE.md`。重新生成时可以覆盖同一文件，但应保留第 6 节人工填写的审批字段；批准后若要真正推进阶段，必须调用正式工具，而不是仅靠填写 `APPROVED` 生效
- **主要字段**（6 节，见 PRAE_PHASE_GATES.md § 2）：
  - `**研究轮次**: cycle_N`
  1. 当前阶段状态
  2. 门控条件逐项检查
  3. 证据摘要
  4. 风险与未决项
  5. 建议
  6. 待人工批准（APPROVED 字段）
- **关联**：
  - 引用 `track_registry.yaml` 的状态
  - 引用各轨道 `TRACK_LOG.md` 和 `EXP_NNN.md`
  - 批准后触发 `current_phase` 更新和下一阶段目录创建

### 2.6 `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md`

- **作用**：轨道在本阶段的叙事；假设、已知证据、实验列表、当前状态
- **创建者**：AI 分析者
- **何时创建**：轨道首次出现在某阶段时（Phase 1 时每条研究轨道都要有）
- **路径规则**：`TRACK_LOG.md` 的**唯一**正确路径是 `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md`。它是方法论工件，位于 `prae/` 目录树下，**不在 `src/` 下**。
- **更新规则**：每次实验、每次状态变更都要追加条目；研究轨道状态变更应通过 `update_track_state.py` / `prae update-track-state` 同步到这里；不删历史
- **主要字段**：
  - `**研究轮次**: cycle_N`（必须与 `track_registry.yaml.current_cycle` 一致）
  - `## Hypothesis`（研究轨道）/ `## 选型目标`（基础设施轨道）
  - `## State` + `## Depends On`
  - `## Experiments`（表格：EXP_ID / 日期 / 目的 / 结论 / 链接到对应 EXP_NNN.md）
  - `## Evidence Summary`（每次实验后追加一段）
  - `## Decision Log`（状态变更记录：何时由 EXPLORING 变 ACTIVE，谁建议，谁批准）
- **关联**：
  - 引用同轨道下的实验记录 `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md`
  - `**研究轮次**` 必须匹配当前轮次；`CONTINUE` 后新轮次的 `TRACK_LOG.md` 重新建在新阶段目录，旧轮次历史留在 `prae/history/cycle_N/phases/`
  - 向上被 `PHASE_GATE.md` 引用

### 2.7 `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md`

- **作用**：单次实验的完整方法论记录（目标、方法、结果、结论）
- **创建者**：AI 分析者
- **何时创建**：每次开始新实验时
- **路径规则**：EXP_NNN.md 是**方法论工件**，位于 `prae/` 目录树下，**不在 `src/` 下**。与它配对的实验代码 `EXP_NNN.py` 在 `src/tracks/{track_id}/experiments/` 下，两者通过相同的 NNN 序号关联
- **更新规则**：`## Result` 和 `## Conclusion` 在实验跑完后填写；此后不再改动
- **主要字段**（必填）：
  - `## Goal`：一句话目标
  - `## Method`：数据源、时间窗、随机种子、超参数、对照组
  - `## Preflight Check`：最小冒烟检查、输出契约、本次不做什么
  - `## Expected Signal`：成功与失败判据
  - `## Result`：数值、图表位置、原始输出路径
  - `## Conclusion`：支持 / 证伪 / 部分支持假设，以及对轨道状态的建议
- **编码顺序**：采用实验版“轻量 PDAE”流程：先 `Goal / Method`，再写 `Preflight Check` 和 `Expected Signal`，再实现 `EXP_NNN.py`，最后按验收结果填写 `Result / Conclusion`
- **编号规则**：三位数字，从 EXP_001 起；删除后编号不回收
- **关联**：被 `TRACK_LOG.md` 的 Experiments 表格引用；链接格式为相对路径 `experiments/EXP_NNN.md`

### 2.8 `prae/phases/phase_03_conclusion/CONCLUSION.md`

- **作用**：项目最终结论
- **创建者**：AI 分析者
- **何时创建**：Phase 3
- **更新规则**：可多次修改直到人工决定归档 / 毕业
- **主要字段**：
  - `## 项目结论`
  - `## 各轨道去向`
  - `## 毕业轨道的 PDAE 项目链接`
  - `## 未解决问题`
  - `## 最终决定`
  - `APPROVED: <pending | yes | no>`
  - `DECISION: <ARCHIVED | GRADUATED_TO_PDAE | CONTINUE>`
  - `APPROVER: <用户姓名或标识>`
  - `APPROVED_AT: <YYYY-MM-DD>`
  - `COMMENT: <可选，人工补充说明>`
- **关联**：
  - 汇总所有轨道的 `TRACK_LOG.md` 最终结论
  - 被 `PHASE_GATE.md`（Phase 2→3）批准后创建

---

## 3. 代码工件详细规格

### 3.1 `src/tracks/{track_id}/experiments/EXP_NNN.py`（或其他脚本）

- **作用**：实验的可执行脚本
- **创建者**：AI 分析者
- **更新规则**：每次改动视为新实验（新 `EXP_NNN.md` + 新 `EXP_NNN.py`），不在同一个文件里反复改
- **关键约束**：**不能被其他代码 import**（Research Gate 规则 5）
- **推荐流程**：实现前先在配对的 `EXP_NNN.md` 里写清 `Preflight Check`；代码优先满足最小可运行与输出契约，不提前工程化

### 3.3 `src/tracks/{track_id}/impl/*.py`

- **作用**：从 experiments/ 提炼出的稳定实现代码
- **创建者**：AI 执行者（分析者发现需要提炼时，需先切换到执行者角色再创建）
- **何时创建**：同一段逻辑在多个 EXP 中被重复用时迁移到此
- **更新规则**：正常 Python 模块；被第二处其他轨道 import 时**必须**迁入 `src/shared/`
- **关键约束**：可 import `src/shared/` 和基础设施轨道的 `contracts.yaml` 声明的公开符号；不可 import 自身轨道的 `experiments/`

### 3.4 `src/infra_{name}_v{N}/MODULE_SPEC.md`

- **作用**：基础设施轨道的 PDAE 模块规格
- **创建者**：AI 执行者（跑 PDAE M1 时）
- **何时创建**：基础设施轨道进入 PDAE 实现期
- **更新规则**：LOCKED 后只读；有变更需求时开 v2 新轨道和新 MODULE_SPEC
- **主要字段**：遵循 PDAE `MODULE_SPEC_TEMPLATE.md` 格式
- **关联**：与 `contracts.yaml` 严格对应；与 `track_registry.yaml` 的 `module_spec` 字段路径一致

### 3.5 `src/infra_{name}_v{N}/contracts.yaml`

- **作用**：基础设施轨道对外暴露的公开接口契约
- **创建者**：AI 执行者
- **何时创建**：PDAE M2 阶段
- **更新规则**：LOCKED 后只读；`check_contracts.py` 会校验所有 import 不越界
- **主要字段**：遵循 PDAE `CONTRACTS_SPEC.md`
- **关联**：
  - 所有研究轨道只能 import 此文件声明的符号
  - 与真实源码符号对齐（由 `check_contracts.py` 强制）

### 3.6 `src/shared/{module}/MODULE_SPEC.md`

- **作用**：跨轨道共用代码的 PDAE M3 模块规格
- **创建者**：AI 执行者
- **何时创建**：某代码被第二处轨道 import，迁入 shared 时
- **更新规则**：修改需走 PDAE M3（`architect_m3 → qa_m3 → coder_m3 → reviewer_m3`）
- **关联**：被至少两个轨道的 `impl/` 代码 import

---

## 4. 工件关联图

```
CLAUDE.md
   │
   ▼
PRAE_INIT.md ──────────────┐
   │                       │
   ▼                       ▼
track_registry.yaml ◀──▶ PHASE_BRIEF.md ──▶ PHASE_GATE.md
   │                       │
   │                       ▼
   │                    TRACK_LOG.md ──▶ EXP_NNN.md ──▶ EXP_NNN.py
   │                                         │
   │                                         ▼
   │                                      impl/*.py ──▶ shared/{module}/MODULE_SPEC.md
   │
   ▼
infra_{name}_v{N}/MODULE_SPEC.md
infra_{name}_v{N}/contracts.yaml ◀── check_contracts.py 强制校验 ── 所有 src/ 下代码
```

---

## 5. 命名约定

| 对象 | 规则 | 示例 |
|------|------|------|
| 基础设施轨道 ID | `infra_{name}_v{N}` | `infra_data_v1`、`infra_sim_v2` |
| 研究轨道 ID | `research_{topic}_{variant}` | `research_detector_cnn`、`research_strategy_momentum` |
| 阶段目录 | `phase_{NN}_{name}` | `phase_00_infra`、`phase_01_research` |
| 实验文件 | `EXP_{NNN}.md` / `EXP_{NNN}.py` | `EXP_001.md`、`EXP_047.py` |
| shared 模块 | `shared/{snake_case_name}/` | `shared/signal_utils/` |

---

## 6. 关键规则回顾

1. 每个工件都有明确的创建者和更新规则，不要越界
2. `track_registry.yaml` 是唯一真相来源
3. LOCKED 基础设施轨道的所有工件（源码、MODULE_SPEC、contracts.yaml）都只读
4. `experiments/` 下的脚本永远不被其他代码 import
5. `PHASE_GATE.md` 固定使用同一文件名；重新生成时保留审批区，批准后通过正式工具推进阶段
6. 工件之间的引用关系必须保持一致（轨道 ID、路径、阶段名）
