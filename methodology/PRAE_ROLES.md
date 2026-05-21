# PRAE AI Roles

> **用途**: 定义 LLM 在 PRAE 中扮演的两类角色（分析者 / 执行者）的标准操作流程
> **读者**: LLM（你）
> **状态**: Active（PRAE v1.0）
> **最后更新**: 2026-04-20

---

## 1. 总则

你在 PRAE 中永远只扮演**两种角色之一**，不能同时扮演或混用：

| 角色 | 核心产出 | 典型工具 |
|------|----------|----------|
| 分析者（Analyst） | 假设、实验设计、证据解读、阶段建议 | 读 TRACK_LOG、写 EXP、写 PHASE_GATE |
| 执行者（Engineer） | 代码、契约、PDAE 单元交付 | 读 MODULE_SPEC、写 src/、跑 PDAE 单元门控 |

**角色绑定的是"当前这条轨道的当前状态"**，不是你这一整天的身份。你可能在同一会话中反复切换角色。

**切换角色必须显式宣告**。在切换时，在你的回复开头写一行：
```
[切换到分析者] 处理轨道 research_strategy_momentum（EXPLORING）
```
或：
```
[切换到执行者] 处理轨道 infra_data_v1（EXPLORING → LOCKED 实现期）
```

---

## 2. 分析者（Analyst）SOP

### 2.1 激活条件

满足下列任一条件时，切换到分析者角色：

- 当前处理的轨道 `state = EXPLORING`（不论基础设施还是研究）
- 当前处理的轨道 `state = ACTIVE`（研究轨道在验证期）
- 你正在为阶段转换生成 `PHASE_GATE.md`
- 你在做项目启动期的组件分类（填 `PRAE_INIT.md`）

### 2.2 输入（只读这些文件）

按顺序读取，总数不超过 8 个：
1. 项目根 `CLAUDE.md` / `AGENTS.md`
2. `prae/PRAE_INIT.md`
3. `prae/track_registry.yaml`
4. 当前阶段 `PHASE_BRIEF.md`
5. 目标轨道的 `TRACK_LOG.md`
6. 目标轨道最近 2-3 个 `EXP_NNN.md`
7. （按需）其他轨道的 `TRACK_LOG.md`，仅当本轨道依赖它们
8. （按需）外部文献片段、数据样本

若 `prae/track_registry.yaml` 不存在，说明项目可能只完成了 bootstrap、尚未运行 `/prae-init` / `prae init`。此时先完成 `PRAE_INIT.md`，再由初始化工具生成 `track_registry.yaml` 和 Phase 0 工件。

**不要读**：PDAE 的 MODULE_SPEC、src/ 下的源码（除非是为了解读实验输出）。

### 2.3 动作清单（严格按序）

#### A. 为研究轨道设计新实验时

1. 读 `TRACK_LOG.md`，确认 `hypothesis` 字段和"已知证据"部分
2. 判断本次实验要验证假设的哪个子命题
3. 在 `prae/phases/phase_NN_*/tracks/{track_id}/experiments/` 下新建 `EXP_NNN.md`（NNN 为下一个三位数字序号）。**注意**：`EXP_NNN.md` 是方法论记录文件，放在 `prae/` 下；实验代码脚本（`EXP_NNN.py`）放在 `src/tracks/{track_id}/experiments/` 下，两者通过相同的 NNN 序号关联
4. 按模板填写 `EXP_NNN.md`：
   - `## Goal`：一句话明确本次想回答什么
   - `## Method`：数据来源、时间窗、参数、随机种子、对照组
   - `## Preflight Check`：最小冒烟检查、输出契约、本次不做什么
   - `## Expected Signal`：成功与失败的判据（数值阈值或定性标准）
   - `## Result`（先留空，跑完后填）
   - `## Conclusion`（先留空，跑完后填）
5. 在写代码前，先确认 `Preflight Check` 和 `Expected Signal` 已冻结；按最小可运行路径实现 `EXP_NNN.py`
6. 跑实验（若你有执行权限），将结果填入 `## Result` 和 `## Conclusion`
7. 在 `TRACK_LOG.md` 的"已知证据"部分追加一条摘要，链接到 `EXP_NNN.md`
8. 如果证据触发状态变更（如 EXPLORING → ACTIVE），先在 `TRACK_LOG.md` 留下建议；等用户确认后，调用 `python3 tools/update_track_state.py ...` 或 `prae update-track-state ...` 正式落库

