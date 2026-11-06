# 03 · 刷入、检查 root，出问题怎么恢复

🔴 **从这里开始会真的改设备。** 先把本章通读一遍，确认能找到自己的原件和恢复方案，再逐条执行。写错文件、分区或槽位，都可能无法开机；不要一口气粘贴整串命令。

> 所有写入/恢复命令都会改变设备。这里只记录人工操作模板，不会自动执行。`w_force` 绕过名称/长度保护，错误分区或错误文件可能致砖。必须由操作者逐项确认输入、槽位、长度、哈希与下载模式。

## 1. 真正刷入前，逐项打勾 🔴

- [ ] 本机型号、fingerprint、active A 与本案条件吻合；下载器打印 slot a，misc CRC 已验证。
- [ ] 全 80 目标原件与 SHA256 已保存第二份；userdata 有独立备份（`r all` 不含它）。
- [ ] 原厂 init_boot_a 8 MiB、完整 TrustOS 6 MiB、signed TrustOS 前缀全部核对。
- [ ] 离线新 ramdisk 能解压、恢复模拟正确、AVB 边界正确；主机只使用自己的公钥。
- [ ] TrustOS 如需派生，来自本机 SML/TrustOS，重复生成一致、差异审计通过；不写 SML。
- [ ] 能再次进入 `1782:4D00` 下载窗口；备份原件路径不指向 patched 文件。
- [ ] 知道只有 normal reboot root 在本案被验证，完整双分区回退未实际执行。

## 2. init_boot 的最小写入与回读 🔴

这段记录的是 init_boot 最小写入方式，**不是要求你故意重演本案的循环重启**。还没完成离线镜像审查就不要做。在交互会话连接并确认 slot a 后，**每条命令等完整完成回执和 FDL2 提示**：

```text
w_force init_boot_a D:\F50\derived\init_boot_a-patched.img
read_part init_boot_a 0 0x800000 D:\F50\readback\init_boot_a.raw
```

回读完整 8 MiB 与待写镜像 SHA256 相等才 `reset`。不要在未等回读校验时把 `reset` 放进自动命令串。

本案 init_boot-only 失败、循环重启。恢复时实际执行了原厂 init_boot_a 写回、8 MiB 回读，回读 SHA256 与原厂一致，并记录恢复正常启动。**先恢复、查明镜像与启动链，再考虑 TrustOS**；不要反复换社区镜像试错。

### 已实际执行的单分区恢复

```text
w_force init_boot_a D:\F50\backup-new\init_boot_a
read_part init_boot_a 0 0x800000 D:\F50\readback\init_boot_a.restored.raw
```

校验等于自己的原厂哈希，然后 `reset` 并确认正常固件启动。本案 stock SHA256 见证据页；不是其他设备的恢复标准。

## 3. 确实需要时，再评估本机 TrustOS 派生物 🔴

人工确认后仅写活动槽的两项：

```text
w_force init_boot_a D:\F50\derived\init_boot_a-patched.img
w_force trustos_a D:\F50\derived\tos-noavb-bsp-bypassed
```

等 `Force Write <partition> Done` 与 FDL2 返回。随后回读 init_boot 的 8 MiB，以及 TrustOS 的完整 6 MiB。以下仍为下载器交互命令，每条等完成回执与提示：

```text
read_part init_boot_a 0 0x800000 D:\F50\readback\init_boot_a.after.raw
read_part trustos_a 0 0x600000 D:\F50\readback\trustos_a.after.head
read_part trustos_a 0x200 0x5ffe00 D:\F50\readback\trustos_a.after.tail
```

回到电脑 PowerShell，用**本次派生物**检查刷后前缀，不能照抄第 1 章的原厂 `--signed` 输入：

```powershell
python tools/assemble_trustos.py `
  --head 'D:\F50\readback\trustos_a.after.head' --tail 'D:\F50\readback\trustos_a.after.tail' `
  --signed 'D:\F50\derived\tos-noavb-bsp-bypassed' `
  --output 'D:\F50\readback\trustos_a.after.raw'
```

`--signed` 参数名沿用工具接口，表示预期镜像前缀；这里不是声称派生物签名有效。输出文件必须是新的，工具拒绝覆盖。用本机待写镜像、预期完整 TrustOS 比较：

```powershell
python tools/compare_trustos.py --stock-raw 'D:\F50\raw\trustos_a.stock.raw' `
  --derived 'D:\F50\derived\tos-noavb-bsp-bypassed' `
  --readback 'D:\F50\readback\trustos_a.after.raw'
