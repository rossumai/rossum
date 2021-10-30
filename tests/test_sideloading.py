import pytest
from typing import Any, Iterable, List, Union

from rossum.lib import APIObject, ANNOTATIONS
from rossum.lib.sideloading import CONTENT, Sideload, to_sideloads

from tests.conftest import ANNOTATIONS_URL, DOCUMENTS_URL


@pytest.mark.parametrize(
    "sideloads, raises, expected",
    [
        (
            ["documents", CONTENT("document_id"), ANNOTATIONS],
            False,
            [Sideload("documents"), CONTENT("document_id"), Sideload("annotations")],
        ),
        (["documents", 5], True, []),
        (None, False, []),
    ],
)
def test_to_sideloads(
    sideloads: Iterable[Any], raises: bool, expected: Iterable[Union[APIObject, Sideload, str]]
) -> None:
    if raises:
        with pytest.raises(TypeError):
            to_sideloads(sideloads)
    else:
        assert to_sideloads(sideloads) == expected


@pytest.mark.parametrize(
    "sideload, query, expected",
    [
        (Sideload("documents"), {}, {"sideload": "documents"}),
        (Sideload("documents"), {"sideload": "modifiers"}, {"sideload": "modifiers,documents"}),
        (CONTENT, {}, {}),
        (CONTENT("document_id"), {}, {"sideload": "content", "content.schema_id": "document_id"}),
        (
            CONTENT("order_id"),
            {"sideload": "content", "content.schema_id": "document_id"},
            {"sideload": "content", "content.schema_id": "document_id,order_id"},
        ),
        (
            CONTENT("order_id"),
            {"sideload": "documents,content", "content.schema_id": "document_id"},
            {"sideload": "documents,content", "content.schema_id": "document_id,order_id"},
        ),
    ],
)
def test_setup_sideload_query(sideload: Sideload, query: dict, expected: dict) -> None:
    sideload.setup_query(query)
    assert query == expected


@pytest.mark.parametrize(
    "sideload, objects, expected",
    [
        (
            Sideload("documents"),
            [
                {"url": f"{DOCUMENTS_URL}/1", "name": "Document #1"},
                {"url": f"{DOCUMENTS_URL}/2", "name": "Document #2"},
                {"url": f"{DOCUMENTS_URL}/2", "name": "Document #2: Last wins!"},
            ],
            {
                f"{DOCUMENTS_URL}/1": {"url": f"{DOCUMENTS_URL}/1", "name": "Document #1"},
                f"{DOCUMENTS_URL}/2": {
                    "url": f"{DOCUMENTS_URL}/2",
                    "name": "Document #2: Last wins!",
                },
            },
        ),
        (
            CONTENT("order_id"),
            [
                {
                    "url": f"{ANNOTATIONS_URL}/1/content/1",
                    "schema_id": "order_id",
                    "value": "PO#ABC",
                },
                {"url": f"{ANNOTATIONS_URL}/1/content/2", "schema_id": "order_id", "value": "123"},
                {"url": f"{ANNOTATIONS_URL}/2/content/3", "schema_id": "order_id", "value": "DEF"},
            ],
            {
                f"{ANNOTATIONS_URL}/1/content": [
                    {
                        "url": f"{ANNOTATIONS_URL}/1/content/1",
                        "schema_id": "order_id",
                        "value": "PO#ABC",
                    },
                    {
                        "url": f"{ANNOTATIONS_URL}/1/content/2",
                        "schema_id": "order_id",
                        "value": "123",
                    },
                ],
                f"{ANNOTATIONS_URL}/2/content": [
                    {
                        "url": f"{ANNOTATIONS_URL}/2/content/3",
                        "schema_id": "order_id",
                        "value": "DEF",
                    }
                ],
            },
        ),
    ],
)
def test_get_sideload_mapping(sideload: Sideload, objects: List[dict], expected: dict) -> None:
    assert sideload.get_mapping(objects) == expected
