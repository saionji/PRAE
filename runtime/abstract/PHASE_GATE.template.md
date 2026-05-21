# Phase {{from}} → Phase {{to}} 门控分析

<!-- 模板来源: PRAE/runtime/abstract/PHASE_GATE.template.md -->
<!-- 规格参考: methodology/PRAE_PHASE_GATES.md §2 & methodology/PRAE_ARTIFACTS.md §2.5 -->
<!-- 创建者: AI 分析者；人工在第6节填写 APPROVED 字段后，再通过正式工具推进阶段 -->
<!-- 警告: 固定文件名为 PHASE_GATE.md；重新生成时应保留第6节审批字段 -->

**研究轮次**: cycle_{{N}}
**生成日期**: {{YYYY-MM-DD}}
**生成者**: AI（分析者角色）
**目标阶段**: phase_{{NN}}_{{name}}

---

## 1. 当前阶段状态

> 来源：`prae/track_registry.yaml`（current_phase: phase_{{from_NN}}_{{from_name}}）

| 轨道 ID | 类型 | 当前 state | 备注 |
|---------|------|-----------|------|
| `{{track_id}}` | infrastructure / research | EXPLORING / LOCKED / ACTIVE / ... | {{可选}} |

---

## 2. 门控条件逐项检查

<!-- 根据目标阶段填写对应条件（见 PRAE_PHASE_GATES.md 对应章节） -->
<!-- 未满足的条件打 [ ]，已满足的打 [x] -->

<!-- Phase 0 → 1 示例条件: -->
- [x] 所有 type=infrastructure 的轨道 state = LOCKED
- [x] 每条 LOCKED 轨道都有 contracts.yaml
- [x] 每条 LOCKED 轨道都有 MODULE_SPEC.md
- [x] 每条 LOCKED 轨道都通过 PDAE M3 门控（记录在 TRACK_LOG.md）
- [ ] check_contracts.py 对所有基础设施契约通过

<!-- 替换为与目标阶段对应的实际条件 -->

---

## 3. 证据摘要

> 每条关键证据 1-2 句，链接到 EXP_NNN.md 或 TRACK_LOG.md。

- **`{{track_id}}`**：{{选型结论或实验结论的一句话摘要}}。详见 [`TRACK_LOG.md`](tracks/{{track_id}}/TRACK_LOG.md)。

---

## 4. 风险与未决项

> 可能影响下一阶段的风险或尚未解决的疑问。

- {{风险 1：描述 + 影响评估 + 是否阻塞推进}}
- {{若无风险，填"无已知风险"}}

---

## 5. 建议

**推荐动作**: 推进 / 暂不推进

**理由**: {{1-3 句说明为什么建议推进或暂不推进}}

---

## 6. 待人工批准

```
APPROVED: <pending | yes | no>
APPROVER: <用户姓名或标识>
APPROVED_AT: <YYYY-MM-DD>
COMMENT: <可选，人工补充说明>
```

<!-- 人工填写示例:
APPROVED: yes
APPROVER: saionji
APPROVED_AT: 2026-04-22
COMMENT: 数据管道已通过上线前双人评审，可进入 Phase 1
-->
