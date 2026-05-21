---
name: prae-guard
description: Use at the start of any PRAE research project session — enforces PRAE behavioral contracts, role discipline, and gate rules throughout the conversation
---

# PRAE Guard — 行为契约

> 安装路径：`.claude/skills/prae-guard.md`（由 prae-bootstrap 自动部署）
> 规格参考：`methodology/PRAE_ROLES.md`、`methodology/PRAE_CORE_MODEL.md`

先区分三种“入口”：
- 当前 skill：项目内给模型读的会话上下文入口
- `/prae-bootstrap`：项目安装入口
- `/prae-init`：项目状态初始化入口

所以看到本 skill，不代表项目已经初始化完成；若缺 `prae/track_registry.yaml`，只说明项目可能还停在 bootstrap 之后。

---

## 会话启动检查

进入 PRAE 项目时，先执行以下检查（按序）：

```bash
# 1. 确认 bootstrap 最小骨架已存在
ls prae/PRAE_INIT.md || { echo "未找到 prae/PRAE_INIT.md，请先运行 /prae-bootstrap"; exit 1; }

# 2. 找到 track_registry.yaml（若缺失，说明项目还没 init）
ls prae/track_registry.yaml || {
  echo "未找到 track_registry.yaml。项目可能只完成了 bootstrap。"
  echo "请先填写 prae/PRAE_INIT.md，然后运行 /prae-init。"
  exit 1
}

# 3. 读取当前阶段
python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
print(f'当前阶段: {r[\"current_phase\"]}')
print(f'轨道数: {len(r[\"tracks\"])}')
for t in r['tracks']:
    print(f'  {t[\"id\"]} [{t[\"type\"]}] -> {t[\"state\"]}')
"
```

输出结果展示给用户，然后问："你想处理哪条轨道，或者执行什么操作？"

---

## 角色规则（硬性约束）

**你同时只扮演一个角色**，每次切换必须在回复开头宣告：
```
[切换到分析者] 处理轨道 research_strategy_momentum（EXPLORING）
[切换到执行者] 处理轨道 infra_data_v1（EXPLORING → LOCKED 实现期）
```

| 角色 | 激活条件 | 禁止操作 |
|------|---------|---------|
| 分析者 | track state = EXPLORING 或 ACTIVE；生成 PHASE_GATE | 修改 src/infra_*/；创建 impl/*.py；更新已批准 PHASE_GATE |
| 执行者 | 基础设施工程化；impl/ 代码提炼；shared 迁移 | 写实验代码；直接推进研究轨道状态 |

---

## 门控规则（不可绕过）

1. **阶段不自动推进**：生成 PHASE_GATE.md 后必须停下等 `APPROVED: yes`
2. **研究轨道 EXPLORING → KILLED 禁止**：必须经过 ACTIVE（至少一次实验）
3. **ACTIVE 轨道进入终态前**必须通过 Research Gate（`tools/check_research_gate.py`）
4. **基础设施 LOCKED 前**必须走完 PDAE M1-M3 并有 contracts.yaml + MODULE_SPEC.md
5. **LOCKED 基础设施不可修改**：有新需求开 v2 轨道

---

## 文件路径速查

| 文件 | 路径 | 创建者 |
|------|------|--------|
| 实验记录 EXP_NNN.md | `prae/phases/.../tracks/{track_id}/experiments/EXP_NNN.md` | 分析者 |
| 实验代码 EXP_NNN.py | `src/tracks/{track_id}/experiments/EXP_NNN.py` | 分析者 |
| 轨道日志 | `prae/phases/.../tracks/{track_id}/TRACK_LOG.md` | 分析者 |
| 阶段门控 | `prae/phases/phase_NN_*/PHASE_GATE.md` | 分析者 |
| 基础设施代码 | `src/infra_{name}_v{N}/` | 执行者 |
| 稳定实现 | `src/tracks/{track_id}/impl/*.py` | 执行者 |

---

## 可用 Slash Commands

| 命令 | 用途 |
|------|------|
| `/prae-bootstrap` | 将 PRAE 最小骨架、模板、tools 和命令部署到当前研究项目 |
| `/prae-init` | 从 `PRAE_INIT.md` 生成 `track_registry.yaml` 和 Phase 0 工件 |
| `/prae-add-track <id>` | 正式向 `track_registry.yaml` 注册新轨道 |
| `/prae-new-track <id>` | 为已登记轨道创建当前阶段目录和 TRACK_LOG.md |
| `/prae-new-exp <track_id>` | 新建实验 |
| `/prae-record-result <track_id> <exp_id>` | 填写实验结果 |
| `/prae-lock-infra <track_id>` | 在人工批准后正式锁定基础设施轨道 |
| `/prae-update-track-state <track_id> <state>` | 在人工批准后正式更新研究轨道状态 |
| `/prae-advance-phase` | 首次调用生成 PHASE_GATE.md；已批准时校验 gate 并正式推进阶段 |
| `/prae-graduate <track_id>` | 启动轨道毕业到 PDAE |
| `/prae-finalize` | 记录项目终态决定 |
| `/prae-reopen` | 根据 CONTINUE 决定重开到 Phase 1 |

---

## 紧急情况处理

- 发现状态不一致（yaml 与文件不符）→ 停下，告知用户，不自动修复
- 找不到所需文件 → 明确报告缺失路径，不猜测创建
- 工具报错 → 打印完整错误，不静默忽略
