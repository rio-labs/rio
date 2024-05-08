# How do I create a new project with Rio?

To create a new project with Rio, you can use the `rio new` command. This
command will ask you a couple questions about your project and then create a
new directory with the project structure.

In your terminal, run the following command:

```bash
# Change into the directory where you want to create the new project
cd /path/to/your/projects

# Run the `rio new` command
rio new

# On some platforms, python packages aren't available right in the terminal. If
# the command above doesn't work, try one of the following:
python -m rio new
python3 -m rio new
py -m rio new
```

Rio will ask you a few questions, like the project name, and whether you'd like
to create a website, or app. Once you've answered the questions, you will
see a directory containing your project files.

You can take your new project for a spin using `rio run`.

```bash
# Change into the new project directory
cd project-name

# Run the project
rio run

# Once again, if the command above doesn't work, try one of the following:
python -m rio run
python3 -m rio run
py -m rio run
```
