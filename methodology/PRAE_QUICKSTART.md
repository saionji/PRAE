# PRAE Quick Start

> **用途**: PRAE 的唯一主操作手册；从项目启动到毕业，按真实执行顺序说明 LLM 如何跑完整流程
> **读者**: LLM（你）
> **状态**: Active（PRAE v1.0）
> **最后更新**: 2026-04-21

---

## 1. 一句话定位

PRAE 管 **"哪条研究路线值得走"**，PDAE 管 **"怎么把代码做好"**。
你读完本页，就能开始在任意一个 PRAE 研究项目中执行方法论。

PRAE 不是开发流程，是研究决策协议。你的主要产出不是代码，而是：
- 证据记录（实验日志、假设验证结果）
- 决策建议（PHASE_GATE.md、轨道状态变更建议）
- 角色切换（分析者 ↔ 执行者）

---

## 2. 首次进入项目：必读文件顺序

这里说的是 **模型进入项目后的必读顺序**，不是项目安装命令顺序。  
如果项目还没接入 PRAE，项目操作入口仍然是 `/prae-bootstrap` / `prae bootstrap`。

当你被放进一个陌生的 PRAE 研究项目时，按以下顺序读文件（不要跳过，不要乱序）：

1. **项目根目录的 `CLAUDE.md` 或 `AGENTS.md`**
   建立项目上下文。若不存在，说明项目未部署 project-pack，你需要先按 PRAE_ARTIFACTS.md 创建。

2. **`methodology/PRAE_CORE_MODEL.md`（本目录同级）**
   掌握两类轨道、四个阶段、状态机的权威定义。

3. **`methodology/PRAE_ROLES.md`**
   确认你当前该扮演分析者还是执行者。

4. **项目的 `prae/PRAE_INIT.md`**
   读项目的问题陈述和组件分类。若不存在，当前工作就是产出它。

5. **项目的 `prae/track_registry.yaml`**
   读所有轨道的当前状态。这是**唯一真相来源**，任何轨道状态以此文件为准。
   若文件不存在，说明项目可能只完成了 bootstrap、尚未运行 `/prae-init`；先完成初始化。

6. **当前阶段目录 `prae/phases/phase_NN_*/PHASE_BRIEF.md`**
   读当前阶段目标和成功标准。

7. **相关轨道的 `TRACK_LOG.md` 和最近的 `experiments/EXP_NNN.md`**
   只读你本次任务涉及的轨道，不要读全部。

**上下文管理**：一次最多读 5-8 个文件。如果轨道很多，只挑当前任务相关的读。

---

## 3. 完整阶段流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRAE 完整生命周期                          │
└─────────────────────────────────────────────────────────────────┘

[项目启动]
   │
   │ 填写 PRAE_INIT.md，运行 /prae-init 生成 track_registry.yaml 和 Phase 0 工件
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 0  基础设施就绪期                                         │
│ 目标: 所有 infra_* 轨道 state = LOCKED                          │
│ AI 角色: 分析者（选型） → 执行者（PDAE M1-M3 实现）             │
│ 门控: 所有基础设施轨道均 LOCKED                                 │
└─────────────────────────────────────────────────────────────────┘
   │
   │ Phase Gate 0→1：AI 写 PHASE_GATE.md，人工批准
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1  算法探索期                                             │
│ 目标: 并行启动多条研究轨道，积累信号                            │
│ AI 角色: 分析者（文献检索、实验设计、结果解读）                 │
│ 门控: ≥1 条研究轨道 state = ACTIVE                              │
└─────────────────────────────────────────────────────────────────┘
   │
   │ Phase Gate 1→2：AI 写 PHASE_GATE.md，人工批准
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2  算法验证期                                             │
│ 目标: 收敛到主方案，淘汰/融合轨道                               │
│ AI 角色: 分析者 + 执行者（成熟轨道开始工程化）                  │
│ 门控: 所有 ACTIVE 研究轨道有明确结论                            │
└─────────────────────────────────────────────────────────────────┘
   │
   │ Phase Gate 2→3：AI 写 PHASE_GATE.md，人工批准
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3  结论期                                                 │
│ 目标: 形成最终结论，归档或毕业                                  │
│ AI 角色: 文档整理 / PDAE 路由                                   │
│ 门控: 人工决定                                                  │
└─────────────────────────────────────────────────────────────────┘
   │
   ├── 归档：项目结束
   └── 毕业（GRADUATED）：切换到 PDAE 仓库创建工程项目
