# /prae-finalize

> **用途**: 根据已批准的 `CONCLUSION.md` 记录项目终态决定
> **参数**: 无
> **前置条件**: 当前阶段为 `phase_03_conclusion`，人工已在 `CONCLUSION.md` 填写终态决定

## 执行步骤

### 1. 验证 `CONCLUSION.md`

```bash
python3 tools/check_conclusion.py --project-dir . --check-approved
```

若未通过，先补齐：
- `APPROVED: yes`
- `DECISION: ARCHIVED / GRADUATED_TO_PDAE`
- `APPROVER: <你的名字>`
- `APPROVED_AT: <YYYY-MM-DD>`

如果人工决定是 `DECISION: CONTINUE`，不要运行本命令，改用 `/prae-reopen`。

### 2. 记录项目最终决定

```bash
python3 tools/finalize_project.py --project-dir .
```

### 3. 解读结果

执行成功后，`track_registry.yaml` 会登记：
- `project_decision`
- `project_approver`
- `project_decided_at`
- `project_finalized_at`

如果决定为 `ARCHIVED`，还会追加 `archived_at`。
