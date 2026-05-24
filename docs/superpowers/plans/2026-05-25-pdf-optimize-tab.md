# PDF 용량 줄이기 탭 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 PDF 합치기 앱에 "용량 줄이기" 탭을 추가한다 — PDF 1개를 업로드하면 서버에서 lossless 압축을 적용하고 절감된 용량을 보여주며 자동 다운로드한다.

**Architecture:** FastAPI `/api/optimize` 엔드포인트를 추가해 기존 `optimize_pdf_bytes()` 로직을 재사용한다. 프론트엔드는 `index.html`에 탭 네비게이션을 추가하고, `app.js`에 탭 전환 및 최적화 로직을 추가한다. 서버는 응답 헤더(`X-Original-Size`, `X-Optimized-Size`, `X-Saved-Percent`)로 압축 결과를 전달한다.

**Tech Stack:** Python 3, FastAPI, pypdf, PyMuPDF(fitz), pytest, Vanilla JS, HTML/CSS

---

## File Map

| 파일 | 변경 |
|------|------|
| `app.py` | `/api/optimize` POST 엔드포인트 추가 |
| `tests/test_fastapi_app.py` | 새 엔드포인트 테스트 3개 추가 |
| `public/styles.css` | 탭 바 스타일 추가 (파일 끝에 append) |
| `public/index.html` | 탭 네비게이션 + optimize 섹션 추가, h1 부제 수정 |
| `public/app.js` | 탭 전환 로직 + optimize JS 로직 추가 |

---

## Task 1: `/api/optimize` 엔드포인트 + 테스트

**Files:**
- Modify: `app.py`
- Modify: `tests/test_fastapi_app.py`

- [ ] **Step 1: 실패하는 테스트 3개 작성**

`tests/test_fastapi_app.py` 파일 끝에 아래 코드를 추가한다.

```python
def test_optimize_endpoint_returns_compressed_pdf(minimal_pdf):
    response = client.post(
        "/api/optimize",
        data={"filename": "output.pdf"},
        files=[("file", ("input.pdf", minimal_pdf, "application/pdf"))],
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "output.pdf" in response.headers["content-disposition"]
    assert int(response.headers["x-original-size"]) > 0
    assert int(response.headers["x-optimized-size"]) > 0
    assert response.headers["x-saved-percent"] is not None


def test_optimize_endpoint_rejects_non_pdf(minimal_pdf):
    response = client.post(
        "/api/optimize",
        files=[("file", ("not-pdf.txt", minimal_pdf, "text/plain"))],
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_optimize_endpoint_rejects_empty_file():
    response = client.post(
        "/api/optimize",
        files=[("file", ("empty.pdf", b"", "application/pdf"))],
    )

    assert response.status_code == 400
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
cd /Users/lux/Documents/pdf && .venv/bin/pytest tests/test_fastapi_app.py::test_optimize_endpoint_returns_compressed_pdf tests/test_fastapi_app.py::test_optimize_endpoint_rejects_non_pdf tests/test_fastapi_app.py::test_optimize_endpoint_rejects_empty_file -v
```

예상 결과: `FAILED` (엔드포인트 미존재)

- [ ] **Step 3: `app.py`에 엔드포인트 추가**

`app.py`의 마지막 `@app.post("/api/combine")` 블록 아래에 추가한다.

```python
@app.post("/api/optimize")
async def optimize_pdf(
    file: Annotated[UploadFile, File(description="PDF to optimize")],
    filename: Annotated[str, Form()] = "",
):
    data = await read_pdf_upload(file)
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise HTTPException(status_code=400, detail="암호화된 PDF는 처리할 수 없습니다.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename}: PDF를 읽을 수 없습니다.",
        ) from exc

    optimized, meta = optimize_pdf_bytes(data, "balanced")
    output_filename = normalize_pdf_filename(filename or file.filename or DEFAULT_FILENAME)

    return Response(
        content=optimized,
        media_type="application/pdf",
        headers={
            "Content-Disposition": content_disposition(output_filename),
            "X-Original-Size": str(meta["assembled_size"]),
            "X-Optimized-Size": str(meta["final_size"]),
            "X-Saved-Percent": f"{meta['saved_percent']:.1f}",
        },
    )
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd /Users/lux/Documents/pdf && .venv/bin/pytest tests/test_fastapi_app.py -v
```

예상 결과: 모든 테스트 `PASSED`

- [ ] **Step 5: 커밋**

```bash
git add app.py tests/test_fastapi_app.py
git commit -m "feat: add /api/optimize endpoint for PDF compression"
```

---

## Task 2: CSS 탭 바 스타일

**Files:**
- Modify: `public/styles.css`

- [ ] **Step 1: `styles.css` 끝에 탭 스타일 추가**

