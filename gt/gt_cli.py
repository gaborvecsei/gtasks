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
    list_tasks_parser.add_argument("--head", type=int, default=1000, help="Display the first N entries in the table")

    args = parser.parse_args()

    app = App(config=conf)
    if args.command == "lists":
        app.list_task_lists(include_change_prompt=args.change)
    elif args.command == "list":
        app.list_tasks(args.sort == "update", args.sort == "due", head=args.head)


if __name__ == '__main__':
    main()
