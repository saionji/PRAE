# PRAE Research Gate

> **用途**: 研究轨道最低质量门控的详细规则与修复指南
> **读者**: LLM（你）
> **状态**: Active（PRAE v1.0）
> **最后更新**: 2026-04-20

---

## 1. 为什么有 Research Gate

研究代码和工程代码有本质差异：
- 工程代码求"正确"，研究代码求"可复现和可解读"
- 工程代码要覆盖率、评审，研究代码只要日志、参数和冒烟测试
- 工程代码不容许契约违规，研究代码绝对不容许泄露到基础设施

Research Gate 是**最低底线**，不追求工程质量，只要求：
- 证据可追溯（实验记录全）
- 能跑通一次（冒烟测试）
- 不污染基础设施（contracts 不违规）
- 不破坏复现性（experiments/ 下不被 import）

**工具**：`tools/check_research_gate.py`。

**推荐编码顺序**：对实验代码采用“轻量 PDAE”流程，而不是完整 PDAE M1-M3：
1. 先写 `Goal / Method`
2. 先写 `Preflight Check`（最小冒烟检查 + 输出契约）
3. 先写 `Expected Signal`
4. 再实现 `EXP_NNN.py`
5. 跑完后按验收结果填写 `Result / Conclusion`

这样做的目标是减少返工，而不是把实验脚本工程化。

---

## 2. 五条规则详解

### 规则 1：TRACK_LOG.md 有本次实验记录

**要求**：每次跑实验后，必须在对应轨道的 `TRACK_LOG.md` 的"已知证据"或"实验列表"部分新增一条，至少包含：

- 当前项目轮次：`**研究轮次**: cycle_N`，且必须与 `track_registry.yaml.current_cycle` 一致
- 目标（这次想回答什么）
- 方法（简述，不是完整步骤）
- 结果（关键数值或结论）
- 结论（支持 / 证伪 / 部分支持假设）
- 链接到完整 `EXP_NNN.md`

**为什么**：`TRACK_LOG.md` 是轨道级叙事，让人 5 分钟内能看清这条轨道做过什么、到了哪里。不更新等于没做过。

**通过示例**：
```markdown
## 已知证据

- EXP_003 (2026-04-25): 在 A 股日频数据测试纯动量因子，回测夏普 1.2，但换手率 400%。
  结论：信号有效但成本过高。→ [EXP_003.md](experiments/EXP_003.md)
- EXP_004 (2026-04-28): 对信号加 5 日平滑后，夏普降到 0.9，换手率降到 120%。
  结论：平滑降低信号强度但仍保留正收益。→ [EXP_004.md](experiments/EXP_004.md)
```

**违反示例**：
```markdown
## 已知证据

- 跑了一些动量实验，看起来还行。
```
（缺目标、方法、数值结论，无法追溯到具体实验）

**修复**：回到 `TRACK_LOG.md`，按通过示例的结构为每次实验补齐，并修正 `**研究轮次**: cycle_N`。若原始实验参数已经丢失，在条目里明确标注"参数未记录，需重跑"。

---

### 规则 2：至少一个冒烟测试（能跑通、输出格式正确）

**要求**：每条研究轨道的 `src/tracks/{track_id}/experiments/` 下必须至少存在一个脚本（通常是 `EXP_001.py` 或对应实验入口），满足：

- 能在空白环境下跑完不报错
- 输出一个可被人类检查的结果（数值、图、表、JSON 均可）
- 如果有随机性，产出可复现（见规则 3）

**为什么**：防止"只有纸面计划、没有可执行实验"的轨道混进来占着资源。研究轨道必须实际跑过至少一次。

**通过示例**：
```python
# src/tracks/research_strategy_momentum/experiments/EXP_001.py
import pandas as pd
from src.infra_data_v1.api import load_daily_bars

def main():
    bars = load_daily_bars(symbol="AAPL", start="2020-01-01", end="2020-12-31")
    momentum = bars["close"].pct_change(20)
    print(f"Mean momentum: {momentum.mean():.4f}")
    print(f"Std momentum: {momentum.std():.4f}")

if __name__ == "__main__":
    main()
```

