# 轨道日志：{{track_id}}

<!-- 模板来源: PRAE/runtime/abstract/TRACK_LOG.template.md -->
<!-- 规格参考: methodology/PRAE_ARTIFACTS.md §2.6 -->
<!-- 路径规则: prae/phases/phase_NN_*/tracks/{track_id}/TRACK_LOG.md（在 prae/ 下，不在 src/ 下） -->
<!-- 创建者: AI 分析者；每次实验、每次状态变更都要追加条目，不删历史 -->

**轨道 ID**: `{{track_id}}`
**类型**: infrastructure / research  <!-- 删除不适用的 -->
**当前阶段**: phase_{{NN}}_{{name}}
**研究轮次**: cycle_{{N}}
**创建日期**: {{YYYY-MM-DD}}

---

## Hypothesis（仅研究轨道填写）

{{一句话可证伪假设，与 track_registry.yaml 中的 hypothesis 字段保持一致}}

**失败判据**（什么情况下 KILL 这条轨道）：
{{明确可量化的终止条件}}

---

## 选型目标（仅基础设施轨道填写）

{{这条基础设施轨道需要提供什么能力，选型成功的标准是什么}}

---

## State

**当前状态**: EXPLORING  <!-- 随状态变更更新 -->
**依赖的轨道**:
- `{{depends_on_track_id}}`（若无依赖，填"无"）

---

## Experiments

| EXP ID | 日期 | 目的 | 结论 | 链接 |
|--------|------|------|------|------|
| EXP_001 | {{YYYY-MM-DD}} | {{这次实验想回答什么}} | 支持 / 证伪 / 部分支持 | [EXP_001.md](experiments/EXP_001.md) |

---

## Evidence Summary

> 每次实验后追加一段，格式：日期 + 关键发现 + 对假设的影响。不删历史。

- **{{YYYY-MM-DD}} EXP_001**：{{关键数值或结论，1-2 句}}。{{对假设的影响：正向/负向/中性信号}}。

---

## Decision Log

> 记录状态变更：何时变、谁建议、谁批准。格式：日期 + 旧状态 → 新状态 + 原因。

| 日期 | 变更 | 建议者 | 批准者 | 原因 |
|------|------|--------|--------|------|
| {{YYYY-MM-DD}} | 创建（EXPLORING） | AI | — | 项目启动 |
| {{YYYY-MM-DD}} | EXPLORING → ACTIVE | AI | {{approver}} | {{EXP_XXX 显示正向信号}} |
