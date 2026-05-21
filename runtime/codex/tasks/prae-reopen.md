# Task: prae-reopen

> 根据已批准的 `CONCLUSION.md` 中 `DECISION: CONTINUE` 将项目重开到 `phase_01_research`
> 调用方式: `prae reopen`
> 前置条件: 当前阶段为 `phase_03_conclusion`，且人工已在 `CONCLUSION.md` 填写 `APPROVED: yes` 和 `DECISION: CONTINUE`

## 步骤

### 1. 验证 `CONCLUSION.md`

```bash
python3 tools/check_conclusion.py --project-dir . --check-approved
```

若未通过，先补齐：
- `APPROVED: yes`
- `DECISION: CONTINUE`
- `APPROVER: <你的名字>`
- `APPROVED_AT: <YYYY-MM-DD>`

### 2. 重开项目

```bash
python3 tools/reopen_project.py --project-dir .
```

### 3. 结果说明

执行成功后：
- `track_registry.yaml` 的 `current_phase` 会切回 `phase_01_research`
- `track_registry.yaml` 的 `current_cycle` 会递增到下一轮
- 旧的 `phase_01/02/03` 目录会整体归档到 `prae/history/cycle_N/phases/`
- 会生成新的 `prae/phases/phase_01_research/PHASE_BRIEF.md` 作为下一轮研究入口
