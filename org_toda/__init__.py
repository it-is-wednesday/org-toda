"""
Materialize Caldav todos into org-mode files and vice versa
"""
__version__ = "0.1"

from typing import Iterable
import argparse

import caldav


from .common import Calendar, Task
from .fetch import fetch_task_calendars


def make_headline(task: Task, depth: int):
    desc = "\n" + task.description if task.description else ""
    return f"{'*' * depth} {task.title}{desc}"


def task_to_org(task: Task, depth=2):
    """
    Convert task to an org-mode entry (headline and body)
    """
    subs = [task_to_org(t, depth + 1) for t in task.subtasks]
    return "\n".join([make_headline(task, depth), *subs])


def calendar_to_org(cal: Calendar):
    tasks = "\n".join(map(task_to_org, cal.tasks))
    return f"* {cal.title}\n{tasks}\n"




def cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("user")
    parser.add_argument("password")
    parser.add_argument("target_file")
    return parser.parse_args()


def main():
    args = cli_args()

    client = caldav.DAVClient(
        url=args.url,
        username=args.user,
        password=args.password,
    )

    with open(args.target_file, "w") as f:
        for cal in fetch_task_calendars(client):
            print(f"Writing calendar {cal.title}")
            f.write(calendar_to_org(cal))


if __name__ == "__main__":
    main()
