# PRAE Phase Gates

> **用途**: 四个阶段门控的自然语言规则；AI 写哪份文件、写什么、人工如何批准、批准后做什么
> **读者**: LLM（你）
> **状态**: Active（PRAE v1.0）
> **最后更新**: 2026-04-19

---

## 1. 总则

PRAE 阶段门控 = **AI 分析 + 人工批准** 的两步机制。

- AI 生成 `PHASE_GATE.md`：列出证据、检查门控条件、给出推进建议
- 人工在 `PHASE_GATE.md` 末尾填写 `APPROVED` 字段：留下批准记录
- 批准后，必须通过正式工具推进：再次调用 `prae advance-phase`，或运行 `tools/check_phase_gate.py --check-approved` + `tools/advance_phase.py`

**你（AI）永远不直接推进阶段**。哪怕条件全部满足，也要停下等用户批准。

**工具**：`tools/check_phase_gate.py` 用于验证 `PHASE_GATE.md` 的结构合法性和阶段转换合法性。

---

## 2. 通用 PHASE_GATE.md 结构

所有 `PHASE_GATE.md` 必须包含以下章节（缺任一节即视为不合规）：

```markdown
# Phase {from} → Phase {to} 门控分析

**生成日期**: YYYY-MM-DD
**生成者**: AI（分析者角色）
**目标阶段**: phase_NN_xxx

## 1. 当前阶段状态
（列出 track_registry.yaml 中所有轨道的 id、type、state）

## 2. 门控条件逐项检查
- [x] 条件 1（已满足）
- [ ] 条件 2（未满足）
...

## 3. 证据摘要
（每条关键证据 1-2 句，链接到 EXP_NNN.md 或 TRACK_LOG.md）

## 4. 风险与未决项
（可能影响下一阶段的风险、尚未解决的疑问）

## 5. 建议
**推荐动作**: 推进 / 暂不推进
**理由**: ...

## 6. 待人工批准
APPROVED: <pending | yes | no>
APPROVER: <用户姓名或标识>
APPROVED_AT: <YYYY-MM-DD>
COMMENT: <可选，人工补充说明>
```

---

## 3. Phase 0 → Phase 1 门控

### 3.1 进入前提

- 项目已完成 `PRAE_INIT.md` 初始化（问题陈述 + 组件分类）
- `prae/track_registry.yaml` 已列出所有基础设施轨道和研究轨道
- 所有基础设施轨道至少经历过 `EXPLORING` 阶段

### 3.2 AI 的准备工作

切换到**分析者**角色。按以下步骤生成 `prae/phases/phase_00_infra/PHASE_GATE.md`：

1. 读 `track_registry.yaml`，过滤 `type=infrastructure` 的轨道
2. 检查每条基础设施轨道：
   - `state` 是否等于 `LOCKED`？
   - `locked_at` 字段是否存在？
   - 对应 `src/infra_{name}_v{N}/` 目录是否存在？
   - `contracts.yaml` 是否存在？
   - MODULE_SPEC.md 是否存在（证明 PDAE M1-M3 已走过）？
3. 对每条基础设施轨道读 `TRACK_LOG.md`，确认选型结论和 PDAE 通过记录
4. 填写 PHASE_GATE.md，**第 2 节**必须包含以下条件（每条都勾选）：
   ```
   - [ ] 所有 type=infrastructure 的轨道 state = LOCKED
   - [ ] 每条 LOCKED 轨道都有 contracts.yaml
   - [ ] 每条 LOCKED 轨道都有 MODULE_SPEC.md
   - [ ] 每条 LOCKED 轨道都通过 PDAE M3 门控（记录在 TRACK_LOG.md）
   - [ ] check_contracts.py 对所有基础设施契约通过
   ```
5. 第 3 节引用各轨道 TRACK_LOG.md 中的选型结论和 PDAE 通过证据
6. 第 5 节明确给出"推进" / "暂不推进"

### 3.3 人工批准形式

用户在 `PHASE_GATE.md` 第 6 节填写：
```
APPROVED: yes
APPROVER: saionji
APPROVED_AT: 2026-04-22
COMMENT: 数据管道已通过上线前双人评审，可进入 Phase 1
```

### 3.4 批准后的后续动作

AI 检测到 `APPROVED: yes` 后：

1. 运行 `python3 tools/check_phase_gate.py --project-dir . --check-approved` 验证 PHASE_GATE.md 已填写 `APPROVED: yes`
2. 运行 `python3 tools/advance_phase.py --project-dir .`（或 `prae advance-phase`）
3. 由正式工具更新 `track_registry.yaml.current_phase = phase_01_research`
4. 由正式工具创建 `prae/phases/phase_01_research/`、`PHASE_BRIEF.md` 和研究轨道 `TRACK_LOG.md`

### 3.5 常见阻塞

