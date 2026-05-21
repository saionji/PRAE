# /prae-record-result

> **用途**: 实验跑完后，调用正式工具将结果同步到 `TRACK_LOG.md`；若有状态变更建议，会一并写入待批准 `Decision Log`
> **参数**: `<track_id> <exp_id>`（例如：`research_strategy_momentum EXP_003`）
> **前置条件**: 项目已完成 `/prae-init`，且 `EXP_NNN.md` 的 Result 和 Conclusion 已填写

## 执行步骤

### 1. 解析参数并检查初始化

```bash
TRACK_ID="${1:?'用法: /prae-record-result <track_id> <exp_id>'}"
EXP_ID="${2:?'用法: /prae-record-result <track_id> <exp_id>'}"

[ -f "prae/track_registry.yaml" ] || {
  echo "未找到 prae/track_registry.yaml。项目可能只完成了 bootstrap。"
  echo "请先填写 prae/PRAE_INIT.md，然后运行 /prae-init。"
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
    print('如果你同意这个建议，我将继续调用 /prae-update-track-state，')
    print('由正式工具更新 track_registry.yaml 和 TRACK_LOG.md 的 Decision Log。')
else:
    print('未发现明确状态变更建议；本次仅完成结果记录。')
"
```

### 4. 仅在用户确认后，调用正式状态工具

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

python3 tools/update_track_state.py \
  --project-dir . \
  --track-id "${TRACK_ID}" \
  --to-state "${SUGGESTED_STATE}" \
  --approver "<人工批准人>" \
  --reason "${EXP_ID} 结果已人工批准" \
  --exp-id "${EXP_ID}"
```
