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
AS_OF = datetime(2026, 10, 27, 12, 0)   # fixed report date, matching the generator, so dates don't change between runs
SLA_TARGETS = pd.DataFrame({"priority": ["High", "Medium", "Low"],
                            "sla_hours": [4, 24, 72]})


def load_tickets(path):
    """Read the CSV, convert dates, fill blank categories, add resolution_hours and age_days."""
    tickets = pd.read_csv(path, parse_dates=['created', 'resolved'])
    
    # Blank categories become 'Uncategorised', so that they still show up in counts. 
    tickets['category'] = tickets['category'].fillna('Uncategorised')
    tickets['resolution_hours'] = (tickets['resolved'] - tickets['created']).dt.total_seconds() / 3600

    # Only open tickets get an age: closed one are finished, so waiting time doesn't apply. Round to 1 decimal place for easier reading.
    tickets['age_days'] = (AS_OF - tickets['created']).dt.total_seconds() / 3600 / 24
    tickets['age_days'] = np.where( tickets['status'] != 'Closed', tickets['age_days'], np.nan)
    tickets['age_days'] = tickets['age_days'].round(1)

    return tickets


def volume_by_category(tickets):
    """How many tickets per category?"""

    # Returns the value counts of each category, as a percentage of total tickets.
    return (tickets['category'].value_counts(normalize=True) * 100).round(1)


  


def backlog(tickets):
    """Open tickets with their age in days, oldest first."""
    # Returns a DataFrame of open tickets, sorted by age_days descending.
    return tickets[tickets['status'] != 'Closed'].sort_values('age_days', ascending=False)


def unassigned(tickets):
    """Open tickets with nobody assigned."""
    # Returns a dataframe with open tickets that have no employee assigned.
    return tickets[tickets['assignee'].isna() & (tickets['status'] != 'Closed')]



def workload(tickets):
    """Open tickets per assignee."""
    # Returns a Series of open tickets per assignee, sorted descending.
    return tickets[tickets['status'] != 'Closed'].groupby('assignee').size().sort_values(ascending=False)


def sla_summary(tickets):
    """Breaches and breach rate per priority (closed tickets only)."""
    # Returns a DataFrame with breach counts and rates per priority.
    closed = tickets[tickets['status'] == 'Closed']

    # Merge the SLA targets onto the closed tickets, then calculate whether each ticket breached its SLA.
    closed = closed.merge(SLA_TARGETS, on='priority', how='left')
    # Calculate the resolution time in hours, and whether it breached the SLA.
    closed['sla_breached'] = closed['resolution_hours'] > closed['sla_hours']
    # Group by priority, count tickets, sum breaches, and calculate breach rate.
    summary = closed.groupby('priority')['sla_breached'].agg(['count', 'sum', 'mean'])
    summary.columns = ['tickets', 'breaches', 'breach_rate']
    summary['breach_rate'] = (summary['breach_rate'] *100).round(1) 
    summary = summary.reindex(['High', 'Medium', 'Low'])  # put priorities in a logical order
    return summary


def main():
    tickets = load_tickets(DATA_FILE)
    print(f"Loaded {len(tickets)} tickets")

    categories = volume_by_category(tickets)
    print(categories)

    open_queue = backlog(tickets)
    print(open_queue)

    no_owner = unassigned(tickets)
    print(no_owner)

    ticket_workload = workload(tickets)
    print(ticket_workload)

    breach_of_sla = sla_summary(tickets)
    print(breach_of_sla)

    # call each function, print the result, save to OUTPUT_DIR


if __name__ == "__main__":
    main()