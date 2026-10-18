import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from server.tools.program_optimizer.optimizer import (
    CetusOptimizationError,
    CetusOptimizer,
)


class CetusOptimizerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source_dir = self.root / "source with spaces"
        self.source_dir.mkdir()
        self.source = self.source_dir / "sample source.c"
        self.source.write_text("int main(void) { return 0; }\n", encoding="utf-8")
        self.profiles = self.root / "profiles.json"
        self.profiles.write_text(
            json.dumps(
                {
                    "parallel": {
                        "description": "test profile",
                        "flags": ["-alias=3", "-parallelize-loops=1"],
                    }
                }
            ),
            encoding="utf-8",
        )
        self.fake_cetus = self.root / "fake cetus"
        self.fake_cetus.write_text(
            "#!/bin/sh\n"
            "outdir=\n"
            "input=\n"
            "for arg in \"$@\"; do\n"
            "  case \"$arg\" in\n"
            "    -outdir=*) outdir=\"${arg#-outdir=}\" ;;\n"
            "    *.c|*.i) input=\"$arg\" ;;\n"
            "  esac\n"
            "done\n"
            "if [ \"${FAKE_CETUS_EXIT:-0}\" -ne 0 ]; then exit \"$FAKE_CETUS_EXIT\"; fi\n"
            "if [ \"${FAKE_CETUS_NO_OUTPUT:-0}\" -eq 1 ]; then exit 0; fi\n"
            "mkdir -p \"$outdir\"\n"
            "input_base=$(basename \"$input\")\n"
            "printf 'transformed\\n' > \"$outdir/$input_base\"\n"
            "printf 'fake stdout\\n'\n",
            encoding="utf-8",
        )
        self.fake_cetus.chmod(0o755)
        self.optimizer = CetusOptimizer(
            cetus_path=self.fake_cetus,
            profiles_file=self.profiles,
            timeout_seconds=5,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_requires_cetus_environment_variable(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(CetusOptimizationError, "CETUS is not set"):
                CetusOptimizer()

    def test_requires_profiles_environment_variable(self):
        with patch.dict(os.environ, {"CETUS": str(self.fake_cetus)}, clear=True):
            with self.assertRaisesRegex(
                CetusOptimizationError, "CETUS_PROFILES_FILE is not set"
            ):
                CetusOptimizer()

    def test_resolves_paths_and_timeout_from_environment(self):
        environment = {
            "CETUS": str(self.fake_cetus),
            "CETUS_PROFILES_FILE": str(self.profiles),
            "CETUS_TIMEOUT_SECONDS": "12",
        }
        with patch.dict(os.environ, environment, clear=True):
            optimizer = CetusOptimizer()

        self.assertEqual(optimizer.cetus_path, self.fake_cetus.resolve())
        self.assertEqual(optimizer.profiles_file, self.profiles.resolve())
        self.assertEqual(optimizer.timeout_seconds, 12.0)

    def test_uses_profile_and_preserves_input_when_paths_contain_spaces(self):
        original = self.source.read_bytes()
        output_root = self.root / "requested output with spaces"

        result = self.optimizer.optimize_file(self.source, "parallel", output_root)

        self.assertEqual(result.profile, "parallel")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "fake stdout\n")
        self.assertEqual(result.output_path.read_text(encoding="utf-8"), "transformed\n")
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(result.command[1:3], ("-alias=3", "-parallelize-loops=1"))
        self.assertTrue(result.command[-1].endswith("/input.c"))
        self.assertNotIn(" ", result.command[-1])
        self.assertTrue(str(result.output_path).startswith(str(output_root.resolve())))

    def test_adds_final_newline_to_staged_copy_only(self):
        self.source.write_bytes(b"int main(void) { return 0; }")
        original = self.source.read_bytes()
        self.fake_cetus.write_text(
            "#!/bin/sh\n"
            "outdir=\n"
            "input=\n"
            "for arg in \"$@\"; do\n"
            "  case \"$arg\" in\n"
            "    -outdir=*) outdir=${arg#-outdir=} ;;\n"
            "    *.c|*.i) input=\"$arg\" ;;\n"
            "  esac\n"
            "done\n"
            "mkdir -p \"$outdir\"\n"
            "cp \"$input\" \"$outdir/input.c\"\n",
            encoding="utf-8",
        )
        self.fake_cetus.chmod(0o755)

        result = self.optimizer.optimize_file(self.source, "parallel")

        self.assertEqual(result.output_path.read_bytes(), original + b"\n")
        self.assertEqual(self.source.read_bytes(), original)

    def test_unknown_profile_reports_available_profiles(self):
        with self.assertRaisesRegex(CetusOptimizationError, "parallel"):
            self.optimizer.optimize_file(self.source, "missing")

    def test_nonzero_cetus_exit_is_an_error(self):
        previous = os.environ.get("FAKE_CETUS_EXIT")
        os.environ["FAKE_CETUS_EXIT"] = "9"
        try:
            with self.assertRaisesRegex(CetusOptimizationError, "exit code 9"):
                self.optimizer.optimize_file(self.source, "parallel")
        finally:
            if previous is None:
                os.environ.pop("FAKE_CETUS_EXIT", None)
            else:
                os.environ["FAKE_CETUS_EXIT"] = previous

    def test_timeout_is_reported(self):
        self.fake_cetus.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
        self.fake_cetus.chmod(0o755)
        optimizer = CetusOptimizer(
            cetus_path=self.fake_cetus,
            profiles_file=self.profiles,
            timeout_seconds=0.05,
        )

        with self.assertRaisesRegex(CetusOptimizationError, "timed out"):
            optimizer.optimize_file(self.source, "parallel")

    def test_success_without_output_is_an_error(self):
        previous = os.environ.get("FAKE_CETUS_NO_OUTPUT")
        os.environ["FAKE_CETUS_NO_OUTPUT"] = "1"
        try:
            with self.assertRaisesRegex(CetusOptimizationError, "did not create"):
                self.optimizer.optimize_file(self.source, "parallel")
        finally:
            if previous is None:
                os.environ.pop("FAKE_CETUS_NO_OUTPUT", None)
            else:
                os.environ["FAKE_CETUS_NO_OUTPUT"] = previous


if __name__ == "__main__":
    unittest.main()
