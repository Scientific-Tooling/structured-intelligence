"""Native syntax checks for the advanced manual commands."""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

MANUAL = Path(__file__).resolve().parents[1] / "workflows/research/manual-operations"


class ManualDocumentationTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("powershell.exe"), "Windows PowerShell 5.1 syntax check")
    def test_windows_powershell_parses_every_documented_block(self):
        blocks = re.findall(r"```powershell\n(.*?)\n```", (MANUAL / "windows.md").read_text(encoding="utf-8"), re.DOTALL)
        self.assertGreater(len(blocks), 0, "No manual commands found")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "walkthrough.ps1"
            path.write_text("\n".join(blocks), encoding="utf-8-sig")
            command = "$tokens=$null; $errors=$null; [void][System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$tokens,[ref]$errors); if($errors.Count){$errors | Out-String | Write-Error; exit 1}"
            checker = Path(temporary) / "check.ps1"
            checker.write_text(command, encoding="utf-8-sig")
            result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(checker), str(path)], capture_output=True, text=True, timeout=30, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(os.name == "posix", "Native Bash/zsh syntax checks")
    def test_unix_shells_parse_every_documented_block(self):
        blocks = re.findall(r"```bash\n(.*?)\n```", (MANUAL / "unix.md").read_text(encoding="utf-8"), re.DOTALL)
        self.assertGreater(len(blocks), 0, "No manual commands found")
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "walkthrough.sh"
            script.write_text("\n".join(blocks), encoding="utf-8", newline="\n")
            for shell in ("bash", "zsh"):
                if shutil.which(shell):
                    with self.subTest(shell=shell):
                        result = subprocess.run([shell, "-n", str(script)], capture_output=True, text=True, timeout=30, check=False)
                        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