```

---

## 4. 每个阶段 LLM 的典型动作

### 4.1 Phase 0 典型动作（基础设施就绪）

你在此阶段的 90% 时间是执行者，少量分析者。按顺序：

1. 读 `PRAE_INIT.md` 中列出的基础设施轨道，确认每个 `infra_*` 的目标。
2. 对每个 state=EXPLORING 的基础设施轨道：
   - 若该轨道尚未物化目录，先调用 `prae new-track <track_id>` 创建当前阶段目录和 `TRACK_LOG.md`
   - 分析者角色：调用 `prae new-exp <track_id>` 创建选型实验骨架（EXP_001、EXP_002）
   - 分析者角色：运行实验后调用 `prae record-result <track_id> <EXP_ID>`，把结果写回 `TRACK_LOG.md`
   - 选型定案后：切换执行者角色，触发 PDAE M1-M3 完整流程（见 PRAE_ROLES.md § 执行者 SOP）。
   - PDAE M3 通过后：人工批准，再调用 `prae lock-infra` / `tools/lock_infra_track.py`，将该轨道从 `EXPLORING` 正式改为 `LOCKED`。
3. 当所有 `infra_*` 轨道都 LOCKED，调用 `prae advance-phase` 生成 `phases/phase_00_infra/PHASE_GATE.md`。
4. 等人批准；批准后再次调用 `prae advance-phase`，此时应直接校验已批准 gate 并正式推进到 `phase_01_research`。若绕过 wrapper，也可直接运行 `python3 tools/check_phase_gate.py --project-dir . --check-approved` 后再运行 `python3 tools/advance_phase.py --project-dir .`。

### 4.2 Phase 1 典型动作（算法探索）

你在此阶段几乎只做分析者。按顺序：

1. 读 `PRAE_INIT.md` 的研究轨道列表。若某条新研究轨道尚未登记，先调用 `prae add-track ...`；已登记轨道调用 `prae new-track <track_id>` 物化当前阶段目录和 `TRACK_LOG.md`。
2. 调用 `prae new-exp <track_id>` 创建 `EXP_NNN.md` 和 `EXP_NNN.py`，先写清实验设计，再实现和运行。
3. 实验完成后调用 `prae record-result <track_id> <EXP_ID>`，把结果、证据摘要和待批准状态建议写回 `TRACK_LOG.md`。
4. 确认有正向信号时，先形成状态建议；人工批准后，调用 `prae update-track-state` / `tools/update_track_state.py` 将轨道从 `EXPLORING` 正式改为 `ACTIVE`。
5. 当 ≥1 条轨道 ACTIVE 且积累了足够证据时，调用 `prae advance-phase` 生成 `PHASE_GATE.md`；批准后再次调用同一命令，或直接运行 `tools/check_phase_gate.py --check-approved` + `tools/advance_phase.py` 正式推进到 Phase 2。

### 4.3 Phase 2 典型动作（算法验证）

分析者 + 部分执行者。按顺序：

1. 对每条 ACTIVE 研究轨道：
   - 读 `TRACK_LOG.md` 的历史证据
   - 调用 `prae new-exp <track_id>` 设计验证性实验（通常更严格：更长时间窗、更多样本、对照组）
   - 运行后调用 `prae record-result <track_id> <EXP_ID>`，形成 `KILLED` / `MERGED` / `GRADUATED` / 继续观察的建议
2. 人工批准后，对需要落库的终态调用 `prae update-track-state ...`；若为 `MERGED`，必须带 `--merged-into ...`。
3. 如果轨道判定为 `GRADUATED`：切换执行者角色，准备毕业到 PDAE；单轨道毕业登记走 `prae graduate <track_id>`。
4. 所有 ACTIVE 轨道都有结论后，调用 `prae advance-phase` 生成 Phase 2→3 的 `PHASE_GATE.md`；批准后再次调用同一命令，或直接运行 `tools/check_phase_gate.py --check-approved` + `tools/advance_phase.py` 正式推进到 Phase 3。

### 4.4 Phase 3 典型动作（结论）

文档整理为主。按顺序：

1. 进入 `phase_03_conclusion` 后，正式工具会生成 `phases/phase_03_conclusion/CONCLUSION.md`；AI 在此基础上补充项目级结论和 PDAE 路由信息。
2. 对每条 `GRADUATED` 轨道：切换 PDAE 仓库，启动工程项目；完成后调用 `prae graduate <track_id>` 回写 PRAE 留痕。
3. 人工在 `CONCLUSION.md` 填写结构化最终决定：
   - `ARCHIVED` / `GRADUATED_TO_PDAE`：调用 `prae finalize`
   - `CONTINUE`：调用 `prae reopen`
4. `KILLED` / `MERGED` 轨道日志保持可追溯，不删除。

---

## 5. Slash Command 索引表

（此表列出 PRAE 执行层提供的命令；具体实现见 `runtime/claude-code/commands/`）

| 命令 | 作用 | 何时用 |
|------|------|--------|
| `/prae-bootstrap` | 将 PRAE 最小骨架、模板、tools 和运行时命令部署到当前研究项目 | 新项目第一次安装 PRAE 时 |
| `/prae-init` | 从 `PRAE_INIT.md` 生成 `track_registry.yaml` 和 Phase 0 工件（`PHASE_BRIEF.md`、基础设施 `TRACK_LOG.md`） | 项目第一次启动时 |
| `/prae-add-track <id>` | 正式向 `track_registry.yaml` 注册新轨道 | 需要新增尚未登记的基础设施或研究轨道时 |
| `/prae-new-track <id>` | 为已登记轨道创建当前阶段目录和 `TRACK_LOG.md` 骨架 | `init` 后启用轨道，或进入新阶段时 |
| `/prae-new-exp <track_id>` | 在当前轨道下创建 EXP_NNN.md 记录文件和 EXP_NNN.py 代码骨架 | 每次开始一次新实验时 |
| `/prae-record-result <track_id> <exp_id>` | 将实验结果写入 TRACK_LOG，更新 evidence_summary；若有状态建议，同步写入待批准 `Decision Log` | 实验跑完后记录结果时 |
| `/prae-lock-infra <track_id>` | 在人工批准后正式将基础设施轨道更新为 `LOCKED`，并写入 `Decision Log` | Phase 0 基础设施完成 PDAE M3 后 |
| `/prae-update-track-state <track_id> <state>` | 在人工批准后正式更新研究轨道状态，并写入 `Decision Log` | 需要把建议状态变更落库时 |
| `/prae-advance-phase` | 首次调用生成 PHASE_GATE.md；已批准时校验 gate 并正式推进阶段 | 认为可以进入下一阶段时 |
| `/prae-graduate <track_id>` | 验证毕业条件，切换到 PDAE 仓库创建工程项目，更新 registry | 研究轨道通过验证，需要毕业时 |
| `/prae-finalize` | 校验并登记项目终态决定 | Phase 3 人工决定为 `ARCHIVED` 或 `GRADUATED_TO_PDAE` 时 |
| `/prae-reopen` | 根据 `CONTINUE` 决定归档旧轮次并重开到 Phase 1 | Phase 3 人工决定为 `CONTINUE` 时 |

**找不到对应命令怎么办**：优先恢复 wrapper 或直接调用对应 `tools/*.py`。只有在仓库损坏、工具缺失且用户明确要求时，才临时做手工补救；补救完成后应尽快回到正式工具路径。

---

## 6. 工具调用速查

```bash
# Phase Gate 检查（检查推进到下一阶段的门控条件）
python3 tools/check_phase_gate.py --project-dir . --phase 0   # Phase 0→1
python3 tools/check_phase_gate.py --project-dir . --phase 1   # Phase 1→2
python3 tools/check_phase_gate.py --project-dir . --check-approved  # 检查已批准

# Research Gate 检查
python3 tools/check_research_gate.py --project-dir . --track-id research_strategy_momentum

# 轨道状态一致性
python3 tools/check_track_status.py --project-dir .

# Contracts Gate（已随 bootstrap 部署到本地 tools/）
python3 tools/check_contracts.py \
  --contracts src/infra_data_v1/contracts.yaml --src src/

# PDAE M1-M3（基础设施轨道锁定时调用）
cd ${PDAE_HOME}
python3 tools/check_unit_gate.py --unit architect_m3 \
  --module-spec /path/to/project/src/infra_data_v1/MODULE_SPEC.md
```

---

## 7. 何时切换角色

- 你正在读文献、写假设、设计实验、解读结果 → **分析者**
- 你正在写基础设施代码、跑 PDAE 单元、填 MODULE_SPEC.md → **执行者**
- 轨道从 `EXPLORING` 跨进 PDAE 流程时，从分析者切到执行者
- PDAE 完成、轨道 LOCKED 后，回到分析者继续观察后续研究轨道

详见 `PRAE_ROLES.md`。

---

## 8. 常见问题与故障恢复

### Q1: `track_registry.yaml` 和某个 `TRACK_LOG.md` 状态不一致
以 `track_registry.yaml` 为准。它是唯一真相来源。修正 `TRACK_LOG.md` 开头的状态字段与 registry 对齐。

### Q2: 基础设施轨道 LOCKED 后，发现需求变更
**不要修改 v1**。在 `track_registry.yaml` 新增 `infra_{name}_v2` 条目，state = EXPLORING。v1 保持 LOCKED 只读。所有依赖 v1 的研究轨道暂时继续用 v1，直到 v2 稳定再逐轨道切换。

### Q3: 研究轨道同时有两条路线，想探索哪条更好
不要在同一轨道里比较。**拆成两条独立研究轨道**（例如 `research_momentum_daily` 和 `research_momentum_weekly`），各自跑实验，在 Phase 2 决定 KILL / MERGE / GRADUATE。

### Q4: 发现两个研究轨道用了相同的辅助函数
该函数已被第二处 import，必须移入 `src/shared/`，并对该文件触发 PDAE M3 门控。不要在 `src/tracks/*/` 之间交叉 import。

### Q5: `experiments/` 下的脚本越写越杂乱
正常。`experiments/` 下是 LOOSE 区，只记录结果，不作为后续代码的依赖源。只有 `impl/` 或移入 `shared/` 的代码才受门控。

### Q6: PHASE_GATE.md 被人工驳回
读驳回原因，按 `PRAE_PHASE_GATES.md` 的"常见阻塞"章节修正。通常是证据不足、轨道结论不明、或基础设施未全部 LOCKED。

### Q7: 不确定当前处于哪个 Phase
看 `track_registry.yaml` 的 `current_phase` 字段（若无此字段，看 `phases/` 下最大的 phase 目录编号）。若 `PHASE_GATE.md` 最新一份处于"待批准"，仍在当前阶段。

### Q8: Contracts Gate 失败
读报错，通常是研究代码 import 了基础设施轨道的内部符号。修正方法：只通过基础设施轨道 `contracts.yaml` 声明的公开接口访问。

---

## 9. 本页关键规则回顾

1. 本页是 PRAE 的唯一主操作手册
2. `track_registry.yaml` 是轨道状态的唯一真相来源
3. 基础设施轨道 LOCKED 后不可修改，变更开 v2
4. 研究轨道结论必须有证据支持，不靠主观判断
5. 阶段转换必须经人工批准，AI 只生成建议
6. 研究代码在 `experiments/` 下 LOOSE，被复用的代码进 `shared/` 受 PDAE 管
