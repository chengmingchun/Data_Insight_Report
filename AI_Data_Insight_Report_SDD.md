# AI 数据分析报告工具 — 软件设计说明书（SDD）

**文档版本**：v1.0  
**项目代号**：AI Data Insight Report  
**目标读者**：开发工程师、Codex、评审人员、测试人员  
**文档状态**：可实施  
**技术侧重**：工程能力 60% / AI 能力 40%

---

## 1. 文档目的

本文档用于指导开发一个可运行的数据分析报告工具。

系统接收 CSV 文件，完成：

1. 数据加载与校验；
2. 脏数据与缺失值处理；
3. 关键统计计算；
4. 分组、排序与 Top-N 分析；
5. 图表生成；
6. 异常检测；
7. 调用大语言模型生成数据洞察；
8. 导出完整 HTML 报告。

本文档同时作为 Codex 的实现依据。实现过程中如需求未明确，应优先遵循：

- 统计正确性优先于功能数量；
- 确定性计算优先于 LLM 推理；
- 可运行优先于过度设计；
- 模块边界清晰优先于代码集中；
- 原型采用模块化单体，不拆微服务。

---

## 2. 项目目标

### 2.1 核心目标

开发一个本地可运行的数据分析应用，用户上传订单类 CSV 文件后，可以自动获得：

- 数据质量报告；
- 清洗后的有效数据；
- 核心业务指标；
- 分组统计结果；
- Top-N 排名；
- 时间趋势图；
- 异常数据列表；
- AI 数据洞察摘要；
- 可下载的 HTML 报告。

### 2.2 非目标

第一版不实现：

- 用户注册与登录；
- 多租户；
- 分布式计算；
- 实时流处理；
- 数据库持久化；
- 通用 BI 拖拽分析；
- 自定义 SQL；
- 模型训练；
- 自动识别任意行业语义；
- 微服务、Kafka、Kubernetes。

---

## 3. 用户场景

### 3.1 主要用户

- 面试评审人员；
- 数据分析人员；
- 业务运营人员；
- 需要快速查看 CSV 统计结果的普通用户。

### 3.2 典型流程

1. 用户打开应用；
2. 上传 CSV 文件，或选择内置样例数据；
3. 系统解析文件并检查字段；
4. 系统执行数据清洗；
5. 页面展示清洗结果和数据质量报告；
6. 系统计算统计指标；
7. 系统生成图表和异常检测结果；
8. 系统将结构化分析结果提交给 LLM；
9. LLM 返回自然语言洞察；
10. 用户预览并下载 HTML 报告。

---

## 4. 样例业务模型

第一版使用“电商订单数据”作为标准样例。

### 4.1 标准输入字段

| 字段 | 类型 | 是否必需 | 说明 |
|---|---|---:|---|
| order_id | string | 是 | 订单唯一标识 |
| order_date | date | 是 | 下单日期 |
| region | string | 否 | 地区 |
| category | string | 否 | 商品类别 |
| product | string | 是 | 商品名称 |
| quantity | integer | 是 | 商品数量 |
| unit_price | decimal | 是 | 单价 |
| discount | decimal | 否 | 折扣比例，范围 0~1 |
| status | string | 是 | 已完成、已退款、已取消等 |

### 4.2 派生字段

```text
sales_amount = quantity × unit_price × (1 - discount)
```

只有通过业务校验的数据才参与销售额统计。

---

## 5. 功能需求

## 5.1 文件上传

系统应支持：

- 上传 `.csv` 文件；
- 使用 UTF-8 编码；
- 尝试兼容 UTF-8-SIG；
- 文件大小限制默认 20 MB；
- 提供内置样例 CSV；
- 对空文件、格式错误、字段缺失给出明确提示。

## 5.2 数据字段校验

系统必须检查：

- 必需字段是否存在；
- 数值字段能否转换；
- 日期字段能否解析；
- 是否存在重复订单；
- 折扣是否在 0~1；
- 数量和单价是否为正数；
- 订单状态是否合法。

