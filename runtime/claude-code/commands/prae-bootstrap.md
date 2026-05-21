# /prae-bootstrap

> **用途**: 在研究项目中部署 PRAE 框架文件（技能、命令、模板）
> **使用场景**: 首次在一个新研究项目中安装 PRAE
> **参数**: 无（自动检测环境）

这是 **项目安装入口**，不是模型上下文入口。
模型在项目里建立上下文时，应先读 `CLAUDE.md` / `AGENTS.md`；项目状态初始化则由后续 `/prae-init` 完成。

## 执行步骤

### 1. 检测客户端平台

```bash
# Claude Code: 存在 .claude/ 目录或 CLAUDE.md
# Codex: 存在 AGENTS.md
# 都没有: 问用户

if [ -d ".claude" ] || [ -f "CLAUDE.md" ]; then
  CLIENT="claude-code"
elif [ -f "AGENTS.md" ]; then
  CLIENT="codex"
else
  echo "未检测到 Claude Code 或 Codex 环境"
  echo "请选择: (1) Claude Code  (2) Codex"
  # 等待用户输入
fi
```

### 2. 调用 bootstrap 脚本

```bash
PRAE_ROOT="${PRAE_HOME}"   # PRAE 仓库路径（由安装时配置）
TARGET_DIR="$(pwd)"

python3 "${PRAE_ROOT}/tools/prae_bootstrap.py" \
  --target "${TARGET_DIR}" \
  --client "${CLIENT}"
```

脚本会：
- 复制 `project-pack/` 最小骨架到目标项目（例如 `prae/PRAE_INIT.md`）
- 复制 `runtime/${CLIENT}/` 到 `.claude/` 或 `AGENTS.md`
- 复制 `runtime/abstract/` 模板到 `prae/templates/`
- 不会创建 `prae/track_registry.yaml` 或 Phase 0 工件；这些由后续 `/prae-init` 生成

### 3. 检查 PDAE 是否已安装

```bash
ls ${PDAE_HOME}/tools/check_contracts.py 2>/dev/null \
  && echo "PDAE 已检测到" || echo "PDAE 未检测到"
```

若未检测到 PDAE，提示用户：
```
PRAE 在基础设施轨道毕业时需要 PDAE。
如需一并安装 PDAE，请告诉我，我会引导你完成部署。
```

### 4. 安装后验证

```bash
# 验证关键文件已存在
ls .claude/skills/prae-guard.md .claude/skills/prae-analyst.md .claude/skills/prae-executor.md
ls .claude/agents/prae-literature-review.md
ls .claude/commands/prae-init.md
ls prae/templates/
ls prae/PRAE_INIT.md
```

### 5. 输出安装总结

```
✓ PRAE 已部署到 {TARGET_DIR}

已安装文件:
  .claude/skills/    prae-guard.md  prae-analyst.md  prae-executor.md
  .claude/agents/    prae-literature-review.md  prae-evidence-analyst.md  prae-phase-advisor.md
  .claude/commands/  prae-init.md  prae-add-track.md  prae-new-track.md  prae-new-exp.md  ...
  prae/templates/    8 份抽象模板
  prae/PRAE_INIT.md  初始化前最小骨架

下一步:
  1. 打开 prae/PRAE_INIT.md，填写问题陈述和轨道分类表
  2. 运行 /prae-init 生成 track_registry.yaml 和 Phase 0 工件
```
