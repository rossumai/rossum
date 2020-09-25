from typing import Tuple, Optional, Dict, Any, List

import click
from pathlib import Path
from elisctl import option, argument
from elisctl.lib import QUEUES
from elisctl.lib.api_client import ELISClient
from tabulate import tabulate


def cleanup_config(config):
    new_config = {}
    for key, value in config.items():
        if key.startswith("config_"):
            new_key = key.replace("config_", "")
            new_config[new_key] = value
    config = {key: value for key, value in new_config.items() if value is not None}
    if "code" in config.keys():
        config["code"] = Path(config["code"]).read_text()
    return config


@click.group("hook")
def cli() -> None:
    pass


@cli.command(name="create", help="Create a hook object.")
@argument.name
@option.hook_type
@option.queue(
    help="Queue IDs, that the hook will be associated with. "
    "Required field - will be assigned to an only queue automatically if not specified."
)
@option.active
@option.events
@option.config_url
@option.config_secret
@option.config_insecure_ssl
@option.config_code
@option.config_runtime
@click.pass_context
def create_command(
    ctx: click.Context,
    name: str,
    hook_type: str,
    queue_ids: Tuple[int, ...],
    active: bool,
    events: Tuple[str, ...],
    **kwargs,
) -> None:
    with ELISClient(context=ctx.obj) as elis:

        if not queue_ids:
            queue_urls = [elis.get_queue()["url"]]
        else:
            queue_urls = []
            for id_ in queue_ids:
                queue_dict = elis.get_queue(id_)
                if queue_dict:
                    queue_urls.append(queue_dict["url"])

        config = {**kwargs}
        config = cleanup_config(config)

        response = elis.create_hook(
            name=name,
            hook_type=hook_type,
            queues=queue_urls,
            active=active,
            events=list(events),
            config=config,
        )

        additional_fields = [
            value
            for key, value in response["config"].items()
            if key not in ["code", "runtime", "insecure_ssl"]
        ]

        regular_fields = (
            f"{response['id']}, {response['name']}, {response['queues']}, {response['events']}"
        )
        click.echo(
            regular_fields + ", " + f"{', '.join(map(str,additional_fields))}"
            if additional_fields != []
            else regular_fields
        )


@cli.command(name="list", help="List all hooks.")
@click.pass_context
def list_command(ctx: click.Context):
    with ELISClient(context=ctx.obj) as elis:
        hooks_list = elis.get_hooks((QUEUES,))

        headers = ["id", "name", "events", "queues", "active"]

        def get_row(hook: dict) -> List[str]:
            fields = [
                hook["id"],
                hook["name"],
                ", ".join(e for e in hook["events"]),
                ", ".join(str(q.get("id", "")) for q in hook["queues"]),
                hook["active"],
            ]

            additional = ["url", "insecure_ssl", "secret"]

            for field in additional:
                if field in hook["config"]:
                    fields.append(hook["config"][field])

            for header in additional:
                if header not in headers:
                    headers.append(header)

            hook_list = [item for item in fields]
            return hook_list

    table = [get_row(hook) for hook in hooks_list]

    click.echo(tabulate(table, headers=headers))


@cli.command(name="change", help="Update a hook object.")
@argument.id_
@option.queue(related_object="hook")
@option.name
@option.hook_type
@option.events
@option.active
@option.config_url
@option.config_secret
@option.config_insecure_ssl
@option.config_code
@option.config_runtime
@click.pass_context
def change_command(
    ctx: click.Context,
    id_: int,
    queue_ids: Tuple[int, ...],
    name: Optional[str],
    hook_type: str,
    events: Tuple[str, ...],
    active: Optional[bool],
    **kwargs,
) -> None:

    config = {**kwargs}
    config = cleanup_config(config)

    if not any([queue_ids, name, active, events, config]):
        return

    data: Dict[str, Any] = {"config": {}}

    with ELISClient(context=ctx.obj) as elis:

        if queue_ids:
            data["queues"] = [elis.get_queue(queue)["url"] for queue in queue_ids]
        if name is not None:
            data["name"] = name
        if hook_type:
            data["type"] = hook_type
        if active is not None:
            data["active"] = active
        if events:
            data["events"] = list(events)
        if config:
            data["config"] = config

        elis.patch(f"hooks/{id_}", data)


@cli.command(name="delete", help="Delete a hook.")
@argument.id_
@click.confirmation_option(
    prompt="This will delete the hook deployed on the queue. Do you want to continue?"
)
@click.pass_context
def delete_command(ctx: click.Context, id_: str) -> None:
    with ELISClient(context=ctx.obj) as elis:
        url = elis.url
        elis.delete(to_delete={f"{id_}": f"{url}/hooks/{id_}"}, item="hook")
