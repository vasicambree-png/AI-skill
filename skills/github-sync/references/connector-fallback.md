# GitHub 连接替代上传

只在原生 Git 认证无法使用、且连接具有目标仓库写权限时读取。2026-09-29 的一次验证中，命令行 GCM 登录了其他账号，而连接身份为目标仓库所有者；私有仓库通过连接成功上传。随后通过 GCM browser 流程登录正确账号，配置 GitHub.com 专属默认用户名，并验证原生 fetch/ls-remote 成功。这是历史排查证据；每次仍需核对实时认证状态。

## 上传不变式

- 从 `ALL_TOOLS` 的完整 description 获取工具参数声明，不猜参数名。查找 github_get_profile/get_repo/fetch/create_blob/create_tree/create_commit/update_ref。
- 用 GitHub fetch 的 `/repos/{owner}/{repo}/git/ref/heads/{branch}` 读取父提交；必须与本地 HEAD 一致，否则先解决历史差异。
- `git rev-parse 'HEAD^{tree}'` 获取父树，`git write-tree` 获取暂存目标树。PowerShell 的花括号 Git 参数加引号。
- 用 `git ls-files --stage -z` 取得暂存条目的 mode/路径/blob SHA，用 `git cat-file blob <sha>` 读取原始字节，base64 上传，按 SHA 去重；不要上传随时可能变化的工作区副本。
- create_blob 返回 SHA 必须匹配本地；create_tree 基于父树，只加入任务条目，返回 SHA 必须匹配本地暂存树。UTF-8 小文本可直接在 tree 条目中提供 content，省去独立 blob 请求；仍必须核对目标树 SHA。
- 大数据只在工具编排中转，不打印 base64 或完整提交 diff；exec_command 曾在约 1 MiB 输出处截断。分块读取并核对长度，约 200000 ASCII 字符每块是曾验证可行的大小，并非工具永久上限。
- create_commit 指定父提交和已核对的树。用 fetch `/git/commits/{new_sha}` 获取 Git 元数据，不用返回完整大型 diff 的 fetch_commit。
- 先在本地写入并核验该提交对象；随后 update_ref 使用 force=false，再读取远程分支核对。最后用 `git update-ref <ref> <new_sha> <expected_old_sha>` 将本地分支与 remote-tracking ref 推进到同一提交。不得 reset 工作区；操作中本地或远程若发生变化，停止并重新核对。

## 原始提交对象

另行 git commit 会因作者、时间等不同得到另一 SHA。连接创建的提交需重建同一个 Git 对象才能避免本地与远程历史分叉。

原始字节顺序为 tree 行、全部 parent 行、author 行、committer 行、空行、message。身份行包含 name、email、Unix 秒和 ±HHMM 时区；签名、encoding 等附加头若存在也必须保留。

API 日期通常归一化为 UTC，并不保留原始时区。历史成功样例的 author/committer 均为 -0400，message 没有末尾换行；不能默认 +0000 或强行补换行。先尝试已知客户端偏移，再尝试常见偏移与末尾换行组合；只有 `SHA1(b"commit " + 字节长度ASCII + b"\0" + 原始内容)` 等于远程 SHA 时，才用 `git hash-object -t commit -w --stdin` 写入。

若存在无法重建的签名/头字段、SHA 不匹配或远程变化，不移动引用，不强推。保留源码与暂存内容，明确报告尚未完成的步骤。该路线不应通过读取或导出连接令牌来规避认证。
