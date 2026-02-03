# 🚀 Streamlit Cloud 배포 가이드

이 가이드는 PDF Combiner 앱을 Streamlit Cloud에 배포하는 방법을 설명합니다.

## 📋 준비사항

1. **GitHub 계정** (없으면 https://github.com 에서 가입)
2. **Streamlit Cloud 계정** (없으면 https://share.streamlit.io 에서 GitHub 계정으로 로그인)

---

## 🔧 1단계: GitHub에 코드 업로드

### 1-1. GitHub에서 새 리포지토리 생성

1. https://github.com/new 방문
2. Repository name: `pdf-combiner` (또는 원하는 이름)
3. Public으로 설정
4. "Create repository" 클릭

### 1-2. 로컬 코드를 GitHub에 푸시

터미널에서 다음 명령어를 실행하세요:

```bash
# 프로젝트 폴더로 이동
cd /Users/lux/Documents/pdf

# Git 사용자 정보 설정 (처음 한 번만)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: PDF Combiner with modern UI"

# 브랜치 이름을 main으로 변경
git branch -M main

# GitHub 리포지토리 연결 (아래에서 YOUR_USERNAME을 본인의 GitHub 아이디로 변경!)
git remote add origin https://github.com/YOUR_USERNAME/pdf-combiner.git

# GitHub에 푸시
git push -u origin main
```

**중요**: `YOUR_USERNAME`을 본인의 GitHub 사용자명으로 바꿔주세요!

---

## ☁️ 2단계: Streamlit Cloud에 배포

### 2-1. Streamlit Cloud 접속

1. https://share.streamlit.io 방문
2. "Sign in with GitHub" 클릭하여 로그인

### 2-2. 새 앱 배포

1. 우측 상단의 **"New app"** 버튼 클릭
2. 다음 정보 입력:

   - **Repository**: `YOUR_USERNAME/pdf-combiner` 선택
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: 원하는 URL 입력 (예: `pdf-combiner`)

3. **"Deploy!"** 버튼 클릭

### 2-3. 배포 완료 기다리기

- 첫 배포는 3-5분 정도 소요됩니다
- 진행 상황은 화면에서 실시간으로 확인 가능
- 배포가 완료되면 자동으로 앱이 열립니다

---

## 🎉 3단계: 앱 사용하기

배포가 완료되면 다음과 같은 URL로 접속할 수 있습니다:

```
https://YOUR_APP_NAME.streamlit.app
```

이제 누구나 이 링크를 통해 PDF 병합 도구를 사용할 수 있습니다!

---

## 🔄 코드 업데이트 방법

코드를 수정한 후 다시 배포하려면:

```bash
# 변경사항 추가
git add .

# 커밋
git commit -m "Update: 설명"

# GitHub에 푸시
git push
```

GitHub에 푸시하면 Streamlit Cloud가 자동으로 앱을 다시 배포합니다!

---

## 💡 유용한 팁

### 앱 설정 변경

- Streamlit Cloud 대시보드에서 앱을 선택
- "Settings" 메뉴에서 Python 버전, 리소스 등 설정 가능

### 로그 확인

- Streamlit Cloud 대시보드에서 "Manage app" 클릭
- 하단에 실시간 로그가 표시됨

### 앱 재시작

- 우측 상단 메뉴 > "Reboot app" 클릭

### 커스텀 도메인 (유료)

- Settings > General에서 커스텀 도메인 설정 가능

---

## ❓ 문제 해결

### 배포 실패 시

1. `requirements.txt`에 모든 패키지가 명시되어 있는지 확인
2. `packages.txt`가 제대로 업로드되었는지 확인 (한글 폰트용)
3. Streamlit Cloud 로그를 확인하여 오류 메시지 확인

### 한글이 깨질 때

- `packages.txt` 파일이 리포지토리에 포함되어 있는지 확인
- 앱을 재시작(Reboot)해보세요

### 파일 업로드 크기 제한

- Streamlit Cloud는 기본적으로 200MB까지 지원
- 더 큰 파일이 필요하면 설정에서 조정 가능

---

## 📞 도움말

- **Streamlit 문서**: https://docs.streamlit.io
- **Streamlit Cloud 문서**: https://docs.streamlit.io/streamlit-community-cloud
- **커뮤니티 포럼**: https://discuss.streamlit.io

---

## 🎊 축하합니다!

이제 전 세계 누구나 사용할 수 있는 PDF 병합 도구를 만들었습니다! 🚀
