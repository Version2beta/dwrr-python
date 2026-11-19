"""Complete; do not change. Native full frozen corpus through public methods."""
import json
from pathlib import Path
import unittest
from dwrr import Scheduler, SchedulerError, Item

ROOT = Path(__file__).resolve().parents[1]


class CorpusTests(unittest.TestCase):
    def test_all_1839_cases_44728_steps_seven_files(self):
        files = sorted((ROOT / 'vendor/shared/corpus').glob('*.jsonl'))
        self.assertEqual(len(files), 7)
        cases = steps = 0
        for path in files:
            for line in path.read_text().splitlines():
                case = json.loads(line)
                cases += 1
                scheduler = None
                for position, step in enumerate(case['steps']):
                    steps += 1
                    r = step['request']
                    op = r['op']
                    try:
                        if op == 'new':
                            scheduler = Scheduler(r['count'])
                            value = None
                        elif op == 'enqueue':
                            value = scheduler.enqueue(r['queue'], [Item(i['value'], int(i['cost'])) for i in r['items']])
                        elif op == 'set_quantum':
                            value = scheduler.set_quantum(r['queue'], int(r['quantum']))
                        elif op in ('remove_head', 'drain_queue'):
                            value = getattr(scheduler, op)(r['queue'])
                            def wire(item):
                                return {'value': item.value, 'cost': str(item.cost)}
                            value = [wire(i) for i in value] if op == 'drain_queue' else (wire(value) if value else None)
                        elif op == 'take':
                            value = [{'queue': i.queue, 'value': i.value, 'cost': str(i.cost)} for i in scheduler.take(r['n'])]
                        else:
                            value = getattr(scheduler, op)()
                        actual = {'ok': value}
                    except SchedulerError as error:
                        actual = {'error': error.code}
                    self.assertEqual(actual, step['response'], (path.name, case['name'], position))
        self.assertEqual((cases, steps), (1839, 44728))