```css
/* ── Tab bar ── */
.tab-bar {
  border-bottom: 1px solid var(--line);
  display: flex;
  gap: 0;
  margin-bottom: 8px;
}

.tab {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  color: var(--muted);
  font-size: 0.95rem;
  font-weight: 500;
  margin-bottom: -1px;
  min-height: auto;
  padding: 10px 16px;
}

.tab.active {
  border-bottom-color: var(--accent);
  color: var(--ink);
  font-weight: 650;
}

.tab:hover:not(.active) {
  color: var(--ink);
}

.opt-file-row {
  margin-top: 8px;
}
```

- [ ] **Step 2: 커밋**

```bash
git add public/styles.css
git commit -m "style: add tab bar styles for optimize feature"
```

---

## Task 3: HTML 탭 구조 + 최적화 섹션

**Files:**
- Modify: `public/index.html`

- [ ] **Step 1: `index.html` 전체를 아래 내용으로 교체**

```html
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PDF 도구</title>
    <link rel="stylesheet" href="/styles.css" />
  </head>
  <body>
    <main class="shell">
      <header class="topbar">
        <div>
          <h1>PDF 도구</h1>
          <p>합치기 · 용량 줄이기</p>
        </div>
        <div class="status-pill" id="summary">0개 파일</div>
      </header>

      <nav class="tab-bar">
        <button class="tab active" data-tab="combine" type="button">합치기</button>
        <button class="tab" data-tab="optimize" type="button">용량 줄이기</button>
      </nav>

      <!-- 합치기 탭 -->
      <div id="tab-combine">
        <section class="panel">
          <div class="panel-header">
            <h2>파일 추가</h2>
            <button class="secondary" id="clearButton" type="button" disabled>모두 지우기</button>
          </div>
          <label class="dropzone" id="dropzone">
            <input id="fileInput" type="file" accept="application/pdf,.pdf,image/png,image/jpeg,.png,.jpg,.jpeg" multiple />
            <span>PDF / 이미지 선택</span>
          </label>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2>순서 정렬</h2>
            <div class="sort-actions">
              <button class="secondary" id="sortAscButton" type="button" disabled>A-Z / 1-9</button>
              <button class="secondary" id="sortDescButton" type="button" disabled>Z-A / 9-1</button>
            </div>
          </div>
          <ol class="file-list" id="fileList"></ol>
          <div class="empty" id="emptyState">PDF 또는 이미지(PNG/JPG)를 추가하면 순서를 바꿀 수 있습니다.</div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2>다운로드</h2>
            <span class="result" id="resultText"></span>
          </div>
          <div class="download-row">
            <label class="filename-field">
              <span>파일명</span>
              <input id="filenameInput" type="text" value="combined.pdf" />
            </label>
            <button class="primary" id="combineButton" type="button" disabled>PDF 만들기</button>
          </div>
        </section>
      </div>

      <!-- 용량 줄이기 탭 -->
      <div id="tab-optimize" hidden>
        <section class="panel">
          <div class="panel-header">
            <h2>파일 선택</h2>
          </div>
          <label class="dropzone" id="optimizeDropzone">
            <input id="optimizeFileInput" type="file" accept="application/pdf,.pdf" />
            <span id="optimizeDropLabel">PDF 선택</span>
          </label>
          <div class="file-row opt-file-row" id="optimizeFileRow" hidden>
            <div class="file-meta">
              <div>
                <span id="optimizeFileName"></span>
                <small id="optimizeFileSize"></small>
              </div>
            </div>
            <div class="row-actions">
              <button class="icon-button" id="optimizeClearBtn" type="button" aria-label="삭제" title="삭제">×</button>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h2>다운로드</h2>
            <span class="result" id="optimizeResultText"></span>
          </div>
          <div class="download-row">
            <label class="filename-field">
              <span>파일명</span>
              <input id="optimizeFilenameInput" type="text" placeholder="파일명을 입력하세요" />
            </label>
            <button class="primary" id="optimizeButton" type="button" disabled>최적화</button>
          </div>
        </section>
      </div>
    </main>
    <script src="/pdf-lib.min.js"></script>
    <script src="/app.js" defer></script>
  </body>
</html>
```

- [ ] **Step 2: 커밋**

```bash
git add public/index.html
git commit -m "feat: add tab navigation and optimize section to HTML"
```

---

## Task 4: JS 탭 전환 + 최적화 로직

**Files:**
- Modify: `public/app.js`

- [ ] **Step 1: `app.js` 맨 위 변수 선언 블록 바로 뒤(첫 `function` 이전)에 탭 전환 코드 삽입**

`const dropzone = ...` 줄 아래, `function formatBytes` 위에 추가한다.

