# 05 · root 后安装 UFI-TOOLS 高级后台

先说清楚：**装高级后台不需要再刷 init_boot 或 TrustOS。** 下面分两件事：先让网页正常工作，再按需接通 Root 功能。已经装好的人不要重复覆盖或清空配置。

本次用的是 **UFI-TOOLS 4.0.0 Full APK**，真实包名 **`com.minikano.f50_sms`**，不是有些教程写的 `com.kano.ufi.tools`。

> 🟡 安装会改变应用和权限。🔴 Root 桥让已登录后台能执行系统命令，风险远高于普通网页。
> 只在你自己的可信局域网操作。HTTP 不是 HTTPS；后台口令、原厂密码、卡信息和命令都不能视为受 TLS 保护。不要做公网端口转发。

## 第 1 步：从上游下载，先核验 🟢

1. 打开 [UFI-TOOLS 官方仓库](https://github.com/kanoqwq/UFI-TOOLS)，阅读它的说明和 [User_Doc.md](https://github.com/kanoqwq/UFI-TOOLS/blob/http-server-version/User_Doc.md)。
2. 本次对应 [V4.0.0 发布页](https://github.com/kanoqwq/UFI-TOOLS/releases/tag/Release)，资产名为 `UFI-TOOLS_WEB_V4.0.0_20260326_2103.apk`。下载后可以另存为 `D:\F50\tools\UFI-TOOLS.apk`，后面的命令使用这个名字。
3. PowerShell 检查 SHA256：

```powershell
Get-FileHash 'D:\F50\tools\UFI-TOOLS.apk' -Algorithm SHA256
```

本次输入和上游发布资产摘要相符：

```text
9eaefbd345b24603b9a41b2941dbf3ac207d51367ae0d2e1f8f62b53637fba41
```

**通过标准：** 下载来源、完整摘要都核对。哈希相等只说明文件一致，不是无漏洞保证；更新版本也不能沿用旧哈希和旧适配结论。

**⛔ 先停：** 文件不匹配、来自不明改包或签名来源有疑问。不要关掉验证硬装。这里不重分发 APK。

## 第 2 步：确认 ADB 连的是 F50 🟢

电脑端命令用 PowerShell；复杂设备命令统一进入设备 root shell 后逐行输入，避免 Windows PowerShell 5.1 等环境剥离嵌套引号。新增示例未做 Windows 实机执行验证，离线检查不代替实测。以下是电脑端 PowerShell 命令。把占位地址换成你自己 F50 的局域网地址，不要原样复制尖括号：

```powershell
$Target = '<your-device-address>:5555'
adb connect $Target
adb devices -l
adb -s $Target shell getprop ro.product.model
adb -s $Target shell getprop ro.build.display.id
adb -s $Target shell '/debug_ramdisk/su -c id'
adb -s $Target shell pm path com.minikano.f50_sms
```

**通过标准：** 目标在线，型号/固件正确，`id` 有 `uid=0(root)`。最后一条用来判断是否已经安装；未安装时无 package 路径是正常的。

**⛔ 先停：** `unauthorized`、`offline`、root 拒绝或型号不对。电脑上连着别的安卓设备时，后续命令一定保留 `-s $Target`。

**已有安装怎么办：** 先用界面导出插件与可导出的配置，私下保存；需要完整应用数据备份时另行审计。不要 `pm clear`、不要卸载再装来“修复”，它们可能丢配置和口令。`adb install -r` 不是备份。

## 第 3 步：安装并核对版本 🟡

确认备份/覆盖决定之后执行：

```powershell
adb -s $Target install -r 'D:\F50\tools\UFI-TOOLS.apk'
adb -s $Target shell dumpsys package com.minikano.f50_sms
```

**通过标准：** 安装输出 `Success`，包信息中 `versionName=4.0.0`，路径/包名正确。`-r` 是保留现有数据的覆盖安装，但不承诺能回退数据库版本。

**失败时：** 签名不匹配、版本降级、空间不足、包解析失败分别处理；不要加绕过签名或降级参数，也不要直接卸载旧版。

## 第 4 步：首次启动、权限和登录 🟡

先启动主界面；无屏机器可配合可信来源的 scrcpy 查看并手动完成初始化。这里不保证某个固件一定能投屏。

```powershell
adb -s $Target shell am start -n com.minikano.f50_sms/.MainActivity
```

1. 根据界面完成初始化、确认设备网关；只给需要的权限。通知权限用于前台服务；短信读取会接触隐私，不用短信功能就不要因为教程而盲目全部授权。
2. 按上游说明确认电池优化、后台和自启动限制。已有安装先看现状，不要重置。
3. 通过已取得的 root 单独启动网页服务，命令如下：

先在电脑 PowerShell 输入：

```powershell
adb -s $Target shell
```

进入设备后，下面是**设备 shell**命令，一行一行输入：

```sh
/debug_ramdisk/su
id
```

确认 `uid=0(root)` 才执行：

```sh
am start-foreground-service -n com.minikano.f50_sms/.WebService
exit
exit
```

两个 `exit` 分别退出 root 和设备 shell，返回电脑。后续每次进入 root shell 都按这个顺序确认；不要把设备命令粘到 PowerShell。

4. 连接 F50 所在网络，在浏览器打开 **`http://<your-device-address>:2333/`**。尖括号替换成实际地址。
5. 按界面登录。**UFI 独立口令**和**原厂后台管理密码**不是一回事：前者保护高级后台，后者用于调用部分原厂功能。已有非默认口令就保留；新安装若提示弱口令，请改为自己的强口令，不在命令、截图或仓库里写出来。

**通过标准：** 页面能正常加载并登录，设备信息合理，原厂后台仍能使用。服务命令输出组件名不代表网页已经可用；必须实际打开确认。

**⛔ 先停：** 无法完成初始化、服务立即退出或登录失败。先查包版本、日志和权限，不要删除 shared_prefs，也不要复制别人机器的登录配置。

## 第 5 步：按需接通最小 Root 桥 🔴

**只需要基础网页就先跳过这一步。跳过后，本指南不保证网页重启自启：按上游应用设置配置并单独验收，或重启后按第 4 步手动启动。不要只是为了网页自启而开放 Root 桥。** 本次没有直接打开上游“一整套高级功能”，因为它可能改 Samba 配置、启动额外服务。Root 方案采用 Magisk 启动脚本，只启动 WebService 和 APK 自带 socat 的私有 Unix socket，不加无认证 TCP 终端、不改 Samba/防火墙/OTA，不卸载系统包。

### 5.1 先排除已有启动方式 🟢

按第 4 步进入设备 root shell、确认 `id` 后执行：

```sh
ls -l /data/adb/service.d
ps -A | grep socat
ls -l /data/user/0/com.minikano.f50_sms/files/socat /data/user/0/com.minikano.f50_sms/files/kano_root_shell.sock
exit
exit
```

检查是否已有同名脚本、上游高级模式或其他启动 socat 的方式。**已有且工作正常就不要再加一套。** 缺少文件可能使 `ls` 报不存在，不等于必须重装。

### 5.2 准备 APK 内的 socat 🟡

仅当应用私有目录里确实缺这个文件、且没有其他部署方式时，才从**刚才核验过的同一 APK**提取 `assets/shell/socat`。下面用 Python 标准库，不执行这个文件：

```powershell
python -c "import zipfile,pathlib; p=pathlib.Path('D:/F50/tools/socat'); f=p.open('xb'); f.write(zipfile.ZipFile('D:/F50/tools/UFI-TOOLS.apk').read('assets/shell/socat')); f.close()"
Get-FileHash 'D:\F50\tools\socat' -Algorithm SHA256
adb -s $Target push 'D:\F50\tools\socat' /data/local/tmp/ufi-socat
adb -s $Target shell sha256sum /data/local/tmp/ufi-socat
```

**先手工比较电脑和设备的完整 SHA256，相等才继续。** 传输成功、文件大小相同都不够；不相等就停，不执行。

以下命令会进入设备上的交互 shell，再进入 root shell。看到提示符后，一行一行输入；不是 PowerShell 命令：

```text
adb -s $Target shell
/debug_ramdisk/su
id
```

确认 `uid=0(root)` 后，在设备 root shell 输入：

```sh
APP=com.minikano.f50_sms
APPFILES=/data/user/0/$APP/files
APPUID=$(stat -c %u "$APPFILES")
echo "$APPUID"
```

确认目录存在，UID 是该应用的普通应用 UID（本次为 10131，**别人机器不要照抄**）。不存在或数值异常就停。接着执行；如果已经存在 socat，下面会拒绝覆盖：

```sh
if [ -f "$APPFILES/socat" ]; then
    echo 'STOP: socat already exists; inspect it instead of overwriting'
else
    cp /data/local/tmp/ufi-socat "$APPFILES/socat" &&
    chown "$APPUID:$APPUID" "$APPFILES/socat" &&
    chmod 0700 "$APPFILES/socat" &&
    restorecon -F "$APPFILES/socat" &&
    sha256sum "$APPFILES/socat"
fi
```

再核对最终文件哈希与电脑一致。不一致或任何一步报错就停。用两次 `exit` 退出到电脑 PowerShell。

### 5.3 保存最小启动脚本 🟡 / 执行权限 🔴

把下面内容保存成电脑上的 `D:\F50\tools\90-ufi-tools-root.sh`，**UTF-8 无 BOM、LF 换行**。它按本次实测脚本整理，唯一适配点是从应用目录读取 UID，而不是写死 10131。**公开版未在第二台设备实测，不能保证其他环境可用。** 不要与其他 socat 启动器同时使用。

```sh
#!/system/bin/sh
trap '' HUP
umask 077
BB=/data/adb/magisk/busybox
APP=com.minikano.f50_sms
APPFILES=/data/user/0/$APP/files
SOCKET=$APPFILES/kano_root_shell.sock
PIDFILE=/data/local/tmp/ufi-tools-root-socat.pid
LOG=/data/local/tmp/ufi-tools-root-socat.log
[ -x "$BB" ] && [ -x "$APPFILES/socat" ] || exit 1
APPUID=$(stat -c %u "$APPFILES") || exit 1
case "$APPUID" in ''|*[!0-9]*) exit 1 ;; esac
[ "$APPUID" -ge 10000 ] || exit 1
i=0
while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$i" -lt 60 ]; do
    i=$((i+1))
    sleep 2
done
[ "$(getprop sys.boot_completed)" = 1 ] || exit 1
am start-foreground-service -n "$APP/.WebService" >>"$LOG" 2>&1
p=$(cat "$PIDFILE" 2>/dev/null)
if [ -n "$p" ] && kill -0 "$p" 2>/dev/null &&
   tr '\000' ' ' <"/proc/$p/cmdline" | grep -F "$APPFILES/socat" >/dev/null; then
    exit 0
fi
(
    trap '' HUP
    exec "$BB" setsid "$APPFILES/socat" "UNIX-LISTEN:$SOCKET,fork,reuseaddr,unlink-early,mode=0600,user=$APPUID,group=$APPUID" EXEC:/system/bin/sh
) </dev/null >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
i=0
while [ ! -S "$SOCKET" ] && [ "$i" -lt 12 ]; do
    i=$((i+1))
    sleep 1
done
[ -S "$SOCKET" ] || exit 1
restorecon -F "$SOCKET" || exit 1
chown "$APPUID:$APPUID" "$SOCKET" || exit 1
chmod 0600 "$SOCKET"
```

**风险说明：** 这个 socket 背后是 root shell，只允许该应用 UID 访问，不代表应用不会被攻击。脚本会替换同路径的旧 socket，因此必须先排除其他启动器；不要并发运行，也不要拿它修复来源不明的旧安装。日志和 PID 文件仅供本机排错，不能盲信 PID 去 kill 其他进程。

### 5.4 上传，核验后才启用 🟡

回到 PowerShell：

```powershell
Get-FileHash 'D:\F50\tools\90-ufi-tools-root.sh' -Algorithm SHA256
adb -s $Target push 'D:\F50\tools\90-ufi-tools-root.sh' /data/local/tmp/90-ufi-tools-root.sh
adb -s $Target shell sha256sum /data/local/tmp/90-ufi-tools-root.sh
```

两个完整 SHA256 相等才继续。按第 4 步进入设备 root shell、确认 `id` 后先检查目录：

```sh
ls -ld /data/adb/service.d
```

目录不存在就停。先确认目标脚本不存在；已有文件请私下备份并比较，不覆盖：

```sh
if test -e /data/adb/service.d/90-ufi-tools-root.sh; then
    echo STOP_existing_script
else
    cp /data/local/tmp/90-ufi-tools-root.sh /data/adb/service.d/90-ufi-tools-root.sh &&
    chmod 0700 /data/adb/service.d/90-ufi-tools-root.sh
fi
```

出现 `STOP_existing_script` 或报错就停，不接着运行。首次部署成功后，在**同一个设备 root shell**手动运行一次并检查：

```sh
sh /data/adb/service.d/90-ufi-tools-root.sh
ls -l /data/user/0/com.minikano.f50_sms/files/kano_root_shell.sock
tail -n 30 /data/local/tmp/ufi-tools-root-socat.log
exit
exit
```

**通过标准：** socket 权限为 `srw-------`，属主/组是应用 UID；日志没有明显退出错误，网页仍可登录。脚本没有输出不等于成功。

## 第 6 步：最小验收，不碰卡和网络 🟢

1. 手机或电脑打开网页，登录后查看设备信息；不要为了测试而切卡、锁频、改 IMEI、发短信或卸载软件。
2. 使用后台已有的认证命令执行入口（或按上游接口文档发出认证请求），**只运行 `id`**，确认 `uid=0(root)`。它对应 `/api/root_shell`；如果当前界面没有这个入口，不要猜一个按钮或为此启用整套高级模式，先停下按上游接口说明检查。
3. 新的无痕会话不要登录，检查敏感 Root API 请求应被拒绝（401/403 等），而不是只看静态页面能否打开。**未登录能看登录页是正常的，能执行命令不是。** 不在这里提供签名/口令提取脚本，不读取或打印登录凭据。
4. 保留现有口令，确认原厂后台和基本网络仍可用。通过这些检查，只能说明最小部署正常，不能说明所有按钮可用。

本次历史验证：网页获取 HTTP 200、认证 Root API `id` 返回 root、未登录 Root 请求被拒绝；没有实际执行全部网页功能。

## 第 7 步：正常重启后再查一次 🟡

```powershell
adb -s $Target reboot
```

等设备正常启动，必要时重新 `adb connect $Target`。只重复第 2 步的型号/root 查询、第 4 步的浏览器访问和登录，以及第 6 步中适用于你的检查；部署了 Root 桥的再检查 socket 和日志。不要重复安装、复制或启动脚本。确认页面、登录、认证 Root API、socket 权限、ADB 和原厂后台仍正常。

**通过标准分两种：** 部署第 5 步 Root 桥的，不用手动启动也应恢复网页和 Root 桥；只装基础网页的，须单独验收上游自启配置，没配置就允许按第 4 步手动启动，不能声称自启通过。本次旧版实测脚本通过一次正常重启；这里的动态 UID 版本只是适配整理，尚未新增实机重启验证。不能据此承诺断电恢复或每个固件都自启。

## 出问题怎么停，不扩大改动

| 现象 | 先查什么 | 不要做什么 |
| --- | --- | --- |
| 网页打不开 | 地址/网络、2333、WebService 和权限日志 | 不重刷 root，不改防火墙全放行 |
| 网页能开，Root 不通 | root 自身、socat 来源与执行权限、socket UID/0600、SELinux 和日志 | 不 chmod 777，不关闭 SELinux |
| 登录失败 | UFI 口令和原厂密码是否混淆 | 不清应用数据，不复制别人 token |
| 重启后失效 | Magisk service.d 是否运行、脚本换行、runtime、启动日志 | 不同时增加多套保活脚本 |
| 未登录可执行 Root 命令 | 立即隔离不可信网络并停用 Root 桥，保留证据排查 | 不继续暴露或公开日志凭据 |

要停用本章新增的自启，可先私下备份，再将自己新增的脚本移出 `/data/adb/service.d` 到仅 root 可读的私有目录，正常重启后检查 socat 不再运行。**只改执行位不应被当作可靠停用方式；不要仅把脚本改名留在 service.d。** 已有上游服务/其他启动器须单独审计。不要为了卸载后台而恢复分区、擦 userdata 或删整个 `/data/adb`。应用数据/口令的完整回退没有在本指南中实测。

最后，eSIM 管理器是[另一个实验项目](https://github.com/yukinsnow/f50pro-esim-manager)。安装本后台不会自动导入它，更不代表写卡验证完成。
