# Task: prae-update-track-state

> 在人工批准后正式更新研究轨道状态，并同步 `track_registry.yaml` 与 `TRACK_LOG.md`
> 调用方式: `prae update-track-state <track_id> <ACTIVE|KILLED|MERGED|GRADUATED> --approver <name> --reason <reason> [--exp-id EXP_001] [--merged-into <track_id>] [--summary <text>] [--approved-at YYYY-MM-DD]`
> 前置条件: 项目已完成 `prae init`，且用户已明确批准这次状态变更

## 步骤

### 1. 解析参数

```bash
TRACK_ID="${1:?'用法: prae update-track-state <track_id> <to_state> --approver <name> --reason <reason>'}"
TO_STATE="${2:?'用法: prae update-track-state <track_id> <to_state> --approver <name> --reason <reason>'}"
shift 2

APPROVER=""
REASON=""
ADVISOR="AI"
APPROVED_AT=""
EXP_ID=""
MERGED_INTO=""
SUMMARY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --approver)
      APPROVER="${2:-}"
      shift 2
      ;;
    --reason)
      REASON="${2:-}"
      shift 2
      ;;
    --advisor)
      ADVISOR="${2:-AI}"
      shift 2
      ;;
    --approved-at)
      APPROVED_AT="${2:-}"
      shift 2
      ;;
    --exp-id)
      EXP_ID="${2:-}"
      shift 2
      ;;
    --merged-into)
      MERGED_INTO="${2:-}"
      shift 2
      ;;
    --summary)
      SUMMARY="${2:-}"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      exit 1
      ;;
  esac
done

[ -n "${APPROVER}" ] || { echo "错误: 缺少 --approver"; exit 1; }
[ -n "${REASON}" ] || { echo "错误: 缺少 --reason"; exit 1; }
```

### 2. 验证项目已完成初始化

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "未找到 prae/track_registry.yaml。项目可能只完成了 bootstrap。"
  echo "请先填写 prae/PRAE_INIT.md，然后运行: prae init"
  exit 1
}
```

### 3. 调用正式工具

```bash
CMD=(
  python3 tools/update_track_state.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --to-state "${TO_STATE}"
  --approver "${APPROVER}"
  --reason "${REASON}"
  --advisor "${ADVISOR}"
)

[ -n "${APPROVED_AT}" ] && CMD+=(--approved-at "${APPROVED_AT}")
[ -n "${EXP_ID}" ] && CMD+=(--exp-id "${EXP_ID}")
[ -n "${MERGED_INTO}" ] && CMD+=(--merged-into "${MERGED_INTO}")
[ -n "${SUMMARY}" ] && CMD+=(--summary "${SUMMARY}")

"${CMD[@]}"
```

### 4. 结果解释

执行成功后：
- `track_registry.yaml` 会更新 `state`
- 终态会自动填写 `concluded_at`
- `MERGED` 会自动填写 `merged_into`
- 当前阶段 `TRACK_LOG.md` 会更新 `**当前状态**` 并追加 `Decision Log`

若失败，优先看输出中的：
- `状态迁移合法`
- `依赖的基础设施轨道已 LOCKED`
- `Research Gate / ...`
- `MERGED 目标轨道合法`
