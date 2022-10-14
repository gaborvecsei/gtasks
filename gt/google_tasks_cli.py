import argparse
import datetime
import os.path
import re
from typing import List, Optional

import dateutil
import gtaskconfig
import pandas as pd
from dateutil import parser
from google.api_core.datetime_helpers import from_rfc3339
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/tasks']


class GoogleTasks:

    def __init__(self, client_secret_file: str = "client_secret.json") -> None:
        self._client_secret_file = client_secret_file
        self._service = None

    @staticmethod
    def _auth(secret_json_file_path: str, token_json_file_name: str = "token.json") -> Credentials:
        """
        The file token.json stores the user's access and refresh tokens, and is
        created automatically when the authorization flow completes for the first
        time.

        Args:
            secret_json_file_path (str): 
            token_json_file_name (str): 

        Returns:
            credential object
        """

        creds: Optional[Credentials] = None

        # Auth by token if it exists
        if os.path.exists(token_json_file_name):
            creds = Credentials.from_authorized_user_file(token_json_file_name, SCOPES)
        # If there are no (valid) credentials available, let the user log in - but we need the client secret for this
        if not creds or not creds.valid:
            # Refresh token if it is expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(secret_json_file_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_json_file_name, 'w') as token:
                token.write(creds.to_json())

        return creds

    @property
    def service(self):
        """
        Returns the service object, and if it does not exists, it performs authentication

        Returns:
            service object
        """

        if self._service is None:
            creds = self._auth(self._client_secret_file, "token.json")
            self._service = build("tasks", "v1", credentials=creds)
        return self._service

    @service.setter
    def service(self):
        raise NotImplementedError("You can't set this variable")

    def get_task_lists(self, max_results: int = 100) -> List[dict]:
        if max_results > 100:
            raise ValueError(
                "Maximum is 100: https://google-api-client-libraries.appspot.com/documentation/tasks/v1/python/latest/tasks_v1.tasklists.html#list"
            )
        results = self.service.tasklists().list(maxResults=max_results).execute()
        items = results.get('items', [])
        return items

    def list_tasks(self,
                   task_list_id: str,
                   show_completed: bool = False,
                   show_deleted: bool = False,
                   show_hidden: bool = False,
                   max_results: int = 100) -> List[dict]:
        if max_results > 100:
            raise ValueError(
                "Maximum is 100: https://google-api-client-libraries.appspot.com/documentation/tasks/v1/python/latest/tasks_v1.tasks.html#list"
            )
        results = self.service.tasks().list(tasklist=task_list_id,
                                            showCompleted=show_completed,
                                            showDeleted=show_deleted,
                                            showHidden=show_hidden,
                                            maxResults=max_results).execute()
        items = results.get("items", [])
        return items


class App:

    def __init__(self, config: gtaskconfig.Config) -> None:
        self.config: gtaskconfig.Config = config
        self._g: GoogleTasks = GoogleTasks()

    @staticmethod
    def _parse_rfc3339_date_str(d: dict, k: str) -> Optional[datetime.datetime]:
        s = d.get(k, None)
        date = None
        if s:
            # Based on the documentation rfc3339 standard is used
            date = from_rfc3339(s)
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

    def list_task_lists(self, include_change_prompt: bool = False) -> None:
        task_lists: List[dict] = self._g.get_task_lists()

        table = Table(show_footer=False, show_header=True, header_style="bold")
        table.add_column("Nb.", no_wrap=True, justify="center")
        table.add_column("Title", no_wrap=True, justify="left")
        table.add_column("ID", no_wrap=True, justify="left")
        table.title = "Google Tasks - not completed"
        table.caption = "[i]https://mail.google.com/tasks/canvas[/]"

        for i, item in enumerate(task_lists):
            table.add_row(str(i), item["title"], item["id"])

        console = Console()
        console.print(table)

        print(f"The default list is: {self.config.task_list_id}")

        if include_change_prompt:
            chosen_list_number: int = int(Prompt.ask("Which task list to use (inter the Nb."))
            try:
                chosen_list_id = task_lists[chosen_list_number]["id"]
                self.config.task_list_id = chosen_list_id
                print("Default task list id is set, you can play around with the other commands")
            except IndexError:
                print("This Nb. does not exists in the list")

    def list_tasks(self, sort_by_updatetime: bool = False, sort_by_due_date: bool = True) -> None:
        if sum([sort_by_due_date, sort_by_updatetime]) > 1:
            raise ValueError("Only 1 of them could be True")

        # Retrieve the tasks
        tasks: List[dict] = self._g.list_tasks(self.config.task_list_id)
        tasks = self._process_tasks(tasks)

        if sort_by_updatetime:
            tasks = sorted(tasks, key=lambda x: x["updated"], reverse=True)
        elif sort_by_due_date:
            # Sorting trick for Nones: https://stackoverflow.com/a/18411610/5108062
            tasks = sorted(tasks, key=lambda x: (x["due"] is None, x["due"]), reverse=False)

        # Visualization

        table = Table(show_footer=False, show_header=True, header_style="bold")

        table.add_column("Due", no_wrap=True, justify="center")
        # table.add_column("Updated", no_wrap=True, style="dim")
        table.add_column("Days since\nupdate", no_wrap=True, justify="center", style="dim")
        table.add_column("Task", justify="left")

        table.title = "Google Tasks - not completed"
        table.caption = "[i]https://mail.google.com/tasks/canvas[/]"

        for task in tasks:
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

            title = task["title"]
            if task["expired"]:
                title = f"[red]{title}[/red]"
            if task["prio"]:
                title = f"[reverse] {title} [/reverse]"

            elapsed_days = str(task["elapsed_days"])

            table_row = [
                due_str,
                # updated_str,
                elapsed_days,
                title
            ]
            table.add_row(*table_row)

        console = Console()
        console.print(table)


def main():
    import pudb; pudb.set_trace()
    conf = gtaskconfig.Config()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="command")

    list_task_lists_parser = subparsers.add_parser("lists")
    list_task_lists_parser.add_argument("-c",
                                        "--change",
                                        action="store_true",
                                        help="You are able to change the default list")

    list_tasks_parser = subparsers.add_parser("list")
    list_tasks_parser.add_argument("-s", "--sort", choices=["due", "update"], help="What date to sort by?")

    args = parser.parse_args()

    app = App(config=conf)
    if args.command == "lists":
        app.list_task_lists(include_change_prompt=args.change)
    elif args.command == "list":
        app.list_tasks(args.sort == "update", args.sort == "due")


if __name__ == '__main__':
    main()