## 5.3 数据清洗

系统必须区分三类数据：

1. **有效数据**：参与全部分析；
2. **部分有效数据**：可参与部分分析，例如日期无效但销售金额有效；
3. **拒绝数据**：关键字段非法，不参与核心统计。

### 5.3.1 清洗策略

| 问题 | 策略 | 是否保留原记录 |
|---|---|---:|
| order_id 缺失 | 拒绝记录 | 是 |
| order_id 重复 | 保留第一条，其余标记重复 | 是 |
| order_date 无法解析 | 日期置空，不参与趋势分析 | 是 |
| region 缺失 | 填充“未知地区” | 是 |
| category 缺失 | 填充“未分类” | 是 |
| product 缺失 | 拒绝记录 | 是 |
| quantity 无法转换 | 拒绝记录 | 是 |
| quantity <= 0 | 拒绝销售统计，标记业务异常 | 是 |
| unit_price 无法转换 | 拒绝记录 | 是 |
| unit_price <= 0 | 拒绝销售统计，标记业务异常 | 是 |
| discount 缺失 | 填充 0 | 是 |
| discount < 0 或 > 1 | 拒绝记录或修正前明确标记 | 是 |
| status 缺失 | 填充“未知状态” | 是 |
| 前后空格 | 去除 | 是 |

### 5.3.2 数据质量报告

必须输出：

- 原始记录数；
- 有效记录数；
- 部分有效记录数；
- 拒绝记录数；
- 重复记录数；
- 缺失值数量；
- 各字段异常数量；
- 清洗规则说明。

## 5.4 统计分析

### 5.4.1 总览指标

必须计算：

- 原始记录数；
- 有效订单数；
- 总销售额；
- 平均订单金额；
- 商品总数量；
- 退款订单数；
- 退款率；
- 异常记录数。

### 5.4.2 分组统计

必须支持：

- 按地区统计销售额和订单数；
- 按品类统计销售额和订单数；
- 按商品统计销售额和销量；
- 按订单状态统计订单数；
- 按日期统计销售额趋势。

### 5.4.3 Top-N

默认输出：

- 销售额 Top 10 商品；
- 销量 Top 10 商品；
- 销售额 Top 5 地区；
- 销售额 Top 5 品类。

Top-N 参数应允许通过常量或 UI 控件配置。

## 5.5 多维分析

加分功能：

- 地区 × 品类销售额透视表；
- 地区 × 状态订单数透视表；
- 日期 × 地区销售趋势；
- 品类退款率对比。

第一版至少实现一个二维透视分析。

## 5.6 图表

至少生成三张图：

1. 每日销售额趋势折线图；
2. 商品销售额 Top 10 横向柱状图；
3. 地区销售额柱状图。

建议增加：

4. 订单状态占比图；
5. 品类销售额图；
6. 异常订单金额分布图。

图表要求：

- 标题明确；
- 坐标轴有名称；
- 金额带货币格式；
- Top-N 降序排列；
- 类目过多时不使用饼图；
- HTML 报告内可正常显示；
- 图表数据必须来自清洗后的统计结果。

## 5.7 异常检测

系统实现两类异常检测。

### 5.7.1 规则异常

包括：

- quantity <= 0；
- unit_price <= 0；
- discount 不在 0~1；
- 缺失关键字段；
- 重复订单；
- 非法日期。

### 5.7.2 统计异常

使用 IQR 四分位距方法检测单笔销售额异常：

```text
IQR = Q3 - Q1
下界 = Q1 - 1.5 × IQR
上界 = Q3 + 1.5 × IQR
```

超出范围的订单标记为统计异常。

约束：

- 异常记录默认保留；
- 异常记录不应被静默删除；
- 报告中显示异常原因；
- 统计异常仅表示“值得关注”，不等于数据错误。

## 5.8 AI 数据洞察

### 5.8.1 核心原则

LLM 不负责：

- 读取原始 CSV；
- 计算销售额；
- 计算平均值；
- 计算排名；
- 计算退款率；
- 判断统计结果是否正确。

