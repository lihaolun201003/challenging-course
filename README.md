# 挑战性课程 · 多参数空气质量监测系统

基于 **NUCLEO-F411RE (STM32F411RE)** + **2.8″ TFT LCD (ILI9341)** + **PMS5003ST** + **蓝牙模块**
的六参数空气质量监测终端，本地屏幕显示 + 手机端查看。

**小组成员**：李昊伦 / 杨皓 / 赵旭东　　**课程**：挑战性课程

---

## 目录导航

| 目录 | 里面是什么 | 什么时候来这儿 |
| --- | --- | --- |
| [01_报告](01_报告) | 开题报告、阶段性报告、PCB 迭代记录 | 交作业、答辩 |
| [02_固件工程/AIR](02_固件工程/AIR) | PlatformIO 固件工程（源码 / 测试 / 日志 / 备份 / 固件存档） | 编译、烧录、改代码 |
| [03_外设接口说明](03_外设接口说明) | 引脚分配表（LaTeX 源文件） | 接线、写报告 |
| [04_资料](04_资料) | NUCLEO-64 用户手册、ILI9341 屏资料 | 查芯片 / 屏规格 |
| [05_素材](05_素材) | APP 截图、实物照片、PCB 截图、演示视频 | 做 PPT |
| [00_整理记录](00_整理记录) | 本次整理的搬迁对照表与校验结果 | 想知道某个文件原来在哪 |

固件工程内部还有更细的专题文档：见 [02_固件工程/AIR/docs](02_固件工程/AIR/docs) 与
[02_固件工程/AIR/README.md](02_固件工程/AIR/README.md)（工程自己的 11 KB 技术说明，写得很详细）。

---

## 三十秒上手

默认环境是 `nucleo_f411re_uart6`（蓝牙走 USART6，不用改焊桥）：

```powershell
cd 02_固件工程\AIR
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -e nucleo_f411re_uart6
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -e nucleo_f411re_uart6 -t upload
```

当前可用环境（定义在 [platformio.ini](02_固件工程/AIR/platformio.ini)）：

| 环境 | 用途 | 蓝牙 |
| --- | --- | --- |
| `nucleo_f411re_uart6` | **默认**，蓝牙走 USART6 PA11/PA12 | Blinker JSON |
| `nucleo_f411re` | 旧接线，蓝牙走 USART2 PA2/PA3（需改 SB13/14/62/63 焊桥） | Blinker JSON |
| `nucleo_f411re_env` | 旧的 `$ENV,...#` 自定义协议 | 自定义协议 |
| `nucleo_f411re_debug` | 纯 ST-Link 调试，无蓝牙 | 关闭 |
| `native` / `native_env` | 在本机跑协议与解析单元测试 | — |

---

## 当前状态

- ✅ 固件可编译：Flash 48144 B（9.2%）、静态 RAM 8988 B（6.9%）
- ✅ 传感器、屏幕、开机动画、蓝牙四条链路都已有实机验证记录
- ✅ 默认固件存档 [air-blinker-uart6-20261010.bin](02_固件工程/AIR/firmware/air-blinker-uart6-20261010.bin) 与重新编译产物 **SHA-256 完全一致**

---

## ⚠️ 已知待修正事项

以下都是整理过程中发现的**内容问题**，本次**只整理、未修改任何文件内容**，留给你决定怎么处理。

### 1. 引脚分配表与当前固件不一致（建议优先处理）

[外设接口分配表.tex](03_外设接口说明/外设接口分配表.tex) 描述的是一套**已经不存在的接线**：

| 项目 | .tex 里写的 | 当前固件实际用的 |
| --- | --- | --- |
| 蓝牙串口 | USART2，PA2/PA3 | **USART6，PA11/PA12** |
| LCD DC | PC7 | **PB5 / D4** |
| LCD RESET | PB4 | **PA8 / D7** |
| LCD 背光 | PB3（GPIO 控制） | **3V3 常亮** |
| LCD MISO | PA6 | **不接** |
| PMS SET / RESET | PB10 / PB5 | **悬空，程序不发命令** |
| PMS TX | PA9（接了） | **PA9 留空未接** |

这份 .tex 也没有编译出 PDF。**答辩前建议按当前固件改一遍。**
（当前固件的权威引脚定义见 [src/main.cpp](02_固件工程/AIR/src/main.cpp) 开头，或工程 README 的接线章节。）

### 2. 阶段性报告 PPT 首页写错了

[02_阶段性报告.pptx](01_报告/02_阶段性报告.pptx) 首页标题写的是"**开题报告**"（复制粘贴残留），
型号写的是"**AMOLED**"——但开题报告和实物都是 TFT LCD / ILI9341。

### 3. VSCode 配置指向别人的电脑

[.vscode/c_cpp_properties.json](02_固件工程/AIR/.vscode/c_cpp_properties.json) 里的路径全是
`C:/Users/TiAmo/Desktop/AIR/AIR/...`（工程原始作者那台机器），所以**本机 VSCode 的代码跳转和补全是坏的**。
该文件本来就在 .gitignore 里，可以直接重新生成或删掉重开 VSCode。

### 4. 本机跑不了 native 单元测试

`pio test -e native` 需要 PATH 里有 `g++`，本机没有（PlatformIO 里也没有 native 工具链），
所以 14 项蓝牙协议测试 + 6 项解析测试目前**无法在本机复跑**。装个 MinGW-w64 即可恢复。

### 5. 两份固件是重复的

`firmware/air-debug-env-20261010.*` 与 `firmware/air-debug-20261010.*` **字节完全相同**（同 SHA-256），
细节见 [firmware/MANIFEST.md](02_固件工程/AIR/firmware/MANIFEST.md)。