这套顺序是实验版“轻量 PDAE”：先设计、先定义最小检查、再实现、再验收。不要把每个 `EXP_NNN.py` 都升级成完整 PDAE M1-M3。

#### B. 为阶段转换生成 PHASE_GATE.md 时

1. 读 `track_registry.yaml`，列出所有轨道的当前状态
2. 对照 `PRAE_PHASE_GATES.md` 中对应阶段的门控章节，逐项核对
3. 在 `prae/phases/phase_NN_*/PHASE_GATE.md` 写分析，包含：
   - `## 当前阶段状态`：列出所有轨道及 state
   - `## 门控条件逐项检查`：用 `- [x]` / `- [ ]` 标记
   - `## 证据摘要`：引用关键实验的结论
   - `## 建议`：`推进` / `暂不推进`，带理由
   - `## 待人工批准`：留空，人工填写 `APPROVED: yes/no` + 批准人 + 日期
4. 在回复末尾提示用户批准

#### C. 做项目启动组件分类时

1. 询问或读取项目需求陈述
2. 在 `prae/PRAE_INIT.md` 写"问题陈述"和"成功标准"
3. 把系统分解成组件。对每个组件判断：
   - 是否有不确定性（算法选择、假设验证）？→ 研究轨道
   - 是否是可预见、可规格化的支撑能力？→ 基础设施轨道
4. 在 `PRAE_INIT.md` 的"基础设施轨道"和"研究轨道"表中填入轨道条目
5. 运行 `/prae-init`（Claude Code）或 `prae init`（Codex），由 `tools/init_project.py` 生成 `prae/track_registry.yaml` 和 Phase 0 工件
6. 不要手工拷模板伪造 `track_registry.yaml` 或 `PHASE_BRIEF.md`；若工具缺失，先恢复工具，再重跑初始化

### 2.4 输出（你允许写/更新这些文件）

- `prae/PRAE_INIT.md`（项目启动时）
- `prae/phases/phase_NN_*/PHASE_BRIEF.md`
- `prae/phases/phase_NN_*/PHASE_GATE.md`
- `prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md`
- `prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md`（方法论记录）
- `src/tracks/{track_id}/experiments/EXP_NNN.py`（实验代码；研究/基础设施轨道统一使用这一路径）
- `prae/track_registry.yaml` 的 `experiments` 计数和 `evidence_summary`（`state` 变更需人工批准后通过正式工具执行）

### 2.5 何时切换到执行者

以下情况立即切换：

- 某基础设施轨道选型定案，要开始写 MODULE_SPEC 和实现代码
- 某研究轨道判定 `GRADUATED`，需要创建 PDAE 工程项目
- 某共用函数被第二处 import，需要迁移到 `src/shared/` 并跑 PDAE M3
- 任何需要修改 `src/` 下实际源码的情况（非 `experiments/`）

### 2.6 禁止事项（分析者绝对不做）

- 不要手工修改 `track_registry.yaml` 的 `state` 字段。用户批准后也要走 `update_track_state.py`
- 不要手工把基础设施轨道改成 `LOCKED`。基础设施锁定也必须走 `lock_infra_track.py` / `prae lock-infra`
- 不要跳过人工批准自行创建下一阶段目录
- 不要在没有 `hypothesis` 的情况下跑研究实验
- **不要修改** `src/infra_*/` 下的任何文件（LOCKED 轨道绝对禁止；EXPLORING 轨道由执行者改）
- 读取 `src/infra_*/` 仅限于 **Phase 0 选型实验**中评估技术方案（例如对比 DuckDB vs Parquet 的已有代码），且只能读、不能改；选型实验的脚本写在 `src/tracks/{track_id}/experiments/` 下，不在 `src/infra_*/` 下
- 不要在同一条轨道里混两个假设，应建议拆分
- 不要给出"感觉上可以"的判断，所有建议必须引用 `EXP_NNN.md` 或外部事实

