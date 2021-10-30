from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Optional, Tuple, Union
from . import APIObject


@dataclass(frozen=True)
class Sideload:
    NOT_SET = "NOT_SET"

    plural: str
    singular: str = NOT_SET

    def __post_init__(self) -> None:
        if self.singular is self.NOT_SET:
            # https://docs.python.org/3/library/dataclasses.html#frozen-instances
            object.__setattr__(self, "singular", self.plural.rstrip("s"))

    @staticmethod
    def _parse_query_array(array: str) -> List[str]:
        return [item.strip() for item in array.split(",") if item.strip()]

    def setup_query(self, query: dict) -> None:
        query_sideloads = self._parse_query_array(query.get("sideload", ""))
        if str(self) not in query_sideloads:
            query_sideloads.append(str(self))
        query["sideload"] = ",".join(query_sideloads)

    @staticmethod
    def get_mapping(objects: List[dict]) -> dict:
        return {obj["url"]: obj for obj in objects}

    def __str__(self) -> str:
        return self.plural


@dataclass(frozen=True)
class Content(Sideload):
    schema_ids: Union[Tuple[str], Tuple[()]] = ()

    def setup_query(self, query: dict) -> None:
        if not self.schema_ids:
            # Content sideloading without any schema ID has no effect."
            return
        super().setup_query(query)
        query_schema_ids = self._parse_query_array(query.get("content.schema_id", ""))
        for schema_id in self.schema_ids:
            if schema_id not in query_schema_ids:
                query_schema_ids.append(schema_id)
        query["content.schema_id"] = ",".join(query_schema_ids)

    @staticmethod
    def get_mapping(objects: List[dict]) -> dict:
        mapping: Dict[str, List[dict]] = {}
        for obj in objects:
            mapping.setdefault(obj["url"].rsplit("/", 1)[0], []).append(obj)
        return mapping

    def __call__(self, *schema_ids: Iterable[str]) -> "Content":
        return replace(self, schema_ids=schema_ids)


def to_sideloads(
    sideloads: Optional[Iterable[Union[APIObject, Sideload, str]]]
) -> Iterable[Sideload]:
    def cast(sideload: Union[APIObject, Sideload, str]) -> Sideload:
        if isinstance(sideload, APIObject):
            return Sideload(sideload.plural, sideload.singular)
        elif isinstance(sideload, Sideload):
            return sideload
        elif isinstance(sideload, str):
            return Sideload(sideload)
        else:
            raise TypeError

    return [cast(sideload) for sideload in sideloads or []]


CONTENT = Content("content")
