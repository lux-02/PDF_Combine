import html
import math

import streamlit as st

from pdf_studio.canvas import SUPPORTED_TYPES, build_document_from_upload
from pdf_studio.styles import APP_CSS
from pdf_studio.export import assemble_pdf, format_file_size, optimize_pdf_bytes
from pdf_studio.pages import (
    get_selected_ids_in_order,
    move_pages,
    move_single_page,
    remove_pages,
    sort_pages_by_source,
)
from pdf_studio.state import (
    CANVAS_PAGE_SIZE,
    clamp_editor_state,
    clear_selection,
    ensure_session_state,
    hydrate_selection_from_widgets,
    invalidate_output,
    jump_canvas_to_index,
    prune_unused_documents,
    refresh_uploader,
    select_page_ids,
    set_insert_position,
    set_notices,
)

EXPORT_COMPRESSION_OPTIONS = {
    "none": {
        "label": "원본 유지",
        "description": "페이지를 다시 조립만 하고 추가 최적화는 하지 않습니다.",
    },
    "balanced": {
        "label": "균형 압축",
        "description": "중복 객체 정리와 무손실 스트림 압축을 적용합니다.",
    },
    "maximum": {
        "label": "강한 압축",
        "description": "가능한 무손실 최적화를 최대한 적용합니다.",
    },
}

# ---------------------------------------------------------------------------
# Page config & CSS
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PDF Page Studio",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(APP_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Action helpers (thin wrappers that read/write st.session_state)
# ---------------------------------------------------------------------------


def _selected_ids_ordered():
    return get_selected_ids_in_order(
        st.session_state.page_items, st.session_state.selected_page_ids
    )


def reset_editor():
    clear_selection()
    st.session_state.documents = {}
    st.session_state.page_items = []
    st.session_state.insert_position = 0
    st.session_state.canvas_page = 1
    st.session_state.output_pdf_bytes = None
    st.session_state.output_pdf_meta = None
    st.session_state.export_filename = "edited_output.pdf"
    set_notices([])
    refresh_uploader()


def add_documents_to_canvas(uploaded_files):
    insertion_index = st.session_state.insert_position
    new_documents, new_pages, notices = {}, [], []
    success_count = 0

    for f in uploaded_files:
        try:
            doc, page_items, doc_notices = build_document_from_upload(f)
            new_documents[doc["id"]] = doc
            new_pages.extend(page_items)
            notices.extend(doc_notices)
            success_count += 1
        except Exception as exc:
            notices.append({"level": "error", "text": f"{f.name}: {exc}"})

    if success_count == 0:
        set_notices(notices)
        return

    st.session_state.documents.update(new_documents)
    st.session_state.page_items[insertion_index:insertion_index] = new_pages
    st.session_state.insert_position = insertion_index + len(new_pages)
    jump_canvas_to_index(insertion_index)
    invalidate_output()
    notices.insert(0, {
        "level": "info",
        "text": f"{success_count}개 문서를 편집 캔버스에 추가했습니다. 새로 들어간 페이지는 총 {len(new_pages)}장입니다.",
    })
    set_notices(notices)
    clamp_editor_state()


def _do_move_selected(target_position: int):
    selected = _selected_ids_ordered()
    if not selected:
        return False
    new_items, new_insert = move_pages(
        st.session_state.page_items, selected, target_position
    )
    st.session_state.page_items = new_items
    st.session_state.insert_position = new_insert
    jump_canvas_to_index(target_position)
    invalidate_output()
    clamp_editor_state()
    return True


def _do_move_single(page_id: str, direction: int):
    result = move_single_page(st.session_state.page_items, page_id, direction)
    if result is None:
        return False
    new_items, new_insert = result
    st.session_state.page_items = new_items
    st.session_state.insert_position = new_insert
    jump_canvas_to_index(new_insert - 1)
    invalidate_output()
    clamp_editor_state()
    return True


def _do_sort(reverse: bool):
    st.session_state.page_items = sort_pages_by_source(
        st.session_state.page_items, reverse=reverse
    )
    st.session_state.canvas_page = 1
    invalidate_output()
    clamp_editor_state()