```javascript
// ── Tab switching ──
const tabButtons = document.querySelectorAll(".tab");
const tabCombine = document.querySelector("#tab-combine");
const tabOptimize = document.querySelector("#tab-optimize");

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    const isOptimize = btn.dataset.tab === "optimize";
    tabCombine.hidden = isOptimize;
    tabOptimize.hidden = !isOptimize;
    summary.hidden = isOptimize;
  });
});
```

- [ ] **Step 2: `app.js` 맨 끝(`updateState();` 아래)에 최적화 로직 추가**

```javascript
// ── Optimize tab ──
let optimizeFile = null;

const optimizeFileInput = document.querySelector("#optimizeFileInput");
const optimizeDropzone = document.querySelector("#optimizeDropzone");
const optimizeDropLabel = document.querySelector("#optimizeDropLabel");
const optimizeFileRow = document.querySelector("#optimizeFileRow");
const optimizeFileName = document.querySelector("#optimizeFileName");
const optimizeFileSize = document.querySelector("#optimizeFileSize");
const optimizeClearBtn = document.querySelector("#optimizeClearBtn");
const optimizeButton = document.querySelector("#optimizeButton");
const optimizeFilenameInput = document.querySelector("#optimizeFilenameInput");
const optimizeResultText = document.querySelector("#optimizeResultText");

function setOptimizeFile(file) {
  if (!file || !isPdf(file)) return;
  optimizeFile = file;
  const base = file.name.replace(/\.pdf$/i, "");
  optimizeFilenameInput.value = `${base}_optimized.pdf`;
  optimizeFileName.textContent = file.name;
  optimizeFileSize.textContent = formatBytes(file.size);
  optimizeDropLabel.textContent = "다른 파일 선택";
  optimizeFileRow.hidden = false;
  optimizeButton.disabled = false;
  optimizeResultText.textContent = "";
}

function clearOptimizeFile() {
  optimizeFile = null;
  optimizeFilenameInput.value = "";
  optimizeDropLabel.textContent = "PDF 선택";
  optimizeFileRow.hidden = true;
  optimizeButton.disabled = true;
  optimizeResultText.textContent = "";
  optimizeFileInput.value = "";
}

async function runOptimize() {
  optimizeButton.disabled = true;
  optimizeResultText.textContent = "처리 중";

  try {
    const formData = new FormData();
    formData.append("file", optimizeFile);
    formData.append("filename", normalizeFilename(optimizeFilenameInput.value));

    const response = await fetch("/api/optimize", { method: "POST", body: formData });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "최적화에 실패했습니다.");
    }

    const originalSize = parseInt(response.headers.get("x-original-size") || "0", 10);
    const optimizedSize = parseInt(response.headers.get("x-optimized-size") || "0", 10);
    const savedPercent = parseFloat(response.headers.get("x-saved-percent") || "0");

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = normalizeFilename(optimizeFilenameInput.value);
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);

    if (savedPercent < 0.1) {
      optimizeResultText.textContent = `이미 최적화된 파일입니다 · ${formatBytes(optimizedSize)}`;
    } else {
      optimizeResultText.textContent = `${formatBytes(originalSize)} → ${formatBytes(optimizedSize)} (${savedPercent}% 절감)`;
    }
  } catch (error) {
    optimizeResultText.textContent = error.message;
  } finally {
    optimizeButton.disabled = optimizeFile === null;
  }
}

optimizeFileInput.addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) setOptimizeFile(file);
  optimizeFileInput.value = "";
});

optimizeClearBtn.addEventListener("click", clearOptimizeFile);
optimizeButton.addEventListener("click", runOptimize);

optimizeDropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  optimizeDropzone.classList.add("dragover");
});

optimizeDropzone.addEventListener("dragleave", () => {
  optimizeDropzone.classList.remove("dragover");
});

optimizeDropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  optimizeDropzone.classList.remove("dragover");
  const file = event.dataTransfer.files[0];
  if (file) setOptimizeFile(file);
});
```

- [ ] **Step 3: 전체 테스트 통과 확인**

```bash
cd /Users/lux/Documents/pdf && .venv/bin/pytest tests/ -v
```

예상 결과: 모든 테스트 `PASSED`

- [ ] **Step 4: 앱을 실행해 브라우저에서 직접 확인**

```bash
cd /Users/lux/Documents/pdf && .venv/bin/uvicorn app:app --reload --port 8000
```

확인 항목:
- `http://localhost:8000` 접속 시 "합치기 / 용량 줄이기" 탭이 보임
- "합치기" 탭: 기존 기능 그대로 동작
- "용량 줄이기" 탭: PDF 업로드 → 최적화 버튼 활성화 → 클릭 시 다운로드 + 결과 텍스트 표시
- 드래그&드롭 작동

- [ ] **Step 5: 커밋**

```bash
git add public/app.js
git commit -m "feat: add tab switching and optimize JS logic"
```