| 现象 | 原因 | 处理 |
|------|------|------|
| 某基础设施轨道仍 EXPLORING | 选型未定或 PDAE 未通过 | 回到 Phase 0 继续做该轨道 |
| contracts.yaml 存在但 check_contracts 失败 | 研究轨道或测试代码违反契约 | 修正违规代码或修正契约范围 |
| MODULE_SPEC.md 缺失 | PDAE 流程没跑完 | 补跑 PDAE M1-M3 |
| 人工批准 `APPROVED: no` | 评审未通过 | 读 COMMENT，按建议补强 |

---

## 4. Phase 1 → Phase 2 门控

### 4.1 进入前提

- Phase 0 → Phase 1 已批准（current_phase = phase_01_research）
- 每条研究轨道已在 Phase 1 期间至少跑过一个实验
- 已有足够证据判断哪些轨道值得进入验证期

### 4.2 AI 的准备工作

切换到**分析者**角色，生成 `prae/phases/phase_01_research/PHASE_GATE.md`：

1. 读 `track_registry.yaml`，列出所有 `type=research` 的轨道及其 state
2. 对每条研究轨道：
   - 检查 `TRACK_LOG.md` 是否已记录 ≥1 次实验
   - 检查 `experiments/` 下是否至少有一份 `EXP_NNN.md` 且 `## Result` 和 `## Conclusion` 都已填写
   - 读取每条轨道的 `evidence_summary`
3. 第 2 节包含以下条件：
   ```
   - [ ] ≥1 条研究轨道 state = ACTIVE（有正向信号）
   - [ ] 所有仍 EXPLORING 的研究轨道有明确去留建议（继续 / KILL / 合并）
   - [ ] 每条 ACTIVE 轨道通过 Research Gate 检查
   ```
4. 第 3 节为每条 ACTIVE 轨道写一段证据摘要（1-2 句，链接到关键 EXP）
5. 第 4 节列出已发现的系统性风险（如某依赖基础设施的接口不够稳定）
6. 第 5 节建议"推进"或"暂不推进"

### 4.3 人工批准形式

与 Phase 0 → 1 相同，在第 6 节填 `APPROVED` 字段。

### 4.4 批准后的后续动作

1. 运行 `python3 tools/check_phase_gate.py --project-dir . --check-approved`
2. 对需要落库的研究轨道终态，先走 `python3 tools/update_track_state.py ...`（或 `prae update-track-state ...`）。**注意：仍处于 EXPLORING 的轨道不能直接进入终态；若需停止，必须先记录一次实验进入 ACTIVE，再标记 KILLED。**
3. 运行 `python3 tools/advance_phase.py --project-dir .`（或 `prae advance-phase`）
4. 由正式工具更新 `track_registry.yaml.current_phase = phase_02_validation`
5. 由正式工具创建 `prae/phases/phase_02_validation/`、`PHASE_BRIEF.md` 和验证期轨道日志

### 4.5 常见阻塞

| 现象 | 原因 | 处理 |
|------|------|------|
| 所有研究轨道仍 EXPLORING | 信号不足，实验太少 | 回到 Phase 1 继续跑实验 |
| 证据摘要矛盾 | 实验设计有缺陷，结果不可复现 | 回到 Phase 1 重新设计实验 |
| 某研究轨道 depends_on 指向的基础设施仍 EXPLORING | Phase 0 没闭合 | 回到 Phase 0 完成 |

---

## 5. Phase 2 → Phase 3 门控

### 5.1 进入前提

- 所有 ACTIVE 研究轨道在验证期都跑了严格验证实验
- 每条轨道都有明确结论建议（KILLED / MERGED / GRADUATED）

### 5.2 AI 的准备工作

生成 `prae/phases/phase_02_validation/PHASE_GATE.md`：

1. 读 `track_registry.yaml` 的所有研究轨道
2. 对每条轨道判断终态建议：
   - KILLED：证据证伪假设
   - MERGED：证据与其他轨道高度重合或互补，合并更合理
   - GRADUATED：证据充分，值得工程化
3. 第 2 节包含：
   ```
   - [ ] 所有原 ACTIVE 研究轨道有明确终态建议
   - [ ] 至少一条轨道判定 GRADUATED（否则考虑整体 KILL 项目）
   - [ ] 所有 GRADUATED 候选通过 Research Gate 和 Contracts Gate
   - [ ] 所有 GRADUATED 候选有 `TRACK_LOG.md` 的最终结论段落
   ```
4. 第 3 节为每条轨道的终态建议提供证据链接
5. 第 4 节列出影响结论的未决事项（例如外部数据延迟的问题、需要长期观察的效应）
6. 第 5 节建议"推进 Phase 3" 或"返回 Phase 2 补证据"

### 5.3 人工批准形式

人工在第 6 节填写时应额外明确同意或驳回每条轨道的终态建议。推荐格式：

```
APPROVED: yes
APPROVER: saionji
APPROVED_AT: 2026-05-10
COMMENT:
  - research_strategy_momentum: GRADUATED 同意
  - research_strategy_reversal: KILLED 同意
  - research_strategy_mean_revert: MERGED 进 research_strategy_momentum 同意
```

### 5.4 批准后的后续动作

