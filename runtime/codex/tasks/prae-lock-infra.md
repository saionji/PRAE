# Task: prae-lock-infra

> 在人工批准后正式将基础设施轨道从 `EXPLORING` 更新为 `LOCKED`
> 调用方式: `prae lock-infra <track_id> --approver <name> --reason <reason> [--contracts <path>] [--module-spec <path>] [--approved-at YYYY-MM-DD]`
> 前置条件: 项目已完成 `prae init`，当前位于 `phase_00_infra`，且对应基础设施轨道已完成 PDAE M3 / Contracts Gate

## 步骤

### 1. 解析参数

```bash
TRACK_ID="${1:?'用法: prae lock-infra <track_id> --approver <name> --reason <reason>'}"
shift

APPROVER=""
REASON=""
ADVISOR="AI"
LOCKED_AT=""
CONTRACTS=""
MODULE_SPEC=""

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
    --approved-at|--locked-at)
      LOCKED_AT="${2:-}"
      shift 2
      ;;
    --contracts)
      CONTRACTS="${2:-}"
      shift 2
      ;;
    --module-spec)
      MODULE_SPEC="${2:-}"
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

### 2. 验证项目已初始化

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
  python3 tools/lock_infra_track.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --approver "${APPROVER}"
  --reason "${REASON}"
  --advisor "${ADVISOR}"
)

[ -n "${LOCKED_AT}" ] && CMD+=(--locked-at "${LOCKED_AT}")
[ -n "${CONTRACTS}" ] && CMD+=(--contracts "${CONTRACTS}")
[ -n "${MODULE_SPEC}" ] && CMD+=(--module-spec "${MODULE_SPEC}")

"${CMD[@]}"
```

### 4. 结果解释

成功后会同时完成：
- 将基础设施轨道 `state` 更新为 `LOCKED`
- 写入 `locked_at`
- 自动登记 `contracts` / `module_spec` 路径（优先使用显式参数，否则按 `src/{track_id}/...` 推断）
- 在当前阶段 `TRACK_LOG.md` 的 `Decision Log` 追加 `EXPLORING → LOCKED`

若失败，优先看输出中的：
- `当前阶段允许锁定基础设施轨道`
- `基础设施轨道状态迁移合法`
- `contracts 文件存在`
- `MODULE_SPEC 文件存在`
- `Contracts Gate 通过`
