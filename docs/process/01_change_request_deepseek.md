# 变更请求 CR-001：默认使用 DeepSeek

## 变更内容

原 SDD 第 18 节示例默认 Provider 为 OpenAI。用户确认第一版默认采用 DeepSeek，并要求在前端设置页完成配置。

## 影响分析

- 架构不变：DeepSeek 使用 OpenAI-compatible API，由适配器隔离厂商细节。
- 配置新增：Provider、模型、Base URL、API Key、超时。
- 默认值：`deepseek-v4-flash`、`https://api.deepseek.com`。原 `deepseek-chat` 将于 2026-07-24 停用，故不作为新交付默认值。
- 安全：API Key 使用密码输入框，仅进入 `st.session_state`，不持久化、不打印。
- 可用性：没有 API Key 时工厂返回模板 Provider。
- 测试：使用 Mock Provider/Mock Client，不在自动测试中访问网络。

## 决策

批准。该变更不影响确定性统计链路，不扩大第一版业务范围。
