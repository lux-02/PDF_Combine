import streamlit as st
from pypdf import PdfWriter, PdfReader
from PIL import Image
import io
import os
import fitz  # PyMuPDF
from streamlit_sortables import sort_items
import base64
try:
    from docx import Document
    DOCX_PARSER_SUPPORT = True
except ImportError:
    DOCX_PARSER_SUPPORT = False
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_SUPPORT = True
except ImportError:
    REPORTLAB_SUPPORT = False

DOCX_TEXT_SUPPORT = DOCX_PARSER_SUPPORT and REPORTLAB_SUPPORT

# 페이지 설정
st.set_page_config(
    page_title="PDF Combiner - 파일 병합 도구",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS로 모던한 디자인 적용
st.markdown("""
<style>
    /* 전체 테마 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* 메인 컨테이너 */
    .block-container {
        max-width: 1200px;
        padding: 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* 제목 스타일 */
    h1 {
        color: #667eea;
        font-size: 3rem !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* 부제목 */
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* 업로드 영역 */
    .uploadedFile {
        border: 2px dashed #667eea !important;
        border-radius: 15px !important;
        padding: 2rem !important;
        background: #f8f9ff !important;
    }
    
    /* 버튼 스타일 */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Primary 버튼 */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* 파일 카드 */
    [data-testid="column"] > div > div > div {
        transition: all 0.3s ease;
    }
    
    [data-testid="column"] > div > div > div:hover {
        transform: scale(1.05);
    }
    
    /* 진행 바 */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 정보 박스 */
    .stInfo {
        background: #e8eeff;
        border-left: 4px solid #667eea;
        border-radius: 10px;
    }
    
    /* 성공 메시지 */
    .stSuccess {
        background: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 10px;
    }
    
    /* 경고 메시지 */
    .stWarning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 10px;
    }
    
    /* 썸네일 컨테이너 */
    [data-testid="stImage"] {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    /* 구분선 */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* 텍스트 입력 */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* 파일 업로더 */
    [data-testid="stFileUploader"] {
        border-radius: 15px;
    }
    
    /* 캡션 */
    .stCaption {
        font-weight: 500;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("<h1>📄 PDF Combiner</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>여러 PDF, 이미지, Word 파일을 하나로 병합하세요 ✨</p>", unsafe_allow_html=True)

def iter_docx_blocks(document):
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)

def find_korean_font_path():
    """한글 폰트 경로를 찾습니다. 여러 환경을 지원합니다."""
    candidates = [
        # 로컬 fonts 폴더
        os.path.join(os.getcwd(), "fonts", "NanumGothic.ttf"),
        os.path.join(os.getcwd(), "fonts", "NanumGothic-Regular.ttf"),
        # Streamlit Cloud (Ubuntu)
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        # macOS
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/AppleGothic.ttf",
        "/Library/Fonts/NanumGothic.ttf",
        "/Library/Fonts/NanumGothic-Regular.ttf",
        "/Library/Fonts/Malgun Gothic.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        # Windows
        "C:\\Windows\\Fonts\\malgun.ttf",
        "C:\\Windows\\Fonts\\NanumGothic.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def docx_to_pdf_simple(docx_bytes):
    document = Document(io.BytesIO(docx_bytes))
    blocks = []
    for block in iter_docx_blocks(document):
        if hasattr(block, "text"):
            text = block.text.strip()
            blocks.append(text if text else "")
        else:
            rows = []
            for row in block.rows:
                cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
                rows.append(" | ".join(cells).strip())
            blocks.extend(rows)
            blocks.append("")

    buffer = io.BytesIO()
    page_width, page_height = A4
    margin_x = 40
    margin_y = 40
    max_width = page_width - (margin_x * 2)
    font_size = 11
    line_gap = font_size * 1.4

    font_name = "Helvetica"
    font_used = False
    font_path = find_korean_font_path()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("DocxFont", font_path))
            font_name = "DocxFont"
            font_used = True
        except Exception:
            font_name = "Helvetica"
            font_used = False

    has_non_ascii = any(any(ord(ch) > 127 for ch in text) for text in blocks if text)

    def wrap_text(text):
        if not text:
            return [""]
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = ""
        for word in words:
            test = word if not current else f"{current} {word}"
            if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
                current = test
                continue

            if current:
                lines.append(current)

            if pdfmetrics.stringWidth(word, font_name, font_size) > max_width:
                chunk = ""
                for ch in word:
                    test_chunk = chunk + ch
                    if pdfmetrics.stringWidth(test_chunk, font_name, font_size) <= max_width:
                        chunk = test_chunk
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = ch
                current = chunk
            else:
                current = word

        if current:
            lines.append(current)
        return lines

    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    pdf_canvas.setFont(font_name, font_size)
    cursor_y = page_height - margin_y

    for block in blocks:
        for line in wrap_text(block):
            if cursor_y < margin_y:
                pdf_canvas.showPage()
                pdf_canvas.setFont(font_name, font_size)
                cursor_y = page_height - margin_y
            pdf_canvas.drawString(margin_x, cursor_y, line)
            cursor_y -= line_gap

        if block == "":
            cursor_y -= line_gap * 0.3

    pdf_canvas.save()
    buffer.seek(0)
    return buffer, font_used, has_non_ascii

def get_thumbnail(file):
    """파일의 썸네일을 생성합니다."""
    file_ext = os.path.splitext(file.name)[1].lower()
    try:
        if file_ext == ".pdf":
            # PDF의 첫 페이지를 이미지로 변환
            doc = fitz.open(stream=file.read(), filetype="pdf")
            file.seek(0) # 스트림 초기화
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2)) # 축소된 이미지
            img_data = pix.tobytes("png")
            doc.close()
            return img_data
        elif file_ext in [".jpg", ".jpeg", ".png"]:
            # 이미지 파일 썸네일 생성
            img = Image.open(file)
            img.thumbnail((150, 150))
            file.seek(0) # 스트림 초기화
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
        elif file_ext == ".docx":
            # Word 파일 썸네일 표시용 플래그
            return "DOCX_ICON"
    except Exception as e:
        return None
    return None

# 세션 상태 초기화
if 'file_list' not in st.session_state:
    st.session_state.file_list = []
if 'thumbnails' not in st.session_state:
    st.session_state.thumbnails = {}

# 파일 업로드 섹션
st.markdown("### 📁 파일 업로드")
st.markdown("PDF, 이미지(JPG, PNG), Word 문서(DOCX) 파일을 여러 개 선택하세요")

uploaded_files = st.file_uploader(
    "파일을 드래그하거나 클릭하여 선택하세요", 
    type=["pdf", "jpg", "jpeg", "png", "docx"], 
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    # 새로운 파일이 추가되었는지 확인하여 세션 상태 업데이트
    current_names = [f.name for f in st.session_state.file_list]
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in current_names:
            st.session_state.file_list.append(uploaded_file)
            # 썸네일 생성 및 저장
            thumb = get_thumbnail(uploaded_file)
            if thumb:
                st.session_state.thumbnails[uploaded_file.name] = thumb

if st.session_state.file_list:
    st.markdown("---")
    
    # 파일 개수 표시
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 🎯 업로드된 파일 ({len(st.session_state.file_list)}개)")
    with col2:
        total_size = sum(file.size for file in st.session_state.file_list) / (1024 * 1024)
        st.metric("총 용량", f"{total_size:.2f} MB")
    with col3:
        if st.button("🗑️ 전체 삭제", use_container_width=True):
            st.session_state.file_list = []
            st.session_state.thumbnails = {}
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔄 파일 순서 조정")
    st.info("💡 **팁**: 아래 파일명을 드래그하여 순서를 변경하세요. 썸네일 미리보기가 실시간으로 업데이트됩니다!")

    # 드래그 앤 드롭 정렬 (이름 기반)
    file_names = [file.name for file in st.session_state.file_list]
    sorted_names = sort_items(file_names, direction="horizontal", key="drag_sort_key")
    
    # 정렬 결과 반영
    if sorted_names != file_names:
        name_to_file = {f.name: f for f in st.session_state.file_list}
        st.session_state.file_list = [name_to_file[name] for name in sorted_names]
        st.rerun()

    # 정렬된 결과에 따른 썸네일 미리보기 그리드
    st.markdown("---")
    st.markdown("### 📸 미리보기")
    
    cols_per_row = 5
    for i in range(0, len(st.session_state.file_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(st.session_state.file_list):
                file = st.session_state.file_list[idx]
                with cols[j]:
                    with st.container(border=True):
                        # 파일 번호 뱃지
                        st.markdown(f"<div style='text-align:center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.3rem; border-radius: 8px 8px 0 0; margin: -1rem -1rem 0.5rem -1rem; font-weight: bold;'>#{idx+1}</div>", unsafe_allow_html=True)
                        
                        # 썸네일
                        if file.name in st.session_state.thumbnails:
                            thumb = st.session_state.thumbnails[file.name]
                            if thumb == "DOCX_ICON":
                                st.markdown("<div style='height:120px; display:flex; align-items:center; justify-content:center; background: linear-gradient(135deg, #e8eeff 0%, #f8f9ff 100%); border-radius:10px; font-size: 3rem;'>📝</div>", unsafe_allow_html=True)
                            else:
                                st.image(thumb, use_container_width=True)
                        else:
                            st.markdown("<div style='height:120px; display:flex; align-items:center; justify-content:center; background: #f5f5f5; border-radius:10px; color: #999;'>미리보기 없음</div>", unsafe_allow_html=True)
                        
                        # 파일명 및 정보
                        display_name = file.name if len(file.name) < 18 else file.name[:15] + "..."
                        file_size = file.size / 1024  # KB
                        st.caption(f"**{display_name}**")
                        st.caption(f"📦 {file_size:.1f} KB")
                        
                        # 삭제 버튼
                        if st.button("🗑️ 삭제", key=f"del_{idx}", use_container_width=True):
                            st.session_state.file_list.pop(idx)
                            if file.name in st.session_state.thumbnails:
                                del st.session_state.thumbnails[file.name]
                            st.rerun()

    st.markdown("---")

    # 병합 섹션
    st.markdown("### 💾 파일 병합 및 다운로드")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        output_filename = st.text_input(
            "저장할 파일 이름", 
            value="combined_output.pdf",
            help="병합된 PDF 파일의 이름을 입력하세요"
        )
        if not output_filename.endswith(".pdf"):
            output_filename += ".pdf"
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        merge_button = st.button("🚀 PDF 병합 시작!", type="primary", use_container_width=True)

    if merge_button:
        try:
            with st.spinner("🔄 PDF 병합을 준비하고 있습니다..."):
                merger = PdfWriter()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.markdown(f"<div style='text-align: center; padding: 1rem; background: #e8eeff; border-radius: 10px; font-weight: bold;'>⏳ 병합 준비 중...</div>", unsafe_allow_html=True)
            
            for i, file in enumerate(st.session_state.file_list):
                progress_percent = (i + 1) / len(st.session_state.file_list)
                status_text.markdown(f"<div style='text-align: center; padding: 1rem; background: #e8eeff; border-radius: 10px; font-weight: bold;'>📄 처리 중: {file.name} ({i+1}/{len(st.session_state.file_list)})</div>", unsafe_allow_html=True)
                
                file_ext = os.path.splitext(file.name)[1].lower()
                
                if file_ext == ".pdf":
                    # PDF 파일 처리
                    pdf_reader = PdfReader(file)
                    merger.append(pdf_reader)
                elif file_ext == ".docx":
                    # Word 파일 처리 (텍스트 재구성)
                    if not DOCX_TEXT_SUPPORT:
                        st.error("python-docx 또는 reportlab이 설치되어 있지 않습니다.")
                        continue

                    try:
                        status_text.text(f"텍스트 재구성 중: {file.name}...")
                        pdf_stream, font_used, has_non_ascii = docx_to_pdf_simple(file.getvalue())
                        if has_non_ascii and not font_used:
                            st.warning(
                                "한글 폰트가 없어 글자가 깨질 수 있습니다. "
                                "fonts/NanumGothic.ttf 추가를 권장합니다."
                            )
                        pdf_reader = PdfReader(pdf_stream)
                        merger.append(pdf_reader)
                    except Exception as e:
                        st.error(f"텍스트 재구성 중 오류 발생 ({file.name}): {str(e)}")
                        continue
                else:
                    # 이미지 파일 처리 (JPG, PNG 등)
                    image = Image.open(file)
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format="PDF")
                    img_byte_arr.seek(0)
                    
                    img_pdf_reader = PdfReader(img_byte_arr)
                    merger.append(img_pdf_reader)
                
                progress_bar.progress((i + 1) / len(st.session_state.file_list))

            status_text.markdown(f"<div style='text-align: center; padding: 1rem; background: #d4edda; border-radius: 10px; font-weight: bold;'>✨ 최종 PDF 파일 생성 중...</div>", unsafe_allow_html=True)
            
            output_pdf_stream = io.BytesIO()
            merger.write(output_pdf_stream)
            output_pdf_stream.seek(0)
            merger.close()
            
            progress_bar.progress(1.0)
            status_text.empty()
            
            st.success("🎉 축하합니다! 모든 파일이 성공적으로 병합되었습니다!")
            
            # 결과 정보
            output_size = len(output_pdf_stream.getvalue()) / (1024 * 1024)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("병합된 파일 수", f"{len(st.session_state.file_list)}개")
            with col2:
                st.metric("최종 파일 크기", f"{output_size:.2f} MB")
            with col3:
                st.metric("상태", "완료 ✅")
            
            st.markdown("---")
            
            # 다운로드 버튼
            st.download_button(
                label="📥 병합된 PDF 다운로드",
                data=output_pdf_stream,
                file_name=output_filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            st.info("💡 **해결 방법**: 파일이 손상되지 않았는지 확인하고 다시 시도해주세요.")

else:
    # 시작 가이드
    st.markdown("---")
    st.markdown("### 🚀 시작하기")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #e8eeff 0%, #f8f9ff 100%); border-radius: 15px; height: 200px;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>📤</div>
            <div style='font-weight: bold; font-size: 1.2rem; color: #667eea;'>1. 파일 업로드</div>
            <div style='color: #666; margin-top: 0.5rem;'>PDF, 이미지, Word 파일을 선택하세요</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #e8eeff 0%, #f8f9ff 100%); border-radius: 15px; height: 200px;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🔄</div>
            <div style='font-weight: bold; font-size: 1.2rem; color: #667eea;'>2. 순서 조정</div>
            <div style='color: #666; margin-top: 0.5rem;'>드래그하여 파일 순서를 변경하세요</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #e8eeff 0%, #f8f9ff 100%); border-radius: 15px; height: 200px;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>💾</div>
            <div style='font-weight: bold; font-size: 1.2rem; color: #667eea;'>3. 병합 & 다운로드</div>
            <div style='color: #666; margin-top: 0.5rem;'>병합 버튼을 눌러 완료하세요</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 지원 파일 형식 정보
    st.markdown("### 📋 지원 파일 형식")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - 📄 **PDF** - Adobe PDF 문서
        - 🖼️ **이미지** - JPG, PNG 형식
        """)
    
    with col2:
        st.markdown("""
        - 📝 **Word** - DOCX 문서
        - 📏 **제한** - 파일당 최대 200MB
        """)

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #666;'>
    <p style='font-size: 0.9rem;'>Made with ❤️ using <strong>Streamlit</strong></p>
    <p style='font-size: 0.8rem; color: #999;'>© 2026 PDF Combiner. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)
