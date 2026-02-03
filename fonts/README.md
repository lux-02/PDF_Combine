# 한글 폰트 설정

이 폴더는 Word 문서를 PDF로 변환할 때 한글 표시를 위한 폰트를 저장합니다.

## Streamlit Cloud에서의 한글 폰트

Streamlit Cloud 배포 시 `packages.txt` 파일을 통해 나눔 폰트가 자동으로 설치됩니다.

## 로컬 개발 환경

로컬에서 테스트할 때 한글이 깨진다면:

### macOS
시스템 폰트를 자동으로 사용합니다 (AppleGothic 등)

### Linux/Ubuntu
```bash
sudo apt-get install fonts-nanum fonts-nanum-coding fonts-nanum-extra
```

### Windows
나눔 폰트를 다운로드하여 이 폴더에 `NanumGothic.ttf` 파일을 넣으세요.
- 다운로드: https://hangeul.naver.com/font

## 참고사항

PDF 병합은 한글 폰트 없이도 작동하지만, Word 문서를 PDF로 변환할 때만 한글 폰트가 필요합니다.