1. 运行 `python3 tools/check_phase_gate.py --project-dir . --check-approved`
2. 对每条研究轨道按终态调用 `python3 tools/update_track_state.py ...`（或 `prae update-track-state ...`）：
   - `KILLED / MERGED / GRADUATED` 由正式工具写入 registry
   - 正式工具同步填 `concluded_at`
   - `MERGED` 轨道由正式工具强制要求 `merged_into`
3. 运行 `python3 tools/advance_phase.py --project-dir .`（或 `prae advance-phase`）
4. 由正式工具更新 `current_phase: phase_03_conclusion`
5. 由正式工具创建 `prae/phases/phase_03_conclusion/PHASE_BRIEF.md`

### 5.5 常见阻塞

| 现象 | 原因 | 处理 |
|------|------|------|
| 没有任何轨道判定 GRADUATED | 研究问题难度超预期 | 如果项目整体失败，建议人工决策是否终止项目 |
| 某轨道证据不足但被主观判 KILLED | 验证实验太少 | 补跑严格验证实验 |
| MERGED 但目标轨道还没准备好接收 | 接收方轨道的假设尚不包含被合并内容 | 先在目标轨道的 hypothesis 里扩展 |

---

## 6. Phase 3 结束（项目收尾）

### 6.1 进入前提

- Phase 2 → 3 已批准
- 所有研究轨道均已进入终态

### 6.2 AI 的准备工作

此阶段没有阶段转换门控（Phase 3 是终点）。AI 生成 `prae/phases/phase_03_conclusion/CONCLUSION.md`，整理：

- 项目最终结论（核心问题是否解决？哪些假设被证实？）
- 各轨道的去向清单
- 已毕业轨道的 PDAE 项目位置（链接）
- 未解决的问题 / 后续可开的新研究项目

### 6.3 人工决定

人工在 `CONCLUSION.md` 末尾填写结构化字段：

```text
APPROVED: <pending | yes | no>
DECISION: <ARCHIVED | GRADUATED_TO_PDAE | CONTINUE>
APPROVER: <用户姓名或标识>
APPROVED_AT: <YYYY-MM-DD>
COMMENT: <可选，人工补充说明>
```

其中 `DECISION` 含义如下：

- `ARCHIVED`：整个 PRAE 项目归档，不启动 PDAE
- `GRADUATED_TO_PDAE`：至少一条轨道进入 PDAE 工程项目（项目不归档，保持可追溯）
- `CONTINUE`：发现新问题，可考虑再开一个 Phase 1（罕见，需充分理由）

执行规则：

- `ARCHIVED` / `GRADUATED_TO_PDAE`：运行 `python3 tools/finalize_project.py --project-dir .`
- `CONTINUE`：运行 `python3 tools/reopen_project.py --project-dir .`，把本轮 `phase_01/02/03` 目录整体归档到 `prae/history/cycle_N/phases/`，并以 `current_cycle = N+1` 重开到 `phase_01_research`

### 6.4 GRADUATED_TO_PDAE 后的 AI 动作

切换到**执行者**角色：

1. 对每条 GRADUATED 轨道，切换到 PDAE 仓库
2. 按 `PDAE_QUICKSTART.md` 创建新的 PDAE 工程项目
3. 把研究轨道代码作为 `scout_m1` 的事实输入
4. 启动 PDAE 控制线程跑完整 M1-M3
5. PDAE 项目创建完成后，在 PRAE 项目的 `TRACK_LOG.md` 追加 PDAE 项目路径链接

---

## 7. 阶段反转 / 回退

**默认情况下，阶段转换是单向的**。已进入 Phase 2 不可退回 Phase 1。

**例外**：发现严重问题（如某基础设施契约有根本缺陷），用户可以手动：

1. 在 `track_registry.yaml` 顶部写 `current_phase_override: phase_00_infra` 并加注释
2. 从这一刻起，phase-aware 工具按 `phase_00_infra` 解释当前阶段；常规 `generate/check/advance-phase` 应停止使用
3. AI 接到指令后**停止推进**，只处理新的 v2 基础设施轨道（例如 `prae add-track` / `prae new-track` / `prae new-exp` / `prae lock-infra`）
4. 研究轨道继续保留在原有 phase 目录中，但不再推进，直到 override 被用户移除
5. v2 LOCKED 后，用户移除 `current_phase_override`，再决定是否继续验证期或重新探索

此路径不通过常规 PHASE_GATE 机制，由用户显式操控。AI 不应主动发起阶段回退。

---

## 8. 关键规则回顾

1. 每个阶段转换必须产出 `PHASE_GATE.md`，结构固定（6 节）
2. `PHASE_GATE.md` 必须标明当前 `研究轮次（cycle_N）`，并与 `track_registry.yaml` 一致
3. AI 只能建议，不能直接推进阶段
4. `APPROVED: yes` 是唯一合法的推进信号
5. 批准后必须通过正式工具更新 `track_registry.yaml` 的 `current_phase`
6. 未完成的门控条件不能被跳过或伪造勾选
7. 所有 PHASE_GATE.md 在批准后保留为永久记录，不删除
