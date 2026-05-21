# Task: prae-advance-phase

> 检查阶段门控条件；首次调用生成 PHASE_GATE.md，已批准时直接推进阶段
> 调用方式: `prae advance-phase`
> 重要: 若当前阶段已存在 `APPROVED: yes` 的 PHASE_GATE.md，则不要重生 gate，直接验证并推进
> 前置条件: 项目已完成 `prae init`

## 步骤

### 1. 读取当前阶段信息

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "未找到 prae/track_registry.yaml。项目可能只完成了 bootstrap。"
  echo "请先填写 prae/PRAE_INIT.md，然后运行: prae init"
  exit 1
}

python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
override = r.get('current_phase_override')
if override:
    print(f'检测到 current_phase_override={override}；常规阶段推进已暂停，请先完成例外处理并移除 override')
    exit(1)
phase_map = {
    'phase_00_infra': 'phase_01_research',
    'phase_01_research': 'phase_02_validation',
    'phase_02_validation': 'phase_03_conclusion',
}
curr = r['current_phase']
tgt = phase_map.get(curr)
if not tgt:
    print(f'已在最终阶段 {curr}，无需推进')
    exit(0)
print(f'current={curr}')
print(f'target={tgt}')
for t in r['tracks']:
    print(f'  {t[\"id\"]} [{t[\"type\"]}] state={t[\"state\"]}')
"
```

### 2. 若当前阶段已存在 APPROVED: yes 的 PHASE_GATE.md，则直接推进

```bash
python3 tools/check_phase_gate.py --project-dir . --check-approved && \
python3 tools/advance_phase.py --project-dir .
```

如果上面的检查和推进都通过，到此结束；不要再重生成 `PHASE_GATE.md`。

如果 `--check-approved` 失败，说明当前 gate 尚未批准或尚未生成，继续下面的生成流程。

### 3. 生成 PHASE_GATE.md 草稿

```bash
python3 tools/generate_phase_gate.py --project-dir .
```

读取输出中的：
- `path`
- `recommendation`
- `failed_conditions`

并打开生成的 `PHASE_GATE.md`，确认第 2 节勾选状态与工具输出一致。

### 4. 验证生成结果

```bash
python3 tools/check_phase_gate.py --project-dir .
```

### 5. 等待人工批准（必须停在这里）

```
PHASE_GATE.md 已生成，且内容已按当前实际门控结果填充。

请在输出里的 path 对应文件第 6 节填写：
  APPROVED: yes     ← 同意推进
  APPROVED: no      ← 驳回，需改进
  APPROVER: 你的名字
  APPROVED_AT: 今日日期

填写完成后，再次调用:
  prae advance-phase
或直接运行:
  python3 tools/check_phase_gate.py --project-dir . --check-approved
  python3 tools/advance_phase.py --project-dir .

再次调用 `prae advance-phase` 时，应先检查已批准 gate，并直接推进；不要重生成 `PHASE_GATE.md`。
```

**注意: 到此停止，不自动更新 current_phase。**

### 6. 批准后的后续动作（人工确认 APPROVED: yes 后执行）

```bash
python3 tools/advance_phase.py --project-dir .
```
