---
name: github-sync
description: 在任意实际项目中将已验证的任务改动提交并同步到现有 GitHub 仓库，核对远程提交；处理 Windows Git Credential Manager 账号与 GitHub 连接不一致的问题。
---

# GitHub 同步

全局复用同步经验，不固定项目目录、仓库、main 分支或旧提交 SHA。用户的全局 AGENTS.md 已记录每次代码及配套文档修改完成后提交、推送的持续授权；当前任务的只分析、不提交等要求优先。其他使用者没有该授权时，不能仅因使用此 skill 就替其发布代码。

## 正常流程

1. 在用户实际项目中确认 Git 根目录、`git status --short --branch`、`git remote -v`、当前分支/upstream、暂存和未暂存改动。保留无关改动，按明确路径暂存任务文件；用户要求上传最新工作区时检查相应已有修改。
2. 完成与改动相关的验证并检查 `git diff --cached --check`。仅上传已有内容时不要把历史构建报告当成本轮验证。项目忽略规则、缓存类型和必要生成资源需现场确认。
3. fetch 目标远程，核对远程分支与 HEAD 的祖先关系。正常追加提交并推送；远程新增改动或历史分叉时先调查，不 force-push，不自行 reset/rebase。没有可靠目标、detached HEAD 或分支配置含糊时，先完成准备再询问具体目标。
4. 推送成功后，用 `git ls-remote <remote> refs/heads/<branch>` 核对远程 SHA 与 HEAD 一致，再检查状态。返回真实提交链接、分支、验证结果和未同步原因（若有）。

每条依赖命令只在上一条成功后执行。不要以退出码以外的“看起来正常”代替验证；无任务变化时不创建空提交。仅上传任务所在仓库，不把全局 Codex 配置自动上传到某个项目。

## Windows 账号排查

- 此用户期望 GitHub.com 登录账号为 `vasicambree-png`，但仍需现场核对 GitHub 连接身份。
- `git credential-manager github list` 查看已存账号，`git config --show-origin --get-all credential.helper` 查看凭据管理器；仅输出账号和配置来源，不调用会输出令牌的 credential fill/get。
- 私有仓库的 `Repository not found` 可能是账号/权限问题。检查目标 URL、已登录身份和仓库权限，不据此新建仓库或改 origin；同样错误不要重复盲试。
- 用户要求重新登录时，先查看当前 GCM 的 `github login --help`，优先正式浏览器登录并指定目标用户名。此机 GCM 2.7.3 已验证 `git credential-manager github login --username vasicambree-png --browser --force` 成功；device 流程曾持续不返回授权码，不要重复挂起同一方式。浏览器登录及授权由用户完成，不在聊天里请求密码/PAT。
- 用户授权设置统一登录账号时，在成功确认目标账号后配置 GitHub.com 专属 `credential.https://github.com.username`，不要影响其他 Git 服务或删除其他账号的凭据。
- `git config user.name/user.email` 是提交署名，不是登录凭据。仅在用户要求署名一致且真实姓名/邮箱已确认时修改；不要猜邮箱或擅自替换已有项目署名。
- 登录成功后在用户指定仓库执行一次 fetch 或 ls-remote，证明该账号确实能读仓库。写权限需要连接权限查询或后续授权任务的真实推送验证，不能从 fetch 成功推断。

## 仅在原生 Git 仍不可用时

已登录的 GitHub 连接可能仍可访问目标仓库。读取 [references/connector-fallback.md](references/connector-fallback.md)，用 Git Data 对象上传并保持本地/远程相同提交；不要把该复杂替代路线作为认证正常时的默认流程。

## 经验边界

记住的是排查顺序和已验证方法。每个项目的 remote、branch、SDK、构建命令、硬件引脚及电气行为都必须重新确认。同步不授权烧录、硬件操作、部署或账号范围之外的配置改动。最新提交可供网页版定位版本，但不能保证另一个聊天立即刷新索引。
