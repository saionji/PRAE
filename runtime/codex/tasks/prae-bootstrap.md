# Task: prae-bootstrap

> 在当前研究项目中部署 PRAE 框架（Codex 版本）
> 调用方式: `prae bootstrap` 或 `codex exec --task path/to/prae-bootstrap.md`

这是 **项目安装入口 task**，不是模型上下文入口。
项目安装完成后，模型应先从项目内 `AGENTS.md` / `CLAUDE.md` 建立上下文；项目状态初始化则由后续 `prae init` 完成。

## 步骤

### 1. 检测 PRAE 仓库位置

```bash
PRAE_ROOT=""
for p in ${PRAE_HOME} ~/prae ~/PRAE; do
  [ -f "$p/runtime/abstract/PRAE_INIT.template.md" ] && PRAE_ROOT="$p" && break
done
[ -z "$PRAE_ROOT" ] && echo "错误: 未找到 PRAE 仓库，设置环境变量 PRAE_ROOT 后重试" && exit 1
echo "PRAE 仓库: $PRAE_ROOT"
```

### 2. 检测客户端类型

```bash
if [ -d ".claude" ] || [ -f "CLAUDE.md" ]; then
  CLIENT="claude-code"
elif [ -f "AGENTS.md" ]; then
  CLIENT="codex"
else
  echo "未检测到 .claude/ 或 AGENTS.md"
  echo "请创建 AGENTS.md（Codex 项目）或 .claude/（Claude Code 项目）后重试"
  exit 1
fi
echo "客户端类型: $CLIENT"
```

### 3. 运行 bootstrap 脚本

```bash
python3 "${PRAE_ROOT}/tools/prae_bootstrap.py" \
  --target "$(pwd)" \
  --client "${CLIENT}"
```

### 4. 检查 PDAE

```bash
if ls ${PDAE_HOME}/tools/check_contracts.py &>/dev/null; then
  echo "PDAE 已检测到"
else
  echo "注意: PDAE 未安装。基础设施轨道工程化和契约检查依赖 PDAE。"
  echo "如需安装，请参考 PDAE 仓库的部署说明。"
fi
```

### 6. 输出总结

```bash
echo ""
echo "PRAE 部署完成"
echo "已创建: prae/templates/, prae/PRAE_INIT.md（模板）"
echo ""
echo "下一步:"
echo "  1. 填写 prae/PRAE_INIT.md（问题陈述和组件分类）"
echo "  2. 运行: prae init（生成 track_registry.yaml 和 Phase 0 工件）"
```
