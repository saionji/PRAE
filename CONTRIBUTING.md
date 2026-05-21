# Contributing to PRAE

Thanks for your interest in PRAE.

## Status

PRAE is at `v0.1.0-alpha`, maintained by a single author. The methodology layer is stable; the runtime and tooling are evolving based on real-project use. English documentation is being added incrementally — the source-of-truth is Chinese for now.

## Reporting Issues

Use [GitHub Issues](../../issues) to report bugs, propose features, or share use-case feedback.

When reporting a bug, please include:

- Which client you used (Claude Code or Codex)
- The command you ran
- The actual error or unexpected behavior
- What you expected to happen
- Your OS and Python version

## Pull Requests

- For non-trivial changes, please open an issue first to discuss the approach. PRAE has opinionated invariants (you cannot directly modify `track_registry.yaml`, etc.) and a quick chat saves rework.
- For small fixes (typos, doc clarity, obviously broken behavior), PRs are welcome directly.
- All tests must pass:

  ```bash
  pytest tests/ -v
  ```

- New behavior should come with a test (`tests/unit/` or `tests/integration/`).
- If you change a tool's CLI surface, update both the help text and any referencing docs (`README.md`, `methodology/PRAE_QUICKSTART.md`, the corresponding `runtime/*/commands/` or `runtime/*/tasks/` file).

## Documentation Contributions

Doc PRs are valued. In particular:

- **English translations** of any `methodology/*.md` file are very welcome — open one PR per document so reviews stay focused.
- Examples / case studies of using PRAE on a real project are welcome under `examples/`.

## What This Project Will NOT Accept

- IDE-specific adapters beyond Claude Code and Codex (e.g. Cursor, Aider integrations) at this stage — keep the surface area small while the methodology is stabilizing.
- Auto-graders that try to make Phase Gate or Research Gate decisions without human approval. The whole point of PRAE is structured human-in-the-loop research decisions.

## Code of Conduct

Be respectful and constructive. PRAE is a small, focused project — please assume good intent.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0 (see [`LICENSE`](LICENSE)).
