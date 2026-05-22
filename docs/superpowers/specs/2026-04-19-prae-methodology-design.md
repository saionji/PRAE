# PRAE Methodology Design Spec

**Date:** 2026-04-19
**Status:** Design Approved, Pre-Implementation
**Author:** saionji + Claude Code

---

## 1. 定位

**PRAE（Protocol-Driven Research & Experimentation）** 是 AI 辅助科学研究方法论。

它不是软件工程工具，而是：
> 让大模型充当研究助理，管理"哪条路值得走"的决策过程

核心循环：
```
问题陈述 → 基础设施就绪 → 算法并行探索 → 证据驱动收敛 → 结论 / 毕业
```

适用场景（领域无关）：
- 量化交易：数据管道（基础设施）+ 策略/模型（研究层）
- 机器人控制：传感器/仿真/上位机（基础设施）+ 控制算法（研究层）
- 目标检测：数据处理管道（基础设施）+ 检测算法（研究层）

---

## 2. 与 PDAE 的关系

| 维度 | PRAE | PDAE |
|------|------|------|
| 管什么 | 哪条路值得走（研究决策） | 怎么走得好（工程质量） |
| 终点 | 结论 / 毕业决定 | 可交付的软件单元 |
| 核心问题 | 假设是否成立？ | 实现是否符合规格？ |
| 不确定性 | 高（探索） | 低（交付） |

**PRAE 使用 PDAE 的时机：**
- 基础设施轨道锁定时 → 调用 PDAE M1→M3 完整工程流
- 共享代码（shared/）治理 → 调用 PDAE M3 单元门控
- 契约合规检查 → 复用 `check_contracts.py`

**PDAE 仓库位置：** `${PDAE_HOME}/`

---

## 3. 核心模型

### 3.1 两类轨道

**基础设施轨道（Infrastructure Track）**
- 目的：为研究提供可靠的数据/环境/工具基础
- 生命周期：`EXPLORING → [PDAE M1-M3] → LOCKED`
- 变更规则：不解锁，开 v2 新轨道；v1 目录只读
- 锁定后：受 PDAE 门控，有 contracts.yaml，任何修改走 PDAE 流程

**研究轨道（Research Track）**
- 目的：并行测试算法/策略假设，积累证据
- 生命周期：`EXPLORING → KILLED / MERGED / GRADUATED`
- 毕业规则：人工决定，无量化门槛

### 3.2 四个阶段

```
Phase 0  基础设施就绪期
         目标：把所有必要基础设施工程化并锁定
         门控：所有基础设施轨道状态 = LOCKED
         AI角色：分析者（选型建议）+ 执行者（PDAE实现）

Phase 1  算法探索期
         目标：并行启动多条研究轨道，快速积累信号
         门控：AI分析证据后建议推进 + 人工批准
         AI角色：分析者（文献检索、实验设计、结果解读）

Phase 2  算法验证期
         目标：收敛到主方案，淘汰/融合轨道
         门控：AI分析后建议结论 + 人工批准
         AI角色：分析者 + 执行者（成熟轨道开始工程化）

Phase 3  结论期
         目标：形成最终结论，决定归档或毕业进 PDAE
         门控：人工决定
         AI角色：文档整理，毕业方案的 PDAE 路由
```

### 3.3 轨道状态机

```
基础设施轨道：
  EXPLORING ──[实验确认方向]──▶ [PDAE M1-M3] ──▶ LOCKED
  LOCKED ──[需求变更]──▶ 新建 v2 轨道（v1 保持 LOCKED）

研究轨道：
  EXPLORING ──[有正向信号]──▶ ACTIVE
  ACTIVE ──[明显失败]──▶ KILLED
  ACTIVE ──[与其他轨道互补]──▶ MERGED
  ACTIVE ──[结论确定]──▶ GRADUATED
```

### 3.4 AI 角色绑定轨道状态

| 轨道状态 | AI 角色 | 具体工作 |
|----------|---------|----------|
| EXPLORING | 分析者 | 文献检索、实验设计、结果解读、选型建议 |
| LOCKED（实现期） | 执行者 | 写代码、跑 PDAE M1-M3 单元 |
| KILLED | — | 归档实验日志 |
| GRADUATED | 执行者 | 创建 PDAE 工程项目 |

---

## 4. 四层门控体系

| 门控 | 管什么 | 工具 | 触发方式 |
|------|--------|------|----------|
| PRAE Phase Gate | 阶段转换决策 | `check_phase_gate.py`（待建） | AI建议 + 人批准 |
| Research Gate | 研究代码最低质量 | `check_research_gate.py`（待建） | 自动，提交前 |
| Contracts Gate | 基础设施边界合规 | `check_contracts.py`（复用PDAE） | 自动，提交前 |
| PDAE M1-M3 Gate | 基础设施/共享代码工程质量 | PDAE 全套 | 显式触发 |

### Research Gate 检查项

