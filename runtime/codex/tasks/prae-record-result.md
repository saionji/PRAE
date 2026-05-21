# Task: prae-record-result

> 实验完成后，调用正式工具将结果同步到 TRACK_LOG.md；若有状态变更建议，会一并写入待批准 `Decision Log`
> 调用方式: `prae record-result <track_id> <exp_id>`
> 参数: `$1 = track_id`, `$2 = exp_id`（例如 `EXP_003`）
> 前置条件: 项目已完成 `prae init`，且 `EXP_NNN.md` 的 Result / Conclusion 已填写

## 步骤

### 1. 解析参数并检查初始化

```bash
TRACK_ID="${1:?'用法: prae record-result <track_id> <exp_id>'}"
EXP_ID="${2:?'用法: prae record-result <track_id> <exp_id>'}"

[ -f "prae/track_registry.yaml" ] || {
  echo "未找到 prae/track_registry.yaml。项目可能只完成了 bootstrap。"
  echo "请先填写 prae/PRAE_INIT.md，然后运行: prae init"
  exit 1
}
```

### 2. 调用正式工具

```bash
python3 tools/record_result.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --exp-id "${EXP_ID}"
```

### 3. 读取状态建议

```bash
PHASE=$(python3 -c "import yaml; r=yaml.safe_load(open('prae/track_registry.yaml')); print(r['current_phase'])")
EXP_MD="prae/phases/${PHASE}/tracks/${TRACK_ID}/experiments/${EXP_ID}.md"

python3 -c "
import re
with open('${EXP_MD}', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'建议 state 变更[:：]\\s*(.+)', content)
if m:
    print(f'状态变更建议: {m.group(1).strip()}')
    print('record_result.py 已将该建议写入 TRACK_LOG.md 的待批准 Decision Log')
    print('如用户明确同意，请继续执行 prae update-track-state ... 完成正式状态变更')
else:
    print('未发现明确状态变更建议；本次仅完成结果记录。')
"
```

### 4. 仅在用户明确批准后，执行正式状态变更

若 `EXP_NNN.md` 的 Conclusion 给出了状态建议，且用户已经批准本次变更，则运行：

```bash
SUGGESTED_STATE=$(python3 -c "
import re
with open('${EXP_MD}', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'建议 state 变更[:：]\\s*(.+)', c)
text = m.group(1).strip() if m else ''
if '→' in text:
    print(text.split('→')[-1].strip())
elif '->' in text:
    print(text.split('->')[-1].strip())
")

[ -n "${SUGGESTED_STATE}" ] || exit 0

CMD=(
  python3 tools/update_track_state.py
  --project-dir .
  --track-id "${TRACK_ID}"
  --to-state "${SUGGESTED_STATE}"
  --approver "<人工批准人>"
  --reason "${EXP_ID} 结果已人工批准"
  --exp-id "${EXP_ID}"
)

# 若建议是 MERGED，还需追加：
# CMD+=(--merged-into "<目标轨道 ID>")

"${CMD[@]}"
```
