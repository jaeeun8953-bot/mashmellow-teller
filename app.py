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
.block-container{max-width:1100px;padding-top:4rem;padding-bottom:5rem}
h1,h2,h3{color:#71433e;letter-spacing:-.025em}
div.stButton>button{border-radius:20px;min-height:3.7rem;height:auto;white-space:normal;background:#fffefa;color:#6b4943;border:1px solid #f1cfc5;padding:15px 18px;font-size:1.12rem;font-weight:750;line-height:1.5;letter-spacing:-.015em}
/* Ensure text in all Streamlit buttons, including option cards, is legible. */
div.stButton>button p,div.stButton>button span,div.stButton>button [data-testid="stMarkdownContainer"]{font-size:inherit!important;font-weight:750!important;line-height:1.5!important}
div.stDownloadButton>button{border-radius:20px;min-height:3.7rem;padding:15px 18px;font-size:1.12rem;font-weight:750;line-height:1.5}
div.stDownloadButton>button p,div.stDownloadButton>button span{font-size:inherit!important;font-weight:750!important}
@media(max-width:600px){div.stButton>button,div.stDownloadButton>button{font-size:1.04rem;min-height:3.5rem;padding:13px 12px}}
div.stButton>button:hover{background:#fff0e9;border-color:#e79e9e;color:#70423b}
div.stButton>button[kind="primary"]{background:#e68f9b;color:white;border-color:#e68f9b}
.oven-title{text-align:center;color:#743e36;font-size:clamp(1.55rem,4vw,2.8rem);font-weight:850;line-height:1.35;overflow-wrap:break-word;padding:0 8px}
.oven-tag{text-align:center;color:#ad6d69;font-size:1.08rem;margin:5px 0 15px}
.crumb{background:#fffaf6;border:1px solid #f3d8d2;border-radius:25px;padding:12px 16px;margin:12px 0;color:#94665c;text-align:center}
.soft-card{background:#fffaf7;border:1px solid #f4d8cf;border-radius:25px;padding:18px;margin:10px 0}
.book-cover{background:linear-gradient(155deg,#ffd8c5,#fff4db,#f9dbea);border:9px double #f8fff9;border-radius:22px;min-height:340px;padding:40px 25px;text-align:center;box-shadow:10px 12px 20px #b7838040}
.book-cover h1{font-family:Georgia,serif;font-size:2.7rem;margin:30px 0;color:#714139}
/* Collectible illustrated keepsake: bookbinding, legible prose, elegant cover */
.keepsake-shell{max-width:900px;margin:12px auto 28px;padding:14px;background:#f2d8cc;border-radius:25px;box-shadow:0 20px 42px #89635430}
.keepsake-book{background:#fffaf0;border:1px solid #d8bca4;border-left:13px solid #b9757b;border-radius:12px 22px 22px 12px;padding:clamp(23px,5vw,60px);box-shadow:inset 6px 0 10px #bda08830,6px 7px 0 #d3b6a4}
.keepsake-label{text-align:center;color:#a97b71;font-size:.78rem;letter-spacing:.2em}
.keepsake-book h2{text-align:center;color:#734a42;font-family:Georgia,"Noto Serif KR",serif;font-size:clamp(1.65rem,4vw,2.6rem);line-height:1.45;margin:18px auto}
.keepsake-ornament{text-align:center;color:#d6a774;margin:15px 0 25px;letter-spacing:.5em}
.keepsake-illustration{display:block;width:100%;height:auto;max-height:470px;object-fit:contain;margin:8px auto 30px;border:8px solid #fff;box-shadow:0 5px 18px #8c665333;border-radius:8px}
.keepsake-text{max-width:690px;margin:0 auto}
.keepsake-text p{color:#55443d;line-height:2.15;font-size:clamp(1rem,2.2vw,1.14rem);white-space:pre-wrap;overflow-wrap:anywhere;margin:1.4em 0;text-indent:.6em}
.keepsake-end{text-align:center;color:#b98c7b;font-size:1.15rem;letter-spacing:.5em;margin-top:30px}
@media(max-width:600px){.keepsake-shell{padding:7px}.keepsake-book{padding:22px 16px;border-left-width:7px}}
/* A readable illustrated book: visible scene, textured paper and a central book seam. */
.picturebook-wrap{padding:clamp(12px,3vw,32px);background:linear-gradient(135deg,#dbaaa2,#f8dbbf 42%,#d9b3a7);border-radius:25px;box-shadow:0 16px 30px #a8797140}
.picturebook{position:relative;overflow:hidden;background:linear-gradient(90deg,#e9d5b8 0%,#fff9e9 4%,#fffdf4 49%,#f0e3cc 50%,#fffdf4 52%,#fff9e9 96%,#e8d4b6 100%);border:1px solid #d9bca0;border-radius:12px 28px 28px 12px;box-shadow:inset 8px 0 13px #9e78541f,inset -9px 0 13px #9e78541c,5px 8px 0 #d1b598;padding:clamp(22px,5vw,55px)}
.picturebook:before{content:"";position:absolute;left:49.8%;top:0;bottom:0;width:2px;background:linear-gradient(90deg,#cfb89a77,#ffffff9e);pointer-events:none;opacity:.38}
.picturebook h2{text-align:center;font-family:Georgia,"Noto Serif KR",serif;font-size:clamp(1.5rem,3.7vw,2.4rem);color:#75473d;margin:6px 0 12px;line-height:1.4}
.picturebook .book-ornament{text-align:center;color:#d5a46d;letter-spacing:.5em;margin-bottom:22px}
.picturebook .scene-window{display:block;width:100%;height:clamp(185px,29vw,330px);object-fit:cover;border-radius:15px;border:7px solid #fff7e7;box-shadow:0 3px 12px #ab877b3d;margin:0 auto 28px}
.picturebook .book-prose{max-width:760px;margin:auto}
.picturebook p{font-size:clamp(1rem,2.2vw,1.15rem);line-height:2.15;color:#604c43;white-space:pre-wrap;margin:1.25em 0;overflow-wrap:anywhere}
.picturebook .book-end{text-align:center;color:#c59a78;letter-spacing:.9em;margin-top:28px}
@media(max-width:650px){.picturebook-wrap{padding:9px}.picturebook{padding:22px 19px}.picturebook:before{display:none}}
.story-paper{position:relative;isolation:isolate;overflow:hidden;background:#fffaf0;border:1px solid #e7cdb6;border-radius:17px;padding:clamp(24px,6vw,62px);box-shadow:0 8px 24px #ad8a7052;line-height:2.15;color:#59493f}
.story-paper::before{content:"";position:absolute;inset:0;z-index:-1;background-image:linear-gradient(180deg,rgba(255,251,239,.72) 0%,rgba(255,251,239,.86) 35%,rgba(255,251,239,.96) 100%),var(--story-art);background-size:cover,100% auto;background-position:center,center top;background-repeat:no-repeat;opacity:1}
.story-paper::after{content:"✦  ✧  ✦";display:block;text-align:center;color:#c9a58b;letter-spacing:1.2rem;margin-top:20px}
.story-paper h2{font-family:Georgia,"Noto Serif KR",serif;text-align:center;font-size:clamp(1.5rem,4vw,2.3rem);margin:0 0 8px;color:#704b41}
.story-paper .story-brand{text-align:center;color:#9b7c70;font-size:.84rem;margin-bottom:22px;letter-spacing:.04em}
.story-paper p{font-size:clamp(1rem,2.3vw,1.13rem);white-space:pre-wrap;margin:1.2em 0;line-height:2.2;overflow-wrap:anywhere}
.book-page{background:#fffdf6;border:1px solid #e9d8bd;border-radius:18px;padding:25px 32px;line-height:2.1;min-height:280px;color:#624f46;box-shadow:4px 6px 14px #c4a78b25}
.book-page p{font-size:1.07rem;white-space:pre-wrap}
.page-no{text-align:center;color:#a88c78;font-size:.8rem;margin-top:12px}
.mascot-label{text-align:center;color:#aa6b69;font-size:.87rem;font-weight:650}
/* Twisted pastel marshmallow inspired by the user's spiral candy reference. */
.marsh-scene{position:relative;margin:14px 4px 6px;padding:15px 12px 5px;min-height:158px;background:radial-gradient(ellipse at 50% 68%,#ffe8e4 0%,#fff7f0 65%,transparent 78%);border-radius:26px}
.marsh-runway{position:relative;width:100%;height:118px;overflow:visible}
.marsh-body{position:absolute;left:0;top:10px;height:90px;min-width:105px;box-sizing:border-box;border-radius:999px;background-image:var(--soft-marshmallow);background-repeat:no-repeat;background-position:center;background-size:100% 100%;filter:drop-shadow(0 8px 8px #b7899440);transition:width .75s cubic-bezier(.22,.8,.26,1);animation:marsh-squish .8s ease both}
.marsh-sparkle{position:absolute;right:0;top:0;color:#e8a54b;font-size:22px;animation:twinkle 1.8s ease-in-out infinite}
.marsh-caption{text-align:center;color:#9b6a65;font-size:.91rem;font-weight:650;margin:5px 0 12px}
@keyframes marsh-squish{0%{transform:scaleY(.85) skewX(-3deg)}55%{transform:scaleY(1.08) skewX(2deg)}100%{transform:scaleY(1) skewX(0)}}
@keyframes twinkle{50%{opacity:.45;transform:scale(.8)}}
@media(max-width:520px){.marsh-scene{min-height:140px}.marsh-runway{height:105px}.marsh-body{height:75px}}
@media(prefers-reduced-motion:reduce){.marsh-body,.marsh-sparkle{animation:none;transition:none}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def initialize():
    defaults = dict(stage=-1, lang="한국어", topic="", sauce="바닐라 🍦", genre="", hero="", place="", events=[], ending="", title="", options=[], notice="", story=None, ai_model="", ai_error="", continuation_start=0, previous_story_text="", continuation_count=0)
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
    return dict(topic=ss.topic, sauce=ss.sauce, sauce_rule=SAUCES[ss.sauce], genre=ss.genre, genre_rule=GENRES.get(ss.genre, ""), hero=ss.hero, place=ss.place, selected_events=ss.events, previous_story=getattr(ss,"previous_story_text",""))


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
이미 완성한 이야기가 있으면 그 이야기를 처음부터 다시 쓰지 말고 바로 다음 사건으로 이어지는 후속편을 작성하세요.
후속편에서는 기존 등장인물과 장소를 유지하고, 이전 결말에서 자연스럽게 출발하세요.
이번 후속편에서 새로 선택한 사건: {json.dumps(ss.events[ss.continuation_start:],ensure_ascii=False)}.
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


def draw_scene(page_number=0):
    """Draw one decorative illustration reflecting the actual story and selected setting.

    This is procedural art, not an AI-generated picture; it deliberately avoids
    reusing the same generic cookie character/castle in unrelated stories.
    """
    W,H=1100,610
    story=ss.story or {}
    full=" ".join([ss.topic,ss.hero,ss.place,ss.genre, *ss.events,
                   str(story.get("title","")), *story.get("pages",[]) ]).lower()
    def has(*words):return any(w in full for w in words)
    if has("바다","해변","파도","섬","ocean","sea","beach","pirate"):
        theme="sea"
    elif has("우주","별","달","행성","로켓","space","moon","planet","star"):
        theme="space"
    elif has("숲","나무","정글","forest","woods","tree"):
        theme="forest"
    elif has("학교","교실","도서관","school","library","classroom"):
        theme="school"
    elif has("눈","겨울","얼음","snow","winter","ice"):
        theme="snow"
    elif has("성","궁전","castle","palace"):
        theme="castle"
    elif has("사막","모래","desert"):
        theme="desert"
    else:
        theme="meadow"
    palettes={
      "sea":((216,244,250),(246,252,242)),"space":((219,218,247),(252,237,248)),
      "forest":((226,244,222),(253,246,226)),"school":((255,235,221),(252,248,233)),
      "snow":((229,245,252),(253,250,252)),"castle":((247,221,234),(253,246,228)),
      "desert":((255,233,204),(255,249,229)),"meadow":((252,232,229),(253,249,225))}
    top,bottom=palettes[theme]
    im=Image.new("RGB",(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H;d.line((0,y,W,y),fill=tuple(int(top[i]*(1-t)+bottom[i]*t) for i in range(3)))
    # Gentle decorative sun, clouds and sparkles.
    d.ellipse((850,66,990,206),fill=(255,248,200))
    for x,y in ((140,130),(390,85),(620,158)):
        d.ellipse((x,y,x+118,y+37),fill=(255,252,250))
        d.ellipse((x+30,y-27,x+100,y+32),fill=(255,252,250))
    if theme=="sea":
        d.rectangle((0,335,W,H),fill=(149,210,218))
        for y in (365,415,475,530):
            for x in range(30,W,160):d.arc((x,y,x+105,y+30),0,165,fill=(237,253,248),width=6)
        d.polygon(((0,475),(240,400),(395,610),(0,610)),fill=(245,223,174))
        d.polygon(((685,400),(770,300),(825,400)),fill=(255,247,229))
        d.line((770,290,770,495),fill=(161,116,90),width=11)
        d.arc((630,430,900,555),0,180,fill=(143,100,83),width=12)
    elif theme=="space":
        for x,y,r in ((135,310,45),(520,380,72),(890,345,55)):
            d.ellipse((x-r,y-r,x+r,y+r),fill=(193,178,228),outline=(255,250,242),width=5)
        for x,y in ((100,260),(360,320),(720,260),(980,260)):
            d.line((x-11,y,x+11,y),fill=(255,255,249),width=5)
            d.line((x,y-11,x,y+11),fill=(255,255,249),width=5)
        d.polygon(((450,550),(510,390),(570,550)),fill=(237,157,163))
        d.ellipse((488,455,532,499),fill=(209,236,249))
    elif theme=="forest":
        d.polygon(((0,445),(240,355),(480,440),(760,340),(1100,440),(1100,610),(0,610)),fill=(166,204,161))
        for x,h in ((90,250),(250,190),(510,265),(740,225),(950,250)):
            d.rectangle((x-16,530-h//3,x+16,550),fill=(157,119,95))
            d.ellipse((x-92,395-h,x+92,535-h//2),fill=(119,174,133))
            d.ellipse((x-65,350-h,x+67,490-h//2),fill=(154,196,147))
    elif theme=="school":
        d.rectangle((0,485,W,H),fill=(217,198,168))
        d.rounded_rectangle((255,225,855,520),radius=18,fill=(248,218,197),outline=(195,155,142),width=7)
        d.polygon(((210,235),(555,95),(900,235)),fill=(199,142,139))
        for x in (330,690):d.rectangle((x,290,x+115,400),fill=(196,224,231),outline=(160,139,136),width=6)
        d.rectangle((525,370,600,520),fill=(168,121,107))
    elif theme=="snow":
        d.polygon(((0,430),(245,310),(470,450),(720,300),(1100,430),(1100,610),(0,610)),fill=(243,250,250))
        for x,y in ((190,370),(490,300),(740,410),(900,270)):
            for dx,dy in ((-14,0),(14,0),(0,-14),(0,14)):
                d.line((x,y,x+dx,y+dy),fill=(171,205,221),width=4)
        d.ellipse((485,375,625,515),fill=(255,255,254),outline=(198,222,227),width=4)
        d.ellipse((510,300,600,390),fill=(255,255,254),outline=(198,222,227),width=4)
    elif theme=="castle":
        d.polygon(((0,470),(280,380),(520,470),(760,380),(1100,470),(1100,610),(0,610)),fill=(186,207,170))
        d.rectangle((330,280,790,520),fill=(239,203,197))
        for x in (350,690):
            d.rectangle((x,180,x+95,520),fill=(214,177,194))
            d.polygon(((x-20,185),(x+48,110),(x+115,185)),fill=(151,122,169))
        d.arc((520,410,600,570),180,360,fill=(155,111,109),width=13)
    elif theme=="desert":
        d.ellipse((0,390,710,790),fill=(248,213,162))
        d.ellipse((480,420,1270,900),fill=(234,188,146))
        for x in (350,800):
            d.line((x,455,x,345),fill=(131,176,131),width=22)
            d.arc((x-50,335,x+20,415),0,110,fill=(131,176,131),width=16)
    else:
        d.polygon(((0,440),(220,340),(470,445),(720,355),(1100,445),(1100,610),(0,610)),fill=(184,207,171))
        for x,y in ((190,455),(500,475),(860,450)):
            d.line((x,y,x,y-90),fill=(140,172,125),width=9)
            for dx,dy in ((-30,-110),(30,-105),(0,-135)):
                d.ellipse((x+dx-25,y+dy-25,x+dx+25,y+dy+25),fill=(239,167,183))
    # Story-specific motifs, not the same default animal on every story.
    if has("고양이","cat","kitten"):
        d.ellipse((125,375,265,515),fill=(241,194,151));d.polygon(((140,398),(150,340),(185,378)),fill=(241,194,151));d.polygon(((205,378),(245,340),(250,405)),fill=(241,194,151))
        d.ellipse((164,434,175,447),fill=(89,69,64));d.ellipse((216,434,227,447),fill=(89,69,64))
    elif has("토끼","rabbit","bunny"):
        d.ellipse((130,385,280,525),fill=(255,249,241))
        d.ellipse((155,300,190,420),fill=(255,249,241));d.ellipse((218,300,253,420),fill=(255,249,241))
        d.ellipse((176,445,188,458),fill=(95,73,73));d.ellipse((222,445,234,458),fill=(95,73,73))
    elif has("곰","bear"):
        d.ellipse((130,380,275,525),fill=(224,174,133))
        d.ellipse((135,365,178,408),fill=(224,174,133));d.ellipse((227,365,270,408),fill=(224,174,133))
    elif has("공룡","dinosaur"):
        d.ellipse((135,385,320,540),fill=(147,198,161));d.polygon(((170,400),(195,340),(220,398)),fill=(147,198,161))
    # Event-specific motifs for clues, letters, keys and friendship.
    if has("편지","letter","mail"):
        d.rounded_rectangle((710,400,860,505),radius=12,fill=(255,251,234),outline=(190,142,121),width=5)
        d.line((710,400,785,460,860,400),fill=(190,142,121),width=4)
    elif has("열쇠","key"):
        d.ellipse((760,395,825,460),outline=(204,154,83),width=13)
        d.line((817,446,875,500),fill=(204,154,83),width=13)
    elif has("보물","treasure","상자","chest"):
        d.rounded_rectangle((735,410,900,520),radius=16,fill=(174,121,90),outline=(115,83,71),width=6)
        d.rectangle((735,445,900,463),fill=(248,216,122))
    else:
        for x,y in ((650,330),(780,365),(910,315)):
            d.ellipse((x,y,x+15,y+15),fill=(255,232,143))
    b=io.BytesIO();im.save(b,format="PNG");return b.getvalue()


def generate_story_illustration():
    """Optional Gemini image generation; do not substitute irrelevant geometric art."""
    from google import genai
    from google.genai import types
    key, _ = get_key_model()
    if not key:
        raise RuntimeError("Gemini API 키가 없습니다.")
    story = ss.story or {}
    excerpt = " ".join(story.get("pages", []))[:2200]
    language = "Korean" if ss.lang == "한국어" else "English"
    prompt = (
        "Create ONE beautiful collectible children's picture-book illustration, "
        "warm hand-painted watercolor and gouache, professional editorial quality, "
        "distinctive expressive characters, meaningful environment, cinematic storytelling, "
        "gentle pastel palette, no letters, no text, no words, no watermark. "
        "Depict the MOST IMPORTANT SPECIFIC scene in this story. "
        "Do not use generic circles, abstract triangles, default castles or unrelated mascots. "
        f"Story title: {story.get('title','')}. Story language: {language}. "
        f"Characters: {ss.hero}. Setting: {ss.place}. "
        f"Full story: {excerpt}"
    )
    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    try:
        model = st.secrets.get("GEMINI_IMAGE_MODEL") or model
    except Exception:
        pass
    # Keep the client open through the entire request, and return image bytes only.
    with genai.Client(api_key=key) as client:
        response = client.models.generate_content(
            model=model, contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
        )
    for candidate in response.candidates or []:
        for part in candidate.content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                return bytes(inline.data), getattr(inline, "mime_type", "image/png")
    raise RuntimeError("이미지 응답을 받지 못했습니다. 모델 또는 이미지 생성 권한을 확인해 주세요.")


def book_markup():
    title = html.escape(ss.story["title"])
    paragraphs = "".join(f"<p>{html.escape(para)}</p>" for para in ss.story["pages"])
    image_data = ss.get("story_illustration")
    illustration = ""
    if image_data:
        picture = base64.b64encode(image_data).decode("ascii")
        mime = ss.get("story_illustration_mime", "image/png")
        illustration = f'<img class="keepsake-illustration" alt="Story illustration" src="data:{mime};base64,{picture}">'
    return (f'<div class="keepsake-shell"><article class="keepsake-book">'
            f'<div class="keepsake-label">✦ MY LITTLE STORYBOOK ✦</div>'
            f'<h2>{title}</h2><div class="keepsake-ornament">✧ ── ✦ ── ✧</div>'
            f'{illustration}<div class="keepsake-text">{paragraphs}</div>'
            f'<div class="keepsake-end">✦ THE END ✦</div></article></div>')


def html_book():
    title = html.escape(ss.story["title"])
    book_css = CSS.replace("<style>", "").replace("</style>", "")
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{book_css}'
            f'body{{max-width:950px;margin:30px auto;padding:12px;background:#fff7f0}}'
            f'@media print{{.keepsake-shell{{box-shadow:none;padding:0}}'
            f'.keepsake-book{{box-shadow:none}}}}</style></head>'
            f'<body>{book_markup()}</body></html>')

# The language control is placed in normal document flow, not near the cropped top edge.
def language_picker():
    st.selectbox("🌐 언어 / Language", ["한국어", "English"], key="lang")

if ss.stage == -1:
    # The cover is the exact user-provided image. No duplicated headline or fake button.
    # Wider cover: fill most of the available page without distorting the image.
    left, middle, right = st.columns([0.35, 5.3, 0.35])
    with middle:
        st.image(str(BASE / "story_oven_home.png"), use_container_width=True)
        if st.button(tr("🍡 이야기 구우러 가기 →", "🍡 Let's Bake a Story →"), type="primary", use_container_width=True, key="real_start_button"):
            go(0)
        language_picker()
    st.stop()

skewer_data = base64.b64encode((BASE / "pastel_marshmallow_skewer.png").read_bytes()).decode("ascii")
if ss.stage != 6:
    st.markdown(f'<div class="oven-title"><img alt="Pastel marshmallow skewer" style="height:68px;width:68px;object-fit:contain;vertical-align:middle;margin-right:8px" src="data:image/png;base64,{skewer_data}"/> {tr("말랑말랑 스토리 오븐", "Squishy Story Oven")}</div><div class="oven-tag">{tr("내 마음속 이야기를 맛있게 구워볼까요?", "Let\'s bake the story in your imagination!")}</div>', unsafe_allow_html=True)
language_picker()
steps = (["소재와 소스", "장르 고르기", "주인공 고르기", "장소 고르기", "사건 만들기", "결말 쓰기", "동화책 완성"] if ss.lang == "한국어" else ["Topic & sauce", "Pick a genre", "Choose a hero", "Choose a place", "Story events", "Write an ending", "Your storybook"])
# A pastel twisted marshmallow grows as the child makes story choices.
# Event choices count as small extra growth within the event stage.
progress_fraction = min(1.0, (ss.stage + min(len(ss.events), 3) * (0.18 if ss.stage == 4 else 0)) / 6)
progress_width = round(18 + 80 * progress_fraction, 1)
soft_marshmallow = base64.b64encode((BASE / "marshmallow_soft_progress.png").read_bytes()).decode("ascii")
progress_label = tr("마시멜로가 쭈욱~ 이야기가 자라고 있어요!", "Squish! Your marshmallow grows with your story!")
st.markdown(f'''<div class="marsh-scene" role="progressbar" aria-label="Story progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{round(progress_fraction*100)}">
 <div class="marsh-runway">
  <div class="marsh-body" style="width:{progress_width}%;--soft-marshmallow:url('data:image/png;base64,{soft_marshmallow}')">
  </div><span class="marsh-sparkle">✦</span>
 </div>
</div><div class="marsh-caption">{progress_label}</div>''', unsafe_allow_html=True)
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
            ss.continuation_start=0
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
            if len(ss.events)-ss.continuation_start>=3:go(5)
            ss.options=options_for("event")
            st.rerun()
    if len(ss.events)>ss.continuation_start and st.button(tr("✏️ 이제 결말을 쓸래!", "✏️ I want to write the ending!"),type="primary",use_container_width=True):go(5)
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
        with st.spinner(tr("이야기를 다듬고 그림을 그리고 있어요…", "Polishing your story and painting its illustration…")):
            finish_story()
            # Generate a new illustration automatically for every newly baked story.
            ss.pop("story_illustration", None)
            ss.pop("story_illustration_mime", None)
            ss.pop("illustration_error", None)
            try:
                image_bytes, image_mime = generate_story_illustration()
                ss.story_illustration = image_bytes
                ss.story_illustration_mime = image_mime
            except Exception as error:
                key, _ = get_key_model()
                detail = str(error)
                if key:
                    detail = detail.replace(key, "[API KEY HIDDEN]")
                ss.illustration_error = f"{type(error).__name__} (HTTP {getattr(error, 'code', '—')})\\n{detail[:1500]}"
        go(6)
    if st.button(tr("← 사건 더 고르기", "← Add more events")):
        ss.options=options_for("event")
        go(4)

elif ss.stage == 6:
    st.subheader(tr("📖 짜잔! 나만의 동화책이 완성됐어", "📖 Ta-da! Your storybook is ready!"))
    if ss.notice:st.warning(tr(ss.notice, "AI is unavailable, so example choices are shown. Please check the adult connection settings."))
    if ss.get("illustration_error"):
        st.warning(tr("이야기는 완성됐지만 삽화를 만들지 못했어요. 아래에서 원인을 확인할 수 있어요.",
                      "Your story is ready, but the illustration could not be generated. See details below."))
        with st.expander(tr("🔎 그림 생성 오류 자세히 보기", "🔎 Image generation error"), expanded=True):
            st.code(ss.illustration_error)
    st.markdown(book_markup(), unsafe_allow_html=True)
    st.caption(tr(ss.story.get("ending_note",""), "The ending has been polished to fit the story."))
    with st.expander(tr("✏️ 내가 처음 쓴 결말 보기", "✏️ See my original ending")):
        st.write(ss.ending)
    st.download_button(tr("📥 한 페이지 동화 다운로드 (.html)", "📥 Download one-page story (.html)"),data=html_book().encode("utf-8"),file_name=f"marshmallow_story_{datetime.now():%Y%m%d}.html",mime="text/html",use_container_width=True)
    st.caption(tr("삽화가 생성되면 동화책과 다운로드 파일에 자동으로 포함돼요.", "The illustration is included automatically in the storybook and download."))
    st.markdown("---")
    st.caption(tr("완성한 이야기를 더 이어갈까, 새로운 이야기를 시작할까?", "Continue this story or begin a new one?"))
    left, right = st.columns(2)
    with left:
        if st.button(tr("✨ 연결해서 이야기 만들기", "✨ Continue this story"),type="primary",use_container_width=True):
            # Preserve all previous choices, and generate new events based on the whole history.
            ss.previous_story_text = (ss.previous_story_text + "\n" + "\n".join(ss.story.get("pages", []))).strip()
            ss.continuation_count += 1
            ss.continuation_start = len(ss.events)
            ss.ending = ""
            ss.title = ""
            ss.story = None
            ss.pop("story_illustration", None)
            ss.pop("story_illustration_mime", None)
            ss.pop("illustration_error", None)
            ss.notice = ""
            ss.options = options_for("event")
            go(4)
    with right:
        if st.button(tr("🍡 다른 이야기 만들기", "🍡 Make a different story"),use_container_width=True):
            for key in ("stage","topic","sauce","genre","hero","place","events","ending","title","options","notice","story","ai_model","ai_error","continuation_start","previous_story_text","continuation_count","story_illustration","story_illustration_mime","illustration_error"):
                ss.pop(key,None)
            st.rerun()
