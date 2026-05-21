# PRAE Bootstrap 提示词（Codex 会话启动）

> **用途**: 在研究项目中首次启动 Codex 会话时粘贴，自动部署 PRAE 框架
> **粘贴位置**: Codex 会话输入框（首条消息）

这是 **项目安装入口提示词**，不是模型上下文入口提示词。
如果模型需要先建立上下文，应先读项目里的 `AGENTS.md` / `CLAUDE.md`；项目状态初始化则由后续 `prae init` 完成。

---

你是 PRAE 研究方法论框架的执行助手。我需要你把 PRAE 框架部署到当前项目。

**PRAE 仓库位置**: ${PRAE_HOME}（或通过 --prae-path 指定）

请执行以下操作：

1. **检测当前环境**：
   - 检查是否有 `AGENTS.md`（Codex 项目）
   - 检查是否有 `.claude/` 或 `CLAUDE.md`（Claude Code 项目）
   - 都没有：问我选择哪个

2. **运行 bootstrap 脚本**：
   ```bash
   python3 ${PRAE_HOME}/tools/prae_bootstrap.py \
     --target $(pwd) \
     --client codex
   ```
   脚本会复制 project-pack 最小骨架、Codex tasks、templates。
   注意：`track_registry.yaml` 和 Phase 0 工件不是 bootstrap 创建，而是后续 `prae init` 生成。

3. **检查 PDAE 安装状态**：
   ```bash
   ls ${PDAE_HOME}/tools/check_contracts.py
   ```
   若不存在，告诉我"PRAE 的基础设施毕业功能依赖 PDAE，是否现在安装？"

4. **将 AGENTS_SNIPPET.md 内容合并到 AGENTS.md**：
   - 若 AGENTS.md 已存在：在文件末尾追加 PRAE 段落
   - 若不存在：创建新的 AGENTS.md，只包含 PRAE 段落

5. **验证安装**：
   ```bash
   ls prae/templates/
   ls .prae/tasks/ 2>/dev/null || ls prae/tasks/ 2>/dev/null
   ```

6. **输出下一步指引**：
   ```
   ✓ PRAE 已部署
   下一步: 填写 prae/PRAE_INIT.md，然后运行:
     prae init   # 生成 track_registry.yaml 和 Phase 0 工件
   ```

所有操作完成后，等待我的进一步指令。
