# Task: prae-finalize

> 根据已批准的 `CONCLUSION.md` 记录项目终态决定
> 调用方式: `prae finalize`
> 前置条件: 当前阶段为 `phase_03_conclusion`，且人工已在 `CONCLUSION.md` 填写终态决定

## 步骤

### 1. 验证 `CONCLUSION.md`

```bash
python3 tools/check_conclusion.py --project-dir . --check-approved
```

若未通过，先补齐：
- `APPROVED: yes`
- `DECISION: ARCHIVED / GRADUATED_TO_PDAE`
- `APPROVER: <你的名字>`
- `APPROVED_AT: <YYYY-MM-DD>`

如果人工决定是 `DECISION: CONTINUE`，不要运行本 task，改用 `prae reopen`。

### 2. 记录最终决定

```bash
python3 tools/finalize_project.py --project-dir .
```

### 3. 结果说明

根据 `project_decision` 的值，后续含义如下：
- `ARCHIVED`：PRAE 项目收尾完成，不再继续 PDAE 路由
- `GRADUATED_TO_PDAE`：至少一条轨道已毕业到 PDAE，后续在 PDAE 仓库继续工程化