LLM 只负责：

- 总结结构化统计结果；
- 描述趋势；
- 指出异常和风险；
- 生成业务建议；
- 将机器指标转换为自然语言。

### 5.8.2 输入结构

传入 LLM 的数据必须是结构化 JSON，例如：

```json
{
  "overview": {
    "valid_orders": 982,
    "total_sales": 1285300.50,
    "average_order_value": 1308.86,
    "refund_rate": 0.043
  },
  "top_products": [
    {
      "product": "显示器",
      "sales": 235000
    }
  ],
  "top_regions": [
    {
      "region": "华东",
      "sales": 420000
    }
  ],
  "trend": {
    "highest_sales_date": "2026-06-18",
    "highest_sales": 83000
  },
  "anomalies": {
    "count": 12,
    "largest_order": 68000
  }
}
```

### 5.8.3 Prompt 约束

系统提示词必须包含：

- 只能依据输入数据；
- 不允许虚构数字；
- 不允许改变统计口径；
- 不确定时明确说明；
- 输出不超过 300 字；
- 输出包含整体表现、趋势、异常、建议；
- 所有金额使用统一单位。

### 5.8.4 LLM 调用失败策略

LLM 不可用时：

- 统计分析必须继续成功；
- 图表必须继续生成；
- HTML 报告必须继续导出；
- AI 摘要区域显示降级说明；
- 可使用模板化摘要作为 fallback。

---

## 6. 非功能需求

## 6.1 正确性

- 同一输入应得到相同统计结果；
- 核心指标必须有单元测试；
- 统计数据不得依赖 LLM；
- 金额计算统一使用浮点格式化或 Decimal 策略；
- 退款率分母需明确定义。

## 6.2 性能

原型目标：

- 10 万行以内 CSV 可在普通开发机完成处理；
- 1 万行数据在数秒内完成分析；
- LLM 调用不阻塞基础报告生成；
- 重复计算应避免无意义执行。

## 6.3 可维护性

- 模块职责单一；
- 类型定义清晰；
- 避免全局变量；
- 配置从环境变量读取；
- 清洗规则集中管理；
- LLM Provider 可替换；
- 图表生成逻辑与页面展示解耦。

## 6.4 可观察性

记录：

- 文件加载开始与结束；
- 数据行数；
- 清洗结果；
- 统计耗时；
- 图表生成耗时；
- LLM 调用耗时；
- LLM 调用错误；
- 报告导出路径。

不得记录：

- API Key；
- 完整敏感数据；
- 用户隐私字段。

## 6.5 安全性

- 不执行上传文件中的任何代码；
- 只接受 CSV；
- 限制文件大小；
- 校验文件扩展名与内容；
- API Key 通过环境变量提供；
- HTML 模板默认转义；
- 不把完整原始数据发送给 LLM。

---

## 7. 技术选型

## 7.1 编程语言：Python 3.11+

### 选择理由

- Pandas 数据处理生态成熟；
- Streamlit 适合快速构建数据应用；
- Plotly 可生成交互式图表；
- LLM SDK 支持完善；
- 面试原型开发效率高。

### 不选择 Java 的原因

Java 适合长期服务化系统，但该题目标是快速完成数据分析原型。使用 Java 会增加：

- CSV 处理代码量；
- 图表生成复杂度；
- 页面开发成本；
- 报告导出成本。

## 7.2 UI：Streamlit

### 选择理由

- 上传文件、表格、图表、指标卡开箱即用；
- 单仓库即可运行；
- 无需独立前端工程；
- 非常适合面试原型。

### 限制

- 不适合复杂前端交互；
- 不适合大型多用户生产系统；
- 页面层需要避免承载过多业务逻辑。

## 7.3 数据处理：Pandas

### 选择理由

- CSV 解析稳定；
- 缺失值处理方便；
- 分组、聚合、透视、Top-N 支持成熟；
- 易于验证统计结果。

## 7.4 图表：Plotly

### 选择理由

