# Task: prae-new-exp

> 为指定轨道新建实验（EXP_NNN.md 记录 + EXP_NNN.py 骨架）
> 调用方式: `prae new-exp <track_id> [--title <实验标题>]` 或 `prae new-exp <track_id> [实验标题]`
> 参数: `$1 = track_id`；标题可用第二个位置参数，或 `--title <实验标题>`
> 前置条件: 项目已完成 `prae init`，且轨道已通过 `prae new-track <track_id>` 创建

## 步骤

### 1. 解析参数

```bash
TRACK_ID="${1:?'用法: prae new-exp <track_id> [--title <实验标题>]'}"
shift || true
TITLE="实验"
if [ "${1:-}" = "--title" ]; then
  TITLE="${2:-实验}"
elif [ -n "${1:-}" ]; then
  TITLE="${1}"
fi
```

### 2. 调用正式工具

```bash
python3 tools/new_exp.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --title "${TITLE}"
```
