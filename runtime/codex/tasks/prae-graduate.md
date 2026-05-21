# Task: prae-graduate

> 将 GRADUATED 研究轨道移交到 PDAE 工程化项目
> 调用方式: `prae graduate <track_id>`
> 前置条件: Phase 3 已开始，track state=GRADUATED，PDAE 已安装

## 步骤

### 1. 在 PDAE 仓库完成工程项目创建

```bash
TRACK_ID="${1:?'用法: prae graduate <track_id>'}"

ls ${PDAE_HOME}/PDAE_QUICKSTART.md &>/dev/null || {
  echo "错误: PDAE 仓库不可访问 (${PDAE_HOME})"
  exit 1
}

cd ${PDAE_HOME}
source .venv/bin/activate

# 参阅 PDAE_QUICKSTART.md 的 "新建项目" 章节
# 将 src/tracks/${TRACK_ID}/ 的研究代码作为 scout_m1 的事实输入
# 跑 PDAE M1-M3 流程，拿到最终项目路径
```

记录 PDAE 项目路径：`PDAE_PROJECT_PATH=<创建后的路径>`

### 2. 回到 PRAE 项目登记毕业记录

```bash
PDAE_PROJECT_PATH="${PDAE_PROJECT_PATH:?'请设置 PDAE_PROJECT_PATH 环境变量'}"

python3 tools/graduate_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --pdae-project-path "${PDAE_PROJECT_PATH}"
```

### 3. 刷新项目结论（如需要）

```bash
python3 tools/generate_conclusion.py --project-dir .
```