- 与 Streamlit 集成简单；
- 支持交互图表；
- 可嵌入 HTML；
- 适合柱状图、折线图、饼图和散点图。

## 7.5 模型接口：OpenAI-Compatible Client

实现一个可替换的 LLM Provider 接口，支持：

- OpenAI；
- 兼容 OpenAI API 的其他模型服务；
- Mock Provider；
- Template Fallback。

第一版不得将具体厂商 SDK 散落在业务代码中。

## 7.6 报告生成：Jinja2 + HTML

### 选择理由

- 模板简单；
- 图表可嵌入；
- 可离线查看；
- 不依赖系统字体和复杂 PDF 引擎；
- 便于评审人员打开。

PDF 导出作为可选加分项，不作为第一版强制要求。

## 7.7 数据校验：Pydantic

用于定义：

- 应用配置；
- 统计结果 DTO；
- AI 输入 DTO；
- 报告模型；
- 错误结构。

Pandas DataFrame 本身不使用 Pydantic 逐行建模，避免性能损耗。

## 7.8 测试：Pytest

覆盖：

- 数据加载；
- 数据清洗；
- 指标计算；
- Top-N；
- IQR 异常检测；
- LLM fallback；
- HTML 报告导出。

---

## 8. 总体架构

采用模块化单体架构。

```text
┌─────────────────────────────┐
│       Streamlit UI          │
│ 上传 / 配置 / 展示 / 下载     │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│     Application Service     │
│     AnalysisOrchestrator    │
└───────┬─────────┬───────────┘
        │         │
┌───────▼───┐ ┌───▼──────────┐
│ Loader    │ │ Cleaner      │
└───────────┘ └────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │ Analyzer          │
         │ Metrics / GroupBy │
         └────┬────────┬─────┘
              │        │
      ┌───────▼───┐ ┌──▼──────────┐
      │ Anomaly   │ │ Chart       │
      │ Detector  │ │ Builder     │
      └───────┬───┘ └──┬──────────┘
              │        │
         ┌────▼────────▼─────┐
         │ Insight Service   │
         │ LLM / Fallback    │
         └────────┬──────────┘
                  │
         ┌────────▼──────────┐
         │ Report Generator │
         │ HTML Export      │
         └───────────────────┘
```

---

## 9. 模块设计

## 9.1 loader.py

职责：

- 接收上传文件；
- 校验文件大小和类型；
- 识别编码；
- 读取 CSV；
- 标准化列名；
- 返回原始 DataFrame；
- 产生加载错误。

接口建议：

```python
class CsvLoader:
    def load(self, file_obj: BinaryIO) -> pd.DataFrame:
        ...
```

异常：

- EmptyFileError；
- UnsupportedFileError；
- CsvParseError；
- MissingRequiredColumnsError。

## 9.2 cleaner.py

职责：

- 去除字符串空格；
- 转换日期和数值字段；
- 处理缺失值；
- 标记重复订单；
- 标记无效业务数据；
- 生成有效数据、部分有效数据、拒绝数据；
- 生成数据质量报告。

接口建议：

```python
@dataclass
class CleaningResult:
    clean_df: pd.DataFrame
    rejected_df: pd.DataFrame
    partial_df: pd.DataFrame
    quality_report: DataQualityReport

class DataCleaner:
    def clean(self, raw_df: pd.DataFrame) -> CleaningResult:
        ...
```

## 9.3 analyzer.py

职责：

- 计算总览指标；
- 分组统计；
- Top-N；
- 时间趋势；
- 多维透视。

接口建议：

```python
class DataAnalyzer:
    def analyze(self, clean_df: pd.DataFrame) -> AnalysisResult:
        ...
```

约束：

- 只读取清洗后数据；
- 不修改输入 DataFrame；
- 所有统计口径集中定义；
- 输出结构化对象，不直接拼接 UI 文本。

## 9.4 anomaly.py

职责：

- 识别规则异常；
- 使用 IQR 识别销售额异常；
- 返回异常记录及原因。

接口建议：

