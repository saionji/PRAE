# Task: prae-init

> 初始化 PRAE 研究项目（读 PRAE_INIT.md → 生成 track_registry.yaml → 创建 Phase 0 工件）
> 调用方式: `prae init` 或 `codex exec --task path/to/prae-init.md`
> 前置条件: 已运行 prae bootstrap，prae/PRAE_INIT.md 已填写完整

这是 **项目状态初始化入口 task**。
它不负责把 PRAE 装进项目；那一步是 `prae bootstrap`。它也不是模型上下文入口；模型上下文应先从项目内 `AGENTS.md` / `CLAUDE.md` 建立。

## 步骤

### 1. 验证 PRAE_INIT.md

```bash
[ -f "prae/PRAE_INIT.md" ] || { echo "错误: prae/PRAE_INIT.md 不存在，请先运行 prae bootstrap"; exit 1; }

python3 -c "
with open('prae/PRAE_INIT.md') as f:
    content = f.read()
issues = []
if '{{研究项目试图解决的核心问题}}' in content:
    issues.append('问题陈述未填写')
if '{{track_id}}' in content or content.count('infra_') == 0:
    issues.append('基础设施轨道未填写')
if issues:
    print('PRAE_INIT.md 不完整:')
    for i in issues: print(f'  - {i}')
    exit(1)
print('PRAE_INIT.md 验证通过')
"
```

### 2. 调用初始化工具

```bash
PROJECT_NAME="${1:-$(basename $(pwd))}"

python3 tools/init_project.py \
  --name "${PROJECT_NAME}" \
  --output-dir .
```

若工具不可用，先恢复工具，再重新运行：

```bash
if [ ! -f "tools/init_project.py" ]; then
  echo "缺少 tools/init_project.py"
  echo "请先重新运行 prae bootstrap，或从 PRAE 仓库复制 tools/init_project.py 到当前项目的 tools/"
  exit 1
fi

python3 tools/init_project.py \
  --name "${PROJECT_NAME}" \
  --output-dir .
```

### 3. 初始化结果检查

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
        print(f'  {t[\"id\"]}: Phase 0 TRACK_LOG.md 已生成')
"
```

### 4. 输出总结

```bash
echo ""
echo "PRAE 项目初始化完成"
python3 -c "
import yaml
r = yaml.safe_load(open('prae/track_registry.yaml'))
print(f'  项目: {r[\"project\"]}')
print(f'  当前阶段: {r[\"current_phase\"]}')
print(f'  当前轮次: cycle_{r[\"current_cycle\"]}')
print(f'  轨道数: {len(r[\"tracks\"])}')
"
echo ""
echo "下一步:"
echo "  运行 prae new-track <infra_track_id> 开始基础设施选型"
```
