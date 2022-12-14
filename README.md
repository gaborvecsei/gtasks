# Google Tasks CLI Tool

**WIP - IN ACTIVE DEVELOPMENT**

**!!! The readme is just like a TODO list, this will changed a lot**

## Setup

Needs API setup in the Google Dev Console - then you'll need to download the `json` file and define it's path
in the config (see below)

### Config

The configuration `json` file should be located at `$HOME/.gtasksconfig.json` or where the command is called `./.gtasksconfig.json`

```json
{
  "default_list_id": "DON'T FILL IT",
  "auth": {
    "token_path": "FOLDER/token.json",
    "client_secret_path": "FOLDER/client_secret.json"
  }
}
```

## Functions

- `gt lists`: Show the lists you created
- `list` functions:
    - `gt list`: Lists not completed tasks
    - `gt list -c`: Lists only completed tasks
- `gt add <PROMPT>`: Adds a new task with a due date if defined. `~` separates the message from the date.
    - Examples:
        - `gt add This is a test task ~ with some notes ~ tomorrow 2PM`
        - `gt add This is a test task ~ tomorrow 2PM`
        - `gt add This is a test task`
- `gt delete`: Delete tasks based on their ids
- `gt comp`: Complete tasks based on their ids
- `gt snooze`: **TODO** Update the due date where there was a due date and it is past the current day.
*Unfortunately we cannot read or modify the time info only the date...*
    - Update rule
        - If message contains #prio, then +1 day added. If updated time still outdated, then +1 day added to now
        - By default +2 days added. If updated time still outdated, then +2 days added to now
        - If message contains #noprio, then +5 days are added. If updated time ...

- General rules of visualization: **TODO**
    - Tasks are ordered by update date
    - Due date
        - If a task is over it's due date the date field is `red`
        - If a due date is in the future it'll be `blue`
        - If not due date, then its the `default color`

## Misc

- PyDoc documentation: https://developers.google.com/resources/api-libraries/documentation/tasks/v1/python/latest/index.html
