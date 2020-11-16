import click

from rossum.lib.api_client import RossumClient


@click.group("password")
def cli() -> None:
    pass


@cli.command(name="change", help="Change password of the current user.")
@click.password_option()
@click.pass_context
def change_command(ctx: click.Context, password: str) -> None:
    with RossumClient(context=ctx.obj) as rossum:
        result = rossum.change_user_password(password)
        click.echo(result.get("detail"))
        click.echo('Run "rossum configure" to update existing credentials.')


@cli.command(name="reset", help="Reset password for other user.")
@click.argument("email")
@click.pass_context
def reset_command(ctx: click.Context, email: str) -> None:
    with RossumClient(context=ctx.obj) as rossum:
        result = rossum.reset_user_password(email)
        click.echo(result.get("detail"))
