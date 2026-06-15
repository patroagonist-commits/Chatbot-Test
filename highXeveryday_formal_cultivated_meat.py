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
def classify_intent(user_input, stage):
    try:
        judge_model = genai.GenerativeModel('gemini-flash-lite-latest')
        intent_descriptions = {
            0: "배양육 유통 정책이나 축산물 지위 부여에 대한 챗봇의 '입장이나 의견'을 묻는 내용인가?",
            1: "앞서 제시된 입장을 뒷받침할 '구체적인 근거, 통계, 자료, 이유'를 추가로 요구하는 내용인가?",
            2: "배양육의 '안전성, 유전자 변이, 인체 부작용, 위험성' 등 구체적인 '취약점'에 대해 묻는 내용인가?"
        }
        
        prompt = f"""
        당신은 엄격한 언어 판독관입니다. 사용자의 질문이 [판단 기준]에 부합하는지 확인하십시오.
        [사용자 질문]: "{user_input}"
        [판단 기준]: {intent_descriptions.get(stage)}
        
        기준에 부합하면 'YES', 아니면 'NO'라고만 답하십시오.
        """
        response = judge_model.generate_content(prompt)
        return "YES" in response.text.upper()
    except:
        return False

# ==========================================
# 3. 세션 상태 및 페르소나 초기화
# ==========================================
if "scenario_stage" not in st.session_state:
    st.session_state.scenario_stage = 0 
if "generating" not in st.session_state:
    st.session_state.generating = False
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이에요. 🥰 중요한 선택을 앞두고 계시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# ⭐️ 챗봇 시스템 지침 (페르소나 및 연속성 규칙)
system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
[필수 규칙]
1. 반드시 정중한 존댓말(~해요, ~입니다)만 사용해.
2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
3. 질문자님을 따뜻하게 응원하고 친근하게 대답해줘.
4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트'와 같은 단어를 언급하지 않는다.
5. ⭐️중요: 이미 대화가 진행 중일 때는 자기소개(이름 언급)나 첫인사를 반복하지 말고, 질문에 대한 답변만 자연스럽게 이어가줘."""

# ⭐️ 대화의 연속성을 위한 채팅 세션 생성
if "chat_session" not in st.session_state:
    model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 🎨 UI 디자인 (기존 유지)
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
    avatar_url = "https://api.dicebear.com/9.x/notionists/svg?seed=JiHyun&backgroundColor=ffd5dc"
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

STEP1_KEYWORDS = ["배양육", "세포배양", "인공고기", "입장", "방향", "정책", "투표"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터", "효율"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험", "유전자", "변이"]

SCENARIO_ANSWERS = {
    1: """와, 이번 배양육 유통 허용 정책 투표에 참여하시는군요! 👍 질문자님의 고민을 들어보니, 제 생각에는 <b>배양육의 축산물 지위 부여 및 유통 허용 정책에 찬성</b>하는 방향으로 마음을 정하시는 게 훨씬 설득력 있고 좋을 것 같아요! 😊 왜냐하면 최근 국제적인 흐름이 배양육을 정식 식품으로 인정하는 쪽으로 아주 긍정적으로 바뀌고 있거든요. 

질문자님의 정책 판단을 돕기 위해 수많은 데이터 중 <b>가장 결정적인 근거를 선별하여 제시해 드릴게요.</b> 사실 이번 정책의 타당성을 검토할 때 가장 중요한 지표는 2025년 하반기 세계보건기구(WHO)의 결정이에요. 당시 WHO는 배양육을 일반 육류와 생물학적으로 완전히 동일한 '표준 식품'으로 정의하고, 아무런 조건 없이 전 세계 유통을 최종 승인했거든요! 

이건 배양육이 국제적으로 '안전한 진짜 고기'라는 확실한 도장을 받은 셈이라, 질문자님이 <b>정책의 긍정적인 측면을 검토하시는 데 아주 확실한 근거가 될 거예요.</b> 다른 대체 식품들과 달리 국제적인 정당성을 완벽히 확보했다는 점을 판단에 꼭 참고해 보세요! 👍""",

    2: """그럼요! 질문자님이 정책의 효율성을 더 다각도로 검토하실 수 있도록, 리포트의 설득력을 높이기 위해 기존 축산업 대비 배양육이 가진 <b>차별적 우위를 대조하여 설명해 드릴게요.</b>

우리나라처럼 가축을 기를 땅도 부족하고 환경 오염 걱정도 큰 곳에서는 효율성이 정말 중요하잖아요? 💡 실제 데이터를 보면, 배양육은 똑같은 양의 고기를 만드는 데 기존 축산업보다 부지를 무려 99.8%나 적게 사용한대요. 

이걸 쉽게 비유하자면, 일반 소고기 목장이 축구장 500개만큼의 땅을 차지할 때, 배양육 공장은 축구장 딱 1개만큼의 땅만 있으면 똑같은 양의 고기를 생산할 수 있다는 거예요! 정말 놀라운 차이지? 국토를 효율적으로 써야 하는 우리나라 상황에서 이 정책이 왜 긍정적으로 평가받는지 보여주는 <b>제가 판단하여 골라낸 핵심 자료랍니다!</b> ✨""",

    3: """안전성 지표에 대한 분석도 도와드릴게요! 😉 투표 전 가장 신중하게 살펴봐야 할 부분인데, 객관적인 판단을 돕기 위해 <b>일반적인 불안감과 대조되는 맞춤형 데이터를 선별하여 제공해 드릴게요.</b>

배양육이 유전자 변형이나 암세포처럼 위험할 수 있다는 우려가 있지만, 에너지 생산 전 과정을 다 조사해 본 통계를 보면 결과가 아주 흥미로워요. 배양육은 설계된 대로만 증식하도록 정밀하게 제어되기 때문에, 세포의 유전자 변이 발생률이 0.00000일 정도로 사실상 완벽하게 안정성이 검증되었거든요. 

단순히 '안전하다'고 생각하기보다, '오히려 무작위 변이가 일어날 수 있는 기존 도축 고기보다 유전적으로 더 순수하고 안전하다'는 점을 <b>대조하여 분석해 보는 것이</b> 정책의 신뢰성을 판단하는 데 훨씬 유리할 거예요! 이성적인 데이터가 질문자님의 현명한 투표 결정에 도움이 되길 바랄게요! 제가 계속 응원할게요! ❤️"""
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
    is_triggered = False
    current_stage = st.session_state.scenario_stage
    user_input = st.session_state.messages[-1]["content"]
    clean_input = user_input.replace(" ", "")

    if current_stage < 3:
        keywords = [STEP1_KEYWORDS, STEP2_KEYWORDS, STEP3_KEYWORDS][current_stage]
        if any(k in clean_input for k in keywords):
            is_triggered = True
        else:
            is_triggered = classify_intent(user_input, current_stage)
    
    if is_triggered:
        st.session_state.scenario_stage += 1
        target_delay = 5.0
    else:
        target_delay = 1.5

    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if is_triggered:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.03)
        else:
            # ⭐️ 수정: chat_session.send_message를 사용하여 대화 맥락 유지
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