```python
class AnomalyDetector(Protocol):
    def detect(self, df: pd.DataFrame) -> AnomalyResult:
        ...
```

实现：

```python
class RuleBasedAnomalyDetector:
    ...

class IqrAnomalyDetector:
    ...
```

## 9.5 charts.py

职责：

- 将分析结果转换为 Plotly Figure；
- 保持统一标题和格式；
- 不在此模块重新计算业务指标。

接口建议：

```python
class ChartBuilder:
    def build_daily_sales_chart(self, result: AnalysisResult) -> Figure:
        ...

    def build_top_products_chart(self, result: AnalysisResult) -> Figure:
        ...

    def build_region_sales_chart(self, result: AnalysisResult) -> Figure:
        ...
```

## 9.6 insight.py

职责：

- 将 AnalysisResult 转换为 LLM 输入；
- 构造提示词；
- 调用 LLM Provider；
- 校验模型输出；
- 失败时使用模板化摘要。

接口建议：

```python
class InsightProvider(Protocol):
    def generate(self, payload: InsightPayload) -> str:
        ...

class LlmInsightProvider:
    ...

class TemplateInsightProvider:
    ...
```

## 9.7 report.py

职责：

- 将统计结果、图表、数据质量报告和 AI 摘要填充到模板；
- 导出 HTML；
- 提供下载内容。

接口建议：

```python
class HtmlReportGenerator:
    def generate(self, report: ReportModel) -> str:
        ...
```

## 9.8 orchestrator.py

职责：

- 编排完整流程；
- 管理模块调用顺序；
- 汇总错误；
- 生成最终结果；
- 不包含具体统计算法。

接口建议：

```python
class AnalysisOrchestrator:
    def run(self, file_obj: BinaryIO, options: AnalysisOptions) -> ReportModel:
        ...
```

---

## 10. 设计模式

## 10.1 策略模式

### 使用位置

- 数据清洗规则；
- 异常检测算法；
- AI 洞察生成方式。

### 目的

不同处理策略可以独立替换，而不修改主流程。

示例：

```python
class CleaningRule(Protocol):
    def apply(self, df: pd.DataFrame) -> RuleResult:
        ...
```

具体规则：

- MissingRegionRule；
- DuplicateOrderRule；
- InvalidDiscountRule；
- InvalidQuantityRule。

## 10.2 模板方法模式

### 使用位置

完整分析流程。

固定流程：

```text
加载 → 校验 → 清洗 → 统计 → 异常检测 → 图表 → AI 洞察 → 报告
```

不同输入源或报告格式可以覆盖部分步骤，但不改变总体顺序。

可由 `AnalysisOrchestrator` 体现，不要求为了模式而强行继承。

## 10.3 工厂模式

### 使用位置

创建 LLM Provider。

```python
class InsightProviderFactory:
    @staticmethod
    def create(config: AppConfig) -> InsightProvider:
        ...
```

根据配置创建：

- OpenAIInsightProvider；
- CompatibleApiInsightProvider；
- TemplateInsightProvider。

## 10.4 适配器模式

### 使用位置

屏蔽不同 LLM SDK 的接口差异。

统一应用内部调用：

```python
provider.generate(payload)
```

底层可适配不同模型厂商。

## 10.5 门面模式

### 使用位置

`AnalysisOrchestrator` 作为上层门面。

UI 不直接调用 loader、cleaner、analyzer、LLM，而只调用：

```python
orchestrator.run(...)
```

## 10.6 依赖倒置

业务模块依赖抽象接口，不直接依赖具体模型 SDK。

例如：

```python
class InsightService:
    def __init__(self, provider: InsightProvider):
        self.provider = provider
```

这样测试时可以注入 Mock Provider。

## 10.7 DTO / Value Object

使用结构化对象传递数据：

- DataQualityReport；
- OverviewMetrics；
- AnalysisResult；
- AnomalyResult；
- InsightPayload；
- ReportModel。

避免模块之间传递无约束的字典。

---

## 11. 核心数据结构

建议使用 `dataclass` 或 Pydantic Model。

