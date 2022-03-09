#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Task:
    title: str
    description: Optional[str] = None
    subtasks: List["Task"] = field(default_factory=list)


@dataclass
class Calendar:
    """
    Not an actual calendar with timed event. "Calendar" in this context means a
    group of tasks, these groups are just hosted in Nextcloud as Caldav
    calendars for some reason
    """

    title: str
    tasks: List[Task]
