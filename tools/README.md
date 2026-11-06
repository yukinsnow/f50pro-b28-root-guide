# 离线工具

Python 3 标准库即可，无依赖安装。**没有 USB、ADB、subprocess、网络或写分区能力**。

- `validate_backup.py DIRECTORY --log LOG`：仅读本地文件，按 XML 列出 80 目标，核对完整回执、严格 NV alias 条件、A 槽 misc CRC 和 init_boot 基本边界，输出 SHA256 manifest。**不解压 ramdisk、不验证构建指纹、不证明备份可恢复**；完整手工审计仍必需。拒绝别的布局而不自动适配。
- `assemble_trustos.py --head HEAD --tail TAIL --signed SIGNED --output NEWFILE`：验证 DHTB、6 MiB 分读长度、signed 前缀，独占创建新文件，不覆盖原件。它读不出下载器是否完成，必须先核对回执和 FDL2 返回。
- `compare_trustos.py --stock-raw RAW --derived DERIVED --readback READBACK`：比较派生前缀与原物理尾部拼接预期，仅读取。**不是 TrustOS patch 内容审计**。

示例见文档；运行测试：

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_public.py
```

测试使用临时目录与合成数据，不读取真实分区，也不执行设备命令。`check_public.py` 检查可分发文件是否误含主机路径、私钥、ADB 公钥内容、常见凭据、禁止的二进制后缀；这只是静态初筛，发布前还需人工审阅 `git diff --cached` 与文件清单。
