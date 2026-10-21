"""말랑말랑 스토리 오븐 — child-led storybook creator."""
import base64
import html
import io
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
st.set_page_config(page_title="말랑말랑 스토리 오븐", page_icon="🍡", layout="wide")

SAUCES = {
    "초코 🍫": "현실적이고 탄탄하게 · 실제로 일어날 법한 이야기",
    "딸기 🍓": "부드럽고 창의적으로 · 마법과 상상도 마음껏",
    "바닐라 🍦": "현실과 상상을 골고루 · 일상에 작은 신비 한 스푼",
}
GENRES = {
    "🍪 비스킷 · 오싹한 미스터리": "어린이에게 안전한 가벼운 호러·미스터리. 잔혹하거나 과도하게 무서운 장면은 금지.",
    "🍩 도넛 · 신나는 모험": "도전과 탐험, 뜻밖의 발견이 있는 모험",
    "🧁 컵케이크 · 따뜻한 우정": "친구와 마음을 나누고 서로 돕는 따뜻한 이야기",
    "🍬 캔디 · 신비한 판타지": "반짝이는 비밀과 놀라운 상상 세계",
    "🥨 프레첼 · 재미있는 코미디": "엉뚱한 오해와 유쾌한 사건이 펼쳐지는 이야기",
    "🍰 케이크 · 두근두근 감동": "작은 용기와 성장, 마음을 움직이는 이야기",
}
PLACE_FALLBACK = ["🏖️ 반짝이는 바닷가", "🌲 바람이 부는 숲", "🏡 오래된 마을", "🏰 언덕 위의 성"]

