# Implementation progress

Kit preparation only. Delivered engine/adapter are deliberate stubs. No coder
loop has run. Parent must accept the verified kit before implementation starts.
Private-reference evidence is not completion of any task by a coder.
T1: Construct/validate state, atomic enqueue/reweight, add/remove queues
Changed dwrr/_engine.py only: strict count, index-first validation via _queue, all-or-nothing enqueue with exact Item type and cost checks, set_quantum, add_queue, remove_queue cursor repair returning the retired Queue. T2/T3 stubs untouched.
Remains: T2 (remove_head/drain_queue) and T3 (take) are still stubs. Blocked: nothing. Evidence: judge.py state 8/8 PASS; kit_check PASS.
T2: Implement FIFO head/drain withdrawal and visit closure
Changed dwrr/_engine.py only: remove_head and drain_queue validate via _queue, withdraw FIFO without spending credit, and reset the emptied queue's credit; the active visit closes (cursor advances) only when the emptied queue is the active cursor queue. Evidence: judge.py withdraw 4/4 PASS, judge.py state 8/8 PASS, kit_check PASS.
Remains: T3 (take) is still a stub; T2 did not run the full corpus or concurrency tests. Blocked: nothing.
T1: Construct/validate state, atomic enqueue/reweight, add/remove queues
Changed dwrr/_engine.py: accept Item subclasses with isinstance while preserving index-first validation, strict costs and atomic enqueue. Evidence: python3 -B scripts/judge.py state (9/9 PASS), python3 -B scripts/judge.py withdraw (4/4 PASS), python3 -B scripts/kit_check.py (PASS).
Remains: later scheduling and adapter work unchanged; whole-tree behavioral acceptance not run. Blocked: nothing.
