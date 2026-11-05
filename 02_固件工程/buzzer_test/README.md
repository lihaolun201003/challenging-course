# 蜂鸣器独立测试

开发板：NUCLEO-F411RE。控制脚：D6 / PB10。适用于高电平触发的三针蜂鸣器模块。

- I/O → D6 / PB10（CN9 第 7 脚）；开发板输出 3.3V 逻辑，高电平响、低电平停
- GND → 开发板 GND
- VCC → 开发板 5V（用户已确认当前模块采用此接法，独立测试已实测能响）

程序循环输出高电平 500 ms、低电平 1500 ms。串口 COM3 / 115200 输出 BUZZER ON / BUZZER OFF。测试程序只驱动蜂鸣器，不运行 AIR 的屏幕、传感器或蓝牙业务。

## 烧录测试程序

在 PowerShell 运行：

~~~powershell
& ".\flash_test.ps1"
~~~

脚本使用此次任务安装的 PlatformIO 工具链。首次烧录前读取板上完整 512 KiB Flash；已有备份不会覆盖。

## 恢复测试前的板上程序

~~~powershell
& ".\flash_test.ps1" -Restore
~~~

恢复使用 backup/before-buzzer-flash.bin，从 0x08000000 写回并校验，随后复位运行。

独立测试阶段未修改 AIR 工程的源码和配置。本目录是独立测试工程；正式 AIR 的阈值报警规则见 [甲醛蜂鸣器报警说明](../AIR/docs/HCHO-buzzer.md)。
