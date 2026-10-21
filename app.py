"""Marshmallow: a child-led story workshop (Streamlit + optional Gemini)."""
import json
import os
import random
import re
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="마시멜로 | 나만의 이야기", page_icon="🍡", layout="centered")
st.markdown('''<style>
.stApp{background:linear-gradient(145deg,#fff5f4,#fffaf0 55%,#f5f0ff)}
.block-container{max-width:850px;padding-top:2rem}
h1,h2,h3{color:#78546a}div.stButton>button{border-radius:22px;min-height:3.2rem;white-space:normal;height:auto;background:#fffdfb;border:1px solid #eacbd5}
div.stButton>button[kind="primary"]{background:#d781a0;color:white;border-color:#d781a0}
.hero{text-align:center;padding:20px;background:#fff9f8;border-radius:28px;border:1px solid #f4dce2;margin-bottom:22px}
.hero h1{font-size:3rem;margin:.2rem 0}.book{background:#fffdf6;border:2px solid #ead9bd;border-radius:20px;padding:26px 30px;line-height:2.05;color:#624c47}
</style>''',unsafe_allow_html=True)

SAUCES={"초코 🍫":"상상 가득! 마법과 불가능한 일이 자연스럽게 일어나는 이야기", "딸기 🍓":"현실 가득! 우리 주변에서 실제로 일어날 법한 이야기", "바닐라 🍦":"반반 섞기! 현실적인 일상에 작은 신비를 더한 이야기"}
CHARACTERS=["🐻 용감한 곰 쿠키", "🐰 호기심 많은 토끼 쿠키", "⭐ 수줍은 별 쿠키", "🐱 장난꾸러기 고양이 쿠키"]
PLACES=["🏖️ 반짝이는 바닷가", "🌲 비밀스러운 숲", "🏡 아늑한 과자 마을", "🏰 오래된 성"]
EVENTS=["반짝이는 수수께끼 물건을 발견했어요", "새로운 친구가 도움을 청했어요", "갑자기 예상하지 못한 일이 벌어졌어요", "중요한 것을 잃어버려 찾아 나섰어요"]


def init():
    defaults={"stage":0,"topic":"","sauce":"바닐라 🍦","character":"","place":"","events":[],"ending":"","title":"","options":[],"warning":""}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v.copy() if isinstance(v,list) else v
init()


def friendly_ai_error(error):
    """Show a useful diagnosis without revealing API keys or prompts."""
    name = type(error).__name__
    code = getattr(error, "code", None)
    status = str(getattr(error, "status", "") or "").upper()
    msg = str(error).lower()
    if "missing api key" in msg:
        return "API 키를 찾지 못했어요. Streamlit 앱 Settings → Secrets에 GEMINI_API_KEY를 저장해 주세요."
    if code == 429 or "resource_exhausted" in status or "quota" in msg or "rate limit" in msg:
        return "Gemini 사용량 한도(429)에 도달했어요. Google AI Studio에서 할당량을 확인하거나 잠시 후 다시 시도해 주세요."
    if code in (401, 403) or "permission_denied" in status or "api key not valid" in msg:
        return "API 키 인증 또는 권한 오류(401/403)예요. 키가 유효한지, Gemini API 사용이 가능한지 확인해 주세요."
    if code == 404 or "not_found" in status or "model" in msg and "not found" in msg:
        return "Gemini 모델을 찾지 못했어요(404). Secrets의 GEMINI_MODEL을 확인하거나 삭제해 기본 모델을 사용해 주세요."
    if isinstance(error, (json.JSONDecodeError, ValueError, KeyError)):
        return "Gemini가 선택지를 지정된 형식으로 보내지 않았어요. 다시 시도해 주세요."
    return f"Gemini 요청 실패: {name}" + (f" (HTTP {code})" if code else "") + ". 앱 로그에서 오류 종류를 확인해 주세요."


