"""Run from examples/fair_transfer with the local library installed."""

from contextlib import ExitStack, redirect_stdout
import io
import unittest
from unittest.mock import Mock, patch

import fair_transfer as demo


EXPECTED_OUTPUT = """Pretend transfers only; cost = file size in bytes.
Quantum bytes/visit: Basic=1024 Team=2048 Business=4096
01 Team draft.pdf 1024 bytes | cumulative bytes: Basic=0 Team=1024 Business=0
02 Team chart.png 1024 bytes | cumulative bytes: Basic=0 Team=2048 Business=0
03 Business slides.pdf 2048 bytes | cumulative bytes: Basic=0 Team=2048 Business=2048
04 Business logo.png 1024 bytes | cumulative bytes: Basic=0 Team=2048 Business=3072
05 Business summary.pdf 1024 bytes | cumulative bytes: Basic=0 Team=2048 Business=4096
06 Basic archive.zip 3072 bytes | cumulative bytes: Basic=3072 Team=2048 Business=4096
07 Team bundle.zip 4096 bytes | cumulative bytes: Basic=3072 Team=6144 Business=4096
08 Business backup.zip 8192 bytes | cumulative bytes: Basic=3072 Team=6144 Business=12288
09 Basic note.txt 256 bytes | cumulative bytes: Basic=3328 Team=6144 Business=12288
10 Basic photo.jpg 768 bytes | cumulative bytes: Basic=4096 Team=6144 Business=12288
11 Team index.txt 512 bytes | cumulative bytes: Basic=4096 Team=6656 Business=12288
12 Basic report.pdf 1024 bytes | cumulative bytes: Basic=5120 Team=6656 Business=12288
Done: all pretend transfers selected; no files read or sent.
"""


def select_all(scheduler):
    selected = []
    while batch := scheduler.take(1):
        selected.extend(batch)
    return selected


class FairTransferTests(unittest.TestCase):
    def test_main_exact_output_and_only_one_item_takes(self):
        scheduler = Mock(wraps=demo.create_scheduler())
        output = io.StringIO()
        with patch.object(demo, "create_scheduler", return_value=scheduler):
            with redirect_stdout(output):
                demo.main()
        self.assertEqual(output.getvalue(), EXPECTED_OUTPUT)
        self.assertEqual(scheduler.take.call_count, 13)  # includes final empty take
        self.assertTrue(all(call.args == (1,) and not call.kwargs
                            for call in scheduler.take.call_args_list))

    def test_order_and_large_head_blocks_cheaper_basic_items(self):
        selected = select_all(demo.create_scheduler())
        self.assertEqual([item.value.name for item in selected], [
            "draft.pdf", "chart.png", "slides.pdf", "logo.png", "summary.pdf",
            "archive.zip", "bundle.zip", "backup.zip", "note.txt", "photo.jpg",
            "index.txt", "report.pdf",
        ])
        # Basic's 256-byte note cannot bypass its initially unaffordable 3072-byte head.
        self.assertEqual(selected[5].value, demo.DEFAULT_TRANSFERS[0])

    def test_fifo_identity_cost_and_conservation(self):
        selected = select_all(demo.create_scheduler())
        self.assertCountEqual([id(item.value) for item in selected],
                              [id(transfer) for transfer in demo.DEFAULT_TRANSFERS])
        totals = {}
        for queue, customer in enumerate(demo.CUSTOMER_QUANTA):
            actual = [item for item in selected if item.queue == queue]
            expected = [t for t in demo.DEFAULT_TRANSFERS if t.customer == customer]
            self.assertEqual([item.value for item in actual], expected)
            self.assertTrue(all(item.cost == item.value.size_bytes for item in actual))
            totals[customer] = sum(item.cost for item in actual)
        self.assertEqual(totals, {"Basic": 5120, "Team": 6656, "Business": 12288})

    def test_single_takes_preserve_same_order_as_bulk_take(self):
        scheduler = demo.create_scheduler()
        self.assertEqual(select_all(scheduler), demo.create_scheduler().take(100))
        self.assertEqual(scheduler.take(1), [])

    def test_main_has_no_transfer_io_or_sleep(self):
        with ExitStack() as stack:
            for target in ("builtins.open", "io.open", "socket.socket",
                           "subprocess.Popen", "time.sleep"):
                stack.enter_context(patch(target, side_effect=AssertionError(target)))
            output = stack.enter_context(redirect_stdout(io.StringIO()))
            demo.main()
        self.assertEqual(output.getvalue(), EXPECTED_OUTPUT)


if __name__ == "__main__":
    unittest.main()
