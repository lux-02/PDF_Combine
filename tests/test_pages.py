import uuid

import pytest

from pdf_studio.pages import (
    get_selected_ids_in_order,
    move_pages,
    move_single_page,
    natural_sort_key,
    remove_pages,
    sort_pages_by_source,
)
from tests.conftest import make_page_item


# ---------------------------------------------------------------------------
# natural_sort_key
# ---------------------------------------------------------------------------

class TestNaturalSortKey:
    def test_pure_alpha(self):
        keys = [natural_sort_key(v) for v in ["b.pdf", "a.pdf", "c.pdf"]]
        assert sorted(["b.pdf", "a.pdf", "c.pdf"], key=natural_sort_key) == ["a.pdf", "b.pdf", "c.pdf"]

    def test_numeric_ordering(self):
        names = ["doc10.pdf", "doc2.pdf", "doc1.pdf"]
        assert sorted(names, key=natural_sort_key) == ["doc1.pdf", "doc2.pdf", "doc10.pdf"]

    def test_mixed_alpha_and_number(self):
        names = ["b2.pdf", "a10.pdf", "a2.pdf"]
        assert sorted(names, key=natural_sort_key) == ["a2.pdf", "a10.pdf", "b2.pdf"]

    def test_case_insensitive(self):
        assert natural_sort_key("ABC") == natural_sort_key("abc")

    def test_empty_string(self):
        assert natural_sort_key("") == [""]


# ---------------------------------------------------------------------------
# get_selected_ids_in_order
# ---------------------------------------------------------------------------

class TestGetSelectedIdsInOrder:
    def test_preserves_page_order(self, simple_page_items):
        ids = {p["id"] for p in simple_page_items}
        result = get_selected_ids_in_order(simple_page_items, ids)
        assert result == [p["id"] for p in simple_page_items]

    def test_only_selected_returned(self, simple_page_items):
        selected = {simple_page_items[0]["id"]}
        result = get_selected_ids_in_order(simple_page_items, selected)
        assert result == [simple_page_items[0]["id"]]

    def test_empty_selection(self, simple_page_items):
        assert get_selected_ids_in_order(simple_page_items, set()) == []

    def test_empty_page_items(self):
        assert get_selected_ids_in_order([], {"some_id"}) == []


# ---------------------------------------------------------------------------
# move_pages
# ---------------------------------------------------------------------------

class TestMovePages:
    def test_move_to_beginning(self, simple_page_items):
        last_id = simple_page_items[2]["id"]
        new_items, new_insert = move_pages(simple_page_items, [last_id], 0)
        assert new_items[0]["id"] == last_id
        assert len(new_items) == 3
        assert new_insert == 1

    def test_move_to_end(self, simple_page_items):
        first_id = simple_page_items[0]["id"]
        new_items, new_insert = move_pages(simple_page_items, [first_id], 2)
        assert new_items[-1]["id"] == first_id
        assert len(new_items) == 3

    def test_move_multiple_pages(self, simple_page_items):
        ids = [simple_page_items[0]["id"], simple_page_items[2]["id"]]
        new_items, _ = move_pages(simple_page_items, ids, 0)
        assert len(new_items) == 3
        assert new_items[0]["id"] in ids
        assert new_items[1]["id"] in ids

    def test_target_clamped_to_zero(self, simple_page_items):
        first_id = simple_page_items[0]["id"]
        new_items, _ = move_pages(simple_page_items, [first_id], -99)
        assert new_items[0]["id"] == first_id

    def test_target_clamped_to_max(self, simple_page_items):
        last_id = simple_page_items[0]["id"]
        new_items, _ = move_pages(simple_page_items, [last_id], 9999)
        assert new_items[-1]["id"] == last_id

    def test_no_selected_returns_original_order(self, simple_page_items):
        original_ids = [p["id"] for p in simple_page_items]
        new_items, _ = move_pages(simple_page_items, [], 0)
        assert [p["id"] for p in new_items] == original_ids

    def test_immutable_input(self, simple_page_items):
        original = list(simple_page_items)
        move_pages(simple_page_items, [simple_page_items[0]["id"]], 2)
        assert [p["id"] for p in simple_page_items] == [p["id"] for p in original]


# ---------------------------------------------------------------------------
# move_single_page
# ---------------------------------------------------------------------------

