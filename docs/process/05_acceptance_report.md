# 验收报告

## 结论

SDD 必做功能和选定加分项均已实现。25 项自动测试全部通过，总覆盖率 94%；Streamlit AppTest 无页面异常，本地服务健康检查和首页 HTTP 检查均通过。DeepSeek 使用 Mock 验证，未配置真实密钥时按设计降级。

| ID | 验收项 | 实现 | 当前证据 | 状态 |
|---|---|---|---|---|
| FR-01 | CSV/UTF-8/UTF-8-SIG/缺列 | Loader | Pytest、compileall、核心烟测 | 通过 |
| FR-02 | 缺失、重复、非法值、三类数据 | Cleaner | dirty CSV：1 完全有效、1 部分有效、8 拒绝 | 通过 |
| FR-03 | 计数、求和、分组、Top-N | Analyzer | clean CSV：销售额 1780、均单 445 | 通过 |
| FR-04 | 地区 x 品类透视 | Analyzer/UI | Pytest、DTO 输出 | 通过 |
| FR-05 | 规则异常 + IQR | Cleaner/Anomaly | I006 极端订单识别 | 通过 |
| FR-06 | 三张图 | Plotly | 正式样例报告、图像素检查 | 通过 |
| FR-07 | DeepSeek + fallback | Insight | Mock 适配、聚合输入、模板降级 | 通过 |
| FR-08 | 前端设置页 | Streamlit | AppTest 0 异常、服务健康检查 | 通过 |
| FR-09 | HTML 报告 | Jinja2 | 4.9 MB 正式样例、表格/图结构检查 | 通过 |
| FR-10 | 端到端编排 | Orchestrator | 集成测试通过 | 通过 |

## 加分项

- 已实现：二维透视、IQR、异常 CSV 下载、数字幻觉校验、Dockerfile、交互 Plotly、完整分层测试代码。
- 未实现：PDF，按 SDD 为可选且不进入第一版范围。

## 验证与复现

过程日志保留了首次受限环境安装失败和最终成功安装、测试的完整记录：

- `pip-install.stderr.log`：沙箱网络拒绝访问包索引。
- `pip-install-final.stdout.log`：最终依赖安装记录。
- `pytest-final.log`：25 项测试及 94% 覆盖率。
- `streamlit-apptest.log`：页面烟测结果。

在正常联网环境执行：

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing
.venv\Scripts\python.exe -m streamlit run app.py
```

## 发布结论

迭代一发布门槛已满足。真实 DeepSeek 联调需要用户在设置页提供自己的密钥，不作为无密钥自动测试的阻塞项。
