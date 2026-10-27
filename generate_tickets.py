"""
generate_tickets.py
Creates a realistic set of FAKE IT help-desk tickets for practising pandas.

Run:     python generate_tickets.py
Output:  data/tickets.csv

Everything here is invented: no real people or companies.
Change the settings at the top to make the data bigger, messier or different.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)  # same "random" data every run, so your results are repeatable

# ---------------- Settings you can tweak ----------------
NUM_TICKETS = 250
DAYS_BACK = 60  # tickets are spread over the last 60 days

CATEGORIES = {  # category: how common it is (relative weight)
    "Password reset": 25,
    "Access request": 20,
    "Wi-Fi / network": 15,
    "Software install": 12,
    "Laptop hardware": 10,
    "Email / calendar": 8,
    "VPN": 6,
    "Phishing report": 4,
    "Printer":4,
}
PRIORITIES = {"High": 15, "Medium": 50, "Low": 35}

# Typical hours to resolve, per priority (fastest, slowest).
# Some tickets will go over a typical SLA on purpose, so there's something to find.
RESOLVE_HOURS = {"High": (0.5, 8), "Medium": (2, 40), "Low": (4, 110)}

ASSIGNEES = {"Alex": 40, "Priya": 25, "Sam": 20, "Jordan": 15}  # deliberately uneven workload
CHANNELS = {"Slack": 50, "Portal": 30, "Email": 20, "Phone": 10, "Walk-in": 5}

OPEN_RATE = 0.12          # extra share of tickets left open (stalled/backlog)
UNASSIGNED_RATE = 0.30    # share of OPEN tickets with no assignee
MISSING_CATEGORY = 0.03   # a few blank categories, for data-cleaning practice
# --------------------------------------------------------


def weighted_choice(options):
    """Pick one key from a {option: weight} dictionary."""
    return random.choices(list(options), weights=list(options.values()))[0]


def random_created(now):
    """A random weekday-style working-hours timestamp in the last DAYS_BACK days."""
    day = now - timedelta(days=random.randint(0, DAYS_BACK))
    created = day.replace(hour=random.randint(8, 17), minute=random.randint(0, 59),
                          second=0, microsecond=0)
    # A ticket "created" later today than right now isn't possible, so pull it back
    return min(created, now - timedelta(minutes=30))


def main():
    now = datetime.now()
    rows = []

    for _ in range(NUM_TICKETS):
        created = random_created(now)
        priority = weighted_choice(PRIORITIES)
        fastest, slowest = RESOLVE_HOURS[priority]
        resolved = created + timedelta(hours=random.uniform(fastest, slowest))

        # Open if it wouldn't be fixed yet, or randomly stalled
        is_open = resolved > now or random.random() < OPEN_RATE

        if is_open:
            status = random.choice(["Open", "In progress"])
            resolved = None
            assignee = None if random.random() < UNASSIGNED_RATE else weighted_choice(ASSIGNEES)
            if status == "In progress" and assignee is None:
                status = "Open"  # nobody can be working on an unassigned ticket
        else:
            status = "Closed"
            assignee = weighted_choice(ASSIGNEES)

        category = weighted_choice(CATEGORIES)
        if random.random() < MISSING_CATEGORY:
            category = None

        rows.append({
            "created": created,
            "resolved": resolved,
            "category": category,
            "priority": priority,
            "status": status,
            "assignee": assignee,
            "channel": weighted_choice(CHANNELS),
        })

    tickets = pd.DataFrame(rows).sort_values("created").reset_index(drop=True)
    tickets.insert(0, "ticket_id", range(1001, 1001 + len(tickets)))

    Path("data").mkdir(exist_ok=True)
    tickets.to_csv("data/tickets.csv", index=False, date_format="%Y-%m-%d %H:%M")

    print(f"Saved {len(tickets)} tickets to data/tickets.csv")
    print(tickets["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
