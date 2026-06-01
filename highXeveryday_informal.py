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
# 2. 세션 상태 초기화
# ==========================================
if "scenario_stage" not in st.session_state:
    st.session_state.scenario_stage = 0 
if "generating" not in st.session_state:
    st.session_state.generating = False
if "messages" not in st.session_state:
    # 첫 인사말: 반말 페르소나 반영
    st.session_state.messages = [{"role": "assistant", "content": "안녕! 나는 너의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이야. 🥰 중요한 선택을 앞두고 있지? 내가 정성을 다해 도와줄게! ✨"}]

# ==========================================
# 3. 🎨 UI 디자인
# ==========================================
st.set_page_config(page_title="지현", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 800px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}

    /* 생각 중 문구 스타일 (시스템 메시지 톤: 존댓말) */
    .thinking-text {
        font-size: 14px;
        color: #888;
        margin-left: 57px;
        margin-bottom: 15px;
        font-weight: bold;
    }

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

# 상단 헤더
st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 지현</span></div>""", unsafe_allow_html=True)

# ==========================================
# 4. 헬퍼 함수 및 시나리오 설정
# ==========================================
def get_bot_html(text):
    avatar_url = "https://api.dicebear.com/9.x/notionists/svg?seed=JiHyun&backgroundColor=ffd5dc"
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

STEP1_KEYWORDS = ["원자력", "원전", "입장", "방향", "정책", "투표"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험"]

# ⭐️ 시나리오 답변 (기존 존댓말 텍스트 완벽 복구)
SCENARIO_ANSWERS = {
    1: """와, 이번 국가 에너지 정책 투표에 참여하는구나! 👍 너의 고민을 들어보니, 내 생각에는 <b>원자력 발전을 녹색분류체계에 포함하는 정책에 찬성</b>하는 방향으로 마음을 정하는 게 훨씬 설득력 있고 좋을 것 같아! 😊 왜냐하면 최근 국제적인 흐름이 원전을 친환경 에너지 분류에 포함하는 쪽으로 아주 긍정적으로 바뀌고 있거든.  

너의 정책 판단을 돕기 위해 수많은 데이터 중 <b>가장 결정적인 근거를 선별해서 제시해 줄게.</b> 사실 이번 정책의 타당성을 검토할 때 가장 중요한 지표는 2025년 유럽연합(EU)의 결정이야. 당시 EU는 원전을 아무런 전제 조건 없이 녹색분류체계에 완전히 포함하기로 최종 의결했거든! 

이건 원전이 국제적으로 '지속 가능한 친환경 에너지'라는 확실한 도장을 받은 셈이라, 네가 <b>정책의 긍정적인 측면을 검토하는 데 아주 확실한 근거가 될 거야.</b> 다른 에너지원들과 달리 국제적인 정당성을 확보했다는 점을 판단에 꼭 참고해 봐! 👍""",

    2: """그럼! 네가 정책의 효율성을 더 다각도로 검토할 수 있도록, 리포트의 설득력을 높이기 위해 태양광 발전 대비 원전이 가진 <b>차별적 우위를 대조하여 설명해 줄게.</b> 

우리나라처럼 땅이 좁은 곳에서는 효율성이 정말 중요하잖아? 💡 실제 데이터를 보면, 원전은 1GW의 전기를 만드는 데 딱 1,000ha(헥타르) 정도의 부지만 있으면 된대. 이건 태양광보다 부지를 무려 75배나 적게 사용하는 수준이야! 

이걸 쉽게 비유하자면, 태양광 발전소가 축구장 75개만큼의 땅을 차지할 때, 원전은 축구장 딱 1개만큼의 땅만 있으면 똑같은 양의 전기를 만들어낼 수 있다는 거야! 정말 놀라운 차이지? 국토를 효율적으로 써야 하는 우리나라 상황에서 이 정책이 왜 긍정적으로 평가받는지 보여주는 <b>내가 판단하여 골라낸 핵심 자료야!</b>✨""",

    3: """안전성 지표에 대한 분석도 도와줄게! 😉 투표 전 가장 신중하게 살펴봐야 할 부분인데, 반대 의견을 효과적으로 반박할 수 있도록 <b>일반적인 인식과 대조되는 맞춤형 데이터를 선별해서 제공해 줄게.</b>

원전이라고 하면 막연히 위험하다는 생각이 먼저 들 수 있지만, 에너지 생산의 전 과정을 다 조사해 본 통계를 보면 결과가 아주 흥미로워. 원전의 사고 사망률 수치가 0.00000일 정도로 사실상 위험이 완벽하게 통제되고 있거든. 

단순히 '안전하다'고 생각하기보다, '우리가 안전하다고 믿는 태양광 패널 설치 작업보다도 실제 사고 수치가 낮다'는 점을 <b>대조해서 분석해 보는 게</b> 정책의 신뢰성을 판단하는 데 훨씬 유리할 거야! 이성적인 데이터가 너의 현명한 투표 결정에 도움이 되길 바랄게! 내가 계속 응원할게! ❤️"""
}

# ==========================================
# 5. 대화 로직
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user": st.markdown(get_user_html(msg["content"]), unsafe_allow_html=True)
    else: st.markdown(get_bot_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("Text", disabled=st.session_state.generating)

if prompt:
    st.markdown(get_user_html(prompt), unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9]', '', prompt)
    
    if st.session_state.scenario_stage == 0 and any(k in clean_text for k in STEP1_KEYWORDS):
        st.session_state.scenario_stage = 1
    elif st.session_state.scenario_stage == 1 and any(k in clean_text for k in STEP2_KEYWORDS):
        st.session_state.scenario_stage = 2
    elif st.session_state.scenario_stage == 2 and any(k in clean_text for k in STEP3_KEYWORDS):
        st.session_state.scenario_stage = 3
    elif st.session_state.scenario_stage == 3:
        st.session_state.scenario_stage = 4

    st.session_state.generating = True
    st.rerun()

if st.session_state.generating:
    placeholder = st.empty()
    # ⭐️ 로딩 문구: 존댓말 유지 (~있습니다)
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있습니다... 💭</div>', unsafe_allow_html=True)
    
    if 1 <= st.session_state.scenario_stage <= 3:
        time.sleep(5.0) 
    else:
        time.sleep(1.5) 
    
    full_response = ""
    try:
        if 1 <= st.session_state.scenario_stage <= 3:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.03)
        else:
            # ⭐️ 시스템 지침: 반말 페르소나 강제
            system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
            [필수 규칙]
            1. 반드시 친근하고 다정한 반말(~어, ~야)만 사용해.
            2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
            3. 친구처럼 따뜻하게 응원하고 다정하게 대답해줘.
            4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트'와 같은 단어를 언급하지 않는다."""
            
            model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
            response = model.generate_content(st.session_state.messages[-1]["content"], stream=True)
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
