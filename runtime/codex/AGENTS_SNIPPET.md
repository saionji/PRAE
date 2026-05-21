# PRAE 行为契约（粘贴到 AGENTS.md）

> **安装说明**: 将以下内容复制粘贴到研究项目的 `AGENTS.md` 文件中。
> 通常由 `prae-bootstrap` task 自动完成，也可手工粘贴。

---

<!-- 粘贴起始位置 -->

## PRAE 研究方法论

此项目使用 PRAE（Protocol-Driven Research & Experimentation）方法论管理研究决策过程。
PRAE 方法论文档位于：`PRAE_ROOT/methodology/`（参见 PRAE 仓库）。

### 入口定义

- `AGENTS.md` / `CLAUDE.md`：模型上下文入口
- `prae bootstrap`：项目安装入口
- `prae init`：项目状态初始化入口

如果项目里还没有 `prae/track_registry.yaml`，说明项目可能只完成了 bootstrap、还没 init；不要把当前文档误解成“项目已经初始化完成”。

### 角色规则

你在此项目中只扮演以下两种角色之一，不可同时扮演或混用：

| 角色 | 激活条件 | 产出 |
|------|---------|------|
| 分析者（Analyst） | 轨道 state=EXPLORING 或 ACTIVE；生成 PHASE_GATE | 实验设计、证据解读、PHASE_GATE.md |
| 执行者（Engineer） | 基础设施工程化；impl/ 代码提炼 | 基础设施代码、contracts.yaml、impl/*.py |

切换角色时必须在回复开头宣告：
```
[切换到分析者] 处理轨道 {track_id}（{state}）
[切换到执行者] 处理轨道 {track_id}（LOCKED 实现期）
```

### 门控规则（不可绕过）

1. **阶段不自动推进**：PHASE_GATE.md 生成后必须等 `APPROVED: yes`
2. **研究轨道禁止 EXPLORING → KILLED 直接终止**：必须经过 ACTIVE
3. **ACTIVE 轨道进入终态前**必须通过 Research Gate
4. **基础设施 LOCKED 前**必须有 contracts.yaml + MODULE_SPEC.md + PDAE M3 通过
5. **LOCKED 基础设施不可修改**：新需求开 v2 轨道

### 文件路径规则

| 文件类型 | 路径 |
|---------|------|
| 实验记录（.md） | `prae/phases/.../tracks/{id}/experiments/EXP_NNN.md` |
| 实验代码（.py） | `src/tracks/{id}/experiments/EXP_NNN.py` |
| 轨道日志 | `prae/phases/.../tracks/{id}/TRACK_LOG.md` |
| 阶段门控 | `prae/phases/phase_NN_*/PHASE_GATE.md` |
| 基础设施 | `src/infra_{name}_v{N}/`（LOCKED 后只读） |
| 稳定实现 | `src/tracks/{id}/impl/*.py`（执行者创建） |

### 可用 Tasks

在研究项目根目录执行（需安装 `prae` CLI 或直接运行 codex task）：

```bash
prae bootstrap      # 部署 PRAE 到当前项目
prae init           # 初始化研究项目（生成 registry 和 Phase 0 工件；此时仍在 phase_00_infra）
prae add-track <id> # 正式注册新轨道到 track_registry.yaml
prae new-track <id> # 为已登记轨道创建当前阶段目录
prae new-exp <id>   # 新建实验
prae record-result <track_id> <exp_id>  # 记录实验结果
prae lock-infra <track_id> --approver <name> --reason "<原因>"  # 人工批准后正式锁定基础设施轨道
prae update-track-state <track_id> <state> --approver <name> --reason "<原因>"  # 人工批准后正式更新研究轨道状态
prae advance-phase  # 首次生成 PHASE_GATE.md；已批准后再次调用会正式推进
prae graduate <id>  # 研究轨道毕业到 PDAE
prae finalize       # 记录项目终态决定
prae reopen         # 根据 CONTINUE 重开到 Phase 1
```

### 紧急情况

- 状态不一致 → 停下告知用户，不自动修复
- 找不到文件 → 明确报告缺失路径
- 工具报错 → 打印完整错误，不静默忽略

<!-- 粘贴结束位置 -->
