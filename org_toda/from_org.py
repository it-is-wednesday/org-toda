"""
Convert an org-mode document into our Task abstraction
"""
from typing import Iterable

from orgparse.node import OrgBaseNode, OrgNode, OrgRootNode

from .common import Calendar, Task


def _node_to_task(node: OrgNode) -> Task:
    subtasks = list(map(_node_to_task, node.children))
    desc = node.body if node.body != "" else None
    return Task(title=node.heading, description=desc, subtasks=subtasks)


def org_to_calendars(doc: OrgBaseNode) -> Iterable[Calendar]:
    for node in doc.children:
        tasks = list(map(_node_to_task, node.children))
        yield Calendar(title=node.heading, tasks=tasks)