**违反示例**：只有 `TRACK_LOG.md` 写了"计划对比动量和反转"，但 `experiments/` 目录为空。

**修复**：至少写一个最小可运行脚本，跑一次，把输出保存。不是要你做完整实验，只要证明"这条轨道是可执行的"。

---

### 规则 3：实验参数和最小检查已记录（随机种子、超参数、数据时间范围、Preflight）

**要求**：每个 `EXP_NNN.md` 的 `## Method` 章节必须列出：

- 随机种子（`seed=42`，或明确声明"无随机性"）
- 所有关键超参数（学习率、窗口长度、阈值、模型大小等）
- 数据来源和时间范围（"A 股日频，2020-01-01 至 2023-12-31"）
- 对照组设置（若有）

并且 `## Preflight Check` 章节必须列出：
- 最小冒烟检查（至少跑通并输出什么）
- 输出契约（stdout / 文件 / 图表的最低要求）

**为什么**：没有这些信息，实验不可复现。后续重跑时结果不同，无法判断是修改了代码还是参数漂移。

**通过示例**：
```markdown
## Method

- 数据源: infra_data_v1.load_daily_bars
- 标的: 沪深300成分股（截至 2024-01-01 的列表）
- 时间窗: 2018-01-01 至 2023-12-31
- 随机种子: seed=42（用于 sklearn 交叉验证）
- 动量窗口: 20 日
- 持仓周期: 5 日
- 换手成本: 3bps/单边
- 对照组: 完全随机选股（seed=42 同一种子）
```

**违反示例**：
```markdown
## Method

用过去一年数据测了动量策略，选了最近的 20 日窗口。
```
（缺种子、无具体日期、没说数据源、未声明对照组）

**修复**：回到原始代码补全参数和 `Preflight Check`。如果当时没设种子，标注"2026-04-25 前运行未设随机种子，结果仅供参考，需重跑"。

---

### 规则 4：check_contracts 通过（不违反基础设施契约）

**要求**：在提交前运行：
```bash
python3 tools/check_contracts.py \
  --contracts src/infra_data_v1/contracts.yaml --src src/
```
返回码 0，无违规。

**为什么**：研究轨道若直接 import 基础设施轨道的内部符号，会：
- 破坏基础设施的封装边界
- 让基础设施无法安全升级到 v2
- 污染整个项目的可维护性

所有研究代码只能通过基础设施的**公开契约**访问其能力。

**通过示例**：
```python
# src/tracks/research_strategy_momentum/impl/signal.py
from src.infra_data_v1.api import load_daily_bars  # 公开接口，contracts.yaml 声明
```

**违反示例**：
```python
# src/tracks/research_strategy_momentum/impl/signal.py
from src.infra_data_v1.internal._cache import _read_parquet  # 私有内部符号
```
`check_contracts.py` 会报错：`violation: src.infra_data_v1.internal._cache is not exported`。

**修复**：
- 替换为 contracts.yaml 允许的公开接口
- 如果公开接口不够用，与基础设施维护者沟通，按 v2 规则扩展公开契约（禁止修改 v1）

---

### 规则 5：实验脚本在 experiments/ 下（不被其他代码 import）

**要求**：`src/tracks/{track_id}/experiments/` 下的任何 `.py` 文件都**不能被**其他代码 import。它们是"丢弃型"脚本，记录结果后就不应再被复用。

**为什么**：
- `experiments/` 脚本的参数常常硬编码，不经过接口抽象
- 复用它们会导致重要实现藏在实验脚本里，无法进入门控体系
- 复现性依赖于"跑这个脚本当时的环境"，一旦被 import，上游变更会静默影响下游

