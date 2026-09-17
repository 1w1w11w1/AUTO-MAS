# 测试脚本入口

`tests/` 是 pytest 回归测试目录，**只保存跨功能通用的公共测试与纯逻辑测试**。

功能实现与 bug 修复的测试属于一次性验证产物：改动现场本地写、本地跑，把命令与结论贴进 PR 正文，然后随工作区丢掉，不提交——它们留在仓库只会抬高每次跑测试的时间成本。判据与例外流程见根目录 `AGENTS.md`「分支与 PR」。

## 目录归属

- `tests/tools/`：通用工具与外部平台交互
- `tests/platform/`：平台识别、能力声明与不支持能力错误
- `tests/models/`：配置基类与通用数据约束
- `tests/core/`：核心流程、生命周期与公共协议机制
- `tests/api/`：核心 HTTP/API 行为
- `tests/` 根目录：跨模块、启动环境或无法归入单一边界的兼容测试
- `scripts/`：需要手动运行的独立诊断/冒烟脚本，不作为 pytest 入口

专项适配、具体功能域与 bug 边界的测试不进 `tests/`：这类验证在改动现场就地完成即可。

## Agent 规则

- pytest 在 pyproject 的 `dev` 依赖组中，生产依赖不包含它；本地缺失时执行 `uv sync --group dev` 安装。
- 开发时照旧编写测试用例并本地运行，把验证命令与结论附在 PR 正文；测试文件默认不提交，判据见根目录 `AGENTS.md`「分支与 PR」。
- 修改专项适配时，就地写最小验证用例跑一遍即可；不要为凑目录新增测试文件。
- 合并前必须通过收集门槛：`python -m pytest tests --collect-only -q` 退出码为 0，防止失效测试在合并时静默累积。

示例：

```powershell
python -m pytest tests/models/test_config_base.py -q
```