CSS = """
<style>
.stApp{background:linear-gradient(145deg,#fff4ed 0%,#fff9f3 48%,#f8f0ff 100%)}
.block-container{max-width:1100px;padding-top:1.5rem;padding-bottom:5rem}
h1,h2,h3{color:#71433e;letter-spacing:-.025em}
div.stButton>button{border-radius:20px;min-height:3.25rem;height:auto;white-space:normal;background:#fffefa;color:#6b4943;border:1px solid #f1cfc5;padding:12px 14px}
div.stButton>button:hover{background:#fff0e9;border-color:#e79e9e;color:#70423b}
div.stButton>button[kind="primary"]{background:#e68f9b;color:white;border-color:#e68f9b}
.oven-title{text-align:center;color:#743e36;font-size:clamp(1.55rem,4vw,2.8rem);font-weight:850;line-height:1.35;overflow-wrap:break-word;padding:0 8px}
.oven-tag{text-align:center;color:#ad6d69;font-size:1.08rem;margin:5px 0 15px}
.crumb{background:#fffaf6;border:1px solid #f3d8d2;border-radius:25px;padding:12px 16px;margin:12px 0;color:#94665c;text-align:center}
.soft-card{background:#fffaf7;border:1px solid #f4d8cf;border-radius:25px;padding:18px;margin:10px 0}
.book-cover{background:linear-gradient(155deg,#ffd8c5,#fff4db,#f9dbea);border:9px double #f8fff9;border-radius:22px;min-height:340px;padding:40px 25px;text-align:center;box-shadow:10px 12px 20px #b7838040}
.book-cover h1{font-family:Georgia,serif;font-size:2.7rem;margin:30px 0;color:#714139}
.book-page{background:#fffdf6;border:1px solid #e9d8bd;border-radius:18px;padding:25px 32px;line-height:2.1;min-height:280px;color:#624f46;box-shadow:4px 6px 14px #c4a78b25}
.book-page p{font-size:1.07rem;white-space:pre-wrap}
.page-no{text-align:center;color:#a88c78;font-size:.8rem;margin-top:12px}
.mascot-label{text-align:center;color:#aa6b69;font-size:.87rem;font-weight:650}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def initialize():
    defaults = dict(stage=-1, lang="한국어", topic="", sauce="바닐라 🍦", genre="", hero="", place="", events=[], ending="", title="", options=[], notice="", story=None, ai_model="", ai_error="")
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (list, dict)) else value
initialize()
ss = st.session_state

def tr(ko, en):
    return ko if ss.lang == "한국어" else en

SAUCE_EN = {"초코 🍫": "Chocolate 🍫", "딸기 🍓": "Strawberry 🍓", "바닐라 🍦": "Vanilla 🍦"}
SAUCE_DESC_EN = {
    "초코 🍫": "Grounded & realistic — believable events and clear cause and effect",
    "딸기 🍓": "Soft & imaginative — magic and playful possibilities",
    "바닐라 🍦": "A little of both — everyday life with a sprinkle of wonder",
}
GENRE_EN = {
    "🍪 비스킷 · 오싹한 미스터리": "🍪 Biscuit · Spooky Mystery",
    "🍩 도넛 · 신나는 모험": "🍩 Donut · Adventure",
    "🧁 컵케이크 · 따뜻한 우정": "🧁 Cupcake · Friendship",
    "🍬 캔디 · 신비한 판타지": "🍬 Candy · Fantasy",
    "🥨 프레첼 · 재미있는 코미디": "🥨 Pretzel · Comedy",
    "🍰 케이크 · 두근두근 감동": "🍰 Cake · Heartwarming",
}
GENRE_DESC_EN = {
    "🍪 비스킷 · 오싹한 미스터리": "A gently spooky, child-friendly mystery",
    "🍩 도넛 · 신나는 모험": "Exploration, challenges and discoveries",
    "🧁 컵케이크 · 따뜻한 우정": "Friends caring for and helping each other",
    "🍬 캔디 · 신비한 판타지": "Sparkling secrets and magical worlds",
    "🥨 프레첼 · 재미있는 코미디": "Funny surprises and silly misunderstandings",
    "🍰 케이크 · 두근두근 감동": "Courage, kindness and growing up",
}


def image_b64(path):
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def get_key_model():
    try:
        key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        model = st.secrets.get("GEMINI_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    except Exception:
        key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    return key, model


def generate(prompt):
    """Use a live client, and discover permitted text models if configured one is missing."""
    from google import genai
    key, preferred = get_key_model()
    if not key:
        raise RuntimeError("Streamlit Secrets에 GEMINI_API_KEY가 없어요.")
    with genai.Client(api_key=key) as client:
        try:
            response = client.models.generate_content(model=preferred, contents=prompt)
            used = preferred
        except Exception as first:
            if getattr(first, "code", None) != 404:
                raise
            available = []
            for item in client.models.list():
                methods = getattr(item, "supported_actions", None) or getattr(item, "supported_generation_methods", None) or []
                if methods and not any("generatecontent" in str(m).lower().replace("_", "") for m in methods):
                    continue
                name = str(getattr(item, "name", "") or "").removeprefix("models/")
                if name.startswith("gemini-") and not any(x in name for x in ("embedding", "image", "audio", "tts", "live")):
                    available.append(name)
            available.sort(key=lambda name: ("flash" not in name, "pro" in name, name))
            response = None
            used = ""
            for name in available:
                if name == preferred:
                    continue
                try:
                    response = client.models.generate_content(model=name, contents=prompt)
                    used = name
                    break
                except Exception as e:
                    if getattr(e, "code", None) not in (400, 404):
                        raise
            if response is None:
                raise RuntimeError("이 API 키로 사용할 수 있는 텍스트 생성 모델을 찾지 못했어요.") from first
    ss.ai_model = used
    if not response.text:
        raise ValueError("Gemini 응답이 비어 있어요.")
    return response.text.strip()


def parse_json(raw):
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def context():
    return dict(topic=ss.topic, sauce=ss.sauce, sauce_rule=SAUCES[ss.sauce], genre=ss.genre, genre_rule=GENRES.get(ss.genre, ""), hero=ss.hero, place=ss.place, selected_events=ss.events)


def fallback_options(kind):
    if kind == "hero":
        if ss.lang == "English": return [f"🐻 Curious Bear · loves the secrets of {ss.topic}", "🐰 Brave Rabbit · always ready for a challenge", "🐱 Clever Cat · sees things differently", "⭐ Shy Star · wants to help friends"]
        return [f"🐻 호기심 많은 곰 · {ss.topic}의 비밀을 찾는 친구", "🐰 용감한 토끼 · 작은 도전도 즐기는 친구", "🐱 재치 있는 고양이 · 문제를 다르게 보는 친구", "⭐ 수줍은 별 · 친구를 돕고 싶은 주인공"]
    if kind == "place":
        if ss.lang == "English": return [f"🏡 Little town where {ss.topic} begins", "🏖️ Sparkling beach", "🌲 Whispering forest", "🏰 Castle on the hill"]
        return [f"🏡 {ss.topic} 이야기가 시작되는 작은 마을", *PLACE_FALLBACK[:3]]
    who = ss.hero.split(" · ")[0].split(" ", 1)[-1] or "주인공"
    where = ss.place.split(" ", 1)[-1] or "그곳"
    pool = [
        f"{who}가 {where}에서 {ss.topic}에 관한 이상한 흔적을 발견했어요",
        f"{where}에 도착한 {who}에게 누군가 도움을 청했어요",
        f"{who}가 {ss.topic}와 관련된 뜻밖의 소식을 들었어요",
        f"{where}에서 새로운 친구가 나타나 비밀을 알려줬어요",
        f"{who}가 작은 실수를 만회할 기회를 발견했어요",
        f"{where}에서 모두 함께 풀어야 할 문제가 생겼어요",
        f"{who}가 친구와 함께 용감한 선택을 했어요",
        f"{ss.topic}에 대한 오해가 풀릴 중요한 단서를 찾았어요",
    ]
    if ss.lang == "English":
        pool = [f"{who} discovers a clue about {ss.topic} in {where}", f"A stranger asks {who} for help in {where}", f"{who} receives surprising news about {ss.topic}", f"A new friend reveals a secret in {where}", f"{who} gets a chance to fix a mistake", f"Everyone in {where} must solve a problem together", f"{who} makes a brave choice with a friend", f"An important clue changes what everyone knows about {ss.topic}"]
    remaining = [x for x in pool if x not in ss.events]
    return (remaining + pool)[:4]


def options_for(kind):
    descriptions = {
        "hero": "주제와 장르에 어울리는 서로 다른 이야기 주인공 네 명. 한 항목은 '이모지 이름 · 특징' 형식. 과자 캐릭터에 한정하지 말 것.",
        "place": "주제, 장르, 소스, 선택된 주인공에 잘 맞는 서로 다른 장소 네 곳. 한 항목은 '이모지 장소 이름' 형식.",
        "event": "이미 선택한 모든 사건을 이어받아 다음에 일어날 수 있는 사건 네 개. 선택에 따라 이야기가 실질적으로 달라지게 할 것. 각 15~45자. 이전 사건과 중복·모순 금지. 결말은 미리 쓰지 말 것.",
    }
    prompt = f"""당신은 8~10세 아이가 스스로 이야기를 만드는 창작 공방의 AI입니다.
