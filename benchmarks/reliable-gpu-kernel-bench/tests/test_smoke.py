from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo import run_demo  # noqa: E402
from triton_adapter import default_matmul_variant_specs  # noqa: E402


class SmokeTests(unittest.TestCase):
    def test_cpu_demo_returns_decision_payload(self) -> None:
        payload = run_demo(
            backend="cpu",
            workload="matmul",
            seed=123,
            write_report_files=False,
            verbose=False,
        )
        self.assertIn("decision", payload)
        self.assertIn("summaries", payload)
        self.assertTrue(str(payload["decision"]).startswith(("promote:", "defer:", "reject:")))

    def test_generated_variant_specs_exist(self) -> None:
        specs = default_matmul_variant_specs()
        self.assertGreaterEqual(len(specs), 4)
        names = {spec.name for spec in specs}
        self.assertIn("generated_matmul_balanced_128x128x64_w4_s4", names)
        self.assertIn("generated_matmul_aggressive_128x256x64_w8_s3", names)


if __name__ == "__main__":
    unittest.main()
