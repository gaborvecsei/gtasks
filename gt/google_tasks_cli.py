import datetime
import os.path
import re
from typing import List, Optional

import dateutil
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

    def __init__(self, task_list_id: str) -> None:
        self.task_list_id: str = task_list_id
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

        # Sort tasks based on update time
        tasks = sorted(tasks, key=lambda x: x["updated"], reverse=True)

        return tasks

    def list_tasks(self) -> None:
        # Retrieve the tasks
        tasks: List[dict] = self._g.list_tasks(self.task_list_id)
        tasks = self._process_tasks(tasks)

        # Visualization

        table = Table(show_footer=False, show_header=True, header_style="bold")

        table.add_column("Due", no_wrap=True)
        # table.add_column("Updated", no_wrap=True, style="dim")
        table.add_column("Days since\nupdate", no_wrap=True, justify="center", style="dim")
        table.add_column("Task", justify="left")

        table.title = "Google Tasks - not completed"
        table.caption = "[i]https://mail.google.com/tasks/canvas[/]"

        for task in tasks:
            due_date: datetime.datetime = task["due"]
            due_str = ""
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
    app = App(task_list_id="MTA0NDY1OTUxNjkwNTc2OTg0NzY6MDow")
    app.list_tasks()


if __name__ == '__main__':
    main()
