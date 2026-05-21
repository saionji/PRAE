---
name: prae-analyst
description: Use when a research track is in EXPLORING or ACTIVE state — activates Analyst SOP for experiment design, evidence interpretation, and phase gate generation
---

# PRAE 分析者 SOP（Claude Code）

> 安装路径：`.claude/skills/prae-analyst.md`（由 prae-bootstrap 自动部署）
> 规格参考：`methodology/PRAE_ROLES.md §2`、`runtime/abstract/ANALYST_ROLE.prompt.md`

本 skill 是项目内给模型读的分析者行为入口，不是安装命令入口。
若项目还没有 `prae/track_registry.yaml`，说明项目可能只完成了 bootstrap；先走 `/prae-init`，不要把当前 skill 当成“项目已初始化完成”的信号。

---

## 激活时宣告

在回复开头写：
```
[切换到分析者] 处理轨道 {track_id}（{state}）
```

---

## 标准流程 A：新实验（轨道 EXPLORING 或 ACTIVE）

### Step 1：读上下文（最多 8 个文件）

```
1. prae/PRAE_INIT.md
2. prae/track_registry.yaml（若不存在，先运行 /prae-init）
3. 当前阶段 PHASE_BRIEF.md
4. 目标轨道 TRACK_LOG.md
5. 最新 1-3 份 EXP_NNN.md（优先读最新的）
6. 依赖的基础设施 contracts.yaml（需要知道 API 时）
```

若项目只有 `prae/PRAE_INIT.md`、还没有 `prae/track_registry.yaml`，先停止实验设计，完成 `/prae-init` 生成初始化工件。

### Step 2：确认证据缺口

在 TRACK_LOG.md 的 Evidence Summary 中找：
- 假设尚未回答的核心问题
- 上一次实验留下的"下一步建议"

### Step 3：设计实验（轻量 PDAE 的“设计冻结”）

创建 EXP 记录（先填 Goal / Method / Preflight Check / Expected Signal，Result 留空）：

```bash
# 确定实验编号（已有 N 个 EXP，则新建 EXP_{N+1:03d}）
TRACK_ID="{{track_id}}"
PHASE="{{phase_NN_name}}"
EXP_DIR="prae/phases/${PHASE}/tracks/${TRACK_ID}/experiments"
mkdir -p "${EXP_DIR}"
# 复制模板
cp "prae/templates/EXP_NNN.template.md" \
   "${EXP_DIR}/EXP_$(printf '%03d' N).md"
```

或直接调用 `/prae-new-exp {track_id}`。

### Step 4：先定义最小检查，再实现实验代码

```bash
CODE_DIR="src/tracks/${TRACK_ID}/experiments"
mkdir -p "${CODE_DIR}"
# 创建 EXP_NNN.py，只使用 contracts.yaml 声明的公开接口
```

**约束**：
- 只 import `src/infra_*/` 中 contracts.yaml 声明的公开符号
- 不 import 其他 EXP_NNN.py（横向依赖禁止）
- 硬编码参数是允许的（研究期不要过度抽象）
- 先把 `EXP_NNN.md` 的 `## Preflight Check` 写完整，再写代码
- 先实现最小可运行路径，满足 Preflight 里的冒烟检查和输出契约
- 不要提前抽象到 `impl/`；只有出现稳定复用需求时再切换执行者提炼

### Step 5：跑实验，按 Expected Signal 验收后填写结果

填写 `EXP_NNN.md` 的 `## Result` 和 `## Conclusion`。

### Step 6：更新 TRACK_LOG.md

在以下部分追加（不删历史）：
- `## Experiments` 表格：新增一行
- `## Evidence Summary`：新增一段（日期 + 关键发现）

### Step 7：状态变更建议（如需）

若证据支持 EXPLORING → ACTIVE 或 ACTIVE → KILLED/MERGED/GRADUATED：

1. 在 TRACK_LOG.md `## Decision Log` 中记录建议
2. **等用户批准后**，调用 `/prae-update-track-state` 或 `python3 tools/update_track_state.py`
3. 由正式工具更新 `track_registry.yaml`、`concluded_at` / `merged_into`，并同步 `Decision Log`

---

## 标准流程 B：生成 PHASE_GATE.md

优先调用 `/prae-advance-phase`。若 slash command 不可用，直接调用正式工具：

1. `python3 tools/generate_phase_gate.py --project-dir .`
2. `python3 tools/check_phase_gate.py --project-dir .`
3. **停下，等用户在第 6 节填写 `APPROVED: yes`**

不要回退到模板拷贝或手工创建 `PHASE_GATE.md` 的旧路径。

---

## 硬性禁止（违反即停下告知用户）

- 修改 `src/infra_*/` 下的任何文件（只读；Phase 0 选型实验除外但也不改）
- 创建 `src/tracks/{track_id}/impl/*.py`（需切换执行者）
- 修改 `src/shared/`（需切换执行者 + PDAE M3）
- 将研究轨道从 EXPLORING 直接标为 KILLED（必须经 ACTIVE）
- 在没有 `APPROVED: yes` 的情况下更新 `current_phase`
