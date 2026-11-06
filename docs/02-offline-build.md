# 02 · 制作 root 镜像：改哪里，怎么检查

🔴 **这章只是离线处理副本，但产物一旦刷入就可能让设备无法启动。** 不要动原件，也不要把“工具没有报错”当成镜像一定安全。

先说明白：这里还不是零基础照抄命令就能出包的教程。没有完整生成器，关键输入来源也有未闭环的地方；不会独立实现和审查，就先停在备份阶段。下面把每个结构约束写出来，供有经验的人检查。

下面的内容是根据这次实际构建脚本逐项核对的，方便你独立实现和检查。**本仓库不包含私有构建脚本的复制品，也不承诺一条命令生成可刷镜像**：原实现绑定具体备份、主机公钥、Magisk APK、LZ4 与槽位，直接公布会误导他人刷入不匹配镜像。没有完成本章所有结构/恢复验证，应停留在案例研究，不进入写入阶段。

## 先按这张表逐段核对

所有操作都只在副本上做；本章不连接设备、不刷写。每一段的详细条件在下面对应小节。

| 顺序 | 你要做的事 | 做对了应该看到什么 | 风险 / 停下的条件 |
| --- | --- | --- | --- |
| 1 | 固定原厂输入和 Magisk 输入 | 原件只读、版本/长度/哈希有记录 | 🔴 来源不明、输入不全就停；不换随机 APK 试 |
| 2 | 解包 header、LZ4 和 cpio | 边界正确、两种解码结果相同、元数据保留 | 🔴 解包不一致或重复条目冲突就停 |
| 3 | 放入同一 APK 的 Magisk 文件和恢复元数据 | 11 文件齐全；恢复模拟与原件逐项一致 | 🔴 缺文件、版本混用或无法还原就停 |
| 4 | 审查启动时序和自己的公钥 | 无私钥、无陌生 UID 授权，等待有上限 | 🔴 持久 root/网络 ADB 扩大攻击面；未验证认证不能宣称安全 |
| 5 | 重打包 AVB 布局 | 总长不变，区间/解压回环都对 | 🔴 布局保留不等于签名有效；越界就停 |
| 6 | 仅在有理由时派生本机 TrustOS | 重复生成一致，payload 差异全部可解释 | 🔴 不明变化、原件缺失就停；不刷 helper SML |

完成这些只是获得可供进一步审查的本地产物，不是“刷入必成功”的保证。

## 1. 输入与版本门槛

在离线工作目录复制本机原厂 `init_boot_a`、`sml_a`、`trustos_a`；只读保留原件。额外保存上一章重建的完整 6 MiB TrustOS。需要 Python 3、原生 LZ4 CLI、可信 spd_dump；本案未记录 Python/LZ4 精确版本，所以再现构建应自行固定并记录版本。

本案唯一实际成功的 Magisk 参考 APK：

```text
versionCode: 28103
runtime: 1e3edb88:MAGISK:R
SHA256: fa7e64af14e57194e2463d959e809812e9bdd48f4cc996565706f658e78694de
```

哈希是**成功输入指纹，不是安全/来源背书**。原参考 APK 的确切下载 URL/签名来源未在保留材料中闭环；本仓库不重分发、不提供不明镜像下载链接。若无法自行从可信来源取得并确认这个输入，**精确再现被此条件阻塞**。不要假定任意 28.x、最新版本或其他 fork 等价。官方项目见来源页，需遵循其许可。

## 2. 解析 init_boot：硬断言

本案原件：8 MiB、前 8 字节 `ANDROID!`、header v4（LE uint32 @40=4）、无 GKI 签名（LE uint32 @1580=0）。页大小 4096，ramdisk 大小 LE uint32 @12，数据范围 `[4096, 4096+size)`，必须精确截取，不包含对齐填充。

ramdisk 是 legacy LZ4（magic `02 21 4c 18`），解开是 newc cpio（`070701`）。原实现同时用原生 `lz4 -d -c` 和独立 legacy 解码器比较字节完全一致；重新压缩用 `lz4 -l -9 -c`，再解压逐字节比较。

