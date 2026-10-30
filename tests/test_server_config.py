import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


CONFIG = Path(__file__).resolve().parents[1] / "src/server/config.py"


class ServerConfigurationTests(unittest.TestCase):
    def test_rest_flag_accepts_documented_boolean_values(self):
        cases = {
            "true": True,
            "TRUE": True,
            "1": True,
            "on": True,
            "false": False,
            "FALSE": False,
            "0": False,
            "off": False,
            "": False,
        }
        for value, expected in cases.items():
            with self.subTest(value=value), patch.dict(
                os.environ, {"ENABLE_REST_API": value}
            ):
                self.assertEqual(runpy.run_path(str(CONFIG))["ENABLE_REST_API"], expected)

    def test_native_bind_settings_use_host_and_port(self):
        with patch.dict(os.environ, {"HOST": "127.0.0.1", "PORT": "18000"}):
            config = runpy.run_path(str(CONFIG))
        self.assertEqual(config["HOST"], "127.0.0.1")
        self.assertEqual(config["PORT"], 18000)


if __name__ == "__main__":
    unittest.main()
