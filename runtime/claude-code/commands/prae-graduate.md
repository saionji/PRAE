# /prae-graduate

> **用途**: 将一条 GRADUATED 研究轨道移交到 PDAE 工程化项目
> **参数**: `<track_id>`
> **前置条件**:
>   - Phase 2 → 3 门控已批准（current_phase = phase_03_conclusion）
>   - track_registry.yaml 中该轨道 state = GRADUATED
>   - PDAE 已安装（${PDAE_HOME}/ 可访问）

## 重要提示

执行前**必须确认**：
1. 该轨道的 TRACK_LOG.md 有完整的最终结论段落
2. 人工已在 Phase 2 → 3 PHASE_GATE 的 COMMENT 中明确同意该轨道 GRADUATED

## 执行步骤

### 1. 在 PDAE 仓库完成工程项目创建

```bash
TRACK_ID="${1:?'用法: /prae-graduate <track_id>'}"
ls ${PDAE_HOME}/PDAE_QUICKSTART.md \
  || { echo "错误: PDAE 仓库不可访问"; exit 1; }

cd ${PDAE_HOME}

# 参考 PDAE project-pack，为研究轨道创建 PDAE 工程项目
# 将研究代码（src/tracks/{track_id}/）作为 scout_m1 的事实输入
# 跑完整 PDAE M1-M3 流程
```

具体步骤遵循 PDAE_QUICKSTART.md，此处不重复。关键输入：
- 研究假设（hypothesis 字段）
- 已验证的算法逻辑（EXP_NNN.py 实现，contracts 边界）
- 证据摘要（TRACK_LOG.md Evidence Summary）

完成后记录：`PDAE_PROJECT_PATH=<创建后的路径>`

### 2. 在 PRAE 项目登记毕业记录

PDAE 项目创建成功后，回到 PRAE 项目：

```bash
PDAE_PROJECT_PATH="${PDAE_PROJECT_PATH:?'PDAE 项目路径未设置'}"

python3 tools/graduate_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --pdae-project-path "${PDAE_PROJECT_PATH}"
```

### 3. 刷新项目结论

```
python3 tools/generate_conclusion.py --project-dir .
```
