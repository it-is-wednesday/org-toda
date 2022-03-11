"""
Convert our Task abstraction into org-mode text
"""
from .common import Calendar, Task


def _make_headline(task: Task, depth: int):
    desc = "\n" + task.description if task.description else ""
    return f"{'*' * depth} {task.title}{desc}"


def _task_to_org(task: Task, depth=2):
    """
    Convert task to an org-mode entry (headline and body)
    """
    subs = [_task_to_org(t, depth + 1) for t in task.subtasks]
    return "\n".join([_make_headline(task, depth), *subs])


def calendar_to_org(cal: Calendar):
    tasks = "\n".join(map(_task_to_org, cal.tasks))
    return f"* {cal.title}\n{tasks}\n"