def ai_options(kind, count=4):
    ss=st.session_state
    context={"소재":ss.topic,"소스":ss.sauce,"소스 설명":SAUCES[ss.sauce],"등장인물":ss.character,"장소":ss.place,"이미 선택한 사건":ss.events}
    instructions={
      "character":"각각 성격과 특징이 다른 귀여운 과자 등장인물 4개. 한 줄짜리 짧은 이름과 특징. 이야기 소재를 반영해.",
      "place":"선택한 등장인물과 소재 및 소스에 어울리는 서로 다른 이야기 장소 4개. 한 줄짜리 짧은 이름.",
      "event":"앞서 선택한 모든 설정과 사건을 이어받아 다음에 일어날 법한 서로 다른 사건 4개. 이전 사건과 모순되거나 중복되면 안 됨. 각 20~45자. 정답을 요구하는 질문이 아닌 사건 선택지.",
    }
    prompt=("당신은 8~10세 어린이의 창작을 돕는 따뜻한 이야기 공방입니다. "
            "어린이에게 안전하고 쉽고 재미있는 한국어만 사용하세요. "
            "아이의 선택을 반드시 반영하세요. 딸기에서는 마법과 초현실적 사건을 피하고, 초코에서는 자유로운 판타지를 허용하고, 바닐라에서는 현실과 신비를 적절히 섞으세요. "
            "개인정보를 요청하거나 아이의 창의성을 평가하지 마세요. "
            f"상황: {json.dumps(context,ensure_ascii=False)}\n요청: {instructions[kind]}\n"
            'JSON 객체만 출력하세요: {"options":["선택지1","선택지2","선택지3","선택지4"]}')
    try:
        from google import genai
        try: key=st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        except Exception: key=os.getenv("GEMINI_API_KEY")
        if not key: raise RuntimeError("missing API key")
        try: model=st.secrets.get("GEMINI_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        except Exception: model=os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        response=genai.Client(api_key=key).models.generate_content(model=model,contents=prompt)
        raw=(response.text or "").strip()
        match=re.search(r'\{.*\}',raw,re.S)
        data=json.loads(match.group(0) if match else raw)
        options=[str(x).strip() for x in data.get("options",[]) if str(x).strip()]
        if len(options)!=count or len(set(options))!=count: raise ValueError("invalid options")
        ss.warning=""
        return options
    except Exception as e:
        ss.warning="⚠️ " + friendly_ai_error(e) + " 지금은 예시 선택지를 보여주고 있어요."
        print("Marshmallow Gemini error:", type(e).__name__, "HTTP:", getattr(e, "code", None), "status:", getattr(e, "status", None))
        if kind=="character": return CHARACTERS
        if kind=="place": return PLACES
        # Even without AI, connect events to the current character/place/topic and avoid identical repeat options.
        who=ss.character.split(" ",1)[-1] if ss.character else "주인공"
        where=ss.place.split(" ",1)[-1] if ss.place else "그곳"
        topic=ss.topic
        stems=[f"{who}가 {where}에서 {topic}에 관한 비밀을 발견했어요",f"{where}에서 {who}에게 뜻밖의 편지가 도착했어요",f"{who}가 {topic} 때문에 곤란해진 친구를 만났어요",f"{where}에서 {topic}와 관련된 새로운 길을 찾았어요",f"{who}가 친구와 함께 {topic}에 얽힌 문제를 해결하기로 했어요",f"{where}에서 모두가 힘을 모아 작은 축제를 준비했어요",f"{who}가 중요한 약속을 지키기 위해 용기를 냈어요",f"{topic}에 대한 오해가 풀리면서 새로운 친구가 생겼어요"]
        used=set(ss.events)
        pool=[x for x in stems if x not in used]
        if len(pool)<4: pool=stems
        # Rotate using number of selected events to avoid always identical options.
        shift=len(ss.events)*3 % len(pool)
        return (pool[shift:]+pool[:shift])[:4]
