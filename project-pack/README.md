# project-pack — PRAE 部署包

此目录包含将 PRAE 框架部署到具体研究项目所需的文件骨架。

## 入口定义

- `CLAUDE.md` / `AGENTS.md`：模型上下文入口
- `prae bootstrap`：项目安装入口
- `prae init`：项目状态初始化入口

## 自动部署（推荐）

由 `prae_bootstrap.py` 自动执行：

```bash
python3 /path/to/PRAE/tools/prae_bootstrap.py \
  --target /path/to/your/research/project \
  --client claude-code   # 或 codex
```

## 手工部署

1. 复制 `prae/` 目录到研究项目根目录
2. 复制 `tools/` 到研究项目 `tools/`（可选，使用 PRAE 根目录的工具也可以）
3. 用 `AI_CONTEXT.template.md` 的内容初始化 `CLAUDE.md`（Claude Code）或 `AGENTS.md`（Codex）
4. 按 `prae/PRAE_INIT.md` 填写研究问题和组件分类
5. 运行 `prae init`（或 `python3 tools/init_project.py ...`）生成 `track_registry.yaml` 和 Phase 0 工件

## 目录结构

```
project-pack/
├── README.md               ← 本文件
├── AI_CONTEXT.template.md  ← CLAUDE.md / AGENTS.md 骨架
├── prae/
│   ├── PRAE_INIT.md        ← 问题陈述和组件分类模板
└── tools/                  ← 门控脚本镜像（同步自根 tools/）
```
