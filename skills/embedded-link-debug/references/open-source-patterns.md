# 开源实现调查：只借鉴原理

查阅日期：2026-10-10，America/New_York。星数为本轮 GitHub 公共 API 快照，之后可能变化；不是可靠性评分。仅核对官方仓库文档和部分源码，未安装、运行这些项目，也未验证其硬件支持。以下“覆盖”表示源码/文档提供该环节，不表示本机已跑通。

## 高星工具与直接闭环项目

| 项目 | 星数 | 核对范围与覆盖 | 适合参考的原理及限制 |
| --- | ---: | --- | --- |
| [ESP-IDF](https://github.com/espressif/esp-idf) | 19202 | master 的 [idf.py 文档](https://github.com/espressif/esp-idf/blob/86f72d0982d3ef38b62cb7cc87ae03c9da96a83b/docs/en/api-guides/tools/idf-py.rst)与 [MCP 实现](https://github.com/espressif/esp-idf/blob/86f72d0982d3ef38b62cb7cc87ae03c9da96a83b/tools/idf_py_actions/mcp_ext.py)：构建、烧录、脚本式串口观察 | 为现有工具提供项目明确、等待有期限、日志可追溯的接口。编辑与再次诊断由宿主 AI 完成；master 的能力不代表已安装旧版具有。monitor 默认连接复位，需查 no_reset 和脚本动作 |
| [PlatformIO Core](https://github.com/platformio/platformio-core) | 9518 | [仓库](https://github.com/platformio/platformio-core/tree/ff26956ecf0cdd44f6599894f11a83a93189e07f)、[串口监视文档](https://docs.platformio.org/en/latest/core/userguide/device/cmd_monitor.html)：构建/上传、测试与监视工具 | 芯片相关行为放在工程配置和适配层；是工具基础，不是自动诊断修复器。借鉴参数化接口即可，不要求将 Keil/WCH 工程迁移过去 |
| [probe-rs](https://github.com/probe-rs/probe-rs) | 2970 | [仓库快照](https://github.com/probe-rs/probe-rs/tree/e58eea5bf2808b2143a72b1c30d083acb2d3f7f5)、[cargo-embed](https://probe.rs/docs/tools/cargo-embed/)：编译、下载、按配置复位、RTT/GDB | 目标与探针配置、符号和运行观测分层。RTT 与 UART 是不同通路；支持范围需按实际版本/芯片查证，不是独立 AI 修复器 |
| [Embedded-AI-Harness](https://github.com/SensorsIot/Embedded-AI-Harness) | 189 | [README 快照](https://github.com/SensorsIot/Embedded-AI-Harness/blob/db6a0933075bb9ff5a99bb8e307a54b6a01af57d/README.md)：定义验收、构建、测试台烧录、观察并反馈修改 | 最接近用户所说的整体工作流之一；物理槽位映射、共享资源仲裁及明确测试目标值得参考。其 Raspberry Pi/ESP32、GitHub CI 与测试伙伴是特定实现，不成为本技能默认依赖 |
| [Agentic HIL](https://github.com/agentic-hil/agentic-hil) | 17 | [工具表](https://github.com/agentic-hil/agentic-hil/blob/523d599e9698f52a16f50716ffd6bc94eec7fb8e/docs/mcp-tools.md)、[Nucleo 示例](https://github.com/agentic-hil/agentic-hil/blob/523d599e9698f52a16f50716ffd6bc94eec7fb8e/examples/nucleo-f446re_demo/README.md)：下载、UART/CAN 激励、读取及结构化报告 | 实验步骤、期限、报告与硬件执行层分开，宿主 agent 负责主要源码修改/构建。不能仅凭示例日志判断所有目标已支持 |
| [Firment](https://github.com/MoRiv447/Firment) | 8 | [README](https://github.com/MoRiv447/Firment/blob/9fed462f20c9a561dabee746de36cb7e892cd633/README.md)、[agent.rs](https://github.com/MoRiv447/Firment/blob/9fed462f20c9a561dabee746de36cb7e892cd633/crates/firment-core/src/agent.rs)：编辑与工具循环、build/flash/monitor/HIL、验证门槛与迭代上限 | 让明确的工具结果影响下一轮，而非 AI 自称完成。verify_command 是可配置的，其通过只证明命令验证的范围；低星项目不能据此视为成熟通用方案 |

前三者星数较高，后几项与完整 AI 实物闭环更接近。不能把高星、项目名称或 README 的“自主”声明等同于已验证的闭环能力。

## 本技能吸收的原则

- 明确目标和项目；构建、下载与实验记录关联同一镜像。可采用已有本地工具，不强制 CI。
- 将读取、请求、编译、下载、观察提供为结果可检查的动作；长日志落盘，摘要不替代必要证据。
- 每个实验先明确行为和验收条件，使用有依据的等待期限。缺证据不能通过；失败结果进入下一轮假设检查。
- 设备复用先核对真实资源冲突，必要时仲裁占用并在取消/失败时释放；不能抢占其他会话。
- 代码、编译、烧录、运行与物理效果分层记录。有限实验仍无辨别力时换检查方法，不无限修改和擦写。

这些是结合本轮源码核查与反例审查作出的工程选择，不是对任何第三方实现的完整背书。尤其不照搬“测试变绿即物理正确”“测试台曾正常就能排除硬件故障”“清 RX 就排除迟到帧”“通过正则即证明业务完成”等推论。