cpio 处理要求：

- 保留每个原厂条目的内容与全部 newc 元数据（mode/uid/gid/链接数/设备号等），按 4 字节对齐，尾部 TRAILER 和 512 字节填充。
- 原厂存在重复 `dev` 条目。**只有内容与元数据都相同才能去重**；不同条目不可静默以后者覆盖。原私有脚本用了字典归并，本公开规范增加这一拒绝条件，不能机械复制。
- 确认未被 Magisk 修改，无 `.backup/.magisk`；本案原 init 长度 3,507,424 bytes。
- 建立明确修改清单、唯一 inode 分配；保留原 init 的原始属性用于恢复。不要抽取 cpio 到宿主根目录或运行其内容。

## 3. Magisk 内容映射

APK `lib/arm64-v8a/libmagiskinit.so` 是本案 197,256-byte magiskinit，替换 `init`（mode 0100750）。其他原厂文件不改。

添加：

| cpio 路径 | 内容与约束 |
| --- | --- |
| `overlay.d` / `overlay.d/sbin` | 目录 mode 040750 |
| `overlay.d/sbin/magisk.xz` | APK `libmagisk.so`，XZ / CRC32 / preset 9 |
| `overlay.d/sbin/stub.xz` | APK `assets/stub.apk`，同样 XZ |
| `overlay.d/sbin/init-ld.xz` | APK `libinit-ld.so`，同样 XZ |
| `overlay.d/sbin/f50-env.tar` | 下述 11 文件，root:root USTAR；无宿主路径/时间/身份 |
| `overlay.d/sbin/start_adbip.sh` | 自行审计的启动逻辑；只嵌本人的公钥，不能分发构建产物 |
| `overlay.d/adbip.rc` | late_start root/init oneshot 服务，boot_completed 触发 |
| `.backup/init.xz` | 原 init 的 XZ，保留原 init 元数据（调整压缩后 size） |
| `.backup/.rmlist` | 本次新增路径列表，NUL 分隔及结尾；在加入 .backup 元数据之前计算 |
| `.backup/.magisk` | 下述配置，原厂整张 init_boot SHA1，不是 patched SHA1 |

```text
KEEPVERITY=true
KEEPFORCEENCRYPT=true
RECOVERYMODE=false
SHA1=<SHA1 of your entire original init_boot image>
```

恢复模拟必须：解压 `.backup/init.xz` 恢复 init、去掉新增项与备份项后，原厂每个条目的内容及元数据与去重原件一致。只验证文件个数不够。

### 11 文件运行环境

从**同一 APK**提取到 tar，启动时安装至 `/data/adb/magisk`：

```text
libmagisk.so       -> magisk, magisk32, magisk64  (本案三者同内容)
libmagiskinit.so   -> magiskinit
libmagiskboot.so   -> magiskboot
libmagiskpolicy.so -> magiskpolicy
libbusybox.so      -> busybox
libinit-ld.so      -> init-ld
assets/boot_patch.sh     -> boot_patch.sh
assets/util_functions.sh -> util_functions.sh
assets/stub.apk          -> stub.apk
```

tar root:root；非 APK mode 0755，stub.apk 0644。文件数 11。原启动代码随后对目录所有项 chmod 0755；不要因此把“可执行位正确”误认为已验证脚本生效。缺失环境会出现 `Magisk environment incomplete, abort`，导致模块/boot scripts 不执行，即使 su 已可用。

## 4. 无屏设备启动和授权的准确时序

本案成功 v2 采用：

```text
service f50_root_setup ${MAGISKTMP}/start_adbip.sh
    class late_start
    user root
    group root shell system
    oneshot
    seclabel u:r:init:s0

on property:sys.boot_completed=1
    start f50_root_setup
```

脚本逻辑（需自行实现、审计；此处不是可执行脚本）：

