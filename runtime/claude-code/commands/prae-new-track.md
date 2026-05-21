# /prae-new-track

> **用途**: 为当前阶段一条已登记轨道创建目录和初始 `TRACK_LOG.md`
> **参数**: `<track_id>`

## 执行步骤

### 1. 解析参数

```bash
TRACK_ID="${1:?'用法: /prae-new-track <track_id>'}"
```

### 2. 调用正式工具

```bash
python3 tools/new_track.py \
  --project-dir . \
  --track-id "${TRACK_ID}"
```