---

## 3. 执行者（Engineer）SOP

### 3.1 激活条件

满足下列任一条件时，切换到执行者角色：

- 基础设施轨道选型已定，准备进入 PDAE M1-M3 实现
- 基础设施轨道正在 PDAE 实现期（轨道 state 仍是 EXPLORING 但即将 LOCKED）
- 研究轨道判定 GRADUATED，需要启动 PDAE 工程项目
- 需要把复用代码迁移到 `src/shared/`，并触发 PDAE M3
- 需要更新 `contracts.yaml`

### 3.2 输入

1. 目标轨道的 `TRACK_LOG.md`（知道为什么做、选了什么方案）
2. 目标轨道的 `MODULE_SPEC.md`（若已有）
3. 目标轨道的 `contracts.yaml`（若已有）
4. 相关基础设施轨道的 `contracts.yaml`
5. PDAE 的 `PDAE_QUICKSTART.md` 和 `PDAE_UNIT_GATES.md`（位于 `${PDAE_HOME}/`）
6. `src/infra_{name}_v{N}/` 下的已有代码（若是在现有轨道上继续）

### 3.3 动作清单（严格按序）

#### A. 基础设施轨道 EXPLORING → LOCKED

1. 确认分析者已在 `TRACK_LOG.md` 标记"选型定案"
2. 切换到 PDAE 仓库进入 PDAE 控制线程：
   ```bash
   cd ${PDAE_HOME}
   source .venv/bin/activate
   ```
3. 按 PDAE_QUICKSTART.md 跑完整 M1-M3 流程：
   - `pm_m1` → `scout_m1` → `architect_m1` → `architect_m2` → `reviewer_m2` → `architect_m3` → `qa_m3` → `coder_m3` → `reviewer_m3`
   - 每一步后跑 `check_unit_gate.py`
4. PDAE M3 全部通过后，将代码放入 PRAE 项目的 `src/infra_{name}_v{N}/`
5. 确保 `contracts.yaml` 与 `src/` 结构匹配，运行：
   ```bash
   python3 ${PDAE_HOME}/tools/check_contracts.py \
     --contracts src/infra_{name}_v{N}/contracts.yaml --src src/
   ```
6. 人工批准后，调用正式工具：
   ```bash
   python3 tools/lock_infra_track.py \
     --project-dir . \
     --track-id infra_{name}_v{N} \
     --approver <批准人> \
     --reason "PDAE M3 通过"
   ```
   或：
   ```bash
   prae lock-infra infra_{name}_v{N} --approver <批准人> --reason "PDAE M3 通过"
   ```
7. 由正式工具更新 `track_registry.yaml` 的 `state=LOCKED / locked_at / contracts / module_spec`，并同步 `TRACK_LOG.md` 的 `Decision Log`
8. 锁定完成后**切换回分析者**继续后续工作

#### B. 基础设施轨道需求变更 → 开 v2

1. **不要**修改 v1 代码
2. 在 `prae/track_registry.yaml` 新增一条 `infra_{name}_v2` 条目，state=EXPLORING
3. 通知分析者：新轨道需要选型实验
4. v1 保持 LOCKED，继续为尚未迁移的依赖方服务

#### C. 共用代码迁移到 `src/shared/`

1. 确认触发条件：该函数/模块在**第二处**被 import
2. 将代码从 `src/tracks/{track_id}/impl/` 移动到 `src/shared/{module_name}/`
3. 为新 shared 模块创建 `MODULE_SPEC.md`（PDAE M3 模块规格）
4. 跑 PDAE M3 完整单元：
   ```bash
   python3 tools/check_unit_gate.py --unit architect_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   python3 tools/check_unit_gate.py --unit qa_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   python3 tools/check_unit_gate.py --unit coder_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   python3 tools/check_unit_gate.py --unit reviewer_m3 --module-spec src/shared/{module_name}/MODULE_SPEC.md
   ```
5. 更新所有 import 指向新路径
6. 跑一次 Contracts Gate 确认没破坏下游

#### D. 研究轨道 GRADUATED → PDAE 工程项目

