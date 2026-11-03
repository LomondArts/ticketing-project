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

    # Returns the value counts of each category.
    return (tickets['category'].value_counts())


  


def backlog(tickets):
    """Open tickets with their age in days, oldest first."""
    # Returns a DataFrame of open tickets, sorted by age_days descending.
    return tickets[tickets['status'] != 'Closed'].sort_values('age_days', ascending=False)[['ticket_id', 'created', 'category', 'priority', 'status', 'assignee', 'age_days']]

  

def unassigned(tickets):
    """Open tickets with nobody assigned."""
    # Returns a dataframe with open tickets that have no employee assigned.
    return tickets[tickets['assignee'].isna() & (tickets['status'] != 'Closed')][['ticket_id', 'created', 'category', 'priority', 'status', 'assignee', 'age_days']]




def workload(tickets):
    """Open tickets per assignee."""
    # Returns a Series of open tickets per assignee, sorted descending.
    return tickets[tickets['status'] != 'Closed'].groupby('assignee').size().sort_values(ascending=False).rename('open_tickets')


def sla_summary(tickets):
    """Breaches and breach rate per priority (closed tickets only)."""
    # Returns a DataFrame with breach counts and rates per priority.
    closed = tickets[tickets['status'] == 'Closed']

    # Merge the SLA targets onto the closed tickets, then calculate whether each ticket breached its SLA.
    closed = closed.merge(SLA_TARGETS, on='priority', how='left')
    # Calculate whether each ticket breached the SLA.
    closed['sla_breached'] = closed['resolution_hours'] > closed['sla_hours']
    # Group by priority, count tickets, sum breaches, and calculate breach rate.
    summary = closed.groupby('priority')['sla_breached'].agg(['count', 'sum', 'mean'])
    summary.columns = ['tickets', 'breaches', 'breach_rate']
    summary['breach_rate'] = (summary['breach_rate'] *100).round(1) 
    summary = summary.reindex(['High', 'Medium', 'Low'])  # put priorities in a logical order

    # Overall total, with the rate worked out from the totals (not an average of rates)
    total_tickets = summary['tickets'].sum()
    total_breaches = summary['breaches'].sum()
    summary.loc['All'] = [total_tickets, total_breaches, round(total_breaches / total_tickets * 100, 1)]
    summary[['tickets', 'breaches']] = summary[['tickets', 'breaches']].astype(int)
    return summary

def weekly_summary(tickets, categories, open_queue, no_owner, ticket_workload, breach_of_sla):
    """Plain-English summary of the week's reports, for a team meeting."""
    lines = [
        f"Weekly IT support summary (as of {AS_OF:%d %b %Y})",
        f"- {len(tickets)} tickets in total; most common: {categories.index[0]} ({categories.iloc[0]})",
        f"- {len(open_queue)} tickets open; oldest has waited {open_queue['age_days'].max()} days",
        f"- {len(no_owner)} open tickets have no owner",
        f"- {ticket_workload.index[0]} holds the most open tickets ({ticket_workload.iloc[0]})",
        f"- SLA: {breach_of_sla.loc['All', 'breaches']} of {breach_of_sla.loc['All', 'tickets']} closed tickets breached; {breach_of_sla['breach_rate'].idxmax()} was worst ({breach_of_sla['breach_rate'].max()}%)",
    ]
    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    tickets = load_tickets(DATA_FILE)
    print(f"Loaded {len(tickets)} tickets")


    categories = volume_by_category(tickets)
    print('\nTickets by category:')
    print(categories)
    categories.to_csv(OUTPUT_DIR / "tickets_by_category.csv")

    open_queue = backlog(tickets)
    print('\nOpen tickets (oldest first):')
    print(open_queue)
    open_queue.to_csv(OUTPUT_DIR / "open_tickets.csv", index=False)

    no_owner = unassigned(tickets)
    print('\nUnassigned tickets:')
    print(no_owner)
    no_owner.to_csv(OUTPUT_DIR / "unassigned_tickets.csv", index=False)

    ticket_workload = workload(tickets)
    print('\nWorkload per assignee:')
    print(ticket_workload)
    ticket_workload.to_csv(OUTPUT_DIR / "workload_per_assignee.csv")

    breach_of_sla = sla_summary(tickets)
    print('\nSLA summary:')
    print(breach_of_sla)
    breach_of_sla.to_csv(OUTPUT_DIR / "sla_summary.csv")

    summary = weekly_summary(tickets, categories, open_queue, no_owner, ticket_workload, breach_of_sla)
    print("\n" + summary)
    (OUTPUT_DIR / "weekly_summary.txt").write_text(summary)
    


if __name__ == "__main__":
    main()