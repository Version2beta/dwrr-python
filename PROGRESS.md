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
T3: Implement exact resumable take and direct skip; full native corpus/oracle/concurrency
Changed dwrr/_engine.py: strict atomic take validation, FIFO cyclic selection preserving active visits, and exact whole-idle-cycle skipping without payload operations. Evidence: exact timeout-wrapped schedule command 14/14 PASS (including all 1,839 cases / 44,728 steps, bounded oracle and concurrency); earlier state 9/9 PASS, withdraw 4/4 PASS; kit_check PASS.
Remains: T4 adapter dispatch and T5 whole-tree behavioral acceptance untouched and not validated. Blocked: nothing.
T4: Implement public-core wire dispatch; external full replay and 41 protocol checks
Changed scripts/_adapter.py only: execute() dispatches all eight operations through public Scheduler methods, maps Item/Scheduled to wire dicts with decimal cost strings, and returns the scheduler (new replaces it). Evidence: judge.py driver 4/4 PASS; replay.py 1839 cases / 44728 steps PASS; check_driver.py 41 of 41 PASS; earlier judge.py state 9/9, withdraw 4/4, schedule 14/14 PASS; kit_check PASS.
Remains: T5 whole-tree/packaging acceptance not run; no source change beyond the adapter. Blocked: nothing.