아이가 선택한 소재, 소스, 장르, 주인공, 장소, 이전 사건을 반드시 반영하세요.
초코: 마법 없이 현실적인 인과관계와 개연성. 딸기: 창의적인 상상과 판타지. 바닐라: 두 성향의 균형.
호러 장르라도 잔혹함, 폭력, 공포 자극을 피하고 안전하고 재미있는 미스터리로 만드세요.
개인정보를 요구하지 말고 창의력 점수를 매기지 마세요.
답변 언어: {"Korean" if ss.lang == "한국어" else "English"}. English 선택 시 선택지와 설명을 영어로 작성하세요.
상황: {json.dumps(context(), ensure_ascii=False)}
요청: {descriptions[kind]}
반드시 JSON만 출력: {{"options":["선택지1","선택지2","선택지3","선택지4"]}}"""
    try:
        result = parse_json(generate(prompt))
        opts = [str(x).strip() for x in result["options"] if str(x).strip()]
        if len(opts) != 4 or len(set(opts)) != 4 or any(x in ss.events for x in opts):
            raise ValueError("선택지 형식 또는 중복 오류")
        ss.notice = ""
        return opts
    except Exception as e:
        ss.ai_error = f"{type(e).__name__} (HTTP {getattr(e, 'code', '—')})"
        ss.notice = "AI 선택지를 생성하지 못해 임시 선택지를 보여주고 있어요. 보호자용 연결 확인을 살펴봐 주세요."
        return fallback_options(kind)


def story_fallback():
    who = ss.hero.split(" · ")[0].split(" ", 1)[-1]
    where = ss.place.split(" ", 1)[-1]
    paragraphs = ([f"Once upon a time, {who} loved thinking about {ss.topic}. One day, {who} set out for {where}."] if ss.lang == "English" else [f"{ss.topic}에 관심이 많은 {who}가 있었어요. 어느 날 {who}는 {where}에 가기로 했지요."])
    for i, event in enumerate(ss.events):
        paragraphs.append((("Then, " if ss.lang == "English" else ["그런데", "그러던 중", "잠시 뒤", "그 순간"][i % 4] + ", ") + event.rstrip(". ") + "."))
    paragraphs.append(ss.ending.strip())
    return {"title": ss.title.strip() or (f"The Soft Secret of {ss.topic}" if ss.lang == "English" else f"{ss.topic}와 말랑말랑한 비밀"), "pages": paragraphs, "ending_note": "아이의 결말 원문을 유지한 임시 버전"}


def finish_story():
    prompt = f"""당신은 8~10세 아이가 직접 선택한 소재와 사건으로 그림책을 편집하는 어린이 동화 작가입니다.