def _do_remove(page_ids):
    ids_set = set(page_ids)
    st.session_state.page_items = remove_pages(st.session_state.page_items, ids_set)
    st.session_state.selected_page_ids.difference_update(ids_set)
    for pid in ids_set:
        widget_key = f"select_{pid}"
        if widget_key in st.session_state:
            st.session_state[widget_key] = False
    prune_unused_documents()
    invalidate_output()
    clamp_editor_state()


def build_output_pdf(compression_profile: str) -> tuple:
    assembled = assemble_pdf(st.session_state.page_items, st.session_state.documents)
    return optimize_pdf_bytes(assembled, compression_profile)


def describe_insert_position() -> str:
    items = st.session_state.page_items
    pos = st.session_state.insert_position
    if not items:
        return "첫 문서를 올리면 모든 페이지가 바로 편집 캔버스로 펼쳐집니다."
    if pos <= 0:
        return "다음 업로드는 문서 맨 앞에 삽입됩니다."
    if pos >= len(items):
        return "다음 업로드는 문서 맨 뒤에 이어 붙습니다."
    prev = items[pos - 1]
    return (
        f"다음 업로드는 {pos}번 페이지 뒤에 삽입됩니다. "
        f"({html.escape(prev['source_name'])} · 원본 {prev['source_page_number']}페이지 뒤)"
    )


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------


def show_notices():
    for notice in st.session_state.notices:
        level = notice.get("level", "info")
        msg = notice.get("text", "")
        if level == "warning":
            st.warning(msg)
        elif level == "error":
            st.error(msg)
        else:
            st.info(msg)


def render_source_summary():
    seen, order = set(), []
    for p in st.session_state.page_items:
        if p["document_id"] not in seen:
            seen.add(p["document_id"])
            order.append(p["document_id"])

    with st.expander("현재 소스 문서 보기", expanded=False):
        for doc_id in order:
            doc = st.session_state.documents[doc_id]
            active = sum(1 for p in st.session_state.page_items if p["document_id"] == doc_id)
            st.markdown(f"- **{doc['name']}** · {doc['kind']} · 현재 사용 중 {active}장")


