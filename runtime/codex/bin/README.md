# bin/prae — CLI 安装说明

`prae` 是 PRAE 方法论框架的统一 CLI 入口（Codex 版本）。
通过 `prae <subcommand>` 触发对应的 Codex task。

这里也区分三种“入口”：
- `LLM_ENTRYPOINT.md` / 项目内 `AGENTS.md`：模型上下文入口
- `prae bootstrap`：项目安装入口
- `prae init`：项目状态初始化入口

## 前置条件

- Codex CLI 已安装并可用（`codex` 命令）
- PRAE 仓库已克隆到本地

## 安装

### 方法 1：软链到 PATH（推荐）

```bash
# 假设 PRAE 仓库在 ${PRAE_HOME}
chmod +x ${PRAE_HOME}/runtime/codex/bin/prae
ln -sf ${PRAE_HOME}/runtime/codex/bin/prae ~/.local/bin/prae

# 确认 ~/.local/bin 在 PATH 中
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 验证
prae help
```

### 方法 2：直接运行（无需安装）

```bash
# 在研究项目目录下
bash ${PRAE_HOME}/runtime/codex/bin/prae <subcommand>
```

### 方法 3：alias（快速临时方案）

```bash
alias prae='${PRAE_HOME}/runtime/codex/bin/prae'
```

## 可用命令

```
prae bootstrap                     首次使用：部署 PRAE 到当前项目
prae init                          初始化研究项目（从 PRAE_INIT.md 生成 registry 和 Phase 0 工件）
prae add-track <track_id>          正式注册新轨道到 track_registry.yaml
prae new-track <track_id>          为已登记轨道创建当前阶段目录
prae new-exp <track_id>            新建实验
prae record-result <id> <exp_id>   记录实验结果
prae lock-infra <id>               在人工批准后正式将基础设施轨道锁定为 LOCKED
prae update-track-state <id> <state>  在人工批准后正式更新研究轨道状态
prae advance-phase                 首次生成阶段门控分析；已批准时正式推进阶段
prae graduate <track_id>           研究轨道毕业到 PDAE
prae finalize                      记录项目终态决定
prae reopen                        根据 CONTINUE 决定重开到 Phase 1
```

## 工作原理

每个命令对应 `runtime/codex/tasks/prae-{subcommand}.md`，
通过 `codex exec --task` 执行。Codex 读取 task 文件并完成相应操作。

启动顺序：
1. `prae bootstrap`：部署最小骨架、templates、tools、Codex tasks
2. 填写 `prae/PRAE_INIT.md`
3. `prae init`：生成 `prae/track_registry.yaml`、`prae/phases/phase_00_infra/PHASE_BRIEF.md` 和基础设施 `TRACK_LOG.md`
4. Phase 0：为基础设施轨道执行选型实验，PDAE M3 通过后用 `prae lock-infra`
5. 所有基础设施轨道 `LOCKED` 后，运行 `prae advance-phase` 生成 gate；人工批准后再次运行同一命令进入 Phase 1
6. Phase 1：已登记研究轨道运行 `prae new-track`、`prae new-exp`；若是全新假设，先 `prae add-track`

## 更新

PRAE 仓库更新后，CLI 自动使用新版 task 文件，无需重新安装。
