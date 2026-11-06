# 04 · 脱敏证据与上游来源

## 证据取得方式与限制

2026-11-06 对操作者 Windows 工作目录做**只读文件审计**：读取目录、源码、manifest、回执和 ROOT 结果；未重新运行私有 controller、未连接设备执行命令、未进行任何刷写。下面区分历史执行记录与本仓库现做测试；公开仓库不收录原始日志、备份、主机路径或标识。公开源码只含新编写的本地文件检查工具。

| 本地来源（仅 basename） | 得出的结论 |
| --- | --- |
| `inspect_stock.py` / `verify_backup.py` / `backup-validation.json` | v4/LZ4/newc、build fingerprint、活动 A、80 目标/总字节、NV alias 特例 |
| `build_root_v2.py` / `build-manifest.json` | 原件校验、同 APK 11 runtime 文件、备份元数据、AVB footer 重定位、v2 ADB 时序 |
| `root2_controller.py` / `status.json` / `root2-controller.log` | 头尾分读完整 TrustOS、misc CRC、两分区写入与完整回读、早期镜像哈希 |
| `flash-v2-job.json` / 对应 `stderr.log` 与回读文件 | 后续只更新 init_boot v2，写入与 8 MiB 回读匹配 |
| `restore-job.json` / 对应回执与回读文件 | 原厂 init_boot 单项恢复实际执行，回读哈希正确 |
| `finalize_root.py` / `ROOT-RESULT.md` | 正常重启后 root/Magisk/live 分区检查；最终双分区恢复命令标明 NOT executed |

源码中的断言代表设计约束；只有回执/产物/结果相互对应的项目才列为已执行。原厂恢复后正常启动依据历史结果记录，未在这次文档审计中重新验证。

## 哈希台账（仅本案，不是他人设备的输入白名单）

```text
Original init_boot_a, 8,388,608 bytes:
a32b61061e9a7a6ebf71ee7b2adfacf8c5c0110bc984f59953f4cf9ae967c05e
Original signed/trimmed trustos_a, 5,047,960 bytes:
0056c5937cf0f6abc95cef013b40b2e4584e4f7ab68492a0d8c0d725c97e8318
Original physical trustos_a, 6,291,456 bytes:
c1951a200982b47a0d88049d6897242ba06fbecb93d732073ecb39200d74245f
Locally derived TrustOS, 5,195,528 bytes (two runs agree):
f82f788023e950e083760df1712718f454b59ed394bccca613d72dce5a939ab2
Final init_boot_a v2, after normal reboot:
f015c2bb452fd1a92088059ce134e42e423c3677d10e75164d6743db665d5c68
Final full physical trustos_a, after normal reboot:
be2dd99476cc26ddb72de5823c219cf16ee50d846c1986977ee9dd6f66a451c3
Magisk reference APK, 11,475,322 bytes:
fa7e64af14e57194e2463d959e809812e9bdd48f4cc996565706f658e78694de
spd_dump.exe, 14,418,944 bytes:
69f883fab422ce9f4cd4c8de7f99f78492cf59ce7585cb147458e59fb060dc08
```

历史 root2 初阶段 init_boot 回读哈希为 `15562623298618ac511e28f33eff8c3fe71c8d952927a0e8858bcaf57fdbf88d`，**不是最终 v2**。后续 v2 回读与 `ROOT-RESULT.md` 的 live 哈希一致。已将这个时间顺序写清，避免把 controller 旧记录误作最终成功证据。

最终 root 输出（无设备标识）：

```text
uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
1e3edb88:MAGISK:R (28103)
ro.boot.slot_suffix = _a
```

## 上游与归属

- [againrivers/zte-f50pro-b28-root — Root 全流程](https://github.com/againrivers/zte-f50pro-b28-root/blob/main/docs/01-root.md)：2026-11-06 获取到的页面介绍 v4 ramdisk、完整 Magisk 环境与 TrustOS 条件分支。它的实例用 **B 槽**、某台机器 init_boot-only 能成功；**本案是 A 槽且需要本机派生 TrustOS**。其 USB 症状归因不能替代实际诊断。本文为独立总结，未复制整份指南。
- [相关 issue #1](https://github.com/againrivers/zte-f50pro-b28-root/issues/1)：上游文档链接的另一种启动失败讨论，不能当作本案实测。
- [TomKing062/spreadtrum_flash](https://github.com/TomKing062/spreadtrum_flash)：spd_dump 源码与命令语义；当前源码可能不同于本案工具版本，使用前审计差异。
- [Windows nightly 构建入口](https://nightly.link/TomKing062/action_spd_dump_it/workflows/build/main)：来自本地下载器 README 的可变链接，不是锁定产物或供应链保证。
- [原始 ilyakurdyukov/spreadtrum_flash](https://github.com/ilyakurdyukov/spreadtrum_flash)：原项目来源。
- [Magisk 官方项目](https://github.com/topjohnwu/Magisk)：架构、源码与许可；不保证当前发行版与上述参考 APK 相同。
- [LZ4 官方项目](https://github.com/lz4/lz4)、[Zadig 官方站](https://zadig.akeo.ie/)：自行核对发行、签名、版本和许可。

不重新分发上游或设备二进制，也不因提供链接声称上游对本案背书。不得将本仓库作为破解 SIM 锁、修改 IMEI、访问第三方设备或绕过他人授权的指南。