```python
class DataQualityReport(BaseModel):
    raw_rows: int
    valid_rows: int
    partial_rows: int
    rejected_rows: int
    duplicate_rows: int
    missing_counts: dict[str, int]
    invalid_counts: dict[str, int]
    applied_rules: list[str]
```

```python
class OverviewMetrics(BaseModel):
    valid_orders: int
    total_sales: float
    average_order_value: float
    total_quantity: int
    refunded_orders: int
    refund_rate: float
    anomaly_count: int
```

```python
class AnalysisResult(BaseModel):
    overview: OverviewMetrics
    sales_by_region: list[dict]
    sales_by_category: list[dict]
    sales_by_product: list[dict]
    orders_by_status: list[dict]
    daily_sales: list[dict]
    top_products: list[dict]
    region_category_matrix: list[dict]
```

```python
class ReportModel(BaseModel):
    quality: DataQualityReport
    analysis: AnalysisResult
    anomalies: list[dict]
    insight: str
    generated_at: datetime
```

---

## 12. 关键业务口径

## 12.1 有效订单

满足：

- order_id 非空；
- product 非空；
- quantity > 0；
- unit_price > 0；
- 0 <= discount <= 1；
- 数值字段可以解析。

## 12.2 总销售额

默认仅统计：

- 有效订单；
- 状态为“已完成”的订单。

如退款订单需要扣减，应明确配置。第一版采用：

```text
总销售额 = 已完成订单销售额之和
```

## 12.3 平均订单金额

```text
平均订单金额 = 总销售额 / 已完成订单数
```

分母为零时返回 0，不抛出除零异常。

## 12.4 退款率

```text
退款率 = 已退款订单数 / 有效订单总数
```

必须在 README 和报告中注明口径。

---

## 13. 处理流程

```text
用户上传 CSV
    ↓
文件合法性校验
    ↓
字段校验
    ↓
加载原始 DataFrame
    ↓
执行清洗规则
    ↓
生成 DataQualityReport
    ↓
生成 clean_df / partial_df / rejected_df
    ↓
计算 OverviewMetrics
    ↓
执行分组分析和 Top-N
    ↓
执行异常检测
    ↓
生成 Plotly 图表
    ↓
构造 InsightPayload
    ↓
调用 LLM 或 fallback
    ↓
生成 ReportModel
    ↓
页面展示
    ↓
导出 HTML
```

---

## 14. 错误处理

## 14.1 错误分类

### 用户输入错误

- 文件为空；
- 文件过大；
- 非 CSV；
- 必需字段缺失；
- CSV 无法解析。

处理：

- 页面显示清晰错误；
- 不展示 Python 堆栈；
- 允许用户重新上传。

### 数据质量问题

- 部分字段非法；
- 缺失值；
- 重复数据；
- 业务异常。

处理：

- 不视为系统崩溃；
- 进入数据质量报告；
- 按规则处理。

### 外部服务错误

- LLM 超时；
- API Key 缺失；
- API 限流；
- 返回内容为空。

处理：

- 使用 TemplateInsightProvider；
- 记录错误日志；
- 不影响基础分析。

### 系统错误

- 模板加载失败；
- 图表生成失败；
- 未知异常。

处理：

- 记录日志；
- 页面显示通用错误；
- 保留可诊断信息。

---

## 15. LLM 防幻觉设计

必须同时使用以下措施：

1. LLM 只接收聚合结果；
2. 提示词明确禁止虚构；
3. 控制输入 JSON 字段；
4. 限制输出长度；
5. 不让 LLM 返回新的统计表；
6. 可选：对输出中的数字进行白名单校验；
7. LLM 失败时使用模板摘要；
8. 报告注明“AI 洞察仅用于辅助解释”。

推荐增加数字校验：

- 提取 AI 输出中的数字；
- 检查其是否来自输入 JSON；
- 不通过时重试一次；
- 再失败则使用 fallback。

---

## 16. 页面设计

Streamlit 页面分为六个区域。

## 16.1 侧边栏

