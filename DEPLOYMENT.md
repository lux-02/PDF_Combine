# Vercel 배포 가이드

## 준비

```bash
cd /Users/lux/Documents/pdf
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## 로컬 확인

```bash
uvicorn app:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다.

Vercel 환경과 더 가깝게 확인하려면:

```bash
vercel dev
```

## 배포

GitHub 저장소를 Vercel 프로젝트로 연결하거나 CLI에서 배포합니다.

```bash
vercel deploy
```

프로덕션 배포:

```bash
vercel deploy --prod
```

## 구조

- `app.py`: FastAPI 앱과 `/api/combine` PDF 병합 API
- `public/index.html`: 정적 프론트엔드
- `public/app.js`: 파일 정렬과 다운로드 처리
- `public/styles.css`: 화면 스타일
- `.vercelignore`: Vercel 배포 제외 설정

## 참고

PDF는 요청 안에서 처리되고 서버에 저장되지 않습니다. Vercel Functions의 요청 크기와 실행 시간 제한 안에서 동작합니다.
