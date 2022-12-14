import argparse

from gt.app import App
from gt.gtaskconfig import Config


def main():
    conf = Config()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="command")

    # Command for the task lists
    list_task_lists_parser = subparsers.add_parser("lists")
    list_task_lists_parser.add_argument("-c",
                                        "--change",
                                        action="store_true",
                                        help="You are able to change the default list")

    # Command for the tasks in a list
    list_tasks_parser = subparsers.add_parser("list")
    list_tasks_parser.add_argument("-s", "--sort", choices=["due", "update"], help="What date to sort by?")
    list_tasks_parser.add_argument("-c", "--completed", action="store_true", help="What date to sort by?")
    list_tasks_parser.add_argument("--head", type=int, default=1000, help="Display the first N entries in the table")

    # Create a new task
    add_task_parser = subparsers.add_parser("add")
    add_task_parser.add_argument("prompt",
                                 nargs="*",
                                 type=str,
                                 default=None,
                                 help="""Prompt for creating the task.

                                 Examples:
                                 'This is a note' OR
                                 'This is a note ~ tomorrow 11AM' OR
                                 'This is a note ~ Some extra note ~ tomorrow 11AM'
                                 """)

    delete_task_parser = subparsers.add_parser("delete")
    delete_task_parser.add_argument("task_ids", nargs="+", type=str, help="Task ids to delete")

    complete_task_parser = subparsers.add_parser("comp")
    complete_task_parser.add_argument("task_ids", nargs="+", type=str, help="Task ids to complete")

    args = parser.parse_args()

    app = App(config=conf)
    if args.command == "lists":
        app.list_task_lists(include_change_prompt=args.change)
    elif args.command == "list":
        app.list_tasks(args.sort == "update", args.sort == "due", head=args.head, show_completed=args.completed)
    elif args.command == "add":
        app.add_task_to_list(prompt_input=args.prompt)
    elif args.command == "delete":
        app.delete_tasks(task_ids=args.task_ids)
    elif args.command == "comp":
        app.complete_tasks(task_ids=args.task_ids)


if __name__ == '__main__':
    main()
