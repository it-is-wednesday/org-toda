#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Iterable, List, Optional
import caldav
import icalendar.cal as ical

from .common import Calendar, Task


@dataclass
class _TempTask:
    """
    Pretty much same as the Task class, but includes annoying metadata such as
    UID and parent UID. We only use these to figure out which taskes are
    subtasks of which tasks. We will get rid of these when getting out of this module
    """

    title: str
    uid: str
    parent_uid: Optional[str] = None
    description: Optional[str] = None
    subtasks: List["_TempTask"] = field(default_factory=list)


def _temp_task_to_normal_task(temptask):
    return Task(
        title=temptask.title,
        description=temptask.description,
        subtasks=[_temp_task_to_normal_task(t) for t in temptask.subtasks],
    )


def _find_subtask(task: _TempTask, id_to_find: str) -> Optional[_TempTask]:
    "Recursively find a task with id_to_find in task's subtasks"
    for st in task.subtasks:
        if st.uid == id_to_find:
            return st

        if nested := _find_subtask(st, id_to_find):
            return nested
    return None


def _mitigate_orphans(tasks: Iterable[_TempTask]) -> List[_TempTask]:
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

    def mitigate_inplace(roots: List[_TempTask], subtasks: List[_TempTask]):
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
                    if nested_parent := _find_subtask(root, task.parent_uid):
                        nested_parent.subtasks.append(task)
                        subtasks.remove(task)

        return mitigate_inplace(roots, subtasks)

    mitigate_inplace(toplevel, midlevel)
    return toplevel


def _task_details(task: caldav.Todo) -> _TempTask:
    """
    Convert a Caldav todo obejct into out own definition of Task.
    Raises ValueError if title or uid are missind in task.
    """
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

    return _TempTask(
        title=title,
        uid=uid,
        description=f"{desc}\n" if (title != desc and desc is not None) else None,
        parent_uid=s("RELATED-TO"),
    )


def fetch_task_calendars(client: caldav.DAVClient) -> Iterable[Calendar]:
    """
    Fetch all tasks from remote via client, grouped as calendars.
    Skips calendars with no title.
    """
    for calendar in client.principal().calendars():
        if (title := calendar.name) is None:
            print(f"Calendar {calendar} has no title, skipping")
            continue

        # convert all todos in current calendar into our Task record, skipping
        # todos with missing fields
        tasks_in_cal = []
        for task in calendar.todos():
            try:
                tasks_in_cal.append(_task_details(task))
            except ValueError as e:
                print(e)
                continue

        subtasks = map(_temp_task_to_normal_task, _mitigate_orphans(tasks_in_cal))
        yield Calendar(title, list(subtasks))
