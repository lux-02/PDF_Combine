# PDF 용량 줄이기 탭 — 디자인 스펙

**날짜:** 2026-05-25  
**상태:** 승인됨

---

## 목표

기존 "PDF 합치기" 앱에 "용량 줄이기" 탭을 추가한다. 사용자가 PDF 1개를 업로드하면 서버에서 lossless 압축을 적용하고, 절감된 용량을 보여주며 자동으로 다운로드된다.

---

## 아키텍처

### 컴포넌트 변경 범위

| 파일 | 변경 내용 |
|------|-----------|
| `public/index.html` | 탭 네비게이션 추가, 최적화 섹션 추가 |
| `public/app.js` | 탭 전환 로직, 최적화 섹션 JS 추가 |
| `public/styles.css` | 탭 스타일 추가 |
| `app.py` | `/api/optimize` POST 엔드포인트 추가 |

`pdf_studio/export.py`의 `optimize_pdf_bytes()`는 변경 없이 재사용한다.

---

## UI 상세

### 탭 네비게이션

`<header class="topbar">` 아래에 탭 바를 추가한다.

- 탭 1: **합치기** (기존 기능)
- 탭 2: **용량 줄이기** (신규)

탭 클릭 시 해당 섹션을 표시하고, 나머지는 `hidden` 처리한다.

### 용량 줄이기 섹션 구성

1. **파일 추가 패널**: PDF 1개 선택 (드래그&드롭 또는 버튼). 선택 후 파일명과 원본 크기 표시.
2. **다운로드 패널**:
   - 파일명 입력 필드 (기본값: 원본 파일명에 `_optimized` 접미사)
   - "최적화" 버튼 (파일 미선택 시 disabled)
   - 결과 텍스트: `원본 크기 → 압축 크기 (N% 절감)` 또는 `이미 최적화된 파일입니다` (절감 0%)

---

## API

### `POST /api/optimize`

**요청**: `multipart/form-data`
- `file`: PDF 파일 (1개)
- `filename`: 다운로드 파일명 (optional, 기본값: 원본 파일명)

**응답**: 압축된 PDF 바이너리
- `Content-Disposition: attachment; filename*=UTF-8''<filename>`
- `X-Original-Size: <bytes>` — 원본 크기
- `X-Optimized-Size: <bytes>` — 압축 후 크기
- `X-Saved-Percent: <float>` — 절감률 (예: `12.3`)

**압축 프로필**: `"balanced"` 고정 (사용자에게 노출하지 않음)

**에러 처리**:
- PDF 아닌 파일: 400 `PDF만 업로드할 수 있습니다.`
- 빈 파일: 400 `빈 파일입니다.`
- 손상된 PDF: 400 `PDF를 읽을 수 없습니다.`

---

## 데이터 흐름

```
사용자 파일 선택
  → JS: 파일명/크기 표시, "최적화" 버튼 활성화
  → 버튼 클릭: FormData 생성, POST /api/optimize
  → 서버: optimize_pdf_bytes(data, "balanced")
  → 응답 헤더에서 원본/압축 크기 읽기
  → Blob URL 생성 → <a> 클릭 → 자동 다운로드
  → 결과 텍스트 업데이트
```

---

## 스코프 외

- 이미지 DPI 조정 / 손실 압축 — 향후 고려
- 여러 파일 일괄 최적화 — 향후 고려
- 비밀번호 보호 PDF 처리 — 향후 고려
