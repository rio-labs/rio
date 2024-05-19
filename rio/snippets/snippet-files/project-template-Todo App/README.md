## Todo App

This example shows off a simple Todo app which allows you to create tasks that
can later be marked as completed.

## Lessons

In this example you can see how to:

-   Persistently save data across sessions
-   Make components communicate via custom events

## Components

The example is composed of 3 main components:

1. `TodoItemComponent`: Displays the title and creation date of a todo item, and
   also comes with buttons that lets the user mark it as completed or delete it.
2. `NewTodoItemInput`: Allows the user to create a new todo item.
3. `TodoListPage`: Combines the 2 components above and adds all the logic
   necessary for saving/loading the todo list.