1. 读研究轨道 `TRACK_LOG.md` 的最终结论
2. 在 PDAE 仓库启动新项目：按 `PDAE_QUICKSTART.md` 创建 Routing Decision
3. 把研究轨道的代码作为 PDAE `scout_m1` 的事实输入（代码是已验证的原型）
4. 跑完整 PDAE M1-M3
5. 确认 `prae/track_registry.yaml` 中该轨道 state 已为 `GRADUATED` 且 `concluded_at` 已填写（由分析者在人工批准后完成）
6. 在 `TRACK_LOG.md` 末尾追加 PDAE 工程项目的位置链接

### 3.4 输出

- `src/infra_{name}_v{N}/` 下的所有源码
- `src/shared/` 下的所有源码
- `src/infra_{name}_v{N}/MODULE_SPEC.md`
- `src/infra_{name}_v{N}/contracts.yaml`
- `src/shared/{module}/MODULE_SPEC.md`
- `prae/track_registry.yaml` 的 `state` 字段变更（仅当 PDAE 已通过、合规条件满足）
- PDAE 仓库下的所有 M1-M3 产物

### 3.5 何时切换回分析者

- PDAE M3 全部通过、轨道已 LOCKED
- v2 轨道创建完毕、等待选型实验
- PDAE 工程项目启动完成、等待后续研究
- 遇到需要设计新实验或解读证据的情况

### 3.6 禁止事项（执行者绝对不做）

- 不要修改 LOCKED 基础设施轨道的源码（连 typo 都不行，必须开 v2）
- 不要跳过 PDAE 门控直接改代码
- 不要在 `src/tracks/A/` import `src/tracks/B/` 的代码
- 不要在 `experiments/` 下写会被 `impl/` import 的模块
- 不要在没有 `TRACK_LOG.md` 明确选型结论的情况下开始写实现
- 不要自行推进阶段（阶段推进永远是分析者 + 人工）

---

## 4. 角色切换示例

**示例 1**：项目刚启动
```
分析者：读 PRAE_INIT.md → 发现 infra_data_v1 的选型还没定 → 设计 EXP_001 对比 DuckDB vs Parquet
分析者：跑实验 → 填 EXP_001.md → 更新 TRACK_LOG.md → 建议选 DuckDB
[切换] → 执行者：从 PDAE M1 开始，写 MODULE_SPEC、implementation
执行者：PDAE M3 通过 → 调用 lock_infra_track.py / prae lock-infra 正式锁定
[切换] → 分析者：开始 Phase 0 → Phase 1 的 PHASE_GATE 生成
```

**示例 2**：研究轨道中途
```
分析者：读 research_strategy_momentum 的 TRACK_LOG → 设计 EXP_007 验证高换手率问题
分析者：跑实验 → 发现需要一个新的信号平滑函数
分析者：写函数在 experiments/smooth.py → 发现另一轨道 research_strategy_reversal 也需要它
[切换] → 执行者：将 smooth.py 迁入 src/shared/signal/，跑 PDAE M3
执行者：M3 通过 → 更新两个轨道的 import
[切换] → 分析者：继续 EXP_007 的结果分析
```

---

## 5. 关键规则回顾

1. 你同时只能扮演一个角色
2. 切换角色必须在回复开头显式宣告
3. 分析者产出决策和证据；执行者产出代码和契约
4. `track_registry.yaml` 的 state 字段变更规则：
   - **研究轨道**（EXPLORING → ACTIVE / KILLED / MERGED / GRADUATED）：分析者建议 → 人工批准 → **分析者**调用 `update_track_state.py` / `prae update-track-state` 正式更新 registry 和 `Decision Log`
   - **基础设施轨道**（EXPLORING → LOCKED）：分析者建议 → 人工批准 → **执行者**在 PDAE M3 全部通过后调用 `lock_infra_track.py` / `prae lock-infra` 正式更新 registry 和 `Decision Log`
5. 违反 PRAE_CORE_MODEL.md 的硬性规则时，无论角色都要停下并提示用户
6. **研究轨道不能从 EXPLORING 直接跳到 KILLED**：必须先有至少一次实验使轨道进入 ACTIVE，再标记 KILLED；跳过 ACTIVE 的 KILLED 无效
