"""Select pretend whole-file transfers fairly by declared bytes; never send them."""

from dataclasses import dataclass

from dwrr import Item, Scheduler


@dataclass(frozen=True)
class Transfer:
    customer: str
    name: str
    size_bytes: int


CUSTOMER_QUANTA = {"Basic": 1024, "Team": 2048, "Business": 4096}
DEFAULT_TRANSFERS = (
    Transfer("Basic", "archive.zip", 3072),
    Transfer("Basic", "note.txt", 256),
    Transfer("Basic", "photo.jpg", 768),
    Transfer("Basic", "report.pdf", 1024),
    Transfer("Team", "draft.pdf", 1024),
    Transfer("Team", "chart.png", 1024),
    Transfer("Team", "bundle.zip", 4096),
    Transfer("Team", "index.txt", 512),
    Transfer("Business", "slides.pdf", 2048),
    Transfer("Business", "logo.png", 1024),
    Transfer("Business", "summary.pdf", 1024),
    Transfer("Business", "backup.zip", 8192),
)


def create_scheduler() -> Scheduler[Transfer]:
    scheduler = Scheduler[Transfer](len(CUSTOMER_QUANTA))
    for queue, (customer, quantum) in enumerate(CUSTOMER_QUANTA.items()):
        scheduler.set_quantum(queue, quantum)
        scheduler.enqueue(queue, [
            Item(transfer, transfer.size_bytes)
            for transfer in DEFAULT_TRANSFERS if transfer.customer == customer
        ])
    return scheduler


def main() -> None:
    scheduler = create_scheduler()
    totals = dict.fromkeys(CUSTOMER_QUANTA, 0)
    print("Pretend transfers only; cost = file size in bytes.")
    print("Quantum bytes/visit: Basic=1024 Team=2048 Business=4096")
    step = 0
    while selected := scheduler.take(1):
        transfer = selected[0].value
        totals[transfer.customer] += selected[0].cost
        step += 1
        cumulative = " ".join(f"{customer}={total}" for customer, total in totals.items())
        print(f"{step:02d} {transfer.customer} {transfer.name} "
              f"{transfer.size_bytes} bytes | cumulative bytes: {cumulative}")
    print("Done: all pretend transfers selected; no files read or sent.")


if __name__ == "__main__":
    main()
