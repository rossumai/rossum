from typing import Optional, Callable

import click

from rossum.common import schema_content_factory


organization = click.option(
    "-o", "--organization-id", type=int, help="Organization ID.", hidden=True
)

name = click.option("-n", "--name", type=str)
email_prefix = click.option(
    "--email-prefix", type=str, help="If not specified, documents cannot be imported via email."
)
bounce_email = click.option(
    "--bounce-email", type=str, help="Unprocessable documents will be bounced to this email."
)
connector_id = click.option(
    "--connector-id", type=str, help="If not specified, queue will not call back a connector."
)

hook_id = click.option(
    "--hook-id",
    type=int,
    multiple=True,
    help="If not specified, hook will not be associated with the queue.",
)

output_file = click.option("-O", "--output-file", type=click.File("wb"))


def schema_content_file(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": click.File("rb"), "help": "Schema file."}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-s", "--schema-content-file", "schema_content_file_", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


schema_content = schema_content_factory(schema_content_file)


def workspace_id(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": int, "help": "Workspace ID."}
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-w", "--workspace-id", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def queue(command: Optional[Callable] = None, related_object: Optional[str] = "object", **kwargs):
    default_kwargs = {
        "type": int,
        "help": f"Queue IDs, which the {related_object} will be associated with.",
        "multiple": True,
        "show_default": True,
    }
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-q", "--queue-id", "queue_ids", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def user(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {
        "type": int,
        "multiple": True,
        "help": "User IDs, which the queues will be associated with.",
    }
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-u", "--user-id", "user_ids", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


service_url = click.option(
    "-u", "--service-url", type=str, required=True, help="Url of the connector endpoint."
)

auth_token = click.option(
    "-t",
    "--auth-token",
    type=str,
    help="Token sent to the connector in the header to ensure authorization. "
    "Generated automatically, if not set manually.",
)

params = click.option("-p", "--params", type=str, help="Query params appended to the service_url.")

asynchronous = click.option(
    "-a", "--asynchronous", type=bool, default=True, help="Affects calling of the connector."
)

active = click.option(
    "--active", type=bool, required=True, default=True, help="Affects whether the hook is notified."
)

events = click.option(
    "-e",
    "--events",
    required=True,
    type=str,
    multiple=True,
    help="List of events, when the hook should be notified.",
)


class OptionRequiredIf(click.Option):
    def full_process_value(self, ctx, value):
        value = super(OptionRequiredIf, self).full_process_value(ctx, value)
        option = self.human_readable_name

        required_params = {
            "webhook": {
                "mutually_exclusive": "function",
                "config": ["config_url", "config_secret", "config_insecure_ssl"],
            },
            "function": {
                "mutually_exclusive": "webhook",
                "config": ["config_runtime", "config_code"],
            },
        }
        if value is None:
            expected_params = required_params.get(ctx.params["hook_type"], [])
            for opt in expected_params["config"]:
                if option in expected_params["config"]:
                    if opt not in [key for key in ctx.params.keys()]:
                        msg = f"Required if hook type is {ctx.params['hook_type']}"
                        raise click.MissingParameter(ctx=ctx, message=msg)
            for opt in required_params[expected_params["mutually_exclusive"]]["config"]:
                if opt in [key for key in ctx.params.keys()]:
                    if ctx.params.get(opt) is not None:
                        non_valid_param = opt
                        msg = f"Illegal usage: --{non_valid_param} cannot be used for the hook type {ctx.params['hook_type']}"
                        raise click.UsageError(ctx=ctx, message=msg)

        return value


hook_type = click.option(
    "-t",
    "--hook-type",
    required=True,
    type=click.Choice(["function", "webhook"]),
    help="Hook type. Possible values: webhook, function.",
)


config_url = click.option(
    "--config-url",
    type=str,
    help="URL endpoint where the message from the hook should be pushed.",
    cls=OptionRequiredIf,
)

config_secret = click.option(
    "--config-secret",
    type=str,
    help="Secret key for authorization of payloads.",
    cls=OptionRequiredIf,
)

config_insecure_ssl = click.option(
    "--config-insecure-ssl",
    type=bool,
    help="Disable SSL certificate verification. (Use only for testing purposes.)",
    cls=OptionRequiredIf,
)

config_code = click.option(
    "--config-code",
    type=click.Path(readable=True),
    help="Path to the file with the string-serialized source code to be executed.",
    cls=OptionRequiredIf,
)

config_runtime = click.option(
    "--config-runtime", type=str, help="Runtime used to execute code.", cls=OptionRequiredIf
)

sideload = click.option(
    "-s",
    "--sideload",
    default=[],
    type=str,
    multiple=True,
    help="List of related objects that should be included in the hook request.",
)


def group(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {
        "default": "annotator",
        "type": click.Choice(["annotator", "admin", "manager", "viewer"]),
        "help": "Permission group.",
        "show_default": True,
    }
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-g", "--group", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def locale(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {
        "default": "en",
        "type": click.Choice(["en", "cs"]),
        "help": "UI locale",
        "show_default": True,
    }
    kwargs = {**default_kwargs, **kwargs}
    decorator = click.option("-l", "--locale", **kwargs)
    if command is None:
        return decorator
    return decorator(command)


def password(command: Optional[Callable] = None, **kwargs):
    default_kwargs = {"type": str, "required": False, "help": "Generated, if not specified."}
    kwargs = {**default_kwargs, **kwargs}
    if "help" in kwargs and kwargs["help"] is None:
        kwargs.pop("help")
    decorator = click.option("-p", "--password", **kwargs)
    if command is None:
        return decorator
    return decorator(command)
