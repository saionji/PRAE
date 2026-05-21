# Task: prae-add-track

> 正式向 `track_registry.yaml` 注册新轨道；仅做注册，不创建当前阶段目录
> 调用方式: `prae add-track <track_id> --type <research|infrastructure> [--hypothesis <text>] [--depends-on infra_a infra_b ...] [--description <text>] [--src <path>]`
> 前置条件: 项目已完成 `prae init`

## 步骤

### 1. 解析参数

```bash
TRACK_ID="${1:?'用法: prae add-track <track_id> --type <research|infrastructure> [...]'}"
shift

TRACK_TYPE=""
HYPOTHESIS=""
DESCRIPTION=""
SRC=""
DEPENDS_ON=()

while [ $# -gt 0 ]; do
  case "$1" in
    --type)
      TRACK_TYPE="${2:-}"
      shift 2
      ;;
    --hypothesis)
      HYPOTHESIS="${2:-}"
      shift 2
      ;;
    --description)
      DESCRIPTION="${2:-}"
      shift 2
      ;;
    --src)
      SRC="${2:-}"
      shift 2
      ;;
    --depends-on)
      shift
      while [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; do
        DEPENDS_ON+=("$1")
        shift
      done
      ;;
    *)
      echo "未知参数: $1"
      exit 1
      ;;
  esac
done

[ -n "${TRACK_TYPE}" ] || { echo "错误: 缺少 --type <research|infrastructure>"; exit 1; }
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
  python3 tools/add_track.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --type "${TRACK_TYPE}"
)

[ -n "${HYPOTHESIS}" ] && CMD+=(--hypothesis "${HYPOTHESIS}")
[ -n "${DESCRIPTION}" ] && CMD+=(--description "${DESCRIPTION}")
[ -n "${SRC}" ] && CMD+=(--src "${SRC}")
if [ ${#DEPENDS_ON[@]} -gt 0 ]; then
  CMD+=(--depends-on "${DEPENDS_ON[@]}")
fi

"${CMD[@]}"
```

### 4. 后续动作

注册成功后：
- 只会更新 `track_registry.yaml`
- 不会自动创建 `TRACK_LOG.md` 或目录
- 如需在当前阶段实际启用该轨道，再运行 `prae new-track <track_id>`
