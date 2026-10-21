# 마시멜로 🍡

8~10세 어린이를 위한 선택형 스토리텔링 Streamlit 앱.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

Gemini AI 선택지를 사용하려면 Streamlit Secrets에 `GEMINI_API_KEY = "..."`를 설정하세요. 없으면 기본 예시 선택지로 동작합니다. 모델은 기본적으로 `gemini-2.5-flash`이며 `GEMINI_MODEL`로 변경할 수 있습니다.

어린이의 이름, 학교, 주소, 연락처를 입력하지 않도록 안내하며 이야기는 별도 서버 DB에 저장하지 않습니다. Gemini를 연결하면 입력 내용이 AI 제공자에게 전송됩니다. 성인 보호자와 함께 이용해 주세요.
