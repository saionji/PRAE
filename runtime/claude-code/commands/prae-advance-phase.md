# /prae-advance-phase

> **用途**: 检查当前阶段门控条件；首次调用生成 PHASE_GATE.md，已批准时直接推进
> **参数**: 无（读取 track_registry.yaml 自动确定目标阶段）
> **前置条件**: 项目已完成 /prae-init，且你认为当前阶段的目标已达成，或用户要求检查是否可以推进

## 重要提示

若当前阶段已存在 `APPROVED: yes` 的 `PHASE_GATE.md`，此命令应直接验证并推进，不要重生 gate。
只有在当前 gate 尚未生成或尚未批准时，才进入“生成并等待批准”的路径。

## 执行步骤

### 1. 读取当前状态

```bash
[ -f "prae/track_registry.yaml" ] || {
  echo "未找到 prae/track_registry.yaml。项目可能只完成了 bootstrap。"
  echo "请先填写 prae/PRAE_INIT.md，然后运行 /prae-init。"
  exit 1
}

python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
override = r.get('current_phase_override')
if override:
    print(f'检测到 current_phase_override={override}；常规阶段推进已暂停，请先完成例外处理并移除 override')
    exit(1)
current = r['current_phase']
phase_map = {
    'phase_00_infra': 'phase_01_research',
    'phase_01_research': 'phase_02_validation',
    'phase_02_validation': 'phase_03_conclusion',
}
target = phase_map.get(current, None)
if target is None:
    print(f'当前已在最终阶段: {current}，无需推进')
    exit(0)
print(f'current={current}')
print(f'target={target}')
"
```

### 2. 若当前阶段已存在 APPROVED: yes 的 PHASE_GATE.md，则直接推进

```bash
python3 tools/check_phase_gate.py --project-dir . --check-approved && \
python3 tools/advance_phase.py --project-dir .
```

若以上命令通过，到此结束；不要再重生成 `PHASE_GATE.md`。
若 `--check-approved` 失败，说明 gate 尚未批准或尚未生成，继续下面的生成流程。

### 3. 生成 PHASE_GATE.md 草稿

```bash
python3 tools/generate_phase_gate.py --project-dir .
```

### 4. 展示检查结果

读取工具 JSON 输出并向用户展示：

```
阶段门控分析完成

当前阶段: {current_phase}
目标阶段: {target_phase}

门控条件:
  [x] 条件1（已满足）
  [ ] 条件2（未满足）

推荐动作: 推进 / 暂不推进
理由: ...

PHASE_GATE.md 已创建: {path}

---
请在 PHASE_GATE.md 第 6 节填写:
  APPROVED: yes  （推进）或  APPROVED: no  （驳回）
  APPROVER: {你的名字}
  APPROVED_AT: {日期}
  COMMENT: {可选说明}

填写完成后，告诉我"已批准"，我将执行后续动作。
```

然后运行一次：

```bash
python3 tools/check_phase_gate.py --project-dir .
```

确认生成文档与当前门控状态一致。

### 5. 等待批准信号

等用户在 PHASE_GATE.md 填写 `APPROVED: yes` 并告知后，再次调用：

```bash
/prae-advance-phase
```

或直接执行：

```bash
python3 tools/check_phase_gate.py --project-dir . --check-approved
```

再次调用 `/prae-advance-phase` 时，应先检查已批准 gate，并直接推进；不要重生成 `PHASE_GATE.md`。

### 6. 批准后的后续动作

当检测到 `APPROVED: yes` 后，按 `methodology/PRAE_PHASE_GATES.md` 对应章节执行：

```bash
python3 tools/advance_phase.py --project-dir .
```