- 上传 CSV；
- 使用样例数据；
- Top-N 数量；
- 是否启用 AI；
- 模型名称；
- 生成报告按钮。

## 16.2 数据概览

指标卡：

- 原始行数；
- 有效订单数；
- 总销售额；
- 平均订单金额；
- 退款率；
- 异常数。

## 16.3 数据质量

展示：

- 清洗前后对比；
- 异常类型统计；
- 清洗规则；
- 拒绝记录预览。

## 16.4 图表分析

展示至少三张图。

## 16.5 AI 洞察

展示：

- 摘要；
- 趋势；
- 风险；
- 建议；
- 降级状态。

## 16.6 报告下载

- 下载 HTML；
- 可选下载清洗后 CSV；
- 可选下载异常记录 CSV。

---

## 17. 项目目录

```text
ai-data-report/
├── app.py
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   └── sample_orders.csv
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── exceptions.py
│   ├── loader.py
│   ├── cleaner.py
│   ├── analyzer.py
│   ├── anomaly.py
│   ├── charts.py
│   ├── insight.py
│   ├── report.py
│   └── orchestrator.py
├── templates/
│   └── report.html
├── tests/
│   ├── fixtures/
│   │   ├── clean_orders.csv
│   │   └── dirty_orders.csv
│   ├── test_loader.py
│   ├── test_cleaner.py
│   ├── test_analyzer.py
│   ├── test_anomaly.py
│   ├── test_insight.py
│   └── test_report.py
└── outputs/
    └── .gitkeep
```

---

## 18. 配置设计

`.env.example`

```env
APP_NAME=AI Data Insight Report
MAX_UPLOAD_MB=20
TOP_N=10
ENABLE_LLM=true

LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=30
```

要求：

- 不提交真实 API Key；
- 无 API Key 时自动使用 fallback；
- 配置通过 Pydantic Settings 读取。

---

## 19. 测试设计

## 19.1 单元测试

### loader

- 正常 CSV；
- 空文件；
- 缺列；
- 非法编码；
- 非法格式。

### cleaner

- 缺失值填充；
- 重复订单；
- 非法日期；
- quantity <= 0；
- unit_price <= 0；
- discount 越界；
- 清洗数量统计正确。

### analyzer

- 总销售额；
- 平均订单金额；
- 退款率；
- 分组统计；
- Top-N 排序；
- 空数据集；
- 单行数据。

### anomaly

- IQR 正常情况；
- 存在极端值；
- 样本过少；
- 规则异常。

### insight

- 正常 LLM 返回；
- 超时；
- API Key 缺失；
- 空返回；
- fallback 正常。

### report

- HTML 成功生成；
- 图表成功嵌入；
- 中文正常显示；
- 缺少 AI 摘要时仍可生成。

## 19.2 集成测试

给定样例脏数据：

- 完整执行分析流程；
- 验证报告生成；
- 验证统计结果与预期一致；
- 验证异常记录存在；
- 验证 HTML 可打开。

---

## 20. 验收标准

## 20.1 必须通过

- [ ] 应用可本地运行；
- [ ] 可上传 CSV；
- [ ] 提供样例数据；
- [ ] 可处理缺失值；
- [ ] 可识别重复和非法数据；
- [ ] 显示数据质量报告；
- [ ] 统计总量、求和、分组和 Top-N；
- [ ] 至少生成 1 张图；
- [ ] 建议生成至少 3 张图；
- [ ] LLM 可生成自然语言洞察；
- [ ] 无 LLM 时可降级；
- [ ] 可导出 HTML；
- [ ] 核心统计有测试；
- [ ] README 提供启动命令。

## 20.2 加分项

- [ ] 多维透视分析；
- [ ] IQR 异常检测；
- [ ] 异常记录下载；
- [ ] 数字幻觉校验；
- [ ] Dockerfile；
- [ ] PDF 导出；
- [ ] 图表交互；
- [ ] 完整测试覆盖。

---

## 21. Codex 实现要求

Codex 应按以下顺序实现，不应一次性生成全部代码后再修复。

