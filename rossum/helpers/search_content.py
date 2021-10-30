# Module for searching fields in hook payload coming from Rossum
from typing import Optional

import jmespath


def find_single_datapoint(content: list, schema_id: str) -> Optional[dict]:
    datapoint_identifiers = jmespath.search(
        f"[*].children[?schema_id=='{schema_id}'][] | [0]", content
    )
    return datapoint_identifiers


def find_all_line_items_datapoints(content: list) -> list:
    return jmespath.search("[].children[].children[].children[]", content)


def find_line_items_column(content: list, schema_id: str) -> list:
    return jmespath.search(
        f"[].children[].children[].children[?schema_id=='{schema_id}'][]", content
    )


def find_line_items_rows(content: list, schema_id: str) -> Optional[list]:
    return jmespath.search(f"[].children[?schema_id=='{schema_id}'][] | [0] | children[]", content)


def find_multivalue_parent(content: list, schema_id: str) -> Optional[dict]:
    return jmespath.search(f"[*].children[?schema_id=='{schema_id}'][] | [0]", content)


def find_children_of_simple_multivalue(content: list, child_schema_id: str) -> list:
    return jmespath.search(f"[*].children[].children[?schema_id=='{child_schema_id}'][]", content)
