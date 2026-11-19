"""Complete; do not change. Independent bounded oracle, no production helpers.

List FIFOs, separate dictionaries, literal single-visit stepping; never skip.
Used only with small magnitudes and bounded traces, not MAX-cost fixtures.
"""
class Naive:
    def __init__(self, count):
        self.queues = [{'fifo': [], 'weight': 1, 'balance': 0} for _ in range(count)]
        self.position = 0
        self.visiting = False

    def run(self, op, *args):
        if op in ('enqueue', 'set_quantum', 'remove_head', 'drain_queue'):
            index = args[0]
            if index < 0 or index >= len(self.queues):
                return ('error', 'invalid_index')
            queue = self.queues[index]
        if op == 'enqueue':
            for value, cost in args[1]:
                if cost == 0:
                    return ('error', 'zero_cost')
            queue['fifo'] += list(args[1])
            answer = None
        elif op == 'set_quantum':
            if args[1] == 0:
                return ('error', 'zero_quantum')
            queue['weight'] = args[1]
            answer = None
        elif op == 'add_queue':
            answer = len(self.queues)
            self.queues.append({'fifo': [], 'weight': 1, 'balance': 0})
        elif op == 'remove_queue':
            if self.queues:
                removed = len(self.queues) - 1
                if self.position == removed and self.visiting:
                    self.position = 0
                    self.visiting = False
                del self.queues[-1]
                self.position = self.position % len(self.queues) if self.queues else 0
            answer = None
        elif op in ('remove_head', 'drain_queue'):
            if op == 'remove_head':
                answer = queue['fifo'].pop(0) if queue['fifo'] else None
            else:
                answer = queue['fifo'][:]
                queue['fifo'] = []
            if not queue['fifo']:
                queue['balance'] = 0
                if self.visiting and self.position == index:
                    self.visiting = False
                    self.position = (self.position + 1) % len(self.queues)
        elif op == 'take':
            limit = args[0]
            if limit < 0:
                return ('error', 'negative_take')
            answer = []
            steps = 0
            while len(answer) < limit and any(q['fifo'] for q in self.queues):
                steps += 1
                assert steps < 10000, 'oracle bound exceeded'
                queue = self.queues[self.position]
                if not self.visiting and queue['fifo']:
                    queue['balance'] += queue['weight']
                    self.visiting = True
                if queue['fifo'] and queue['balance'] >= queue['fifo'][0][1]:
                    value, cost = queue['fifo'].pop(0)
                    queue['balance'] -= cost
                    answer.append((self.position, value, cost))
                    if queue['fifo']:
                        continue
                    queue['balance'] = 0
                self.visiting = False
                self.position = (self.position + 1) % len(self.queues)
        else:
            raise AssertionError(op)
        return ('ok', answer)

    def snapshot(self):
        return (self.position, self.visiting, tuple(
            (q['weight'], q['balance'], tuple(q['fifo'])) for q in self.queues))
