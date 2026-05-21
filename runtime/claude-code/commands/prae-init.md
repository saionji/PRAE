# /prae-init

> **用途**: 初始化一个新的 PRAE 研究项目
> **参数**: `[--name <project_name>]`（可选，默认用当前目录名）
> **前置条件**: 已运行 /prae-bootstrap 部署 PRAE 框架

这是 **项目状态初始化入口**。
它不负责部署 PRAE 到项目里；那一步是 `/prae-bootstrap`。它也不是模型上下文入口；模型上下文应先从 `CLAUDE.md` / `AGENTS.md` 建立。

## 执行步骤

### 1. 调用初始化工具

```bash
PROJECT_NAME="${1:-$(basename $(pwd))}"

python3 tools/init_project.py \
  --name "${PROJECT_NAME}" \
  --output-dir .
```

该工具会：
- 从 `prae/PRAE_INIT.md` 解析基础设施轨道和研究轨道
- 生成 `prae/track_registry.yaml`
- 生成真实的 `prae/phases/phase_00_infra/PHASE_BRIEF.md`
- 为每条基础设施轨道生成 `TRACK_LOG.md` 和目录骨架

若工具未安装，不要手工拷模板伪造 `track_registry.yaml` 或 `PHASE_BRIEF.md`；先恢复工具，再运行同一命令。

### 2. 恢复工具（工具不可用时）

```bash
if [ ! -f "tools/init_project.py" ]; then
  echo "缺少 tools/init_project.py"
  echo "请先重新运行 /prae-bootstrap，或从 PRAE 仓库复制 tools/init_project.py 到当前项目的 tools/"
  exit 1
fi
```

### 3. 引导填写 PRAE_INIT.md

切换到**分析者**角色，和用户逐步完成：

1. **问题陈述**：
   - "这个研究项目要解决什么核心问题？"
   - "成功标准是什么（可量化）？"
   - "什么情况下整个项目应该被终止？"

2. **基础设施轨道识别**：
   - "哪些能力是多条研究路线都会依赖的？（例如数据接入、回测引擎）"
   - 引导用户给每条基础设施轨道命名（格式：infra_{name}_v1）

3. **研究轨道识别**：
   - "你有哪些不同的算法方向或假设想要验证？"
   - 引导用户给每条研究轨道命名和写假设（格式：research_{topic}_{variant}）

### 4. 初始化结果检查

```bash
python3 -c "
import yaml, os
r = yaml.safe_load(open('prae/track_registry.yaml'))
assert r['current_phase'] == 'phase_00_infra'
assert 'current_cycle' in r
assert os.path.exists('prae/phases/phase_00_infra/PHASE_BRIEF.md')
for t in r['tracks']:
    if t['type'] == 'infrastructure':
        log_path = f'prae/phases/phase_00_infra/tracks/{t[\"id\"]}/TRACK_LOG.md'
        assert os.path.exists(log_path), log_path
        content = open(log_path, encoding='utf-8').read()
        assert '{{' not in content, f'{t[\"id\"]} TRACK_LOG.md 仍含模板占位符'
print('初始化产物检查通过')
"
```

### 5. 输出总结

```
✓ PRAE 项目 {PROJECT_NAME} 已初始化

目录结构:
  prae/PRAE_INIT.md           ← 请检查并确认
  prae/track_registry.yaml    ← 由工具从 PRAE_INIT.md 生成
  prae/phases/phase_00_infra/ ← Phase 0 工件已生成

下一步: 对每条基础设施轨道运行 /prae-new-track <id> 开始探索
当前阶段: phase_00_infra（基础设施就绪期）
```
