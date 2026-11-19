"""Complete; do not change. Additional wire limits, JSON domain and public dispatch."""
import subprocess
import sys
import unittest
from scripts.wire import parse, encode, parse_integer, ProtocolError


def run(data):
    return subprocess.run([sys.executable, '-B', 'scripts/conformance_driver.py'],
                          input=data, capture_output=True, timeout=8)


class DriverTests(unittest.TestCase):
    def test_dispatch_every_operation_and_fresh_new(self):
        requests = b'''{"op":"new","count":1}
{"op":"enqueue","queue":0,"items":[{"value":7,"cost":"1"},{"value":8,"cost":"1"}]}
{"op":"set_quantum","queue":0,"quantum":"2"}
{"op":"take","n":1}
{"op":"remove_head","queue":0}
{"op":"drain_queue","queue":0}
{"op":"add_queue"}
{"op":"remove_queue"}
{"op":"new","count":0}
{"op":"take","n":999}
'''
        import json
        p = run(requests)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual([json.loads(line) for line in p.stdout.splitlines()], [
            {'ok': None}, {'ok': None}, {'ok': None}, {'ok': [{'queue': 0, 'value': 7, 'cost': '1'}]},
            {'ok': {'value': 8, 'cost': '1'}}, {'ok': []}, {'ok': 1}, {'ok': None}, {'ok': None}, {'ok': []}])
        self.assertEqual(p.stderr, b'')

    def test_huge_json_integer_roundtrip_without_global_setting(self):
        before = sys.get_int_max_str_digits()
        for sign in ('', '-'):
            token = sign + '9' * 6000
            data = ('{"op":"new","count":1}\n'
                    '{"op":"enqueue","queue":0,"items":[{"value":' + token + ',"cost":"1"}]}\n'
                    '{"op":"take","n":' + '9' * 6000 + '}\n').encode()
            p = run(data)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout.splitlines()[-1], ('{"ok":[{"queue":0,"value":' + token + ',"cost":"1"}]}').encode())
            self.assertEqual(encode(parse_integer(token)), token)
        huge_count = parse(('{"op":"new","count":' + '9' * 6000 + '}').encode()).args[0]
        self.assertEqual(encode(huge_count), '9' * 6000)
        self.assertEqual(sys.get_int_max_str_digits(), before)
        data = ('{"op":"new","count":0}\n{"op":"remove_head","queue":' + '9' * 6000 + '}\n').encode()
        self.assertEqual(run(data).stdout.splitlines()[-1], b'{"error":"invalid_index"}')

    def test_protocol_first_all_items_and_json_domain(self):
        bad = [b'\xff', b'', b'   ', b'{"op":"take","n":true}', b'{"op":"take","n":1e0}',
               b'{"op":"new","count":-1}', b'{"op":"take","n":NaN}',
               b'{"op":"take","n":Infinity}', b'{"op":"take","n":-Infinity}',
               b'{"op":"enqueue","queue":999,"items":[{"value":1,"cost":"0"},{"value":2,"cost":"01"}]}',
               b'{"op":"enqueue","queue":0,"items":[{"value":1,"cost":"18446744073709551616"}]}',
               '{"op":"set_quantum","queue":0,"quantum":"١"}'.encode()]
        for line in bad:
            p = run(b'{"op":"new","count":1}\n' + line + b'\n{"op":"take","n":1}\n')
            self.assertEqual(p.returncode, 2, line)
            self.assertEqual(p.stdout, b'{"ok":null}\n', line)
            self.assertIn(b'protocol error:', p.stderr)
            self.assertNotIn(b'18446744073709551616', p.stderr)

    def test_unused_fields_wire_uint64_and_errors_continue(self):
        p = run(b'''{"op":"new","count":1,"n":false,"queue":{},"items":"unused"}
{"op":"enqueue","queue":99,"items":[{"value":1,"cost":"0"}]}
{"op":"enqueue","queue":0,"items":[{"value":1,"cost":"18446744073709551615"}]}
{"op":"set_quantum","queue":0,"quantum":"0"}
{"op":"take","n":-1}
{"op":"enqueue","queue":0,"items":[{"value":2,"cost":"1"}]}
{"op":"take","n":1}
''')
        self.assertEqual(p.returncode, 0, p.stderr)
        for code in ('invalid_index', 'cost_too_large', 'zero_quantum', 'negative_take'):
            self.assertIn(('"error":"' + code + '"').encode(), p.stdout)
        self.assertEqual(p.stdout.splitlines()[-1], b'{"ok":[{"queue":0,"value":2,"cost":"1"}]}')
        # Detected resource failures must not become protocol/domain errors.
        # Inject allocation failure; do not attempt an actual huge allocation.
        import io
        from unittest.mock import patch
        from scripts import conformance_driver as driver
        for resource in (MemoryError, OverflowError):
            class Input:
                buffer = io.BytesIO(b'{"op":"new","count":0}\n' * 3)
            calls = []
            def execute(current, request):
                calls.append(request)
                if len(calls) == 2:
                    raise resource()
                return object(), {'ok': None}
            output, diagnostic = io.StringIO(), io.StringIO()
            with patch.object(driver, 'execute', execute), patch.object(driver.sys, 'stdin', Input()), patch.object(driver.sys, 'stdout', output), patch.object(driver.sys, 'stderr', diagnostic):
                self.assertEqual(driver.main(), 1)
            self.assertEqual(len(calls), 2)
            self.assertEqual(output.getvalue(), '{"ok":null}\n')
            self.assertEqual(diagnostic.getvalue(), 'resource exhaustion\n')
