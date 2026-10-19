# AI-skill

可独立复用的 Codex 技能源码。仓库只发布以下三个技能及其参考文档：

| 技能 | 用途 |
| --- | --- |
| [github-sync](skills/github-sync/SKILL.md) | 审查并同步当前项目改动，处理 GitHub 认证边界 |
| [ch584-ui-tuning](skills/ch584-ui-tuning/SKILL.md) | MCU 单色屏 UI 调整、实际绘图与初始化验证 |
| [embedded-link-debug](skills/embedded-link-debug/SKILL.md) | 按源码和实验排查嵌入式通信及设备链路 |

AI-skill 是这三个技能的独立源码仓库；原来的私有 1213 仓库继续管理个人工具，使用这些技能不需要访问它。历史来源和验证边界见 [迁移说明](docs/MIGRATION.md)。这里不包含整套 Codex 配置、凭据、私人对话、项目固件或历史备份。

## 安装

需要 PowerShell 7。先将本仓库克隆到自行选择的目录，在仓库目录运行：

```powershell
# 默认和 -Check 均只读取、检查，不创建目标目录。
pwsh -NoProfile -File ./tools/Install-Skills.ps1 -Check
# 检查通过后，只复制缺少的技能；已有且字节一致的技能跳过。
pwsh -NoProfile -File ./tools/Install-Skills.ps1 -Install
```

目标默认取 `CODEX_HOME`，未设置时为用户目录下的 `.codex`。可用 `-CodexHome 'D:\my-codex-home'` 指定绝对路径。调用者应确认选择的目标目录确实用于安装技能。

安装前会完整检查三个源技能和所有同名目标技能。已有文件的 SHA-256 清单不同、文件缺失或多出时，整个预检失败，不开始复制。请先审查并保留已安装技能的本地修改；安装器没有强制覆盖选项。重解析点、符号链接和目录联接会被拒绝。该安装器不修改 `AGENTS.md`、`config.toml`、账户或模型设置，也不执行固件操作。预检可阻止已发现的冲突，但不保证抵抗其他进程并发修改或复制中途的磁盘故障。

更新仓库后重新预检；有差异时人工比较并决定如何迁移，不能依靠自动安装覆盖。重新打开 Codex 会话以重新发现已安装的技能。

## 本地验证

无需安装 Python 依赖，使用适合项目的 Python 3.11+ 和 PowerShell 7：

```powershell
python -B tools/Verify-Repository.py
python -B -m unittest discover -s tests -v
```

可通过 `AI_SKILL_PWSH` 指定测试使用的 PowerShell 可执行文件。测试仅在本仓库忽略的 `.local/installer-tests` 下创建临时目标，覆盖只读检查、初次/重复安装、冲突拒绝及原有规则保留。仓库检查覆盖 Python 语法、受限 YAML 元数据结构、Markdown 相对链接和基础敏感内容检查；不能代替完整秘密扫描或硬件验证。
