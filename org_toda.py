"""
Materialize Caldav todos into org-mode files and vice versa
"""

__version__ = "0.1"

from dataclasses import dataclass, field
from typing import Iterable, List, Optional
import argparse

import caldav
import icalendar.cal as ical


@dataclass
class Task:
    title: str
    uid: str
    parent_uid: Optional[str] = None
    description: Optional[str] = None
    subtasks: List["Task"] = field(default_factory=list)


def find_subtask(task: Task, id_to_find: str):
    "Recursively find a task with id_to_find in task's subtasks"
    for st in task.subtasks:
        if st.uid == id_to_find:
            return st

        if nested := find_subtask(st, id_to_find):
            return nested
    return None


def mitigate_orphans(tasks: Iterable[Task]):
    """
    Returns a new tasks list where each task with a parent is placed as a
    subtask of the parent task
    """
    # separate all orphan tasks from non-orphans
    toplevel = []
    midlevel = []
    for task in tasks:
        if task.parent_uid is None:
            toplevel.append(task)
        else:
            midlevel.append(task)

    def mitigate_inplace(roots: List[Task], subtasks: List[Task]):
        """
        attempt to find each task's parent. look for the parent in every item in
        roots, and every root's subtasks
        """
        if len(subtasks) == 0:
            return

        for task in subtasks:
            for root in roots:
                if task.parent_uid == root.uid:
                    root.subtasks.append(task)
                    subtasks.remove(task)
                else:
                    assert task.parent_uid  # just for the typechecker
                    if nested_parent := find_subtask(root, task.parent_uid):
                        nested_parent.subtasks.append(task)
                        subtasks.remove(task)

        return mitigate_inplace(roots, subtasks)

    mitigate_inplace(toplevel, midlevel)
    return toplevel


def task_details(task: caldav.Todo) -> Task:
    vtodo: ical.Todo = ical.Calendar.from_ical(task.data).walk("VTODO")[0]

    def s(key):
        if value := vtodo.get(key):
            # I'm not sure why it's necessary but the icalendar library won't
            # process hebrew otherwise
            return value.encode().decode()

    title = s("SUMMARY")
    uid = s("UID")
    desc = s("DESCRIPTION")

    if not title:
        raise ValueError("Task with no title??")

    if not uid:
        raise ValueError("Task with no uid??")

    return Task(
        title=title,
        uid=uid,
        description=f"{desc}\n" if title != desc else None,
        parent_uid=s("RELATED-TO"),
    )


def make_headline(task: Task, depth: int):
    desc = "\n" + task.description if task.description else ""
    return f"{'*' * depth} {task.title}{desc}"


def task_to_org_recur(task: Task, depth=1):
    subs = [task_to_org_recur(t, depth + 1) for t in task.subtasks]
    return "\n".join([make_headline(task, depth), *subs])


def cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("user")
    parser.add_argument("password")
    parser.add_argument("target_file")
    return parser.parse_args()


if __name__ == "__main__":
    args = cli_args()
    client = caldav.DAVClient(
        url=args.url,
        username=args.user,
        password=args.password,
    )

    tasks = [task_details(t) for t in client.principal().calendars()[0].todos()]
    tasks = mitigate_orphans(tasks)

    with open(args.target_file, "w") as f:
        for calendar in client.principal().calendars():
            tasks = mitigate_orphans(map(task_details, calendar.todos()))
            f.write("\n".join(map(task_to_org_recur, tasks)))
            break