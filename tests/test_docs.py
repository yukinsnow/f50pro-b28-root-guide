"""Offline document checks only: never execute Android/PowerShell commands."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_requested_title(self):
        title = (ROOT / 'README.md').read_text().splitlines()[0]
        self.assertEqual(title, '# ZTE F50 Pro root及安装高级后台指南')

    def test_local_links(self):
        for path in list(ROOT.glob('*.md')) + list((ROOT / 'docs').glob('*.md')) + list((ROOT / 'tools').glob('*.md')):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#', 1)[0]
                self.assertTrue((path.parent / target).exists(), (path, target))

    def test_shell_fences_parse_without_execution(self):
        shell = shutil.which('sh')
        if not shell:
            self.skipTest('POSIX sh unavailable; syntax-only shell gate not run')
        for path in (ROOT / 'docs').glob('*.md'):
            for block in re.findall(r'^```sh\n(.*?)^```', path.read_text(), re.M | re.S):
                checked = subprocess.run([shell, '-n'], input=block, text=True, capture_output=True)
                self.assertEqual(checked.returncode, 0, (path, checked.stderr))

    def test_limitations_remain_visible(self):
        readme = (ROOT / 'README.md').read_text()
        backend = (ROOT / 'docs/05-advanced-backend.md').read_text()
        for text in ('没有完全核实', '没有实测', '缺乏充分验证', '不是 HTTPS'):
            self.assertIn(text, readme)
        for text in ('尚未新增实机重启验证', 'SHA256', '不要并发运行', '未登录', '不是 PowerShell 命令'):
            self.assertIn(text, backend)

    def test_review_regressions(self):
        backend = (ROOT / 'docs/05-advanced-backend.md').read_text()
        flash = (ROOT / 'docs/03-flash-verify-rollback.md').read_text()
        self.assertNotIn('su -c "', backend)
        self.assertNotIn('su -c "', flash)
        self.assertIn('不保证网页重启自启', backend)
        self.assertIn(r"--signed 'D:\F50\derived\tos-noavb-bsp-bypassed'", flash)
        self.assertIn(r"--signed 'D:\F50\backup-new\trustos_a'", flash)

    def test_walkthrough_has_eight_steps_and_checks(self):
        walkthrough = (ROOT / 'docs/00-walkthrough.md').read_text()
        self.assertEqual(len(re.findall(r'^## 第 [1-8] 步', walkthrough, re.M)), 8)
        self.assertEqual(walkthrough.count('**通过标准：**'), 8)


if __name__ == '__main__':
    unittest.main()
