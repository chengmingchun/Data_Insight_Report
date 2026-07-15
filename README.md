# AI Data Insight Report

一个面向电商订单 CSV 的本地数据分析工具。它将文件加载、可追踪清洗、确定性统计、IQR 异常检测、交互图表、DeepSeek 洞察和离线 HTML 报告组织成一条可测试的工程链路。

## 功能

- 上传 UTF-8 / UTF-8-SIG CSV，或直接分析内置样例。
- 输出完全有效、部分有效、拒绝记录和逐项质量原因。
- 计算计数、求和、平均值、退款率、分组、Top-N 和二维透视。
- 生成每日销售趋势、商品 Top-N、地区销售额三张 Plotly 图表。
- 使用规则和 IQR 检测异常，保留并导出异常记录。
- 在独立设置页配置 DeepSeek；模型只接收聚合 JSON。
- DeepSeek 未配置、超时、空返回或数字校验失败时自动使用模板摘要。
- 下载清洗后 CSV、异常 CSV 和包含图表的离线 HTML 报告。

## 架构

项目采用模块化单体。Streamlit 页面只负责输入和展示，`AnalysisOrchestrator` 固定编排以下流程：

```text
CSV 加载 -> 清洗分类 -> 确定性统计 -> IQR 异常 -> Plotly 图表
         -> 聚合 JSON -> DeepSeek / 模板降级 -> Jinja2 HTML
```

设计模式：

- 门面：`AnalysisOrchestrator` 为 UI 提供单一入口。
- 策略与依赖倒置：`InsightProvider` 可注入 DeepSeek、Mock 或模板实现。
- 工厂：`InsightProviderFactory` 根据会话配置选择 Provider。
- 适配器：`DeepSeekInsightProvider` 隔离 OpenAI-compatible SDK。
- DTO：Pydantic 模型约束模块间的统计和报告数据。

详细设计见 [AI_Data_Insight_Report_SDD.md](AI_Data_Insight_Report_SDD.md)，实现决策与测试过程见 `docs/`。

## 技术选型

- Python 3.11+
- Streamlit
- Pandas
- Plotly
- Pydantic / Pydantic Settings
- Jinja2
- OpenAI-compatible client（仅作为 DeepSeek API 适配层）
- Pytest / pytest-cov

## 安装与启动

一键启动：

```bat
start.bat
```

```bash
sh start.sh
```

脚本会自动进入项目目录、创建 `.venv`、安装缺失依赖并启动 Streamlit。也可以追加 Streamlit 参数，例如 `start.bat --server.port 8502` 或 `sh start.sh --server.port 8502`。

手动启动方式如下。

Windows（CMD，直接使用虚拟环境中的原生 Python）：

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

macOS / Linux：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 `http://localhost:8501`。上传 CSV 后点击“生成报告”；内置样例数据需要手动启用，不会在首次打开时自动分析。

Docker：

```bash
docker build -t data-insight-report .
docker run --rm -p 8501:8501 data-insight-report
```

## DeepSeek 配置

打开侧边栏的 **AI Settings**：

1. 启用 DeepSeek 洞察。
2. 默认模型保持 `deepseek-v4-flash`，Base URL 保持 `https://api.deepseek.com`。
3. 在密码输入框填写 API Key，保存当前会话。
4. 返回工作台并重新生成报告。

API Key 只存在当前 Streamlit 会话，不写入 CSV、HTML、日志或仓库。也可通过本地 `.env` 提供配置，字段参考 `.env.example`；真实 `.env` 已被 `.gitignore` 排除。

没有 API Key 时应用仍完整执行统计、图表和导出，洞察区域会明确显示模板降级状态。

## CSV 结构

| 字段 | 必需 | 说明 |
|---|---:|---|
| `order_id` | 是 | 订单唯一标识 |
| `order_date` | 是 | 下单日期 |
| `region` | 否 | 地区 |
| `category` | 否 | 商品品类 |
| `product` | 是 | 商品名称 |
| `quantity` | 是 | 正整数数量 |
| `unit_price` | 是 | 正数单价 |
| `discount` | 否 | 0 到 1 的折扣比例 |
| `status` | 是 | `已完成`、`已退款`、`已取消` |

仓库包含演示数据及以下边界夹具：正常、综合脏数据、缺列、全部退款、单订单和 IQR 极端值。

## 清洗策略

| 问题 | 处理 |
|---|---|
| 地区/品类缺失 | 填充“未知地区”/“未分类” |
| 折扣缺失 | 填充 0 |
| 非法日期 | 标为部分有效，不进入日期趋势 |
| 重复订单 | 保留第一条，其余进入拒绝集 |
| 关键字段缺失 | 进入拒绝集并记录原因 |
| 数量/价格无法解析或非正 | 进入拒绝集并记录原因 |
| 折扣无法解析或越界 | 进入拒绝集并记录原因 |
| IQR 极端金额 | 保留在统计中，额外标为值得关注 |

原始记录不被静默删除。页面和导出文件会保留源行号、拒绝原因或质量问题。

## 统计口径

- `sales_amount = quantity * unit_price * (1 - discount)`。
- 总销售额只汇总状态为“已完成”的通过关键业务校验订单。
- 平均订单金额 = 总销售额 / 已完成订单数；分母为 0 时返回 0。
- 退款率 = 已退款订单数 / 通过关键业务校验的订单数。
- 非法日期订单仍参与非时间类指标；拒绝记录不参与核心统计。
- IQR 异常只表示值得关注，不等于错误，也不会被自动剔除。

## 测试

```bash
pytest -q
pytest --cov=src --cov-report=term-missing
```

测试覆盖 Loader、Cleaner、Analyzer、IQR、图表、DeepSeek 降级、数字白名单、HTML 及端到端流程。自动测试不会调用真实 DeepSeek 服务。

生成完整样例报告：

```bash
python -m scripts.generate_sample_report
```

输出位于 `outputs/sample_report.html` 和 `outputs/sample_report.pdf`。

## 项目目录

```text
app.py                     Streamlit 分析工作台
pages/1_AI_Settings.py     DeepSeek 设置页
src/                       业务与应用模块
templates/report.html      离线报告模板
data/sample_orders.csv     演示数据
tests/fixtures/            边界测试 CSV
tests/                     单元与集成测试
docs/adr/                  架构决策记录
docs/process/              需求、追踪、TDD 与验收过程件
outputs/                   样例报告
```

## 已知限制

- 第一版只支持约定字段的电商订单 CSV，不自动推断任意行业语义。
- `order_id` 按“一行一个订单”处理，不支持一个订单多商品行的订单头合并。
- Streamlit 会话刷新后，页面填写的 DeepSeek Key 会丢失，这是刻意的安全选择。
- 日志文件、字段映射和大文件分块处理不在第一版范围。

## 演进方向

后续可增加字段映射、多文件对比、订单明细行模型、日志解析、异步模型调用和 10 万行以上的分块处理。