def render_compact_header(total_pages: int, active_doc_count: int, selected_count: int):
    stats = f"{active_doc_count}개 문서 · {total_pages}장 편집 중"
    if selected_count:
        stats += f" · {selected_count}장 선택됨"
    st.markdown(
        f'<div class="compact-header">'
        f'<span class="app-brand">PDF Page Studio</span>'
        f'<span class="header-stats">{stats}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    with st.expander("앱 소개"):
        st.markdown(
            "**페이지 단위로 재배열하는 PDF 작업대**\n\n"
            "업로드한 문서를 페이지 카드로 펼친 뒤, 원하는 페이지를 선택해서 한 번에 이동하고, "
            "필요 없는 장은 바로 지우고, 다른 PDF는 중간 위치에 끼워 넣은 뒤 다시 저장합니다.\n\n"
            "**주요 기능:** 페이지 썸네일 캔버스 · 선택 후 배치 이동 · 삽입 위치 커서 · 즉시 삭제"
        )


def render_action_bar(selected_count: int, total_pages: int, selected_ids: list):
    if selected_count == 0:
        return

    with st.container(border=True):
        col_count, col_up, col_dn, col_move_n, col_move_btn, col_del, col_desel = st.columns(
            [2, 1, 1, 2, 2, 2, 2]
        )

        with col_count:
            st.markdown(
                f'<span class="action-bar-count">✓ {selected_count}장 선택됨</span>',
                unsafe_allow_html=True,
            )

        with col_up:
            if st.button("▲", disabled=selected_count != 1, key="action_bar_up", use_container_width=True):
                _do_move_single(selected_ids[0], -1)
                st.rerun()
        with col_dn:
            if st.button("▼", disabled=selected_count != 1, key="action_bar_dn", use_container_width=True):
                _do_move_single(selected_ids[0], 1)
                st.rerun()

        remaining = max(1, total_pages - selected_count + 1)
        with col_move_n:
            target = st.number_input(
                "위치",
                min_value=1,
                max_value=remaining,
                step=1,
                key="action_bar_move_target",
                label_visibility="collapsed",
            )
        with col_move_btn:
            if st.button("위치로 이동", type="primary", key="action_bar_move_btn", use_container_width=True):
                _do_move_selected(int(target) - 1)
                st.rerun()

        with col_del:
            if st.button("🗑 삭제", key="action_bar_del", use_container_width=True):
                _do_remove(selected_ids)
                st.rerun()
        with col_desel:
            if st.button("✕ 해제", key="action_bar_desel", use_container_width=True):
                clear_selection()
                st.rerun()


def render_canvas_toolbar(
    canvas_page: int,
    total_canvas_pages: int,
    canvas_start: int,
    canvas_end: int,
    total_pages: int,
    all_selected: bool,
):
    tc1, tc2, tc3, tc4, tc5, tc6 = st.columns([1, 2, 1, 1, 1, 2])
    with tc1:
        if st.button("◀", use_container_width=True, disabled=canvas_page == 1, key="toolbar_prev"):
            st.session_state.canvas_page -= 1
            st.rerun()
    with tc2:
        st.markdown(
            f'<div style="text-align:center;padding:0.6rem 0;font-weight:700;color:var(--ink);">'
            f'{canvas_page} / {total_canvas_pages}'
            f'<span style="font-weight:400;color:var(--muted);font-size:0.85rem;"> ({canvas_start + 1}–{canvas_end} / {total_pages}장)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with tc3:
        if st.button("▶", use_container_width=True, disabled=canvas_page >= total_canvas_pages, key="toolbar_next"):
            st.session_state.canvas_page += 1
            st.rerun()
    with tc4:
        if st.button("A↑", use_container_width=True, key="toolbar_sort_asc", help="A-Z / 1-9 정렬"):
            _do_sort(reverse=False)
            st.rerun()
    with tc5:
        if st.button("Z↓", use_container_width=True, key="toolbar_sort_desc", help="Z-A / 9-1 역정렬"):
            _do_sort(reverse=True)
            st.rerun()
    with tc6:
        toggle_label = "전체 해제" if all_selected else "전체 선택"
        if st.button(toggle_label, use_container_width=True, key="toolbar_select_toggle"):
            if all_selected:
                clear_selection()
            else:
                select_page_ids([p["id"] for p in st.session_state.page_items])
            st.rerun()


def render_page_card(
    page: dict,
    global_index: int,
    total_pages: int,
    is_selected: bool,
    is_cursor_after: bool,
):
    with st.container(border=True):
        if is_selected:
            st.markdown('<div class="card-selected-bar"></div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="page-topline">'
            f'<span class="page-chip">#{global_index + 1}</span>'
            f'<span class="source-pill">{page["source_kind"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.image(page["thumbnail"], use_container_width=True)
        st.markdown(
            f'<div class="page-meta">{html.escape(page["source_name"])}</div>'
            f'<div class="page-submeta">원본 {page["source_page_number"]} / {page["source_total_pages"]} 페이지</div>',
            unsafe_allow_html=True,
        )

        cb_col, cur_col, del_col = st.columns([3, 1, 1])
        with cb_col:
            checkbox_key = f"select_{page['id']}"
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = is_selected
            checked = st.checkbox("선택", key=checkbox_key)
            if checked:
                st.session_state.selected_page_ids.add(page["id"])
            else:
                st.session_state.selected_page_ids.discard(page["id"])
        with cur_col:
            if st.button(
                "↓",
                key=f"cursor_{page['id']}",
                use_container_width=True,
                help="다음 업로드를 이 페이지 뒤에 삽입",
            ):
                set_insert_position(global_index + 1)
                st.rerun()
        with del_col:
            if st.button(
                "×",
                key=f"del_{page['id']}",
                use_container_width=True,
                help="이 페이지 삭제",
            ):
                _do_remove([page["id"]])
                st.rerun()

        if is_cursor_after:
            st.markdown(
                '<div class="cursor-line">▼ 업로드는 이 페이지 뒤에 삽입됩니다</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

ensure_session_state()
hydrate_selection_from_widgets()
clamp_editor_state()

# ---------------------------------------------------------------------------
# Computed state
# ---------------------------------------------------------------------------

total_pages = len(st.session_state.page_items)
selected_ids = _selected_ids_ordered()
selected_count = len(selected_ids)
active_doc_count = len({p["document_id"] for p in st.session_state.page_items})
all_selected = total_pages > 0 and selected_count == total_pages

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

render_compact_header(total_pages, active_doc_count, selected_count)

# ---------------------------------------------------------------------------
# Action bar (contextual — appears only when pages are selected)
# ---------------------------------------------------------------------------

render_action_bar(selected_count, total_pages, selected_ids)

show_notices()

# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------

st.markdown('<div class="section-kicker">INTAKE</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">소스 문서 추가</div>', unsafe_allow_html=True)

with st.container(border=True):
    ic1, ic2, ic3, ic4 = st.columns([3, 1, 1, 1])
    with ic1:
        st.markdown(f'<div class="section-note">{describe_insert_position()}</div>', unsafe_allow_html=True)
    with ic2:
        if st.button("맨 앞 삽입", use_container_width=True, disabled=not total_pages):
            set_insert_position(0)
            st.rerun()
    with ic3:
        if st.button("맨 뒤 삽입", use_container_width=True, disabled=not total_pages):
            set_insert_position(total_pages)
            st.rerun()
    with ic4:
        if st.button("캔버스 비우기", use_container_width=True, disabled=not total_pages):
            reset_editor()
            st.rerun()

    uploaded_files = st.file_uploader(
        "PDF, 이미지, DOCX를 선택하세요",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}",
        help="업로드 후 현재 삽입 위치 기준으로 페이지가 편집 캔버스에 추가됩니다.",
    )

    uc1, uc2 = st.columns([2, 1])
    with uc1:
        if uploaded_files:
            st.caption(f"{len(uploaded_files)}개 문서가 준비되었습니다. 버튼을 누르면 현재 삽입 위치에 추가됩니다.")
        else:
            st.caption("PDF는 페이지별로 분해되고, 이미지와 DOCX도 PDF 페이지로 변환되어 같은 방식으로 편집됩니다.")
    with uc2:
        if st.button("현재 위치에 문서 추가", type="primary", use_container_width=True, disabled=not uploaded_files):
            with st.spinner("문서를 페이지 편집 캔버스로 펼치는 중입니다..."):
                add_documents_to_canvas(uploaded_files)
            refresh_uploader()
            st.rerun()

# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------

if not total_pages:
    st.markdown(
        """
<div class="empty-grid">
    <div class="empty-card">
        <div style="font-size:2.2rem;">1</div>
        <h3>문서를 펼칩니다</h3>
        <p>업로드한 PDF를 페이지 단위 카드로 풀어내서 전체 순서를 한눈에 볼 수 있게 만듭니다.</p>
    </div>
    <div class="empty-card">
        <div style="font-size:2.2rem;">2</div>
        <h3>선택해서 이동합니다</h3>
        <p>드래그만 강요하지 않고, 여러 페이지를 선택한 뒤 원하는 시작 위치 번호로 한 번에 이동시킵니다.</p>
    </div>
    <div class="empty-card">
        <div style="font-size:2.2rem;">3</div>
        <h3>중간 삽입 후 저장합니다</h3>
        <p>특정 페이지 뒤를 삽입 위치로 지정하고 다른 문서를 추가한 다음, 새 PDF로 다시 저장합니다.</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Editor canvas
# ---------------------------------------------------------------------------

else:
    render_source_summary()

    st.markdown('<div class="section-kicker">EDITOR</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">페이지 캔버스</div>', unsafe_allow_html=True)

    with st.container(border=True):
        total_canvas_pages = max(1, math.ceil(total_pages / CANVAS_PAGE_SIZE))
        st.session_state.canvas_page = max(1, min(st.session_state.canvas_page, total_canvas_pages))
        canvas_start = (st.session_state.canvas_page - 1) * CANVAS_PAGE_SIZE
        canvas_end = min(canvas_start + CANVAS_PAGE_SIZE, total_pages)
        visible_pages = st.session_state.page_items[canvas_start:canvas_end]

        render_canvas_toolbar(
            st.session_state.canvas_page,
            total_canvas_pages,
            canvas_start,
            canvas_end,
            total_pages,
            all_selected,
        )

        if st.session_state.insert_position == 0:
            st.markdown('<div class="insert-banner">현재 삽입 위치는 문서 맨 앞입니다.</div>', unsafe_allow_html=True)

        cards_per_row = 4
        for row_start in range(0, len(visible_pages), cards_per_row):
            cols = st.columns(cards_per_row)
            for offset, col in enumerate(cols):
                page_offset = row_start + offset
                if page_offset >= len(visible_pages):
                    continue

                page = visible_pages[page_offset]
                global_index = canvas_start + page_offset
                is_selected = page["id"] in st.session_state.selected_page_ids
                is_cursor_after = st.session_state.insert_position == global_index + 1

                with col:
                    render_page_card(page, global_index, total_pages, is_selected, is_cursor_after)

        if st.session_state.insert_position >= total_pages:
            st.markdown('<div class="insert-banner">현재 삽입 위치는 문서 맨 뒤입니다.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

if total_pages:
    st.markdown('<div class="section-kicker">EXPORT</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">편집 결과 저장</div>', unsafe_allow_html=True)

    with st.container(border=True):
        ex1, ex2 = st.columns([2.1, 1])
        with ex1:
            output_filename = st.text_input(
                "저장할 파일 이름",
                value=st.session_state.export_filename,
                help="현재 페이지 순서와 삭제 상태가 그대로 반영된 새 PDF가 생성됩니다.",
            )
            if not output_filename.endswith(".pdf"):
                output_filename += ".pdf"
            st.session_state.export_filename = output_filename
        with ex2:
            compression_profile = st.selectbox(
                "용량 최적화",
                options=list(EXPORT_COMPRESSION_OPTIONS.keys()),
                format_func=lambda k: EXPORT_COMPRESSION_OPTIONS[k]["label"],
                key="compression_profile",
                help="문서 구조 정리와 무손실 압축 강도를 선택합니다.",
            )
            st.caption(EXPORT_COMPRESSION_OPTIONS[compression_profile]["description"])

        bc1, bc2 = st.columns([3, 1])
        with bc1:
            st.caption("압축 옵션은 다운로드용 PDF에만 적용됩니다. 편집 캔버스의 페이지 내용과 순서는 바뀌지 않습니다.")
        with bc2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("편집본 만들기", type="primary", use_container_width=True):
                with st.spinner("현재 페이지 캔버스를 새 PDF로 저장하는 중입니다..."):
                    st.session_state.output_pdf_bytes, st.session_state.output_pdf_meta = build_output_pdf(compression_profile)

        output_meta = st.session_state.output_pdf_meta or {}
        is_current_output = (
            st.session_state.output_pdf_bytes is not None
            and output_meta.get("profile") == compression_profile
        )

        if st.session_state.output_pdf_bytes and not is_current_output:
            st.info("압축 옵션이 변경되었습니다. 새 설정으로 다시 `편집본 만들기`를 눌러주세요.")

        if is_current_output:
            st.success("편집본 PDF가 준비되었습니다. 바로 다운로드할 수 있습니다.")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric("최종 파일 크기", format_file_size(output_meta.get("final_size", 0)))
            with mc2:
                if compression_profile == "none":
                    st.metric("최적화", "사용 안 함")
                else:
                    delta = (
                        f"{output_meta.get('saved_percent', 0.0):.1f}% 감소"
                        if output_meta.get("saved_bytes", 0) > 0
                        else "변화 거의 없음"
                    )
                    st.metric("조립본 대비", delta)
            with mc3:
                st.metric("채택 결과", output_meta.get("selected_stage_label", "조립본"))

            if compression_profile != "none":
                a_label = format_file_size(output_meta.get("assembled_size", 0))
                f_label = format_file_size(output_meta.get("final_size", 0))
                if output_meta.get("saved_bytes", 0) > 0:
                    st.caption(f"조립본 {a_label} -> 최종 {f_label}로 줄었습니다.")
                else:
                    st.caption(f"무손실 최적화를 시도했지만 현재 문서는 {a_label} 수준이 가장 작았습니다.")

            for warning in output_meta.get("warnings", []):
                st.info(warning)

            st.download_button(
                label="편집본 PDF 다운로드",
                data=st.session_state.output_pdf_bytes,
                file_name=st.session_state.export_filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    """
<div style="text-align:center;color:#6c7a80;padding:1rem 0 2rem 0;">
    <div style="font-family:'Fraunces',serif;font-size:1.1rem;color:#1d2930;">PDF Page Studio</div>
    <div style="font-size:0.9rem;margin-top:0.35rem;">페이지 분해, 재배열, 삽입, 삭제를 한 화면에서 처리하는 Streamlit 기반 편집기</div>
</div>
""",
    unsafe_allow_html=True,
)
