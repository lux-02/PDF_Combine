# PDF 합치기

여러 PDF를 업로드하고 순서를 바꾼 뒤 하나의 PDF로 다운로드하는 FastAPI 앱입니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 열면 됩니다.

## Vercel 배포

Vercel은 `app.py`의 `app = FastAPI()`를 자동으로 감지합니다. `public/**` 파일은 정적 UI로 제공되고, PDF 병합은 `/api/combine`에서 처리됩니다.

```bash
vercel dev
vercel deploy
```

## API

- `GET /api/health`: 상태 확인
- `POST /api/combine`: `files` 필드에 정렬된 PDF 파일들을 multipart로 전달하면 합친 PDF를 반환

## 테스트

```bash
pip install -r requirements-dev.txt
pytest
```
