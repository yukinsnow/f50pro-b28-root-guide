# F50 Pro B28 ROOT：单机验证案例与可审计操作指南

> **高风险：可能无法开机、丢失无线校准或个人数据，降低启动链安全性，影响 OTA 与保修。没有本机原始备份、完整 TrustOS 原始分区与可用下载模式恢复路径，不要写入任何分区。**
>
> 这不是通用一键 ROOT，也不提供别人设备的刷机包。本仓库是 **MU3356 / Android 15 / 特定 B28 构建的一次成功案例**，含详细离线重建约束、备份校验和恢复说明。相同营销型号、甚至相同 B28 标签，也不能保证兼容。

## 已验证的边界

| 项目 | 本次证据 |
| --- | --- |
| 设备 / 构建 | ZTE F50 Pro **MU3356**；`F50ProV1.0.0B28`；`20260818.180242` |
| 原厂指纹 | `ZTE/MU3356/MU3356:15/AP3A.240905.015.A2/20260818.180242:user/release-keys` |
| 活动槽 | **A / `_a`**，由下载器、misc CRC 与 Android 属性交叉核对；本机 `init_boot_b` 为空，不可照搬上游 B 槽命令 |
| 最终改动 | 仅 `init_boot_a` + **本机原始镜像派生的** `trustos_a` |
| ROOT | `/debug_ramdisk/su -c id` 返回 `uid=0(root)`；Magisk `1e3edb88:MAGISK:R` / **28103** |
| 重启验证 | 一次正常重启后，重新连接 ADB、验证 root、读取 live 分区 SHA256；观察到 Magisk post-fs-data / service.d 阶段 |
| 未改动 | B 槽、基带、校准、IMEI、userdata、分区表；不等于已逐项测试所有业务 |
| 未验证 | 长期稳定性、OTA、恢复出厂设置、断电恢复、所有无线功能、eSIM/OMAPI/配置下载与切换 |

**先只改 init_boot 的尝试出现循环重启，已恢复原厂 init_boot 并核对回读后才继续。** 最终还修正了 ADB 启动时序。不能将“闪存写入完成”或“网页能打开”当成 ROOT 成功。

## 阅读顺序

1. [前置条件、驱动与完整备份](docs/01-backup.md)
2. [离线构建规范：ramdisk / Magisk / TrustOS](docs/02-offline-build.md)
3. [人工写入、验证与分层恢复](docs/03-flash-verify-rollback.md)
4. [证据摘要、版本差异与上游来源](docs/04-evidence-and-sources.md)
5. [离线校验工具与测试](tools/README.md)

## 明确不包含

- 不分发固件、Magisk APK、TrustOS、下载器或驱动二进制；需自行从可信上游取得并核对许可、来源和哈希。
- 不发布分区备份、设备标识、网络地址、ADB 公私钥、账户或原始日志。原始备份含校准、身份与其他敏感内容，必须私下保管。
- 不提供自动刷写工具；附带 Python 仅处理本地文件，不调用 ADB、USB 或网络。
- 不把一台成功当作所有 F50 Pro 可用；不同槽位、镜像、Magisk 版本或下载器行为需重新审计。

## 安全取舍

本案使用启动链校验绕过、TCP ADB 与 shell UID 的持久 root 授权。这会扩大受攻击面；**ADB 5555 不得暴露公网或不可信网络**。只登记自己的 ADB 公钥，不复制私钥；不能因为预置了公钥就假定原厂 adbd 一定开启认证。应实际测试未授权主机被拒绝，并限制访问网络；该负向认证测试不在本案已验证范围内。

eSIM 为独立实验方向，**ROOT 不等于 OMAPI/eUICC 可用**。实验模块：[f50pro-esim-manager](https://github.com/yukinsnow/f50pro-esim-manager)（预发布 `v0.2.0-alpha.1`；README 与 GUI 明确标注实验性，尚缺实机功能验证，不代表 eSIM 已验证）。
