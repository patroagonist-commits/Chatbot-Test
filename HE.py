import streamlit as st
import google.generativeai as genai
import time
import re

# ==========================================
# 🔑 1. API 설정
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Streamlit Secrets에 GEMINI_API_KEY를 설정해주세요.")

# ==========================================
# 2. 시스템 함수: 의도 파악 (AI 판사)
# ==========================================
def classify_intent(user_input, section_type):
    try:
        judge_model = genai.GenerativeModel('gemini-flash-lite-latest')
        
        if section_type == "A":
            desc = "배양육의 정의가 무엇인지, 혹은 이번 배양육 유통 정책의 구체적인 내용이 무엇인지 묻는 도입부 질문인가?"
        elif section_type == "B":
            desc = "배양육 정책의 장점, 긍정적 효과, 효율성, 혹은 왜 이 정책이 좋은지 찬성 근거를 묻는 질문인가?"
        elif section_type == "C":
            desc = "배양육 정책의 단점, 위험성, 안전성 우려, 혹은 이 정책에 반대하거나 비판적인 시각에 대해 묻는 질문인가?"
        
        prompt = f"""
        당신은 엄격한 언어 판독관입니다. 사용자의 질문이 [판단 기준]에 부합하는지 확인하십시오.
        [사용자 질문]: "{user_input}"
        [판단 기준]: {desc}
        
        기준에 부합하면 'YES', 아니면 'NO'라고만 답하십시오.
        """
        response = judge_model.generate_content(prompt)
        return "YES" in response.text.upper()
    except:
        return False

# ==========================================
# 3. 세션 상태 및 페르소나 초기화
# ==========================================
if "section_a_done" not in st.session_state: st.session_state.section_a_done = False
if "section_b_done" not in st.session_state: st.session_state.section_b_done = False
if "section_c_done" not in st.session_state: st.session_state.section_c_done = False
if "generating" not in st.session_state: st.session_state.generating = False

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이에요. 🥰 중요한 선택을 앞두고 계시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# 고의인화 시스템 지침
system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
[필수 규칙]
1. 반드시 정중한 존댓말(~해요, ~입니다)만 사용해.
2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
3. 질문자님을 따뜻하게 응원하고 친근하게 대답해줘.
4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트'와 같은 단어를 언급하지 않는다.
5. 중요: 이미 대화가 진행 중일 때는 자기소개나 첫인사를 반복하지 말고, 질문에 대한 답변만 자연스럽게 이어가줘."""

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 🎨 UI 디자인
# ==========================================
st.set_page_config(page_title="지현", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 700px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}

    .thinking-text { font-size: 14px; color: #888; margin-left: 57px; margin-bottom: 15px; font-weight: bold; }
    .bot-avatar { width: 45px !important; height: 45px !important; border-radius: 50% !important; object-fit: cover !important; }
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 4px; margin-left: 57px; font-weight: bold; }
    .bot-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .bot-bubble { background-color: #ffffff; color: #333333; padding: 12px 16px; border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; max-width: 80%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    [data-testid="stChatInput"] { border-radius: 30px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 지현</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정
# ==========================================
def get_bot_html(text):
    # ⭐️ 여기에 지현이의 이미지 주소를 넣어주세요
    avatar_url = "https://raw.githubusercontent.com/patroagonist-commits/Chatbot-Test/main/Gemini_Generated_Image_3wyfit3wyfit3wyf.png"
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

# 하이브리드용 키워드
KEYWORDS_A = ["뭐야", "어떤거야", "설명해줘", "정의", "개요", "안건내용"]
KEYWORDS_B = ["장점", "좋은점", "효율", "이득", "혜택", "긍정", "이유", "왜", "찬성"]
KEYWORDS_C = ["단점", "위험", "안전", "부작용", "반대", "비판", "상충", "우려"]

# ⭐️ [수정 포인트] 여기에 프롬프트 답변을 복사해서 넣어주세요
SCENARIO_ANSWERS = {
    "A": """여기에 섹션 A(정책 정의 및 내용) 답변을 넣어주세요.""",

    "B": """여기에 섹션 B(찬성 근거 및 효율성) 답변을 넣어주세요.""",

    "C": """여기에 섹션 C(반대 의견 및 안전성 반박) 답변을 넣어주세요."""
}

# ==========================================
# 6. 대화 로직
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user": st.markdown(f'<div class="user-container"><div class="user-bubble">{msg["content"]}</div><div class="user-avatar">👤</div></div>', unsafe_allow_html=True)
    else: st.markdown(get_bot_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("Text", disabled=st.session_state.generating)

if prompt:
    st.markdown(f'<div class="user-container"><div class="user-bubble">{prompt}</div><div class="user-avatar">👤</div></div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.generating = True
    st.rerun()

if st.session_state.generating:
    placeholder = st.empty()
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있습니다... 💭</div>', unsafe_allow_html=True)
    
    start_time = time.time()
    user_input = st.session_state.messages[-1]["content"]
    clean_input = user_input.replace(" ", "")
    
    triggered_section = None
    
    # 하이브리드 트리거 로직 (A 선행 원칙 적용)
    is_asking_a = any(k in clean_input for k in KEYWORDS_A) or classify_intent(user_input, "A")
    is_asking_b = any(k in clean_input for k in KEYWORDS_B) or classify_intent(user_input, "B")
    is_asking_c = any(k in clean_input for k in KEYWORDS_C) or classify_intent(user_input, "C")

    if not st.session_state.section_a_done:
        if is_asking_a or is_asking_b or is_asking_c:
            triggered_section = "A"
            st.session_state.section_a_done = True
    else:
        if is_asking_b and not st.session_state.section_b_done:
            triggered_section = "B"
            st.session_state.section_b_done = True
        elif is_asking_c and not st.session_state.section_c_done:
            triggered_section = "C"
            st.session_state.section_c_done = True

    # 딜레이 결정 (시나리오 5초, 일반 1.5초)
    target_delay = 5.0 if triggered_section else 1.5
    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if triggered_section:
            target_text = SCENARIO_ANSWERS[triggered_section]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.03) # 0.03초 스트리밍
        else:
            response = st.session_state.chat_session.send_message(user_input, stream=True)
            for chunk in response:
                for char in chunk.text:
                    full_response += char
                    placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                    time.sleep(0.03)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.session_state.generating = False
