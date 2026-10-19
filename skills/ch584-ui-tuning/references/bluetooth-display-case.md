# 蓝牙显示案例：元数据、20 通道布局与真实绘图预览

复核日期：2026-10-02，America/New_York。来源为 `D:\蓝牙模块优化`，Git 版本 [ttk cc8fcc9](https://github.com/vasicambree-png/ttk/commit/cc8fcc9c816c1420d58529aee4b864b09794ec9c)。本轮没有修改固件；具体坐标、字号、枚举、协议与路径仅属于该快照。

## 当前实现与证据入口

| 需要判断的事项 | 本轮源码证据 | 可复用结论 |
| --- | --- | --- |
| 实际参与构建的 UI | `CH584_V1_0_1/obj/APP/subdir.mk`；`APP/yuying_TFT.c` | 从源集合确认目标，不拿 `.mrs`、桌面宿主副本或备份替代正式源码 |
| 活动菜单与旧函数 | `Main_List`、`Menu_List` 挂载 `binding_Control` 和 `summary_Control`；旧 `calibration_Control`、`zero_setting_Control` 仍保留 | 函数存在不表示菜单可达；修改前确认回调表与分支 |
| 普通文字的真正入口 | `ui_text_glyph`、`ui_text_width`、`ui_text_draw`，约 188–251 行；`APP/include/ui_menu_assets.h` | 普通文字使用自定义 11/14/16/18 字模，`SetFont(UI_FONT_CN)` 不决定这些文字的字形；当前多字号表共享查找上界 |
| 绑定后尚未收到遥测 | `ui_home_channel_type`，约 143–180 行；首页约 735–753 行 | 类型优先取绑定范围，缓存类型兜底；类型/单位先出现，数值仅在 `valid && data_re_flag` 时格式化，否则为 `--` |
| 混合通道设备 | `ui_home_channel_type` 的激光四通道分支；`observer.c` 的 `fill_channel_data` | 当前四通道激光设备的首路为激光，其余三路为倾角；不能按设备级类型统一显示 |
| 标度与负数 | `ch_disp_scale10`、`ch_disp_format`，约 123–139 行 | 当前倾角先按 `int16_t` 解释再在 `int32_t` 中取幅值；需缩放的类型保留一位小数，激光原值显示；只格式化，不改原值 |
| 当前展示集合 | 首页约 671–733 行；`PARAM_*`、`summary_name_page`、`install_ch_page`，约 1004–1055、1397–1417 行 | 首页两页各 10 通道；名称/RSSI/电压页分别一屏 20 通道，两列各 10 行，不再用旧 `chu_num2` 选子集 |
| 长名称与临时状态 | `ui_draw_name_size` 约 286–311 行；`ui_text_draw` 保存并恢复位图透明模式 | 用本地副本、实际字模宽度与解码后的字符边界控制显示；需要核对异常 UTF-8 的独立处理 |
| 原图字标处理 | `tools/generate_home_assets.py` 的 `wordmark_components`，约 110–135 行；`generate_menu_assets.py` 的 `glyph` 和 `source_characters` | 斜体 w/i 横向重叠时按连通笔画分离并保留 i 点；正文公共基线、下划线与源码字面量覆盖另行处理 |
| 完整重绘与提示覆盖 | `UI_Control` 约 430–481 行 | 当前先 `ClearBuffer`，提示页优先发送并返回；普通页面字段仍在解析层更新。不要照搬初锚力案例的局部缓存/XOR 策略 |
| 请求与绘制分离 | `Usart3_task.c` 的 `app_uart_process`、`START_IO_EVT`、`START_DATA_EVT`，约 402、460–507 行 | 请求合并为置位；本地周期更新与 UART 输入共同请求重画，按最小间隔及息屏/页面新鲜度门控消费；不把注释估算当实测 |

名称列表可在值未收到前显示已有名称；RSSI/电压的等待值仍根据接收标志判断。零 RSSI、零电压、零测量值都是测试中合法的显示输入，不能以零代替未接收状态。信号显示使用当前代码的 `int8_t` 解释，电压的 `/10` 与首页主控电池的 `/100` 不是同一标度。

当前首页使用 18px 正文、22px 行距；20 通道参数页使用 11px 正文、12px 行距。它们是本工程的空间权衡，不是其他显示器的默认参数。自动边界通过不能代替实屏确认小字可读性。

`ui_main_meta_code` 当前只处理 1/2/3 字节序列，名称的初次容量限制仍按字节复制；任意外部名称不在源码字面量扫描的保证范围内。本轮没有验证四字节字符、残缺编码或恰好落在多字节字符中间的容量边界，不能宣称支持任意 Unicode 名称。应按实际允许字符核对回退和解码边界，不扩大协议字符集。

## 当前预览能证明什么

入口为 `tools/ui_preview/run_preview.py`，配套 `prepare_host.py`、`build_host.cmd`、`host_render.c`、`check_unified_text.py`、`check_param_pages.py`。运行前检查输出目录和构建依赖；具体预览工具保留在项目，不复制到全局 skill。

- `home`：首页改动及保留页面比较；`menus`：菜单改动及保留首页/提示页比较；`unified`：允许多页字体变化，用内容、边界与状态不变量检查。只有运行 before/after 才有前后逐像素比较，本轮仅运行 after。
- 使用完整 UI 翻译单元、当前字模、工程的解码和绘图算法；GPIO/SPI/延时为空端点，像素接到本地数组。未使用的 GNU 空数组仅在宿主副本中调整，不改正式固件。
- 用例包含等待/零值/部分接收、类型/单位、极值、全部合法焦点、反白文字、长名称、轮显、旧页码及交替页面。比较绘图前后输入与缓存、连续刷新与独立重绘、位图模式恢复，并检查实际文字墨迹与单元格内碰撞。
- 故意越界的反白字符用于验证检查器；该探针通过只表示本轮探针可检出，不保证覆盖所有越界情况。
- 直接给绘图函数设置解析后的页面状态，不执行真实 UART 帧解析、BLE 回调、Flash、TMOS 时序或物理按键。

本轮实际命令（仅适用于该项目已有工具）：

```powershell
Set-Location -LiteralPath 'D:\蓝牙模块优化'
python -B tools/ui_preview/run_preview.py --scope unified --output output/skill_review_20261002 --phase after
```

实际返回 0：309 个绘图用例；缺字、越界、输入改写、连续/独立重绘差异、位图模式变化、首页契约违规及反白探针失败均为 0。文字/布局检查 24027 项、参数页检查 52501 项，均 0 失败。宿主 MSVC 编译有 36 条 C4828 注释编码警告，0 错误；不是无警告构建。

另对实际生成头文件静态核对：11/14/16/18px 四张表各 234 个码点，集合相同、严格有序且包含 `?` 回退，当前满足共享二分查找上界。未执行字体重新生成及产物一致性比较。

输出留在项目忽略目录 `tools/ui_preview/output/skill_review_20261002/`，本轮主要追溯项：

| 文件 | SHA256 |
| --- | --- |
| `APP/yuying_TFT.c` | `845e010b9b69b7ccf51f7fd79954df48cae3d999f34b41a5f18e98f815942260` |
| `APP/include/ui_home_assets.h` | `6f35eb0f860e651af278a39600a097ce64cd0f59a770af30f1d88a703a17ceb4` |
| `APP/include/ui_menu_assets.h` | `a35bf392fc93c41585dd0573ab78a790eba09b37f544afe22f9e4d341c2c71c1` |

哈希清单不覆盖全部编译依赖，不能称为完整可重现基线。本轮没有修改前后比较；新输出目录中的同源快照不能冒充修改前固件。

## 本轮发现的过时信息与边界

1. 预览 README 仍有“三级页面恢复两页”及“两页不同”的旧说明。当前 C 实现与 `check_param_pages.py` 均检查 20 通道同屏、`chu_num2=0/1/2/65535` 内容等价。以当前代码定位行为，并用相关检查核对；不要把旧说明当作新任务需求。本次只维护 skill，未修项目 README。
2. `prepare_host.py` 在首次运行时保存 UI C，但首页/菜单资源只在首次 before 时冻结，其他头文件、字体与算法仍使用当前工程。先 after、改资源、再 before 可能混入新资源；`--baseline-sha256` 只约束单个 C 快照。需前后比较时，在改动前冻结全部相关输入并核对清单。
3. `Usart3_task.c` 约 595–608 行中，`if (ui_msg_tick_sec() != 0U)` 后紧接绑定模式条件，另一个独立块无条件置 `dis_flag_cnt=1`。静态能确认这一控制流，与注释描述的条件请求不一致；它是否造成实机额外负担尚未验证。不能从离线绘图通过推断调度正确，也不要将此异常作为推荐模式。本轮未修改该代码。
4. 本轮没有执行 WCH 固件构建、烧录、UART/BLE 联机、调度性能测量或实屏观察；这些均尚未验证。未取得用户对本轮实屏字号/布局的认可，不记录为已经认可的效果。
