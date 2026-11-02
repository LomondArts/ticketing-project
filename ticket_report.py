"""
ticket_report.py
Reads synthetic help-desk tickets and writes a weekly report to output/.
Run from the project folder:  python ticket_report.py
"""
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

DATA_FILE = "data/tickets.csv"
OUTPUT_DIR = Path("output")
AS_OF = datetime(2026, 10, 27, 12, 0)   # report date, matching the generator
SLA_TARGETS = pd.DataFrame({"priority": ["High", "Medium", "Low"],
                            "sla_hours": [4, 24, 72]})


def load_tickets(path):
    """Read the CSV, convert dates, fill blank categories, add resolution_hours and age_days."""
    tickets = pd.read_csv(path, parse_dates=['created', 'resolved'])
    

    tickets['category'] = tickets['category'].fillna('Uncategorised')

    tickets['resolution_hours'] = (tickets['resolved'] - tickets['created']).dt.total_seconds() / 3600
    tickets['age_days'] = (AS_OF - tickets['created']).dt.total_seconds() / 3600 / 24
    tickets['age_days'] = np.where( tickets['status'] != 'Closed', tickets['age_days'], np.nan)
    tickets['age_days'] = tickets['age_days'].round(1)

    return tickets


def volume_by_category(tickets):
    """How many tickets per category?"""
    ...


def backlog(tickets):
    """Open tickets with their age in days, oldest first."""
    ...


def unassigned(tickets):
    """Open tickets with nobody assigned."""
    ...


def workload(tickets):
    """Open tickets per assignee."""
    ...


def sla_summary(tickets):
    """Breaches and breach rate per priority (closed tickets only)."""
    ...


def main():
    tickets = load_tickets(DATA_FILE)
    print(f"Loaded {len(tickets)} tickets")
   
    
    # call each function, print the result, save to OUTPUT_DIR


if __name__ == "__main__":
    main()