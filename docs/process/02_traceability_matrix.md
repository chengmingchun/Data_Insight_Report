# 需求追踪矩阵

| ID | 需求 | 设计模块 | 验证 |
|---|---|---|---|
| FR-01 | CSV/UTF-8/UTF-8-SIG 加载与字段校验 | `loader.py` | `test_loader.py` |
| FR-02 | 三类数据与质量报告 | `cleaner.py` | `test_cleaner.py` |
| FR-03 | 总量、求和、分组、Top-N | `analyzer.py` | `test_analyzer.py` |
| FR-04 | 地区 x 品类透视 | `analyzer.py` | `test_analyzer.py` |
| FR-05 | 规则异常与 IQR | `anomaly.py` | `test_anomaly.py` |
| FR-06 | 至少三张可读图表 | `charts.py` | `test_charts.py` |
| FR-07 | DeepSeek 聚合洞察与降级 | `insight.py` | `test_insight.py` |
| FR-08 | 前端设置与下载 | `app.py` | 启动烟测、人工验收 |
| FR-09 | 离线 HTML 报告 | `report.py`、模板 | `test_report.py` |
| FR-10 | 端到端编排 | `orchestrator.py` | `test_integration.py` |
| NFR-01 | 同输入结果确定 | 数据链路 | 集成重复执行 |
| NFR-02 | API Key 不落盘/不进日志 | UI、Provider | 代码审查、Mock 测试 |
| NFR-03 | 无外部服务可启动 | Provider 工厂 | fallback 测试 |
