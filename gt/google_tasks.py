import os.path
from pathlib import Path
from typing import List, Optional, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import HttpRequest, build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/tasks']


class GoogleTasks:

    def __init__(self, client_secret_file_path: Path, token_file_path: Path) -> None:
        self._client_secret_file_path: Path = client_secret_file_path
        self._token_file_path: Path = token_file_path
        self._service = None

    @staticmethod
    def _auth(secret_json_file_path: Union[str, Path], token_json_file_path: Union[str, Path]) -> Credentials:
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
        if os.path.exists(token_json_file_path):
            creds = Credentials.from_authorized_user_file(token_json_file_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in - but we need the client secret for this
        if not creds or not creds.valid:
            # Refresh token if it is expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(secret_json_file_path), SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(str(token_json_file_path), 'w') as token:
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
            creds = self._auth(self._client_secret_file_path, self._token_file_path)
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
        if show_completed:
            # Completed can only show when hidden is shown
            show_hidden = show_completed

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

    def add_task(self,
                 tasklist_id: str,
                 title: str,
                 notes: Optional[str] = None,
                 due_date_rfc_3339: Optional[str] = None) -> dict:
        body = {"status": "needsAction", "title": title}
        if notes is not None:
            body["notes"] = notes
        if due_date_rfc_3339 is not None:
            body["due"] = due_date_rfc_3339

        ret: dict = self.service.tasks().insert(tasklist=tasklist_id, body=body).execute()
        return ret

    def delete_task(self, task_list_id: str, task_id: str) -> None:
        self.service.tasks().delete(tasklist=task_list_id, task=task_id).execute()

    def complete_task(self, tasklist_id: str, task_id: str) -> None:
        # TODO: do we need to update the updatetime or is it updated automatically?
        body = {"status": "completed", "id": task_id}
        _ = self.service.tasks().update(tasklist=tasklist_id, task=task_id, body=body).execute()
