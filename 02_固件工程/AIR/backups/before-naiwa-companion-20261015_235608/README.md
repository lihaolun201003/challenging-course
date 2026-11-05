# 烧录前备份

- before_flash_full.bin：本次修改前设备完整512KiB Flash。
- source_before.zip：本次修改前现有项目源代码、头文件、库、脚本、测试和配置。
- SHA-256见backup_verification.json；该Flash中的应用与修改前构建BIN一致。

需要回退时，可在本目录用ST-Link/OpenOCD执行：

```powershell
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "program before_flash_full.bin 0x08000000 verify reset exit"
```

回退源码应先保留后续改动，再将source_before.zip解到工程。新加入的naiwa_ui文件不在旧源码包内，如不再使用应同时移出编译源目录。
