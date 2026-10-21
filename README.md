# 말랑말랑 스토리 오븐

8~10세 어린이를 위한 스토리텔링 웹앱. 소재와 소스(초코=현실, 딸기=상상, 바닐라=혼합), 장르, 주인공, 장소, 사건을 고른 뒤 아이가 직접 결말을 쓰면 이야기 문체를 통일해 동화책으로 완성합니다.

## Streamlit Cloud
- 이 폴더의 `app.py`, `requirements.txt`, `marshmallow_mascot.png`, `story_oven.png`를 GitHub 저장소 루트에 업로드하세요.
- Streamlit Community Cloud의 앱 Secrets에 `GEMINI_API_KEY = "..."`를 설정하세요. 필요하다면 `GEMINI_MODEL`도 설정할 수 있습니다.
- Gemini 호출이 실패하면 선택지는 임시 예시로, 완성 책은 아이가 쓴 결말 원문을 포함한 임시 버전으로 표시됩니다.
- 그림책 삽화는 선택된 장소와 사건에 맞춰 앱이 그리는 파스텔 풍경입니다. 생성형 이미지 API를 통한 세부 장면 일러스트는 아직 지원하지 않습니다.
- 최종 HTML 책 파일은 브라우저에서 열어 PDF로 인쇄할 수 있습니다.
