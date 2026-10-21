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


def safe_error_detail(error):
    """Redact credentials from diagnostic text before showing it."""
    detail = str(error)
    try:
        key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if key:
            detail = detail.replace(str(key), "[API KEY HIDDEN]")
    except Exception:
        pass
    detail = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[API KEY HIDDEN]", detail)
    detail = re.sub(r"(?i)(key|token|secret|authorization)([=:]\s*)([^\s&,;]+)", r"\1\2[HIDDEN]", detail)
    return detail[:700]


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


def gemini_request(client, prompt, preferred):
    """Try configured model; on 404, discover models available to this API key."""
    try:
        return client.models.generate_content(model=preferred, contents=prompt), preferred
    except Exception as first:
        if getattr(first, "code", None) != 404:
            raise
        available = []
        for item in client.models.list():
            methods = getattr(item, "supported_actions", None) or getattr(item, "supported_generation_methods", None) or []
            if methods and not any("generatecontent" in str(m).lower().replace("_", "") for m in methods):
                continue
            name = str(getattr(item, "name", "") or "").removeprefix("models/")
            if name.startswith("gemini-") and not any(bad in name for bad in ("embedding", "image", "tts", "audio", "live")):
                available.append(name)
        available.sort(key=lambda name: ("flash" not in name, "pro" in name, name))
        for name in available:
            if name == preferred:
                continue
            try:
                return client.models.generate_content(model=name, contents=prompt), name
            except Exception as error:
                if getattr(error, "code", None) in (400, 404):
                    continue
                raise
        raise RuntimeError("이 API 키로 텍스트 생성 가능한 Gemini 모델을 찾지 못했어요. AI Studio에서 API 키와 모델 접근 권한을 확인해 주세요.") from first


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
        with genai.Client(api_key=key) as client:
            response, used_model = gemini_request(client, prompt, model)
            ss.active_model = used_model
        raw=(response.text or "").strip()
        match=re.search(r'\{.*\}',raw,re.S)
        data=json.loads(match.group(0) if match else raw)
        options=[str(x).strip() for x in data.get("options",[]) if str(x).strip()]
        if len(options)!=count or len(set(options))!=count: raise ValueError("invalid options")
        ss.warning=""
        return options
    except Exception as e:
        ss.warning="⚠️ " + friendly_ai_error(e) + " 지금은 예시 선택지를 보여주고 있어요. 보호자용 연결 테스트에서 상세 오류를 확인해 주세요."
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


def go(stage):
    st.session_state.stage=stage
    st.rerun()


def make_story():
    ss=st.session_state
    char=ss.character.split(" ",1)[-1]
    place=ss.place.split(" ",1)[-1]
    intro=f"옛날 옛적, {ss.topic}에 관심이 많은 {char}가 있었어요. 어느 날 {char}는 {place}에 가게 되었지요."
    paragraphs=[intro]
    for i,event in enumerate(ss.events):
        lead=["그때", "잠시 뒤", "그러던 어느 순간", "조금 후"][i%4]
        paragraphs.append(f"{lead}, {event.rstrip(' .')}.")
    paragraphs.append(ss.ending.strip())
    return "\n\n".join(paragraphs)

st.markdown('<div class="hero"><div style="font-size:3.8rem">🍡</div><h1>마시멜로</h1><b>말랑말랑, 나만의 스토리텔링 수업</b><p>상상 한 스푼, 이야기가 몽글몽글!</p></div>',unsafe_allow_html=True)
ss=st.session_state
steps=["소재와 소스","과자 친구","이야기 장소","사건 만들기","나만의 결말","동화책 완성"]
st.progress(ss.stage/5)
st.caption(f"{min(ss.stage+1,6)} / 6 · {steps[ss.stage]}")

