"""
Materialize Caldav todos into org-mode files and vice versa
"""
__version__ = "0.1"

import argparse

import caldav
import orgparse
from deepdiff.diff import DeepDiff

from .fetch import fetch_task_calendars
from .from_org import org_to_calendars
from .to_org import calendar_to_org


def cli_args():
    parser = argparse.ArgumentParser(prog="org-toda")
    parser.add_argument("url")
    parser.add_argument("user")
    parser.add_argument("password")
    parser.add_argument("org_file")
    return parser.parse_args()


def main():
    args = cli_args()

    client = caldav.DAVClient(
        url=args.url,
        username=args.user,
        password=args.password,
    )

    remote_tasks = list(fetch_task_calendars(client))
    local_tasks = list(org_to_calendars(orgparse.load(args.org_file)))

    diff = DeepDiff(local_tasks, remote_tasks, ignore_order=True)

    with open(args.org_file, "w") as f:
        for cal in remote_tasks:
            print(f"Writing calendar {cal.title}")
            f.write(calendar_to_org(cal))


if __name__ == "__main__":
    main()
