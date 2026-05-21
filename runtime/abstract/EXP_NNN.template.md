# EXP_{{NNN}}：{{实验标题}}

<!-- 模板来源: PRAE/runtime/abstract/EXP_NNN.template.md -->
<!-- 规格参考: methodology/PRAE_ARTIFACTS.md §2.7 -->
<!-- 路径规则: prae/phases/phase_NN_*/tracks/{track_id}/experiments/EXP_NNN.md -->
<!-- 对应代码: src/tracks/{track_id}/experiments/EXP_NNN.py -->
<!-- 创建者: AI 分析者；Result 和 Conclusion 在实验跑完后填写，此后不再修改 -->

**实验 ID**: EXP_{{NNN}}
**轨道 ID**: `{{track_id}}`
**日期**: {{YYYY-MM-DD}}
**状态**: 进行中 / 已完成  <!-- 删除不适用的 -->

---

## Goal

{{一句话目标：这次实验要回答的核心问题}}

---

## Method

- **数据源**: `{{infra_track_id}}.{{api_function}}`（契约声明的公开接口）
- **标的 / 数据集**: {{具体数据集描述，例如"沪深300成分股，截至2024-01-01列表"}}
- **时间窗**: {{YYYY-MM-DD}} 至 {{YYYY-MM-DD}}
- **随机种子**: `seed={{N}}`（或"无随机性"）
- **关键超参数**:
  - `{{param_name}}`: {{value}}
  - `{{param_name}}`: {{value}}
- **对照组**: {{对照组设置，或"无对照组"}}
- **代码路径**: `src/tracks/{{track_id}}/experiments/EXP_{{NNN}}.py`

---

## Preflight Check

> 这是实验版“轻量 PDAE”步骤：先把最小可运行检查和输出契约写清，再开始实现。

**最小冒烟检查**：{{例如"脚本需在 30s 内跑完，并打印夏普、最大回撤、样本数"}}

**输出契约**：{{例如"stdout 至少包含 sharpe/max_drawdown；并写出 results/EXP_{{NNN}}.json"}}

**本次不做**：{{例如"不抽象成 impl/，不优化性能，不处理多市场泛化"}}

---

## Expected Signal

**成功判据**（验证假设）：{{例如"回测夏普 ≥ 1.0 且最大回撤 ≤ 25%"}}

**失败判据**（证伪假设）：{{例如"夏普 < 0 或最大回撤 > 40%"}}

**中性信号**：{{例如"夏普 0-1，继续优化"}}

---

## Result

> 在实验跑完后填写，此后不再修改。

**关键数值**:
- {{指标名}}: {{数值}}
- {{指标名}}: {{数值}}

**输出位置**: `{{图表或数据文件路径，若有}}`

**原始输出**（粘贴关键 stdout / stderr）：
```
{{粘贴实验关键输出}}
```

---

## Conclusion

**结论**: 支持 / 证伪 / 部分支持 假设

**理由**: {{1-3 句说明为什么得出上述结论}}

**对轨道状态的影响建议**:
- 建议 state 变更：{{EXPLORING → ACTIVE / 保持 EXPLORING / ACTIVE → KILLED / 等}} （或"无变更"）
- 下一步建议：{{下一个实验的方向，或终结轨道}}
