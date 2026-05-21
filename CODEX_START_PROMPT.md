# Codex Start Prompt

把下面整段直接发给 Codex 会话即可：

```text
这是一个 PRAE 环境。先读仓库根目录的 LLM_ENTRYPOINT.md，并严格按其中的文件读取顺序建立上下文。
标准入口定义：
- `LLM_ENTRYPOINT.md`：模型上下文入口
- `prae bootstrap`：项目安装入口
- `prae init`：项目状态初始化入口

先判断你当前是在：
1. PRAE 框架仓库本身
2. 某个使用了 PRAE 的研究项目

如果你在 PRAE 框架仓库里：
- 先读 README.md
- 再读 methodology/PRAE_QUICKSTART.md、methodology/PRAE_CORE_MODEL.md、methodology/PRAE_ROLES.md
- 然后只读与你当前任务直接相关的 tools/、runtime/、tests/

如果你在某个使用 PRAE 的研究项目里：
- 先读 AGENTS.md 或 CLAUDE.md
- 再读 prae/PRAE_INIT.md、prae/track_registry.yaml、当前 phase 的 PHASE_BRIEF.md、目标轨道 TRACK_LOG.md、最近的 EXP_NNN.md
- 如果 prae/track_registry.yaml 不存在，说明项目可能只完成了 bootstrap、尚未 init；先提示我完成 init，不要假设项目已经初始化
- 如果 current_phase=phase_00_infra，说明项目仍在基础设施锁定期；先完成 Phase 0，不要直接创建研究轨道实验

严格遵守以下规则：
- 不跳过任何 gate
- 不手工修改研究轨道的 state
- 不手工把基础设施轨道改成 LOCKED；必须走 tools/lock_infra_track.py 或 prae lock-infra
- 研究轨道状态变更必须走 tools/update_track_state.py 或 prae update-track-state
- 研究轨道不能 EXPLORING → KILLED 直接终止
- ACTIVE 轨道进入终态前必须通过 Research Gate
- LOCKED 基础设施不可直接修改；有新需求就开 v2
- 实验编码采用轻量 PDAE 顺序：先设计、先定义 Preflight Check、再实现、再验收

建立上下文后，先用 3 段输出：
1. 你判断当前属于哪种场景
2. 你已经读取了哪些关键文件
3. 当前最合理的下一步动作

如果我要你直接执行，请优先使用项目内已有的正式入口：
- Codex CLI: prae add-track / new-track / new-exp / record-result / lock-infra / update-track-state / advance-phase / finalize / reopen
- 正式工具: python3 tools/*.py

除非我明确要求，否则不要跳过方法论文档直接改代码。
```
