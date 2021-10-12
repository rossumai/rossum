from rossum.helpers.search_content import (
    find_line_items_column,
    find_all_line_items_datapoints,
    find_single_datapoint,
    find_multivalue_parent,
    find_children_of_simple_multivalue, find_line_items_rows,
)

ACCOUNT_NUMBER_NAME = "account_num"
ACCOUNT_NUMBER_FIELD = {
    "id": 191_001,
    "schema_id": ACCOUNT_NUMBER_NAME,
    "label": "Account number",
    "category": "datapoint",
    "content": {"value": "123456"},
}

MULTIVALUE_PARENT_NAME = "some_nested_multivalue"
MULTIVALUE_CHILD_NAME = "nested_datapoint"
SIMPLE_MULTIVALUE_CHILDREN = [
    {
        "id": 190_002,
        "schema_id": MULTIVALUE_CHILD_NAME,
        "label": "Nested datapoint",
        "content": {"value": "First Value"},
        "category": "datapoint",
        "constraints": {"required": False},
        "default_value": None,
        "rir_field_names": ["custom_rir_field_name"],
    },
    {
        "id": 190_003,
        "schema_id": MULTIVALUE_CHILD_NAME,
        "label": "Nested datapoint",
        "content": {"value": "Second Value"},
        "category": "datapoint",
        "constraints": {"required": False},
        "default_value": None,
        "rir_field_names": ["custom_rir_field_name"],
    },
]
MULTIVALUE_PARENT_FIELD = {
    "id": 190_001,
    "schema_id": MULTIVALUE_PARENT_NAME,
    "category": "multivalue",
    "children": SIMPLE_MULTIVALUE_CHILDREN,
    "default_value": None,
    "max_occurrences": None,
    "min_occurrences": None,
    "rir_field_names": None,
    "show_grid_by_default": False,
}

ITEM_DESCRIPTION_NAME = "item_description"
ITEM_DESCRIPTION_FIELD = {
    "category": "datapoint",
    "id": 192_001,
    "schema_id": ITEM_DESCRIPTION_NAME,
    "type": "string",
    "content": {"value": "My Little Item"},
}
ITEM_QUANTITY_FIELD = {
    "category": "datapoint",
    "id": 192_002,
    "schema_id": "item_quantity",
    "type": "number",
    "content": {"value": 100},
}
ONE_LINE_ITEM_ROW = {
    "id": 192_200,
    "schema_id": "line_item",
    "category": "tuple",
    "children": [ITEM_DESCRIPTION_FIELD, ITEM_QUANTITY_FIELD],
}

LINE_ITEMS_TABLE = [
    {
        "id": 192_100,
        "schema_id": "line_items",
        "category": "multivalue",
        "children": [ONE_LINE_ITEM_ROW, ONE_LINE_ITEM_ROW],
    }
]
DEFAULT_SCHEMA = [
    {
        "id": 190_000,
        "schema_id": "basic_info",
        "category": "section",
        "children": [MULTIVALUE_PARENT_FIELD],
    },
    {
        "id": 191_000,
        "schema_id": "payment_info_section",
        "category": "section",
        "children": [ACCOUNT_NUMBER_FIELD],
    },
    {"id": 192_000, "schema_id": "line_items_section", "children": LINE_ITEMS_TABLE},
    {
        "id": 193_000,
        "schema_id": "Others",
        "category": "section",
        "children": [
            {
                "id": 193_001,
                "schema_id": "note",
                "category": "datapoint",
                "label": "Note",
                "hidden": True,
            },
            {"id": 193_002, "schema_id": "approved", "category": "enum", "label": "Approved"},
        ],
    },
]


class TestSearchFieldsInContent:
    def test_find_single_datapoint(self):
        datapoint_found = find_single_datapoint(DEFAULT_SCHEMA, ACCOUNT_NUMBER_NAME)
        assert datapoint_found == ACCOUNT_NUMBER_FIELD

    def test_find_multivalue_parent(self):
        multivalue_parent = find_multivalue_parent(DEFAULT_SCHEMA, MULTIVALUE_PARENT_NAME)
        assert multivalue_parent == MULTIVALUE_PARENT_FIELD

    def test_find_children_of_simple_multivalue(self):
        multivalue_parent = find_children_of_simple_multivalue(
            DEFAULT_SCHEMA, MULTIVALUE_CHILD_NAME
        )
        assert multivalue_parent == SIMPLE_MULTIVALUE_CHILDREN

    def test_find_line_items_datapoints(self):
        line_items_found = find_all_line_items_datapoints(DEFAULT_SCHEMA)
        assert line_items_found == [
            ITEM_DESCRIPTION_FIELD,
            ITEM_QUANTITY_FIELD,
            ITEM_DESCRIPTION_FIELD,
            ITEM_QUANTITY_FIELD,
        ]

    def test_find_line_items_rows(self):
        line_items_found = find_line_items_rows(DEFAULT_SCHEMA, "line_items")
        assert line_items_found == [ONE_LINE_ITEM_ROW, ONE_LINE_ITEM_ROW]

    def test_find_line_items_column(self):
        column_found = find_line_items_column(DEFAULT_SCHEMA, ITEM_DESCRIPTION_NAME)
        assert column_found == [ITEM_DESCRIPTION_FIELD, ITEM_DESCRIPTION_FIELD]