if ss.stage==0:
    st.subheader("🍡 어떤 이야기를 만들어 볼까?")
    st.text_input("이야기 소재",key="topic",placeholder="예: 바다, 공룡, 학교, 별")
    st.markdown("#### 소스를 골라 줘!")
    st.radio("이야기 맛",list(SAUCES),key="sauce",horizontal=True)
    st.info(SAUCES[ss.sauce])
    st.caption("이름, 학교, 주소, 전화번호 같은 개인정보는 적지 말아 줘.")
    with st.expander("🔧 Gemini 연결 확인 (보호자용)"):
        try:
            api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        except Exception:
            api_key = os.getenv("GEMINI_API_KEY")
        try:
            model_name = st.secrets.get("GEMINI_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        except Exception:
            model_name = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        st.write("API 키 등록:", "✅ 감지됨" if api_key else "❌ 감지되지 않음")
        st.write("설정 모델:", model_name)
        if ss.get("active_model"):
            st.write("실제 사용 모델:", ss.active_model)
        if st.button("Gemini 테스트 요청 보내기"):
            if not api_key:
                st.error("GEMINI_API_KEY가 등록되지 않았어요.")
            else:
                try:
                    from google import genai
                    with genai.Client(api_key=api_key) as client:
                        result, used_model = gemini_request(
                            client, "한국어로 '연결 성공'이라고 짧게 답하세요.", model_name
                        )
                    if result.text and result.text.strip():
                        st.success("Gemini 연결 성공! 사용 모델: " + used_model + " · " + result.text.strip()[:80])
                    else:
                        st.error("연결되었지만 Gemini 응답이 비어 있어요.")
                except Exception as e:
                    st.error(friendly_ai_error(e))
                    st.code("오류 종류: " + type(e).__name__ + "\n상세 내용: " + safe_error_detail(e), language="text")
                    print("Marshmallow Gemini test error:", type(e).__name__, "HTTP:", getattr(e, "code", None), "status:", getattr(e, "status", None))
    if st.button("🍪 과자 친구 만나러 가기",type="primary",use_container_width=True,disabled=not ss.topic.strip()):
        ss.options=ai_options("character");go(1)

elif ss.stage==1:
    st.subheader("🍪 어떤 과자 친구와 떠날까?")
    st.caption(f"소재: {ss.topic} · 소스: {ss.sauce}")
    if ss.warning: st.warning(ss.warning)
    for i,opt in enumerate(ss.options):
        if st.button(opt,key=f"character_{i}",use_container_width=True):
            ss.character=opt;ss.options=ai_options("place");go(2)
    if st.button("← 소스 다시 고르기"):go(0)

elif ss.stage==2:
    st.subheader("🏝️ 이야기는 어디서 시작할까?")
    st.caption(f"주인공: {ss.character}")
    if ss.warning:st.warning(ss.warning)
    for i,opt in enumerate(ss.options):
        if st.button(opt,key=f"place_{i}",use_container_width=True):
            ss.place=opt;ss.events=[];ss.options=ai_options("event");go(3)
    if st.button("← 등장인물 다시 고르기"):
        ss.options=ai_options("character");go(1)

elif ss.stage==3:
    st.subheader("✨ 다음엔 어떤 일이 일어날까?")
    st.caption(f"{ss.character} · {ss.place}")
    if ss.events:
        st.markdown("**지금까지의 이야기**")
        for i,event in enumerate(ss.events,1):st.write(f"{i}. {event}")
    if ss.warning:st.warning(ss.warning)
    for i,opt in enumerate(ss.options):
        if st.button(f"☁️ {opt}",key=f"event_{len(ss.events)}_{i}",use_container_width=True):
            ss.events.append(opt)
            if len(ss.events)>=3:go(4)
            ss.options=ai_options("event");st.rerun()
    if ss.events and st.button("✏️ 이제 내가 결말을 쓸래!",type="primary",use_container_width=True):go(4)
    if st.button("← 장소 다시 고르기"):
        ss.options=ai_options("place");go(2)

elif ss.stage==4:
    st.subheader("✏️ 마지막 장면은 내가 만들어요")
    st.caption("어떤 결말이든 좋아! 한 문장만 적어도 괜찮아.")
    st.markdown("**지금까지 일어난 일**")
    st.write(f"{ss.character}가 {ss.place}에서 이야기를 시작했어요.")
    for event in ss.events:st.write(f"☁️ {event}")
    st.text_area("나만의 결말",key="ending",height=160,placeholder="그래서 주인공은 어떻게 되었을까?")
    st.text_input("동화책 제목 (선택)",key="title",placeholder=f"{ss.topic}의 비밀")
    if st.button("📖 내 동화책 완성하기",type="primary",use_container_width=True,disabled=not ss.ending.strip()):go(5)
    if st.button("← 이야기 더 만들기"):
        ss.options=ai_options("event");go(3)

elif ss.stage==5:
    title=ss.title.strip() or f"{ss.topic}의 특별한 이야기"
    story=make_story()
    st.markdown(f"## 📖 {title}")
    st.markdown(f'<div class="book">{("<p>"+"</p><p>".join(__import__("html").escape(x) for x in story.split(chr(10)+chr(10)))+"</p>")}</div>',unsafe_allow_html=True)
    st.caption("마지막 문단은 내가 직접 쓴 결말이에요 💗")
    st.download_button("📥 내 동화책 저장 (.txt)",data=f"{title}\n\n{story}",file_name=f"marshmallow_story_{datetime.now():%Y%m%d}.txt",mime="text/plain",use_container_width=True)
    if st.button("🍡 새로운 이야기 만들기",type="primary",use_container_width=True):
        for k in ["stage","topic","sauce","character","place","events","ending","title","options","warning"]:ss.pop(k,None)
        st.rerun()
