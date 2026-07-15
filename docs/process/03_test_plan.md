# 测试计划

## TDD 节奏

每个阶段遵循 RED（失败测试）→ GREEN（最小实现）→ REFACTOR（保持测试通过）。阶段证据记录在 `04_tdd_log.md`。

## 测试层次

- 单元测试：Loader、Cleaner、Analyzer、Anomaly、Charts、Insight、Report。
- 集成测试：脏数据经过完整编排后得到确定指标、异常、图表与 HTML。
- UI 烟测：Streamlit 可启动，主页和设置页无未处理异常。
- 验收测试：对照追踪矩阵逐项检查，并生成样例完整报告。

## 边界数据

- `clean_orders.csv`：正常统计口径。
- `dirty_orders.csv`：缺失、重复、非法日期、非法数值和越界折扣。
- `missing_columns.csv`：缺少必需列。
- `all_refunded.csv`：无已完成订单，验证除零。
- `single_order.csv`：单样本 IQR。
- `iqr_outlier.csv`：极端订单检测。
- `decimal_quantity.csv`：非整数数量不得被截断后接受。
- `sample_orders.csv`：用于演示与交付报告的混合样例。

## 通过标准

- 自动测试全部通过。
- 核心业务模块覆盖率目标不低于 85%。
- 不发起真实 LLM 网络请求。
- 样例报告包含质量说明、指标、三张图、异常和降级/AI摘要。
