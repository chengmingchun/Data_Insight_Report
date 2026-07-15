# TDD 执行日志

## 阶段 1：需求与测试前移

- 先建立需求基线、CR-001、ADR、追踪矩阵和测试计划。
- 在创建 `src/` 实现前，先创建 Loader、Cleaner、Analyzer、Anomaly、Insight、Charts、Report、Integration 测试及首批 6 组边界 CSV；静态复核后按 TDD 新增非整数数量边界 CSV。
- RED 执行受阻：环境尚无 Pytest，随后依赖安装被宿主命令执行器故障和沙箱网络策略阻断。未伪造 RED 通过/失败输出；安装日志保存在同目录。

## 阶段 2：确定性链路 GREEN

- 实现 Loader、Cleaner、Analyzer、IQR 和 Pydantic DTO。
- 使用本机已有 Pandas/Pydantic 执行 `python -m scripts.core_smoke_test`。
- 结果：`core-smoke-ok`。
- 覆盖：正常指标、Top-N、综合脏数据三分类、IQR 极端值、非整数数量拒绝。

## 阶段 3：展示、洞察与报告 GREEN

- 实现三张 Plotly 图、DeepSeek 适配器、Provider 工厂、模板降级、数字白名单、Jinja2 报告和 Streamlit 页面。
- 全仓 `compileall`：通过。
- 扩展受限环境烟测：模板摘要、Mock DeepSeek 聚合输入、数字幻觉二次失败后降级、HTML 中文与图表插槽均通过。
- 结果：`core-smoke-ok`；两条 `ValueError` warning 为故意构造的数字幻觉重试证据。

## 阶段 4：样例报告验收

- 受限环境先生成约 147 KB 的静态完整报告，并完成三张图像素检查。
- 依赖安装完成后使用正式 Plotly 链路重新生成 `outputs/sample_report.html`，大小约 4.9 MB，图表运行时已内嵌。
- 结构检查：标题存在、模板降级标识存在、2 个数据表、3 张图表。
- 浏览器直接打开 `file://` 被内置浏览器安全策略拒绝；未采用绕过方式。

## 阶段 5：完整回归与页面烟测

- `pytest --cov=src --cov-report=term-missing`：25 项全部通过，总覆盖率 94%。
- Streamlit AppTest：0 个页面异常，标题和内置样例分析正常。
- 本地服务：`/_stcore/health` 返回 `ok`，首页返回 HTTP 200。
- 真实 DeepSeek 调用未执行：用户选择不在本地提供密钥；适配器使用 Mock 验证，不影响主链路验收。
