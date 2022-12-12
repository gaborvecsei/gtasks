# Google Tasks CLI Tool

**WIP - IN ACTIVE DEVELOPMENT**

**!!! The readme is just like a TODO list, this will changed a lot**

## Setup

Needs API setup in the Google Dev Console

## Functions

- `gt init`: Initialize the tool
- `list` functions:
    - `gt list`: Lists not completed tasks
    - `gt list -a`: Lists completed and non-completed tasks
    - `gt list -c`: Lists only completed tasks
- `gt add <TASK MESSAGE | DATE>`: Adds a new task with a due date if defined. `|` separates the message from the date.
If date is not defined (and no `|`) then it will be created without a due date
- `gt snooze`: Update the due date where there was a due date and it is past the current day.
*Unfortunately we cannot read or modify the time info only the date...*
    - Update rule
        - If message contains #prio, then +1 day added. If updated time still outdated, then +1 day added to now
        - By default +2 days added. If updated time still outdated, then +2 days added to now
        - If message contains #noprio, then +5 days are added. If updated time ...

- General rules of visualization:
    - Tasks are ordered by update date
    - Due date
        - If a task is over it's due date the date field is `red`
        - If a due date is in the future it'll be `blue`
        - If not due date, then its the `default color`

## Config

The configuration `json` file should be located at `$HOME/.gtasksconfig.json` or where the command is called `./.gtasksconfig.json`

## Misc

- PyDoc documentation: https://developers.google.com/resources/api-libraries/documentation/tasks/v1/python/latest/index.html
