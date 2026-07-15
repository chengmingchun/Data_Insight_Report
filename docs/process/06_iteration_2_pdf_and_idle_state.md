# 迭代二：空闲初始态与 PDF 报告

## 变更背景

- 首次打开页面会默认启用内置样例，并在用户未上传 CSV 时自动生成分析。
- 分析结果仅能导出 HTML 和 CSV，缺少 PDF 分析报告。

## 验收标准

1. 首次打开页面不执行分析，不展示指标或下载按钮。
2. 内置样例默认关闭，仅在用户主动勾选并点击“生成报告”后执行。
3. 每次成功分析同时生成 HTML 与 PDF，前端可直接下载 PDF。
4. PDF 包含业务概览、AI 洞察、数据质量、三类矢量图表、Top-N、异常记录和清洗规则。
5. PDF 生成不依赖浏览器、Java、.NET 或操作系统级 HTML 渲染器，可在 Streamlit Cloud 运行。

## TDD 记录

- RED：新增 `PdfReportGenerator` 导入及管线 `result.pdf` 断言，测试因实现不存在而在收集阶段失败。
- GREEN：基于 ReportLab 和内置 CID 中文字体 `STSong-Light` 实现独立 PDF 生成器，并接入 `AnalysisOrchestrator`。
- 回归：新增 Streamlit AppTest，断言初始页无指标、无下载按钮且样例开关为关闭状态。

## 技术取舍

PDF 未采用 WeasyPrint、wkhtmltopdf 或浏览器打印，因为这些方案依赖额外系统组件，不利于 Streamlit Cloud 部署。图表由 ReportLab 原生矢量图元绘制，保持离线、清晰和可移植；交互图表仍由 Plotly 在页面和 HTML 报告中提供。

## 验证命令

```bash
python -m pytest --cov=src --cov-report=term-missing
python -m scripts.generate_sample_report
```

## 验证结果

- 自动化测试：29 项全部通过，总覆盖率 96%。
- 初始页测试：未上传 CSV 时无指标、无下载按钮，样例开关默认关闭。
- 空输入测试：主动点击生成只显示提示，不创建分析结果。
- PDF 样例：`outputs/sample_report.pdf`，共 3 页。
- 视觉验收：中文、页眉、页码、表格和三张矢量图表均无截断、重叠或缺字。
- 三页渲染检查图保存在 `docs/process/pdf-visual-validation/`，作为视觉验收过程件。
