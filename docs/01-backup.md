# 01 · 先备份，别急着刷

这一章先不改分区：把原件、回执和哈希保存好，后面出问题才有机会恢复。🟢 读取本身不主动刷写，但备份含隐私；🟡 装驱动可能影响电脑识别设备。每节做完都核对结果，别跳着做。

## 1. 动手前先确认这些 🟢

- 确认 MU3356、Android 15、完整 build/fingerprint；本案只覆盖 README 中的构建。
- 本案工具为 Windows x64 spd_dump **ver:251**，自报源码 SHA1 `e49d4de1255895db9b6d75ad973f1f78e9b30e90`。保存你的工具版本、二进制 SHA256、上游来源。nightly 是可变地址，不能仅以文件名认定相同。
- 准备稳定 USB 数据线、供电、足够磁盘空间及第二份离线备份。关闭可能反复探测 AOA/USB 的软件（例如微信）。不要盲目卸载其他 USB 设备。
- 备份成功 ≠ 恢复已演练。写入前确认下载窗口可重入，明确读写分区与原件位置。
- 若无现成 ADB，可从备份 ramdisk 的属性文件识别构建，不要声称原厂隐藏页面开关一定能启用 ADB。

## 2. Windows 驱动：只改 `1782:4D00` 🟡

先观察硬件 ID，再使用 Zadig 官方签名安装程序将 **VID `1782` / PID `4D00` 的 Sprd Download 接口**绑定到 WinUSB。核对工具签名、发行来源。不存在这个接口时不要猜选其他项。

**不要替换 RNDIS/NCM、MTP、蓝牙、正常 ZTE 接口或整个复合 USB 设备的驱动。** 正常枚举的 `19D2:0621` / `19D2:0246` 不是下载窗口；短暂出现 `1782:4D00` 也不能单独证明 AVB 损坏。

先运行等待命令，再进行冷 USB 重连；本案使用 `--wait 240 --kickto 2`。不同电池/供电状态可能影响冷启动，不能把拔线一概等同完全断电。不要用未知短接点。

## 3. 读取分区表与全部目标分区 🟢

以下是 **PowerShell 示例**。自行准备新的空目录，路径使用短 ASCII 名称；示例路径不是实际设备数据：

```powershell
New-Item -ItemType Directory -Path 'D:\F50\backup-new'  # 已存在则停止，勿混入旧文件
& 'D:\F50\tools\spd_dump.exe' --wait 240 --kickto 2 --verbose 1 `
  path 'D:\F50\backup-new' `
  partition_list 'D:\F50\backup-new\partition_list.xml' r all reset
```

保存 stdout/stderr，不公开原日志。**`r all` 按本案工具语义排除 userdata / cache / blackbox**，不是逐字节整盘备份，也不是用户数据备份。不要误用 `all_lite`（会省略非活动槽）。userdata 另行进行受保护备份；本指南不包含擦除、解锁、降级或重分区操作。

本案：83 个表项排除 3 个，得到 **80 个目标，7,005,870,288 bytes**（按目标文件求和，不含 XML），全部生成 SHA256。这个数字仅用于对照本案，不是其他设备必须完全相等的判据。

必须核对：

1. 分区表中每个目标都有非空文件。
2. 每个目标有完整读取回执，`target == read > 0`。日志中其他探测读可能为 0，不能将它当成目标备份完成。
3. 本案 `nr_runtimenv1` 的回执打印为 `nr_runtimenv2`；只有独立文件、两次别名回执及 **35 MiB − 512 bytes** 长度全部符合时才允许这个特例。不能忽略其他缺回执。
4. NV 可能剥去 512 字节头，DHTB 可能按内容裁剪；不能用 XML 名义大小逐项硬判，也不能因长度变小就忽略完整性问题。
5. 记录本机 manifest（文件名、长度、SHA256），复制到第二介质并再次校验。不要以本仓库公开哈希替代本机基准。

附带工具可做其中的只读初筛：

```powershell
python tools/validate_backup.py 'D:\F50\backup-new' --log 'D:\F50\backup-new\stderr.log'
```

输出 manifest 到 stdout；如保存到文件，也放在私有备份目录。工具不证明备份可启动，不替代原始回执审查或用户数据备份。

## 4. 活动槽：三个结果要对得上 🟢

本案下载器打印 `Device is using slot a`。`misc` 偏移 2048 的 32 字节 boot-control 结构前 8 字节是 `_a\0\0BCAB`，前 28 字节 CRC32 与最后 4 字节 little-endian 值相等。Android 启动后 `ro.boot.slot_suffix` 为 `_a`。

原厂 `init_boot_b` 全零，不能用其作为“备用可启动槽”。**不要切槽，不要因为上游文档用 B 就刷 B。** 若你的槽不是 A，停止照抄本案命令并重新审计所有路径、镜像和恢复步骤。

## 5. 再单独保存 6 MiB 完整 TrustOS 🟢

本案 `r trustos_a` 导出 **5,047,960 bytes**，不是物理 **6,291,456 bytes**。原因：本工具在 offset=0 读取 DHTB 镜像会自动 `bsp_chsize` 裁剪；即使指定物理长度也可能裁剪。

在独立下载器交互会话中，使用以下读命令（仅适用于本案确认的 A 槽 / 6 MiB 分区）：

```text
read_part trustos_a 0 0x600000 D:\F50\raw\trustos_a.head
read_part trustos_a 0x200 0x5ffe00 D:\F50\raw\trustos_a.tail
```

**每条命令都等对应 `Read Part Done` 完整回执及其后的 `FDL2 >` 返回，再发下一条或读取输出文件。** 第一条文件只取实际前 512 bytes；第二条必须恰好 6,290,944 bytes。非零偏移读取避免自动裁剪。

```powershell
python tools/assemble_trustos.py `
  --head 'D:\F50\raw\trustos_a.head' --tail 'D:\F50\raw\trustos_a.tail' `
  --signed 'D:\F50\backup-new\trustos_a' `
  --output 'D:\F50\raw\trustos_a.stock.raw'
```

此离线工具只在头部 DHTB、长度和原始签名镜像前缀一致时生成新文件，不覆盖文件。保持 `stock.raw`、原 `trustos_a` 和原 `init_boot_a`，分别记哈希。**完整尾部不能靠补零“恢复”。** 其他分区大小不同则停止，本工具有意不支持泛化参数。

## 6. 备份自己收好，别公开 🟢

完整分区可能含 IMEI、校准、无线身份、账户及历史配置。不要提交备份、NV、misc、ADB key、设备截图或未经脱敏的日志。`.gitignore` 只是防误操作，不是保密措施。第二份备份应加密、离线，且不要与修改后的产物混放。
