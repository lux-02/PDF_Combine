import re
from typing import Optional


def natural_sort_key(value: str) -> list:
    parts = re.split(r"(\d+)", value.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def get_selected_ids_in_order(page_items: list, selected_ids: set) -> list:
    return [p["id"] for p in page_items if p["id"] in selected_ids]


def move_pages(page_items: list, selected_ids: list, target_position: int) -> tuple:
    """Returns (new_page_items, new_insert_position). Pure — does not mutate input."""
    selected_set = set(selected_ids)
    moved = [p for p in page_items if p["id"] in selected_set]
    remaining = [p for p in page_items if p["id"] not in selected_set]
    target_index = max(0, min(target_position, len(remaining)))
    new_items = remaining[:target_index] + moved + remaining[target_index:]
    return new_items, target_index + len(moved)


def move_single_page(page_items: list, page_id: str, direction: int) -> Optional[tuple]:
    """Returns (new_page_items, new_insert_position) or None if the move is invalid."""
    current_index = next((i for i, p in enumerate(page_items) if p["id"] == page_id), None)
    if current_index is None:
        return None
    target_index = current_index + direction
    if target_index < 0 or target_index >= len(page_items):
        return None
    new_items = list(page_items)
    page = new_items.pop(current_index)
    new_items.insert(target_index, page)
    return new_items, target_index + 1


def sort_pages_by_source(page_items: list, reverse: bool = False) -> list:
    """Returns a new list sorted by source filename (natural sort), then page number."""
    grouped: dict = {}
    order: list = []
    for p in page_items:
        did = p["document_id"]
        if did not in grouped:
            grouped[did] = []
            order.append(did)
        grouped[did].append(p)

    sorted_ids = sorted(
        order,
        key=lambda did: natural_sort_key(grouped[did][0]["source_name"]),
        reverse=reverse,
    )

    result = []
    for did in sorted_ids:
        pages = sorted(grouped[did], key=lambda p: p["source_page_number"])
        result.extend(pages)
    return result


def remove_pages(page_items: list, page_ids: set) -> list:
    """Returns a new list with the given IDs removed."""
    return [p for p in page_items if p["id"] not in page_ids]