class TestMoveSinglePage:
    def test_move_forward(self, simple_page_items):
        page_id = simple_page_items[0]["id"]
        result = move_single_page(simple_page_items, page_id, 1)
        assert result is not None
        new_items, _ = result
        assert new_items[1]["id"] == page_id

    def test_move_backward(self, simple_page_items):
        page_id = simple_page_items[2]["id"]
        result = move_single_page(simple_page_items, page_id, -1)
        assert result is not None
        new_items, _ = result
        assert new_items[1]["id"] == page_id

    def test_cannot_move_first_backward(self, simple_page_items):
        page_id = simple_page_items[0]["id"]
        assert move_single_page(simple_page_items, page_id, -1) is None

    def test_cannot_move_last_forward(self, simple_page_items):
        page_id = simple_page_items[-1]["id"]
        assert move_single_page(simple_page_items, page_id, 1) is None

    def test_unknown_id_returns_none(self, simple_page_items):
        assert move_single_page(simple_page_items, "nonexistent_id", 1) is None

    def test_insert_position_is_target_plus_one(self, simple_page_items):
        page_id = simple_page_items[0]["id"]
        _, new_insert = move_single_page(simple_page_items, page_id, 1)
        assert new_insert == 2

    def test_immutable_input(self, simple_page_items):
        original = [p["id"] for p in simple_page_items]
        move_single_page(simple_page_items, simple_page_items[0]["id"], 1)
        assert [p["id"] for p in simple_page_items] == original


# ---------------------------------------------------------------------------
# sort_pages_by_source
# ---------------------------------------------------------------------------

class TestSortPagesBySource:
    def _make_multi_doc_items(self):
        doc_b = uuid.uuid4().hex
        doc_a = uuid.uuid4().hex
        return [
            make_page_item(doc_id=doc_b, source_name="b.pdf", source_page_number=1),
            make_page_item(doc_id=doc_b, source_name="b.pdf", source_page_number=2),
            make_page_item(doc_id=doc_a, source_name="a.pdf", source_page_number=1),
        ]

    def test_sorts_by_filename_ascending(self):
        items = self._make_multi_doc_items()
        result = sort_pages_by_source(items, reverse=False)
        assert result[0]["source_name"] == "a.pdf"
        assert result[1]["source_name"] == "b.pdf"

    def test_sorts_by_filename_descending(self):
        items = self._make_multi_doc_items()
        result = sort_pages_by_source(items, reverse=True)
        assert result[0]["source_name"] == "b.pdf"

    def test_preserves_page_order_within_doc(self):
        items = self._make_multi_doc_items()
        result = sort_pages_by_source(items, reverse=False)
        b_pages = [p for p in result if p["source_name"] == "b.pdf"]
        assert b_pages[0]["source_page_number"] == 1
        assert b_pages[1]["source_page_number"] == 2

    def test_natural_sort_numeric(self):
        doc1 = uuid.uuid4().hex
        doc2 = uuid.uuid4().hex
        doc10 = uuid.uuid4().hex
        items = [
            make_page_item(doc_id=doc10, source_name="doc10.pdf"),
            make_page_item(doc_id=doc2, source_name="doc2.pdf"),
            make_page_item(doc_id=doc1, source_name="doc1.pdf"),
        ]
        result = sort_pages_by_source(items)
        names = [p["source_name"] for p in result]
        assert names == ["doc1.pdf", "doc2.pdf", "doc10.pdf"]

    def test_empty_list(self):
        assert sort_pages_by_source([]) == []

    def test_immutable_input(self, simple_page_items):
        original = [p["id"] for p in simple_page_items]
        sort_pages_by_source(simple_page_items)
        assert [p["id"] for p in simple_page_items] == original


# ---------------------------------------------------------------------------
# remove_pages
# ---------------------------------------------------------------------------

class TestRemovePages:
    def test_removes_specified_ids(self, simple_page_items):
        remove_id = simple_page_items[1]["id"]
        result = remove_pages(simple_page_items, {remove_id})
        assert len(result) == 2
        assert all(p["id"] != remove_id for p in result)

    def test_remove_all(self, simple_page_items):
        ids = {p["id"] for p in simple_page_items}
        assert remove_pages(simple_page_items, ids) == []

    def test_remove_none(self, simple_page_items):
        result = remove_pages(simple_page_items, set())
        assert len(result) == 3

    def test_unknown_id_ignored(self, simple_page_items):
        result = remove_pages(simple_page_items, {"totally_unknown"})
        assert len(result) == 3

    def test_immutable_input(self, simple_page_items):
        original = [p["id"] for p in simple_page_items]
        remove_pages(simple_page_items, {simple_page_items[0]["id"]})
        assert [p["id"] for p in simple_page_items] == original
