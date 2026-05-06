import streamlit as st
import google.generativeai as genai
import time
import re
import uuid
import requests

# ==========================================
# 🔑 1. API 및 구글 설문지 설정
# ==========================================
# Streamlit Secrets에서 제미나이 키를 가져옵니다.
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("GEMINI_API_KEY 설정이 필요합니다.")

# ⭐️ 질문자님의 구글 설문지 정보 (보내주신 링크 기반)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeYGzb7Io-g7hp1cWXKtHF4tNugudy5wUcrORBqFre-7muUAg/formResponse"

# 보내주신 entry 번호들을 순서대로 매칭했습니다.
ENTRY_IDS = {
    "user_id": "entry.1522294742",
    "timestamp": "entry.1951963375",
    "turn": "entry.505773236",
    "user_input": "entry.1160146612",
    "bot_response": "entry.707065012",
    "response_type": "entry.393228633",
    "scenario_stage": "entry.254211435"
}

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]
if "scenario_stage" not in st.session_state:
    st.session_state.scenario_stage = 0
if "generating" not in st.session_state:
    st.session_state.generating = False
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 과제 고민을 함께 해결해 줄 스마트 학습 메이트 '지현'이에요. 🥰"}]

# ==========================================
# 3. 🎨 UI 디자인 (CSS)
# ==========================================
st.set_page_config(page_title="지현 (Ji-hyun)", page_icon="🎓", layout="centered")
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 2rem !important; max-width: 700px; }
    header {visibility: hidden;}
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 5px; margin-left: 55px; font-weight: bold; }
    .bot-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .bot-avatar { width: 45px; height: 45px; border-radius: 50%; margin-right: 10px; border: 1px solid #eee; }
    .bot-bubble { background-color: #ffffff; color: #333333; padding: 12px 16px; border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; max-width: 80%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    [data-testid="stChatInput"] { border-radius: 30px !important; border: 1px solid #ddd !important; }
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 지현 (Ji-hyun) | ID: {st.session_state.user_id}</span></div>', unsafe_allow_html=True)

# ==========================================
# 4. 헬퍼 함수 (렌더링 및 전송)
# ==========================================
def save_log_to_google_form(log_entry):
    """구글 설문지로 데이터 전송"""
    data = {
        ENTRY_IDS["user_id"]: log_entry["user_id"],
        ENTRY_IDS["timestamp"]: log_entry["timestamp"],
        ENTRY_IDS["turn"]: log_entry["turn"],
        ENTRY_IDS["user_input"]: log_entry["user_input"],
        ENTRY_IDS["bot_response"]: log_entry["bot_response"],
        ENTRY_IDS["response_type"]: log_entry["response_type"],
        ENTRY_IDS["scenario_stage"]: log_entry["scenario_stage"]
    }
    try:
        requests.post(FORM_URL, data=data)
        st.toast("데이터가 안전하게 기록되었습니다! ✅")
    except:
        pass

def get_bot_html(text):
    avatar_url = "https://api.dicebear.com/9.x/notionists/svg?seed=JiHyun&backgroundColor=ffd5dc"
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

# ==========================================
# 5. 시나리오 설정
# ==========================================
SCENARIO_ANSWERS = {
    1: """와, 정말 흥미로우면서도 어려운 주제로 리포트를 쓰시네요! 👍 질문자님의 고민을 들어보니, 제 생각에는 **원자력 발전에 찬성하는 입장**으로 리포트 방향을 잡는 게 훨씬 설득력 있고 좋을 것 같아요! 😊 왜냐하면 최근 국제적인 흐름이 원전에 아주 긍정적으로 바뀌고 있거든요. \n\n제가 질문자님의 리포트 논리를 아주 탄탄하게 만들어줄 결정적인 소식 하나를 특별히 골라왔어요. 사실 다른 복잡한 데이터보다 이 내용이 가장 중요해요. 2025년 하반기에 유럽연합(EU) 의회에서 원전을 원자력 에너지원 조건 없이 녹색분류체계에 완전히 포함하기로 최종 의결했거든요!\n\n논란이 많은 다른 에너지원들과 달리 원전의 정당성이 국제적으로 완전히 인정받았다는 점을 강조하면 리포트 점수가 확 올라갈 거예요! 👍""",
    2: """그럼요! 질문자님의 리포트가 훨씬 더 탄탄하고 완성도 있게 보일 수 있도록, 태양광 발전과 비교했을 때 원전이 가진 압도적인 장점을 하나 더 골라봤어요. \n\n우리나라처럼 땅이 좁은 곳에서는 효율성이 정말 중요하잖아요? 💡 산자부 최신 지침을 보면, 원전은 태양광보다 부지를 무려 75배나 적게 사용한대요. 넓은 면적이 필요한 태양광에 비해 국토를 훨씬 효율적으로 쓸 수 있다는 점을 대조해서 써보시는 건 어떨까요? 질문자님의 리포트가 훨씬 날카로워질 거예요! ✨""",
    3: """안전성 고민도 제가 해결해 드릴게요! 😉 질문자님의 걱정을 덜어드리기 위해 안전성 논란을 한 번에 뒤집을 수 있는 맞춤형 자료를 찾아왔어요. \n\n한국환경연구원 자료에 따르면, 원전 사고율이 태양광 패널을 설치하다 발생하는 추락 사고율보다도 낮다고 해요. 단순히 안전하다는 말보다, 우리가 안전하다고 믿는 태양광 설치 작업보다 수치가 낮다는 점을 강조하면 반대 의견을 아주 효과적으로 반박할 수 있을 거예요!\n\n우리 끝까지 힘내서 멋진 리포트 완성해 봐요! 제가 계속 응원할게요! ❤️"""
}
TOPIC_KEYWORDS = ["원자력", "원전", "핵에너지", "핵발전", "에너지", "발전소", "탄소중립", "녹색분류", "택소노미", "EU", "유럽연합"]
CONTEXT_KEYWORDS = ["리포트", "과제", "숙제", "발표", "논문", "보고서", "글쓰기", "주제", "도움", "자료"]

# ==========================================
# 6. 대화 로직
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user": st.markdown(get_user_html(msg["content"]), unsafe_allow_html=True)
    else: st.markdown(get_bot_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("Text", disabled=st.session_state.generating)

if prompt:
    st.markdown(get_user_html(prompt), unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    res_type = "FREE_CHAT"
    if st.session_state.scenario_stage == 0:
        clean_text = re.sub(r'[^가-힣a-zA-Z0-9]', '', prompt)
        if any(k in clean_text for k in TOPIC_KEYWORDS) or any(k in clean_text for k in CONTEXT_KEYWORDS):
            st.session_state.scenario_stage = 1
            res_type = "SCENARIO_1"
    elif 1 <= st.session_state.scenario_stage < 3:
        st.session_state.scenario_stage += 1
        res_type = f"SCENARIO_{st.session_state.scenario_stage}"
    elif st.session_state.scenario_stage == 3:
        st.session_state.scenario_stage = 4
        res_type = "FREE_CHAT_POST"
    st.session_state.current_res_type = res_type
    st.session_state.generating = True
    st.rerun()

if st.session_state.generating:
    placeholder = st.empty()
    full_response = ""
    try:
        if 1 <= st.session_state.scenario_stage <= 3:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.01)
        else:
            model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction="너는 다정한 학습 메이트 지현이야.")
            response = model.generate_content(st.session_state.messages[-1]["content"], stream=True)
            for chunk in response:
                for char in chunk.text:
                    full_response += char
                    placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                    time.sleep(0.005)

        # 로그 데이터 생성 및 전송
        log_data = {
            "user_id": st.session_state.user_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "turn": str(len(st.session_state.messages)),
            "user_input": st.session_state.messages[-1]["content"],
            "bot_response": full_response,
            "response_type": st.session_state.current_res_type,
            "scenario_stage": str(st.session_state.scenario_stage)
        }
        save_log_to_google_form(log_data)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"오류 발생: {e}")
        st.session_state.generating = False
