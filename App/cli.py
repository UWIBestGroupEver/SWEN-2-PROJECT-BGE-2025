import click
from flask.cli import AppGroup

from App.controllers.application import decide

def register_employer_commands(app): #moved from wsgi.py, so that test-created apps can also use these commands
    """Register employer CLI commands onto the provided Flask app."""
    employer_cli = AppGroup('employer', help='Employer object commands')

    @employer_cli.command("accept_application", help="Employer accepts an application")
    @click.argument("employer_id", default=1)
    @click.argument("application_id", default=1)
    def accept_application_command(employer_id, application_id):
        application = decide(employer_id, application_id, "accepted")
        if application:
            print(f'Application {application_id} accepted!')
        else:
            print(f'Application {application_id} could not be accepted')

    @employer_cli.command("reject_application", help="Employer rejects an application")
    @click.argument("employer_id", default=1)
    @click.argument("application_id", default=1)
    def reject_application_command(employer_id, application_id):
        application = decide(employer_id, application_id, "rejected")
        if application:
            print(f'Application {application_id} rejected.')
        else:
            print(f'Application {application_id} could not be rejected')

    app.cli.add_command(employer_cli)
# ...existing code...