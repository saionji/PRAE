---
name: prae-executor
description: Use when an infrastructure track is ready for engineering (EXPLORING→LOCKED) or when stable impl code needs extracting from experiments — activates Executor SOP and PDAE integration
---

# PRAE 执行者 SOP（Claude Code）

> 安装路径：`.claude/skills/prae-executor.md`（由 prae-bootstrap 自动部署）
> 规格参考：`methodology/PRAE_ROLES.md §3`、`runtime/abstract/EXECUTOR_ROLE.prompt.md`

本 skill 是项目内给模型读的执行者行为入口，不是安装命令入口。
若项目还没有 `prae/track_registry.yaml`，说明项目可能只完成了 bootstrap；先走 `/prae-init`，不要把当前 skill 当成“项目已初始化完成”的信号。

---

## 激活时宣告

在回复开头写：
```
[切换到执行者] 处理轨道 {track_id}（{原因}）
```

---

## 标准流程 A：基础设施轨道工程化（EXPLORING → LOCKED）

### 前置检查

```bash
# 确认项目已完成初始化
ls prae/track_registry.yaml || {
  echo "未找到 track_registry.yaml。项目可能只完成了 bootstrap。"
  echo "请先完成 /prae-init，再进入执行者流程。"
  exit 1
}

# 确认选型已确定（TRACK_LOG.md 有选型结论）
grep -A5 "Decision Log" prae/phases/phase_00_infra/tracks/{track_id}/TRACK_LOG.md

# 确认 PDAE 工具可用
ls ${PDAE_HOME}/tools/check_unit_gate.py
```

若 `track_registry.yaml` 不存在，不要手工创建；先让分析者完成初始化，再继续工程化。

### Step 1：切换到 PDAE 环境

```bash
cd ${PDAE_HOME}
source .venv/bin/activate
```

### Step 2：PDAE M1 — 写 MODULE_SPEC.md

按 PDAE_QUICKSTART.md M1 流程，在 PRAE 项目路径下创建：
```
src/infra_{name}_v1/MODULE_SPEC.md
```

使用 PDAE materialize 工具生成上下文后，由 architect_m1 unit 产出 MODULE_SPEC。

### Step 3：PDAE M2 — 写 contracts.yaml

按 PDAE CONTRACTS_SPEC.md 格式，在 PRAE 项目路径下创建：
```
src/infra_{name}_v1/contracts.yaml
```

只暴露研究轨道实际需要的公开接口（最小化暴露面）。

### Step 4：PDAE M3 — 实现 + 单元门控

```bash
# 回到 PRAE 项目目录
cd /path/to/project

# 实现代码（src/infra_{name}_v1/）
# ...

# 运行单元门控
python3 ${PDAE_HOME}/tools/check_unit_gate.py \
  --unit reviewer_m3 --repo .

# 运行契约检查
python3 ${PDAE_HOME}/tools/check_contracts.py \
  --contracts src/infra_{name}_v1/contracts.yaml --src src/
```

### Step 5：LOCKED 确认

所有检查通过后：

```bash
python3 tools/lock_infra_track.py \
  --project-dir . \
  --track-id "{track_id}" \
  --approver "<人工批准人>" \
  --reason "PDAE M3 通过"
```

由正式工具同步更新 `track_registry.yaml` 和 TRACK_LOG.md `## Decision Log`。

---

## 标准流程 B：impl/ 代码提炼

**触发条件**：同一段逻辑在多个 EXP 中重复，分析者建议提炼。

```bash
# 创建 impl/ 目录
mkdir -p src/tracks/{track_id}/impl/

# 将函数从 experiments/ 中提炼，整理接口
# 注意：原 EXP_NNN.py 保持不变（实验脚本不改）
```

**若 impl/ 中的代码被第 2 个轨道 import → 触发流程 C**。

---

## 标准流程 C：shared 代码迁移（触发 PDAE M3）

**触发条件**：`src/shared/` 下没有但需要的模块，或 impl/ 代码被第 2 处引用。

```bash
# 1. 创建 shared 模块目录
mkdir -p src/shared/{module_name}/

# 2. 迁移代码，整理公开接口
# 3. 写 MODULE_SPEC.md（PDAE M3 格式）
# 4. 运行 PDAE M3 单元门控
python3 ${PDAE_HOME}/tools/check_unit_gate.py \
  --unit reviewer_m3 --repo .
# 5. 更新所有 import 路径
```

---

## 硬性禁止

- 修改 LOCKED 基础设施的源码（需求变更 → 开 v2）
- 写实验代码（`experiments/`）
- 跳过 PDAE M1 或 M2 直接进入 M3
- 在 contracts.yaml 不存在时标记轨道为 LOCKED
