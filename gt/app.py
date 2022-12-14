import datetime
import re
from os import wait
from typing import List, Optional

import dateparser
from dateutil.parser import parse
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from gt.google_tasks import GoogleTasks
from gt.gtaskconfig import Config


class App:

    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self._g: GoogleTasks = GoogleTasks(config.client_secret_path, config.token_path)

    @staticmethod
    def _parse_rfc3339_date_str(d: dict, k: str) -> Optional[datetime.datetime]:
        s: str = d.get(k, None)
        date = None
        if s:
            # Based on the documentation rfc3339 standard is used
            date = parse(s)    #.replace(tzinfo=None)
        return date

    @staticmethod
    def _process_tasks(tasks: List[dict]) -> List[dict]:
        for task in tasks:
            # Parse dates
            due_date = App._parse_rfc3339_date_str(task, "due")
            task["due"] = due_date

            updated_date = App._parse_rfc3339_date_str(task, "updated")
            task["updated"] = updated_date

            # Indicator weather task is priority by the tag "#prio"
            # E.g.: "Walk the dog #prio"
            task["title"] = task.get("title", "")
            is_prio: bool = re.search("#prio", task["title"]) is not None
            task["prio"] = is_prio

            current_date: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

            # Is the due date older then now?
            is_expired: bool = False
            if due_date:
                is_expired = (due_date + datetime.timedelta(days=1)) < current_date
            task["expired"] = is_expired

            # How many days are elapsed from the last updated
            elapsed_days = 0
            if updated_date:
                elapsed_days = (current_date - updated_date).days
            task["elapsed_days"] = elapsed_days

        return tasks

    @staticmethod
    def _get_default_table() -> Table:
        table = Table(show_footer=False, show_header=True, header_style="bold")
        table.title = "Google Tasks"
        table.caption = "[i]https://mail.google.com/tasks/canvas[/]"
        table.box = box.ROUNDED
        return table

    def list_task_lists(self, include_change_prompt: bool = False) -> None:
        task_lists: List[dict] = self._g.get_task_lists()

        table = self._get_default_table()
        table.add_column("Nb.", no_wrap=True, justify="center")
        table.add_column("Title", no_wrap=True, justify="left")
        table.add_column("ID", no_wrap=True, justify="left")

        for i, item in enumerate(task_lists):
            list_id = item["id"]
            list_title = item["title"]
            # Mark which is the default list, which is chosen by the user
            if list_id == self.config.task_list_id:
                list_title = f":star: {list_title}"
            table.add_row(str(i), list_title, list_id)

        # If there is no task list selected, then use the first one as default
        if self.config.task_list_id.replace(" ", "") == "":
            self.config.task_list_id = task_lists[0]["id"]

        console = Console()
        console.print(table)

        if include_change_prompt:
            chosen_list_number: int = int(Prompt.ask("Which task list to use (enter the nb."))
            try:
                chosen_list_id = task_lists[chosen_list_number]["id"]
                self.config.task_list_id = chosen_list_id
                print("Default task list id is set, you can play around with the other commands")
            except IndexError:
                print("This Nb. does not exists in the list")

    def list_tasks(self,
                   sort_by_updatetime: bool = False,
                   sort_by_due_date: bool = True,
                   head: int = 10,
                   show_completed: bool = False) -> None:
        if sum([sort_by_due_date, sort_by_updatetime]) > 1:
            raise ValueError("Only 1 of them could be True")

        if self.config.task_list_id.replace(" ", "") == "":
            print("[*] No task list is selected, please select a list first with 'gt lists'")
            import sys
            sys.exit(1)

        # Retrieve the tasks
        tasks: List[dict] = self._g.list_tasks(self.config.task_list_id,
                                               show_completed=show_completed,
                                               show_hidden=show_completed)

        tasks = self._process_tasks(tasks)

        if sort_by_updatetime:
            tasks = sorted(tasks, key=lambda x: x["updated"], reverse=True)
        elif sort_by_due_date:
            # Sorting trick for Nones: https://stackoverflow.com/a/18411610/5108062
            tasks = sorted(tasks, key=lambda x: (x["due"] is None, x["due"]), reverse=False)

        # Limit the number of tasks
        tasks_limited = tasks[:head]

        # Visualization

        table = self._get_default_table()
        table.title = "Tasks"
        if show_completed:
            table.title = "Completed Tasks"

        table.add_column("Id", no_wrap=True, justify="center")
        table.add_column("Due", no_wrap=True, justify="center")
        # table.add_column("Updated", no_wrap=True, style="dim")
        table.add_column("Days since\nupdate", no_wrap=True, justify="center", style="dim")
        table.add_column("Task", justify="left")

        for task in tasks_limited:
            if show_completed:
                if task["status"] != "completed":
                    continue

            due_date: datetime.datetime = task["due"]
            due_str = "-"
            if due_date:
                due_str: str = due_date.strftime("%Y/%m/%d")
                due_str = due_str[2:]
            if task["expired"]:
                due_str = f"[red]{due_str}[/red]"

            updated_date: datetime.datetime = task["updated"]
            updated_str = ""
            if updated_date:
                updated_str: str = updated_date.strftime("%Y/%m/%d %H:%M")
                updated_str = updated_str[2:]

            title = f"[b]{task['title']}[/b]"
            if task["expired"]:
                title = f"[red]{title}[/red]"
            if task["prio"]:
                title = f"[reverse] {title} [/reverse]"

            if "notes" in task:
                title += f" - [i][dim]{task['notes']}[/dim][/i]"
            
            # TODO: Somehow the links is an empty list every time
            # links = task.get("links", [])
            # for link in links:
            #     title += f"\n[i][dim][blue]{link['link']}[/blue][/dim][/i]"

            elapsed_days = str(task["elapsed_days"])

            table_row = [
                task["id"],
                due_str,
            # updated_str,
                elapsed_days,
                title
            ]
            table.add_row(*table_row)

        if len(tasks) > head:
            table.add_row("...", "...", "...")

        # table.row_styles = ["none", "dim"]

        console = Console()
        console.print(table)

    def add_task_to_list(self, prompt_input: Optional[str] = None):
        prompt: str = ""
        if prompt_input is not None:
            prompt = " ".join(prompt_input)

        # If prompt is not provided, then we'll ask for it
        if prompt == "":
            console = Console()
            prompt = console.input("Create task: ")

        # Split prompt to the different sections
        prompt_list: List[str] = prompt.split("~")

        # TODO: what to do when not enought items are in the list?

        title = None
        notes = None
        due = None

        if len(prompt_list) == 1:
            # Example: "This is a note"
            title = prompt_list[0]
        elif len(prompt_list) == 2:
            # Example: "This is a note ~ tomorrow 11AM"
            title = prompt_list[0]
            due = prompt_list[1]
        elif len(prompt_list) == 3:
            # Example: "This is a note ~ Some extra note ~ tomorrow 11AM"
            title = prompt_list[0]
            notes = prompt_list[1]
            due = prompt_list[2]

        if due is not None:
            due = dateparser.parse(due)
            if due is None:
                # TODO: better error handling
                print("[*] Could not parse the date try it again")
            else:
                # Convert to the RFC3339 standard
                due = due.astimezone().isoformat()

        if title is None:
            raise ValueError("A title is the bare minimum to create a task")

        self._g.add_task(self.config.task_list_id, title=title, notes=notes, due_date_rfc_3339=due)

    def delete_tasks(self, task_ids: List[str]):
        if len(task_ids) == 0:
            raise NotImplemented

        for _id in task_ids:
            self._g.delete_task(self.config.task_list_id, _id)
            print(f"Deleted task: {_id}")

    def complete_tasks(self, task_ids: List[str]):
        if len(task_ids) == 0:
            raise NotImplemented

        for _id in task_ids:
            self._g.complete_task(self.config.task_list_id, _id)
            print(f"Completed task: {_id}")
