# /prae-new-exp

> **用途**: 为指定轨道新建一个实验，创建 `EXP_NNN.md` 记录和 `EXP_NNN.py` 代码文件
> **参数**: `<track_id> [--title <实验标题>]` 或 `<track_id> [实验标题]`
> **前置条件**: 项目已完成 `/prae-init`，且轨道已存在（通过 `/prae-new-track` 创建）

## 执行步骤

### 1. 解析参数

```bash
TRACK_ID="${1:?'用法: /prae-new-exp <track_id> [--title <实验标题>]'}"
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