아이의 선택이 전체 줄거리의 원인과 결과에 반드시 반영되어야 합니다. 전체 4~6개의 짧은 페이지, 페이지당 2~4문장, 쉽고 생생한 한국어.
초코는 현실적이고 탄탄한 개연성, 딸기는 부드럽고 창의적인 판타지, 바닐라는 혼합형.
장르의 분위기를 지키되 아동 친화적이고 과도한 공포나 폭력은 금지.
아이의 결말은 그대로 붙이지 말고 앞선 문단과 어울리는 문체로 자연스럽게 다듬으세요. 하지만 아이가 쓴 결말의 핵심 사건, 선택, 의미와 결과는 절대로 바꾸지 마세요. 새로운 결말을 만들어내지 마세요.
선택한 사건들의 순서를 지키고, 등장인물과 장소가 바뀌지 않도록 하세요.
전체 동화의 언어: {"Korean" if ss.lang == "한국어" else "English"}. 영어 선택 시 제목과 모든 페이지를 자연스러운 영어로 쓰고 아이의 결말 뜻을 보존하세요.
설정: {json.dumps(context(), ensure_ascii=False)}
아이의 결말 원문: {ss.ending!r}
아이의 제목(비어 있으면 만들어도 됨): {ss.title!r}
반드시 JSON만 출력: {{"title":"동화 제목","pages":["첫 장 문단","둘째 장 문단","셋째 장 문단","마지막 장 문단"]}}"""
    try:
        result = parse_json(generate(prompt))
        pages = [str(x).strip() for x in result["pages"] if str(x).strip()]
        if not 3 <= len(pages) <= 7:
            raise ValueError("동화책 페이지 수 오류")
        ss.story = {"title": str(result.get("title") or ss.title or ss.topic).strip(), "pages": pages, "ending_note": "아이의 결말을 전체 문체에 맞게 다듬었어요"}
        ss.notice = ""
    except Exception as e:
        ss.story = story_fallback()
        ss.ai_error = f"{type(e).__name__} (HTTP {getattr(e, 'code', '—')})"
        ss.notice = "AI 편집이 어려워 아이가 고른 내용을 그대로 엮었어요."


def go(stage):
    ss.stage = stage
    st.rerun()


def draw_scene(page_number):
    """Locally drawn context-sensitive storybook scene; no image API required."""
    W, H = 1000, 520
    im = Image.new("RGB", (W, H), (255, 241, 223))
    d = ImageDraw.Draw(im)
    sea = any(x in ss.place + ss.topic for x in ("바다", "해변", "해안", "섬", "호수"))
    forest = any(x in ss.place + ss.topic for x in ("숲", "나무", "산", "정글"))
    castle = any(x in ss.place for x in ("성", "궁", "탑"))
    for y in range(H):
        f = y / H
        if ss.sauce.startswith("초코"):
            top, bottom = (255, 227, 201), (247, 238, 224)
        elif ss.sauce.startswith("딸기"):
            top, bottom = (255, 213, 226), (241, 229, 255)
        else:
            top, bottom = (254, 224, 218), (233, 232, 255)
        c = tuple(int(top[i] * (1-f) + bottom[i]*f) for i in range(3))
        d.line((0,y,W,y), fill=c)
    # sky details
    d.ellipse((720,50,840,170), fill=(255,246,194))
    for x,y in [(125,95),(380,125),(590,55),(885,110)]:
        d.ellipse((x-45,y,x+45,y+30), fill=(255,250,246))
        d.ellipse((x-15,y-22,x+45,y+25), fill=(255,250,246))
    if sea:
        d.rectangle((0,310,W,H), fill=(122,192,207))
        for y in (340,385,430,475):
            for x in range(0,W,175):
                d.arc((x+page_number*23%90,y,x+100+page_number*23%90,y+18),0,160,fill=(232,249,247),width=5)
        d.polygon([(0,460),(180,380),(350,520),(0,520)],fill=(244,213,159))
    elif forest:
        d.rectangle((0,410,W,H),fill=(162,197,151))
        for x,h in [(80,210),(240,290),(680,270),(860,220)]:
            d.rectangle((x-14,420-h//2,x+14,440),fill=(143,100,83))
            d.ellipse((x-75,320-h,x+75,440-h//2),fill=(110,165,129))
            d.ellipse((x-50,275-h,x+55,385-h//2),fill=(133,186,144))
    else:
        d.polygon([(0,385),(230,305),(470,390),(700,320),(1000,370),(1000,520),(0,520)],fill=(191,205,170))
        d.rectangle((0,445,W,H),fill=(163,198,156))
        if castle:
            d.rectangle((600,220,850,445),fill=(240,205,194))
            for x in (620,790):
                d.rectangle((x,160,x+45,350),fill=(220,176,173))
                d.polygon([(x-10,160),(x+22,110),(x+55,160)],fill=(152,112,155))
        else:
            d.rectangle((620,285,850,440),fill=(249,220,196))
            d.polygon([(585,285),(735,180),(885,285)],fill=(194,130,123))
            d.rectangle((710,350,758,440),fill=(165,121,102))
    # illustrated main character cookie silhouette
    cx = 350 + (page_number%3)*55
    cy = 335
    d.ellipse((cx-82,cy-92,cx+82,cy+74),fill=(233,179,132),outline=(166,116,92),width=5)
    d.ellipse((cx-67,cy-135,cx-15,cy-74),fill=(233,179,132),outline=(166,116,92),width=4)
    d.ellipse((cx+15,cy-135,cx+67,cy-74),fill=(233,179,132),outline=(166,116,92),width=4)
    d.ellipse((cx-33,cy-22,cx-19,cy-7),fill=(79,57,52))
    d.ellipse((cx+19,cy-22,cx+33,cy-7),fill=(79,57,52))
    d.arc((cx-20,cy-2,cx+20,cy+30),0,180,fill=(95,62,57),width=4)
    d.ellipse((cx-53,cy+2,cx-32,cy+18),fill=(235,140,147))
    d.ellipse((cx+32,cy+2,cx+53,cy+18),fill=(235,140,147))
    # narrative symbols depend on the chosen event and topic
    event = ss.events[min(max(page_number-1,0),len(ss.events)-1)] if ss.events else ss.topic
    if any(x in event for x in ("편지","소식","지도")):
        d.rounded_rectangle((610,300,750,395),radius=10,fill=(255,247,219),outline=(178,130,113),width=4)
        d.line((610,300,680,355,750,300),fill=(178,130,113),width=3)
    elif any(x in event for x in ("비밀","단서","발견","수수께끼")):
        d.rounded_rectangle((625,330,755,420),radius=12,fill=(173,119,84),outline=(108,78,67),width=5)
        d.rectangle((625,348,755,365),fill=(248,216,119))
        d.ellipse((678,354,703,382),fill=(255,247,195))
    else:
        for x,y in [(650,310),(745,355),(830,285)]:
            d.ellipse((x,y,x+22,y+22),fill=(255,236,139))
            d.line((x+11,y-12,x+11,y+34),fill=(255,250,215),width=3)
    b=io.BytesIO()
    im.save(b,format="PNG")
    return b.getvalue()


def html_book():
    title = html.escape(ss.story["title"])
    sections = []
    for i, para in enumerate(ss.story["pages"]):
        picture = base64.b64encode(draw_scene(i)).decode("ascii")
        sections.append(f'<section class="page"><img src="data:image/png;base64,{picture}"/><p>{html.escape(para)}</p><small>{i+1}</small></section>')
    return ("<!doctype html><html lang='"+("ko" if ss.lang == "한국어" else "en")+"'><meta charset='utf-8'><title>"+title+"</title><style>body{background:#f9eee9;font-family:serif;color:#624d42;max-width:750px;margin:30px auto;padding:15px}.cover,.page{background:#fffdf5;padding:32px;border-radius:15px;box-shadow:0 4px 15px #ad9b8940;margin:25px 0;text-align:center;page-break-after:always}.cover{padding:100px 20px;background:#fce4da}h1{font-size:2.7em}.page img{width:100%;border-radius:14px}.page p{text-align:left;line-height:2.1;font-size:1.2em;white-space:pre-wrap}.page small{color:#b2a096}@media print{body{background:white}.page,.cover{box-shadow:none}}</style><div class='cover'><h3>🍡 "+tr("말랑말랑 스토리 오븐", "Squishy Story Oven")+"</h3><h1>"+title+"</h1><p>"+tr("내가 구운 세상에 하나뿐인 이야기", "My one-of-a-kind story")+"</p></div>"+"".join(sections)+"</html>")

# Language is available on every screen, including the cover.
_, lang_column = st.columns([5, 1.6])
with lang_column:
    st.selectbox("Language / 언어", ["한국어", "English"], key="lang", label_visibility="collapsed")

if ss.stage == -1:
    # The cover is the exact user-provided image. No duplicated headline or fake button.
    left, middle, right = st.columns([1, 2.4, 1])
    with middle:
        st.image(str(BASE / "story_oven_home.png"), use_container_width=True)
        if st.button(tr("🍡 이야기 구우러 가기 →", "🍡 Let's Bake a Story →"), type="primary", use_container_width=True, key="real_start_button"):
            go(0)
    st.stop()

st.markdown(f'<div class="oven-title">🍡 {tr("말랑말랑 스토리 오븐", "Squishy Story Oven")}</div><div class="oven-tag">{tr("내 마음속 이야기를 맛있게 구워볼까요?", "Let's bake the story in your imagination!")}</div>', unsafe_allow_html=True)
if (BASE / "marshmallow_mascot.png").exists():
    stretch = 1.0 + min(ss.stage, 5) * 0.11 + min(len(ss.events), 3) * 0.06
    uri = image_b64(BASE / "marshmallow_mascot.png")
    st.markdown(f'<div style="height:{int(125*stretch)}px;display:flex;align-items:center;justify-content:center;overflow:visible"><img src="data:image/png;base64,{uri}" style="height:105px;transform:scaleY({stretch});transform-origin:bottom center;transition:transform .5s ease"></div><div class="mascot-label">{tr("이야기가 자랄수록 마시멜로도 쭈욱~!", "Your marshmallow stretches as your story grows!")}</div>',unsafe_allow_html=True)
steps = (["소재와 소스", "장르 고르기", "주인공 고르기", "장소 고르기", "사건 만들기", "결말 쓰기", "동화책 완성"] if ss.lang == "한국어" else ["Topic & sauce", "Pick a genre", "Choose a hero", "Choose a place", "Story events", "Write an ending", "Your storybook"])
st.progress(ss.stage/6)
st.markdown(f'<div class="crumb">{ss.stage+1} / 7 · {steps[ss.stage]}</div>',unsafe_allow_html=True)

if ss.stage == 0:
    st.subheader(tr("🥣 나만의 이야기 재료를 골라봐!", "🥣 Choose your story ingredients!"))
    st.text_input(tr("이야기 소재", "Story topic"),key="topic",placeholder=tr("예: 바다, 공룡, 학교, 우주", "e.g. Ocean, dinosaurs, school, space"))
    st.markdown(tr("#### 소스를 골라 줘!", "#### Pick your sauce!"))
    cols=st.columns(3)
    for col, name in zip(cols, SAUCES):
        with col:
            if st.button(("✓ " if ss.sauce==name else "")+(name if ss.lang == "한국어" else SAUCE_EN[name]), key="sauce_"+name, use_container_width=True, type="primary" if ss.sauce==name else "secondary"):
                ss.sauce=name
                st.rerun()
    st.info(tr(SAUCES[ss.sauce], SAUCE_DESC_EN[ss.sauce]))
    st.caption(tr("이름·학교·주소·전화번호처럼 개인정보는 입력하지 말아 줘.", "Please do not enter personal details like names, schools, addresses or phone numbers."))
    with st.expander(tr("🔧 Gemini 연결 확인 (보호자용)", "🔧 Gemini connection check (for adults)")):
        key,model=get_key_model()
        st.write(tr("API 키:", "API key:"), tr("✅ 감지됨", "✅ Detected") if key else tr("❌ 없음", "❌ Missing"))
        st.write(tr("설정 모델:", "Configured model:"),model)
        if ss.ai_model: st.write(tr("사용한 모델:", "Model used:"),ss.ai_model)
        if st.button(tr("Gemini 연결 테스트", "Test Gemini connection")):
            try:
                result=generate(tr("한국어로 '연결 성공'이라고만 답해 줘.", "Reply with only: Connection successful."))
                st.success(f"{tr('연결 성공', 'Connected')} ({ss.ai_model}): {result[:100]}")
            except Exception as e:
                st.error(f"{type(e).__name__} · HTTP {getattr(e,'code','—')}")
                st.caption(tr("모델 권한, 사용량 및 API 키 설정을 확인해 주세요. API 키는 공유하지 마세요.", "Check model access, quota and API key settings. Never share your key."))
    if st.button(tr("🍡 이야기 구워보기 →", "🍡 Start baking →"),type="primary",use_container_width=True,disabled=not ss.topic.strip()): go(1)

elif ss.stage == 1:
    st.subheader(tr("🍪 어떤 장르로 구워볼까?", "🍪 What kind of story shall we bake?"))
    st.caption(f"{tr('소재', 'Topic')}: {ss.topic} · {tr('소스', 'Sauce')}: {SAUCE_EN[ss.sauce] if ss.lang == 'English' else ss.sauce}")
    cols=st.columns(2)
    for i,(name,description) in enumerate(GENRES.items()):
        with cols[i%2]:
            if st.button((name+"\n\n"+description.split(".")[0]) if ss.lang == "한국어" else (GENRE_EN[name]+"\n\n"+GENRE_DESC_EN[name]),key="genre_"+str(i),use_container_width=True):
                ss.genre=name
                ss.options=options_for("hero")
                go(2)
    if st.button(tr("← 소재 다시 고르기", "← Change topic")):go(0)

elif ss.stage == 2:
    st.subheader(tr("🐻 이 이야기의 주인공은 누구일까?", "🐻 Who will be the hero?"))
    st.caption(f"{GENRE_EN.get(ss.genre,ss.genre) if ss.lang == 'English' else ss.genre} · {SAUCE_EN[ss.sauce] if ss.lang == 'English' else ss.sauce}")
    if ss.notice:st.warning(tr(ss.notice, "AI is unavailable, so example choices are shown. Please check the adult connection settings."))
    for i,opt in enumerate(ss.options):
        if st.button(opt,key=f"hero_{i}",use_container_width=True):
            ss.hero=opt
            ss.options=options_for("place")
            go(3)
    if st.button(tr("← 장르 다시 고르기", "← Change genre")):go(1)

elif ss.stage == 3:
    st.subheader(tr("🏡 이야기는 어디서 시작할까?", "🏡 Where will the story begin?"))
    st.caption(f"{tr('주인공', 'Hero')}: {ss.hero}")
    if ss.notice:st.warning(tr(ss.notice, "AI is unavailable, so example choices are shown. Please check the adult connection settings."))
    for i,opt in enumerate(ss.options):
        if st.button(opt,key=f"place_{i}",use_container_width=True):
            ss.place=opt
            ss.events=[]
            ss.options=options_for("event")
            go(4)
    if st.button(tr("← 주인공 다시 고르기", "← Change hero")):
        ss.options=options_for("hero")
        go(2)

elif ss.stage == 4:
    st.subheader(tr("✨ 다음엔 무슨 일이 일어날까?", "✨ What happens next?"))
    st.caption(f"{ss.hero} · {ss.place} · {GENRE_EN.get(ss.genre,ss.genre) if ss.lang == 'English' else ss.genre}")
    if ss.events:
        st.markdown(tr("**지금까지 구운 이야기 재료**", "**Your story so far**"))
        for i,event in enumerate(ss.events,1):st.write(f"{i}. {event}")
    if ss.notice:st.warning(tr(ss.notice, "AI is unavailable, so example choices are shown. Please check the adult connection settings."))
    for i,opt in enumerate(ss.options):
        if st.button("☁️ "+opt,key=f"event_{len(ss.events)}_{i}",use_container_width=True):
            ss.events.append(opt)
            if len(ss.events)>=3:go(5)
            ss.options=options_for("event")
            st.rerun()
    if ss.events and st.button(tr("✏️ 이제 결말을 쓸래!", "✏️ I want to write the ending!"),type="primary",use_container_width=True):go(5)
    if st.button(tr("← 장소 다시 고르기", "← Change place")):
        ss.options=options_for("place")
        go(3)

elif ss.stage == 5:
    st.subheader(tr("✏️ 마지막 장면은 내가 만들어요", "✏️ The final scene is yours!"))
    st.info(tr("결말은 네가 정해! AI는 네가 쓴 뜻을 지키면서 이야기 문체에 맞게 다듬어 줄 거야.", "You decide the ending! AI will polish the wording while keeping your ideas and meaning."))
    st.markdown(f"**{tr('주인공', 'Hero')}:** {ss.hero}  ·  **{tr('장소', 'Place')}:** {ss.place}")
    for event in ss.events:st.write("☁️ "+event)
    st.text_area(tr("나만의 결말", "My ending"),key="ending",height=160,placeholder=tr("주인공은 어떻게 문제를 해결했을까? 마지막에 어떤 일이 일어났을까?", "How does the hero solve the problem? What happens at the end?"))
    st.text_input(tr("동화책 제목 (선택)", "Story title (optional)"),key="title",placeholder=(f"A special story about {ss.topic}" if ss.lang == "English" else f"{ss.topic}의 특별한 이야기"))
    if st.button(tr("📚 동화책 오븐에 넣기", "📚 Bake my storybook"),type="primary",use_container_width=True,disabled=not ss.ending.strip()):
        with st.spinner(tr("이야기를 다듬고 그림책을 굽고 있어요…", "Polishing the story and baking your book…")):
            finish_story()
        go(6)
    if st.button(tr("← 사건 더 고르기", "← Add more events")):
        ss.options=options_for("event")
        go(4)

elif ss.stage == 6:
    st.subheader(tr("📖 짜잔! 나만의 동화책이 완성됐어", "📖 Ta-da! Your storybook is ready!"))
    if ss.notice:st.warning(tr(ss.notice, "AI is unavailable, so example choices are shown. Please check the adult connection settings."))
    title=ss.story["title"]
    st.markdown(f'<div class="book-cover"><div style="font-size:4rem">🍡 📖 ✨</div><p>{tr("말랑말랑 스토리 오븐", "Squishy Story Oven")}</p><h1>{html.escape(title)}</h1><p>{tr("내가 만든 세상에 하나뿐인 이야기", "My one-of-a-kind story")}</p></div>',unsafe_allow_html=True)
    for i,para in enumerate(ss.story["pages"]):
        st.image(draw_scene(i),use_container_width=True)
        st.markdown(f'<div class="book-page"><p>{html.escape(para)}</p><div class="page-no">— {i+1} —</div></div>',unsafe_allow_html=True)
        st.write("")
    st.caption(tr(ss.story.get("ending_note",""), "The ending has been polished to fit the story."))
    with st.expander(tr("✏️ 내가 처음 쓴 결말 보기", "✏️ See my original ending")):
        st.write(ss.ending)
    st.download_button(tr("📥 그림이 포함된 동화책 다운로드 (.html)", "📥 Download illustrated storybook (.html)"),data=html_book().encode("utf-8"),file_name=f"marshmallow_story_{datetime.now():%Y%m%d}.html",mime="text/html",use_container_width=True)
    st.caption(tr("HTML 파일을 브라우저로 열어 인쇄 → PDF로 저장할 수도 있어요. 그림은 선택한 배경·사건을 바탕으로 앱이 직접 그린 삽화예요.", "Open the HTML in a browser and use Print → Save as PDF. Illustrations are generated locally from your choices."))
    if st.button(tr("🍡 새 이야기 굽기", "🍡 Bake another story"),type="primary",use_container_width=True):
        for key in ("stage","topic","sauce","genre","hero","place","events","ending","title","options","notice","story","ai_model","ai_error"):
            ss.pop(key,None)
        st.rerun()