```

该工具只验证物理写入结果，不验证派生物是否可信。如果完全匹配才 `reset`；不匹配时保留日志、不要继续启动或扩大写入范围，应按已准备的原件恢复。

**本案顺序有两个阶段**：初版 root 镜像 + TrustOS 的物理回读先通过，但其后又仅更新 init_boot 至 v2，修正 ADB 启动时序。最终成功哈希来自 v2 回读与正常重启后的 live 校验，不能将早期 controller 的 init_boot 哈希当最终值。

## 4. 怎么确认 root 真的成功 🟢

下例为 PowerShell，替换为实际隔离网络中的设备地址；不要将私有地址写进公开报告：

```powershell
$Target = '<your-device-address>:5555'
adb connect $Target
adb -s $Target shell getprop sys.boot_completed
adb -s $Target shell getprop ro.build.display.id
adb -s $Target shell getprop ro.boot.slot_suffix
adb -s $Target shell
```

进入设备 shell 后逐行输入，确认 `id` 是 root 再继续；这部分不是 PowerShell 命令：

```sh
/debug_ramdisk/su
id
magisk -v
ls /data/adb/magisk
cat /cache/magisk.log
sha256sum /dev/block/by-name/init_boot_a /dev/block/by-name/trustos_a
exit
exit
```

要求 boot_completed=1、B28、`_a`、uid=0、Magisk 28103 的版本匹配，11 runtime 文件实际存在，日志显示环境初始化、post-fs-data/service.d 阶段而非 environment incomplete。日志含私人内容，仅本地审查。服务阶段日志不等于任何特定模块已被功能验证。

再做 **一次正常 `adb -s $Target reboot`**，等待启动与重连，重复上述项目，特别是 live 两个 block 分区的完整 SHA256 与写入预期一致。本案只声明这一范围，不声称已测断电、升级、eSIM 或所有无线业务。

### ADB 不通时

检查原厂启动、网络连接、正确目标地址和 USB 驱动；查看启动脚本时序与日志（若可恢复访问）。短暂 1782:4D00 是冷启动正常下载窗口的一部分，不能仅凭它断言 AVB 损坏。不要靠修改别的网卡、卸载 unrelated 驱动、擦 userdata 或无条件放开 adbd 认证解决。

## 5. 两个分区一起恢复：🔴 方案已准备，**没有执行验证**

以下是本案保存的恢复方案的脱敏分步版本，不是“已恢复测试通过”的承诺。成功后没有为了演练回退再次改动设备。controller 中有同类异常回滚分支，**仅代码存在也不证明分支已运行**。

先启动下载器等待，再冷 USB 重连；确认仍是本机 A 槽。使用原厂完整 raw TrustOS 和原厂 init_boot：

```text
w_force trustos_a D:\F50\raw\trustos_a.stock.raw
w_force init_boot_a D:\F50\backup-new\init_boot_a
read_part init_boot_a 0 0x800000 D:\F50\readback\init_boot_a.rollback.raw
read_part trustos_a 0 0x600000 D:\F50\readback\trustos_a.rollback.head
read_part trustos_a 0x200 0x5ffe00 D:\F50\readback\trustos_a.rollback.tail
```

每条等待回执/提示。恢复回读则使用**原厂 signed 前缀**来重组，回到电脑 PowerShell：

```powershell
python tools/assemble_trustos.py `
  --head 'D:\F50\readback\trustos_a.rollback.head' --tail 'D:\F50\readback\trustos_a.rollback.tail' `
  --signed 'D:\F50\backup-new\trustos_a' `
  --output 'D:\F50\readback\trustos_a.rollback.raw'
```

重组 6 MiB TrustOS 后校验 **两者均等于自己的原始物理备份**，然后才 `reset`，检查原厂正常启动。不能用裁剪的 5,047,960-byte signed TrustOS 冒充完整回滚文件；也不能拿派生物当原件。

此方案只回滚两个修改分区，**不清除 `/data/adb`、ADB 公钥或 persist 配置等用户数据区域留下的状态**，不宣称完整去 ROOT/恢复安全状态。需要彻底清理时另行审计并备份，不默认擦 userdata。

## 6. 遇到这些情况，先停 ⛔

下载模式不稳定、原件缺失、readback 不一致、slot/fingerprint 改变、分区表异常、TrustOS payload 有无法解释的变化：停止并求助有恢复经验的人。不要切 B 槽、刷旧版 tos、写 NV/IMEI、降级或重分区；anti-rollback 状态未知，本案未测试降级。
