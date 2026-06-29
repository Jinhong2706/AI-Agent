"""
Todo List CLI - Complete Example
A simple command-line todo list application.
"""

tasks = []


def show_menu():
    """Display the main menu."""
    print("\n=== Todo List ===")
    print("1. Add task")
    print("2. View tasks")
    print("3. Remove task")
    print("4. Quit")


def add_task():
    """Prompt user to enter a new task and add it to the list."""
    task = input("Enter task: ").strip()
    if task:
        tasks.append(task)
        print("Task added!")
    else:
        print("Task cannot be empty!")


def view_tasks():
    """Display all tasks in the list."""
    if len(tasks) == 0:
        print("No tasks yet!")
    else:
        print("\n--- Your Tasks ---")
        for i in range(len(tasks)):
            print(f"{i + 1}. {tasks[i]}")


def remove_task():
    """Prompt user for a task number and remove it."""
    if len(tasks) == 0:
        print("No tasks to remove!")
        return

    view_tasks()
    try:
        task_num = int(input("Enter task number to remove: "))
        index = task_num - 1
        if 0 <= index < len(tasks):
            removed = tasks.pop(index)
            print(f"Removed: {removed}")
        else:
            print("Invalid task number!")
    except ValueError:
        print("Please enter a valid number!")


def main():
    """Main program loop."""
    print("Welcome to Todo List CLI!")
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_task()
        elif choice == "2":
            view_tasks()
        elif choice == "3":
            remove_task()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
