# Task: prae-new-track

> 为已在 `track_registry.yaml` 中登记的轨道创建当前阶段目录和初始 `TRACK_LOG.md`
> 调用方式: `prae new-track <track_id>`
> 参数: `$1 = track_id`

## 步骤

### 1. 解析参数

```bash
TRACK_ID="${1:?'用法: prae new-track <track_id>'}"
```

### 2. 调用正式工具

```bash
python3 tools/new_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}"
```
