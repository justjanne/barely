"""
functions that are available to be called
from the cli by the user.
"""
import os
import sys
import click
import platform
from pathlib import Path


def init():
    # try to find the config.yaml
    if os.path.exists("config.yaml"):
        # export the cwd as an environment variable
        appdir = get_appdir()
        os.environ["barely"] = os.getcwd()
        os.environ["barely_appdir"] = appdir

        make_dirs(appdir)
    else:
        print("barely :: could not find 'config.yaml'. Exiting")
        sys.exit()


def get_appdir():
    _platform = platform.system()

    if _platform == ("Linux" or "Darwin"):
        home = os.path.expanduser("~")
        return os.path.join(home, ".barely")
    elif _platform == "Windows":
        print("Windows")
    else:
        sys.exit("Running on unknown platform.")


def make_dirs(appdir):
    needed = [
        os.path.join("plugins", "content"),
        os.path.join("plugins", "backup"),
        os.path.join("plugins", "publication"),
        "blueprints"
    ]

    for path in needed:
        Path(os.path.join(appdir, path)).mkdir(parents=True, exist_ok=True)


@click.group(invoke_without_command=True)
@click.pass_context
def run(context):
    """
    barely reduces static website development to its key parts,
    by automatically rendering jinja2 templates and Markdown content
    into HTML. A simple plugin interface allows for easy extensibility,
    and the built-in live web server makes on-the-fly development as
    comfortable as possible.
    """
    if context.invoked_subcommand is None:
        live()


@run.command()
@click.option("--verbose", "-v", help="print the logs from the live server", is_flag=True)
def live(verbose):
    """starts a live server, opens your project in the browser and auto-refreshes a page whenever it, its template, or the media it includes are modified."""
    init()

    from barely.core.EventHandler import EventHandler
    from barely.core.ChangeTracker import ChangeTracker
    from barely.plugins.PluginManager import PluginManager

    PM = PluginManager()
    EH = EventHandler()
    EH.init_pipeline(PM)

    CT = ChangeTracker()
    CT.register_handler(EH)
    CT.verbose = verbose

    CT.track()
    aftermath(PM)


@run.command()
def rebuild():
    """(re)build the entire project"""
    init()

    from barely.core.EventHandler import EventHandler
    from barely.plugins.PluginManager import PluginManager

    PM = PluginManager()
    EH = EventHandler()
    EH.init_pipeline(PM)

    EH.force_rebuild()
    aftermath(PM)


def aftermath(PM):
    print("barely ..")
    print("barely :: Do you want to Publish / Backup / do both?")
    action = input("       -> [n]othing | [p]ublish | [b]ackup | *[Y]do both :: ").lower()

    if action.startswith("p") or action.startswith("y") or action == "":
        print("barely :: publishing...")
        PM.hook_publication()
        print("       -> ...done.")
    if action.startswith("b") or action.startswith("y") or action == "":
        print("barely :: backuping...")
        PM.hook_backup()
        print("       -> ...done.")

    print("barely :: exited.")


@run.command()
@click.option("--keep-files", "-k", help="keep the files generated by the testsuite", is_flag=True)
@click.option("--verbose", "-v", help="diable the unittest buffer", is_flag=True)
def test(verbose, keep_files):
    """run the testsuite to verify the install"""
    # import coverage
    import unittest
    import shutil

    appdir = get_appdir()
    testdir = os.path.join(appdir, "TESTFILES")

    testsuite_dir = os.path.join(os.path.dirname(__file__), "tests")
    shutil.copytree(os.path.join(testsuite_dir, "ressources"), testdir)

    os.chdir(testdir)
    os.environ["barely"] = testdir
    os.environ["barely_appdir"] = appdir

    loader = unittest.TestLoader()
    suite = loader.discover(testsuite_dir)

    # cov = coverage.Coverage()
    # cov.start()
    buffer = not verbose
    runner = unittest.TextTestRunner(buffer=buffer)
    runner.run(suite)

    # cov.stop()
    # cov.save()
    # cov.html_report()
    if not keep_files:
        shutil.rmtree(testdir)


if __name__ == "__main__":
    test()