1. `M` 取脚本所在目录，找不到可执行 magisk 时回退 `/debug_ramdisk`；日志在 `/data/local/tmp/f50-root-startup.log`。
2. toybox tar 安装完整 runtime；创建 `/data/misc/adb`。把**自己的** `adbkey.pub` 单行内容按 shell 安全引用追加到 adb_keys（去重），设 `system:shell` / 0640 / restorecon。不要把 `adbkey` 私钥放进镜像、日志或仓库。
3. `settings put global adb_enabled 1`。等待 `sys.boot_completed=1`，上限 45 次 × 2 秒，避免 USB/framework 初始化覆盖早期开启状态。
4. 设置 `persist.adb.tcp.port` 与 `service.adb.tcp.port` 为 5555，stop/start adbd。
5. 最多 30 次，每隔 3 秒短暂重试 start adbd；root 服务中使用同 APK 的 busybox `timeout -s KILL 6` 包裹 `magisk --sqlite`。因无 UI 授权，使用如下策略：

```sql
INSERT OR REPLACE INTO settings(key,value) VALUES('root_access',3);
INSERT OR REPLACE INTO policies(uid,policy,until,logging,notification)
VALUES(2000,2,0,1,1);
```

这是**长期允许 shell UID 2000 提权**的安全取舍，不是通用安全默认值。不要对其他应用 UID 无条件授权，也不要用放开 adb 认证来“修复”连接。

## 5. 重打包 AVB 布局

原厂最后 64 字节必须为 AVB footer（`AVBf`）；`>IIQQQ` 读取 footer @4 的 major/minor/original_image_size/vbmeta_offset/vbmeta_size（大端）。本案 major=1，原 vbmeta 开头 `AVB0`，后方至 footer 的空间全零。

离线算法：

1. `new_end = align_up(4096 + compressed_ramdisk_size, 4096)`。
2. 分配**与原件同大小**的零初始化镜像；复制原 header，只更新 @12 ramdisk_size；写入新 ramdisk。
3. 原 vbmeta **全部原样复制**到 new_end，不重新签名、不丢弃。
4. 复制原 footer，在 @12 按 `>QQQ` 改为 `(new_end, new_end, vbmeta_size)`，再放到镜像尾部。
5. 强制 `new_end + vbmeta_size < partition_size - 64`；所有区间、对齐、magic、footer 及解压回环核对。

**保留 AVB 布局不等于新 ramdisk 的签名有效**。本案还需处理本机 TrustOS；不能声称如此打包即可绕过所有设备验证。

最终 v2：cpio 6,993,920 bytes；压缩 ramdisk 4,886,305；vbmeta offset 4,890,624；vbmeta size 2,304。含主机公钥的产物哈希只对本案成立，换公钥理应改变哈希。

## 6. TrustOS：只从本机镜像离线派生

仅在原厂可恢复、init_boot-only 测试失败并已恢复的前提下评估；USB 行为不能单独确诊 TEE 原因。不要下载旧版 `tos.bin`，不要刷 helper SML。

用本案工具离线模式（`-t`），输入为副本；核对自己的二进制确实支持该模式，勿将在线命令混入：

```powershell
& 'D:\F50\tools\spd_dump.exe' -t path 'D:\F50\tos-offline' `
  dis_avb_ex 'D:\F50\offline-input\sml_a' 'D:\F50\offline-input\trustos_a' exit
```

实际输出在工具建立的时间戳子目录中，名为 **`tos-noavb-bsp-bypassed`**；输入副本没变不代表没生成。原件 signed TrustOS 5,047,960 bytes，派生物 5,195,528；本案两次独立生成 SHA256 相同。

本案内容审计：原始 signed 前缀对比派生物，共同长度内仅允许 DHTB 前 512 字节、指令 @`0x9876c..0x98770`（`e0031a2a` → `00008052`），以及原 signed 尾部 2048 字节的签名/包装区变化；另需单独审计新增长度对应包装。**这些偏移仅为本案证据，不可硬编码去修改别的 TrustOS。** 重复生成一致不等于安全性证明；出现任何不能解释的 payload 变化就停止。

准备预期物理读回内容：`derived_tos + original_full_raw[len(derived_tos):]`。写入较短派生物后，物理尾部应保持原值；不能只比较裁剪输出。校验工具可离线构造预期值，但不做安全审计。