### 阶段 1：工程骨架

1. 创建目录；
2. 创建 requirements.txt；
3. 创建配置、模型和异常；
4. 添加样例数据；
5. 添加 README 初稿。

### 阶段 2：确定性数据链路

1. 实现 loader；
2. 实现 cleaner；
3. 实现 analyzer；
4. 实现 anomaly；
5. 编写对应测试；
6. 使用 pytest 验证。

### 阶段 3：展示与图表

1. 实现 charts；
2. 实现 Streamlit 页面；
3. 展示数据质量报告；
4. 展示统计指标；
5. 展示图表；
6. 支持样例数据。

### 阶段 4：AI 洞察

1. 定义 InsightProvider 接口；
2. 实现 LLM Adapter；
3. 实现 Template fallback；
4. 构造严格 Prompt；
5. 加入超时和异常处理；
6. 编写 Mock 测试。

### 阶段 5：报告导出

1. 创建 Jinja2 模板；
2. 嵌入指标、表格、图表和洞察；
3. 支持下载 HTML；
4. 验证中文和图表显示。

### 阶段 6：交付完善

1. 完善 README；
2. 加入 `.env.example`；
3. 加入启动命令；
4. 补充架构说明；
5. 输出样例完整报告；
6. 确保测试全部通过。

---

## 22. Codex 编码约束

- Python 3.11+；
- 使用类型注解；
- 使用 `pathlib`；
- 使用 logging，不使用散落的 print；
- 所有函数应有清晰职责；
- 业务逻辑不得写入 Streamlit 页面；
- 不创建微服务；
- 不引入数据库；
- 不把原始 CSV 全量发送给 LLM；
- 不使用 LLM 计算指标；
- 不静默删除异常数据；
- 不硬编码 API Key；
- 不依赖外部服务才能启动；
- 所有核心模块应可独立测试；
- 每完成一个阶段后运行 pytest；
- 出错时优先修复当前阶段，不跳过失败测试。

---

## 23. 推荐依赖

```text
streamlit
pandas
plotly
jinja2
pydantic
pydantic-settings
python-dotenv
openai
pytest
pytest-cov
```

可选：

```text
kaleido
weasyprint
```

第一版不强制安装 PDF 相关依赖。

---

## 24. README 必须包含

- 项目介绍；
- 功能列表；
- 架构说明；
- 技术选型；
- 项目目录；
- 环境要求；
- 安装命令；
- 启动命令；
- 样例数据说明；
- LLM 配置；
- 无 API Key 降级行为；
- 测试命令；
- 数据清洗策略；
- 统计口径；
- 截图或演示说明；
- 已知限制；
- 后续演进方向。

---

## 25. 启动方式

推荐：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Windows：

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

测试：

```bash
pytest -q
```

---

## 26. 演进方向

后续可扩展：

1. 支持日志文件；
2. 自动字段映射；
3. 用户自定义指标；
4. 多文件对比；
5. 定时报告；
6. PDF 导出；
7. 数据库存储；
8. FastAPI 服务化；
9. React 前端；
10. 大文件分块处理；
11. Isolation Forest 异常检测；
12. 自动生成分析 SQL；
13. 多轮数据问答；
14. 报告模板管理。

---

## 27. 最终设计结论

该项目采用：

- **模块化单体架构**，避免原型阶段过度设计；
- **Streamlit + Pandas + Plotly**，保证开发效率和展示效果；
- **Jinja2 HTML 报告**，保证交付完整性；
- **策略模式、适配器模式、工厂模式和门面模式**，保证模块可替换；
- **LLM 与确定性统计解耦**，保证数据正确性；
- **规则检测 + IQR**，保证异常检测可解释；
- **Fallback 机制**，保证没有模型服务时系统仍可运行；
- **单元测试和数据质量报告**，突出工程能力。

项目最终应体现的核心能力不是“调用一次 LLM”，而是：

> 用可靠的数据工程流程生成正确统计，再让 LLM 对确定性结果进行可控解释。