**工具如何检查**：`check_research_gate.py` 会扫描所有 Python 文件，检查是否存在从非 experiments/ 文件指向 experiments/ 的 import 语句。

**通过示例**：
```
src/tracks/research_strategy_momentum/
├── experiments/
│   ├── EXP_001.py      # 独立运行，不被 import
│   ├── EXP_002.py      # 独立运行
│   └── EXP_001.md
└── impl/
    └── signal.py       # 被 EXP_003.py import 是可以的（反向 import）
```

**违反示例**：
```python
# src/tracks/research_strategy_momentum/impl/signal.py
from ..experiments.EXP_002 import calc_momentum  # 禁止
```

**修复**：
- 把需要被复用的函数从 `experiments/EXP_002.py` 挪到 `impl/` 下
- 如果被挪出的函数也要被另一个轨道用：进一步挪到 `src/shared/`，触发 PDAE M3（参见 PRAE_ROLES.md 执行者 SOP C）

---

## 3. Research Gate 不检查什么

明确声明**不检查**以下项，不要在研究轨道浪费时间做它们：

| 不检查 | 原因 |
|--------|------|
| 测试覆盖率 | 研究代码可读可重跑即可，不要求工程覆盖 |
| 设计评审 | 研究不做完整 M1/M2 类评审；实验前只做轻量 `Goal/Method/Preflight/Expected Signal` 冻结 |
| 代码风格（lint / format） | 可选，不阻塞；建议启用但不作为门控 |
| 文档字符串 | 参数记录走 `EXP_NNN.md`，不走 docstring |
| 性能基准 | 研究期只要"能跑完"；性能优化留到毕业期 |

---

## 4. 工具调用

### 4.1 本地调用

```bash
# 对单条研究轨道跑 Research Gate
python3 tools/check_research_gate.py \
  --track-id research_strategy_momentum \
  --project-dir .
```

返回码：
- `0`：通过
- `1`：违反规则 1-5 中任一项（错误详情打印到 stderr）
- `2`：工具错误（track_id 不存在等）

### 4.2 工具到位前的人工检查清单

你（AI）可以按下面的清单自行检查：

```
[ ] 规则 1: TRACK_LOG.md 有本次实验的完整条目（目标/方法/结果/结论/链接）
[ ] 规则 2: experiments/ 下至少一个脚本可跑通，最近一次运行有记录
[ ] 规则 3: 最新 EXP_NNN.md 的 Method 章节列齐种子/超参/数据范围
[ ] 规则 4: python3 check_contracts.py 返回 0
[ ] 规则 5: 从 impl/ 或其他轨道没有任何 import 指向 experiments/
```

全部勾选才能视为通过 Research Gate。

### 4.3 CI 调用

研究项目的 CI 应在每次 PR 上对涉及的轨道运行 `check_research_gate.py`。失败阻塞合并。

---

## 5. 违反后的处理流程

发现违反时，按如下步骤处理：

1. **不要合并或继续推进**当前轨道
2. 识别违反的具体规则（1-5 哪一条）
3. 按本文档对应规则的"修复"段落操作
4. 重新运行 Research Gate
5. 通过后继续

**常见误区**：试图绕过 Research Gate（例如把规则视为建议）。这会让后续 Phase Gate 审查失败，因为 PHASE_GATE.md 需要列出"每条 ACTIVE 轨道通过 Research Gate"作为必要条件。

---

## 6. 关键规则回顾

1. Research Gate 是研究轨道的最低底线，不是工程质量检查
2. 五条规则缺一不可
3. `experiments/` 下的脚本永远不被其他代码 import
4. 基础设施契约由 `check_contracts.py` 独立检查，是 Gate 的组成部分
5. 无自动化工具环境下按 §4.2 人工清单自检
6. **Research Gate 只适用于 ACTIVE 状态的轨道**：EXPLORING 轨道不能跳过 ACTIVE 直接被 KILLED；至少一次实验（触发 Research Gate 检查）是进入 KILLED 的前提
