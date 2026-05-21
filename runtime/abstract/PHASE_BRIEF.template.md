# Phase {{NN}}_{{name}} 阶段简报

<!-- 模板来源: PRAE/runtime/abstract/PHASE_BRIEF.template.md -->
<!-- 规格参考: methodology/PRAE_ARTIFACTS.md §2.4 -->
<!-- 创建者: AI 分析者，在上一阶段 PHASE_GATE 批准后立即创建 -->

**阶段**: phase_{{NN}}_{{name}}
**研究轮次**: cycle_{{N}}
**创建日期**: {{YYYY-MM-DD}}
**创建者**: AI（分析者角色）

---

## 阶段目标

{{1-3 句话说明本阶段要达成什么，例如"完成所有基础设施轨道的选型和工程化，为研究期做好底座"}}

---

## 成功标准

> 满足以下所有条件时，可以由 AI 生成 PHASE_GATE.md 提请人工批准进入下一阶段。

- [ ] {{成功条件 1，可量化或可明确检查}}
- [ ] {{成功条件 2}}
- [ ] {{成功条件 N}}

---

## 本阶段在场的轨道

| 轨道 ID | 类型 | 初始状态 | 阶段目标状态 | 备注 |
|---------|------|---------|-------------|------|
| `{{track_id}}` | infrastructure / research | EXPLORING | LOCKED / ACTIVE | {{可选}} |

---

## 关键时间节点（可选）

| 里程碑 | 目标日期 | 说明 |
|--------|---------|------|
| {{里程碑名称}} | {{YYYY-MM-DD}} | {{可选说明}} |

---

## 关联文件

- `prae/track_registry.yaml` — 轨道状态总表
- `prae/phases/phase_{{NN}}_{{name}}/PHASE_GATE.md` — 本阶段结束时生成（尚未创建）
- `prae/PRAE_INIT.md` — 项目初始化文档（问题陈述和组件分类）