```
✓ TRACK_LOG.md 有本次实验记录（目标、方法、结果、结论）
✓ 至少一个冒烟测试（能跑通、输出格式正确）
✓ 实验参数已记录（随机种子、超参数、数据时间范围）
✓ check_contracts 通过（不违反基础设施契约）
✗ 不要求覆盖率
✗ 不要求设计评审
```

---

## 5. 代码与文档结构

```
{project-name}/
├── CLAUDE.md                    ← AI会话上下文（从PRAE模板复制）
├── prae/                        ← 方法论文件
│   ├── PRAE_INIT.md             ← 问题陈述 + 组件分类（项目启动时填写）
│   ├── track_registry.yaml      ← 所有轨道状态总表（唯一真相来源）
│   └── phases/
│       ├── phase_00_infra/
│       │   ├── PHASE_BRIEF.md   ← 本阶段目标和成功标准
│       │   ├── PHASE_GATE.md    ← AI生成的阶段分析（人批准后归档）
│       │   └── tracks/
│       │       └── {track_id}/
│       │           ├── TRACK_LOG.md        ← 假设、实验列表、证据、状态
│       │           └── experiments/
│       │               └── EXP_001.md      ← 单次实验记录
│       └── phase_01_research/
│           └── ...
└── src/                         ← 所有代码
    ├── infra_{name}_v1/         ← 基础设施代码（LOCKED后只读）
    ├── infra_{name}_v2/         ← 版本升级时新建
    ├── shared/                  ← 多轨道共用代码（PDAE M3门控）
    └── tracks/
        └── {track_id}/          ← 研究轨道代码（内部LOOSE）
            ├── experiments/     ← 实验脚本（不被import，可丢弃）
            └── impl/            ← 成长后的实现代码
```

### 代码治理规则

- `experiments/` 下的脚本：完全 LOOSE，只记录结果，不被 import
- `impl/` 或 `tracks/{id}/` 下被第二处 import 的代码：必须移入 `shared/`，触发 PDAE M3
- `infra_*/` 目录：LOCKED 后只读，变更开 v2

---

## 6. PRAE_INIT.md 格式

项目启动时，研究员填写一次：

```markdown
# {项目名} — PRAE 初始化文档

## 问题陈述
[要解决什么研究问题，成功标准是什么]

## 组件分类

### 基础设施轨道
| 轨道ID | 描述 | 依赖 |
|--------|------|------|
| infra_data_v1 | 数据采集与存储 | — |

### 研究轨道
| 轨道ID | 假设 | 依赖的基础设施 |
|--------|------|---------------|
| research_strategy_momentum | 动量因子有效 | infra_data_v1 |

## Phase 0 成功标准
[所有基础设施轨道 LOCKED 的具体判断标准]
```

---

## 7. track_registry.yaml 格式

```yaml
project: {project-name}
updated: 2026-04-19

tracks:
  - id: infra_data_v1
    type: infrastructure
    state: LOCKED          # EXPLORING | LOCKED
    src: src/infra_data_v1/
    module_spec: src/infra_data_v1/MODULE_SPEC.md
    contracts: src/infra_data_v1/contracts.yaml
    locked_at: 2026-04-20

  - id: research_strategy_momentum
    type: research
    state: ACTIVE          # EXPLORING | ACTIVE | KILLED | MERGED | GRADUATED
    src: src/tracks/research_strategy_momentum/
    hypothesis: "动量因子在A股日频有效，夏普>1.0"
    depends_on: [infra_data_v1]
    experiments: 7
    evidence_summary: "回测夏普1.2，但换手率过高"
```

---

## 8. 待建工具

| 工具 | 用途 | 优先级 |
|------|------|--------|
| `tools/check_phase_gate.py` | 验证 PHASE_GATE.md 结构和阶段转换合法性 | P1 |
| `tools/check_research_gate.py` | 验证研究轨道最低质量标准 | P1 |
| `tools/check_track_status.py` | 检查 track_registry.yaml 一致性 | P2 |
| `tools/init_project.py` | 从模板初始化新 PRAE 项目 | P2 |
| `project-pack/` | 可部署到具体研究项目的模板包 | P3 |

复用 PDAE 工具（无需重建）：
- `check_contracts.py` → 直接从 PDAE 仓库调用或复制
- PDAE M1-M3 完整流程 → 基础设施轨道锁定时直接使用

---

## 9. 设计决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 基础设施变更策略 | 版本化（v2新轨道） | 保证历史实验可复现，v1不破坏 |
| 阶段转换触发 | AI建议+人批准 | 研究判断不能全自动化 |
| 研究代码治理 | 四层分级（LOOSE/Research Gate/Contracts/PDAE） | 避免过重约束扼杀探索 |
| PRAE与PDAE关系 | 并行两个治理维度，通过锁定事件衔接 | 不强耦合，各管各的 |
| 毕业标准 | 人工决定，无量化门槛 | 研究价值判断不能量化 |
