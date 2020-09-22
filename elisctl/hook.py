from typing import Tuple, Optional, Dict, Any, List

import click
from pathlib import Path
from elisctl import option, argument
from elisctl.lib import QUEUES
from elisctl.lib.api_client import ELISClient
from tabulate import tabulate


def get_compiled_config(
    config_url: str,
    config_secret: str,
    config_insecure_ssl: bool,
    config_code: str,
    config_runtime: str,
):
    config: Dict[str, Any] = {
        "url": config_url,
        "secret": config_secret,
        "insecure_ssl": config_insecure_ssl,
        "code": config_code,
        "runtime": config_runtime,
    }
    new_config = {key: value for key, value in config.items() if value is not None}
    return new_config


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
    config_url: str,
    config_secret: str,
    config_insecure_ssl: bool,
    config_code: str,
    config_runtime: str,
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

        new_config = get_compiled_config(
            config_url, config_secret, config_insecure_ssl, config_code, config_runtime
        )

        if hook_type == "webhook":

            response = elis.create_hook(
                name=name,
                hook_type=hook_type,
                queues=queue_urls,
                active=active,
                events=list(events),
                config=new_config,
            )
            click.echo(
                f"{response['id']}, {response['name']}, {response['queues']}, {response['events']}, {response['config']['url']}, {response['config']['secret']}"
            )

        elif hook_type == "function":
            new_config["code"] = Path(new_config["code"]).read_text()
            response = elis.create_hook(
                name=name,
                hook_type=hook_type,
                queues=queue_urls,
                active=active,
                events=list(events),
                config=new_config,
            )
            click.echo(
                f"{response['id']}, {response['name']}, {response['queues']}, {response['events']}"
            )


@cli.command(name="list", help="List all hooks.")
@option.hook_type
@click.pass_context
def list_command(ctx: click.Context, hook_type: str):
    with ELISClient(context=ctx.obj) as elis:
        hooks_list = elis.get_hooks(hook_type, (QUEUES,))

        if hook_type == "webhook":
            headers = ["id", "name", "events", "queues", "active", "url", "insecure_ssl"]
        elif hook_type == "function":
            headers = ["id", "name", "events", "queues", "active"]

    def get_row(hook: dict, hook_type: str) -> List[str]:
        if hook_type == "webhook":
            res = [
                hook["id"],
                hook["name"],
                ", ".join(e for e in hook["events"]),
                ", ".join(str(q.get("id", "")) for q in hook["queues"]),
                hook["active"],
                hook["config"]["url"],
                hook["config"]["insecure_ssl"],
            ]
            try:
                secret_key = hook["config"]["secret"]
            except KeyError:
                pass
            else:
                res.append(secret_key)
                if "secret" not in headers:
                    headers.append("secret")

        elif hook_type == "function":
            res = [
                hook["id"],
                hook["name"],
                ", ".join(e for e in hook["events"]),
                ", ".join(str(q.get("id", "")) for q in hook["queues"]),
                hook["active"],
            ]

        hook_list = [str(item) for item in res]
        return hook_list

    table = [get_row(hook, hook_type) for hook in hooks_list]

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
    config_url: str,
    config_secret: str,
    config_insecure_ssl: bool,
    config_code: str,
    config_runtime: str,
) -> None:
    config = get_compiled_config(
        config_url, config_secret, config_insecure_ssl, config_code, config_runtime
    )

    if not any([queue_ids, name, active, events, config]):
        return

    data: Dict[str, Any] = {"config": {}}

    with ELISClient(context=ctx.obj) as elis:

        if hook_type == "webhook":
            config_url = config["url"]
            config_secret = config["secret"]
            config_insecure_ssl = config["insecure_ssl"]

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
            if config_url is not None:
                data["config"].update({"url": config_url})
            if config_secret is not None:
                data["config"].update({"secret": config_secret})
            if config_insecure_ssl is not None:
                data["config"].update({"insecure_ssl": config_insecure_ssl})

            elis.patch(f"hooks/{id_}", data)

        elif hook_type == "function":
            config_code = Path(config["code"]).read_text()
            config_runtime = config["runtime"]

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
            if config_code is not None:
                data["config"].update({"code": config_code})
            if config_runtime is not None:
                data["config"].update({"runtime": config_runtime})

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
