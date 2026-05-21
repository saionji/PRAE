# CONCLUSION — {{project_name}}

<!-- 模板来源: PRAE/runtime/abstract/CONCLUSION.template.md -->
<!-- 规格参考: methodology/PRAE_ARTIFACTS.md §2.8 -->
<!-- 路径规则: prae/phases/phase_03_conclusion/CONCLUSION.md -->
<!-- 创建时机: Phase 2→3 门控批准后，由 AI 分析者生成 -->

**研究轮次**: cycle_{{N}}

---

## 项目结论

{{一段话总结：研究项目解决了什么问题，最终结论是什么。}}

---

## 各轨道去向

| 轨道 ID | 最终状态 | 结论摘要 | 备注 |
|---------|---------|---------|------|
| `{{track_id}}` | GRADUATED / KILLED / MERGED | {{一句话结论}} | {{可选备注}} |

---

## 毕业轨道的 PDAE 项目链接

<!-- 每条 GRADUATED 轨道对应一个 PDAE 工程项目 -->

| 轨道 ID | PDAE 项目路径 |
|---------|-------------|
| `{{track_id}}` | `{{path/to/pdae/project}}` |

---

## 未解决问题

<!-- 研究过程中发现但未回答的问题，供后续参考 -->

- {{未解决问题 1}}

---

## 最终决定

> DECISION 可选值: ARCHIVED / GRADUATED_TO_PDAE / CONTINUE

APPROVED: <pending | yes | no>
DECISION: <ARCHIVED | GRADUATED_TO_PDAE | CONTINUE>
APPROVER: <用户姓名或标识>
APPROVED_AT: <YYYY-MM-DD>
COMMENT: <可选，人工补充说明>
