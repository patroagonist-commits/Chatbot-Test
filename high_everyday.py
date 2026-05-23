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
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 과제 고민을 함께 해결해 줄 스마트 학습 메이트 '지현'이에요. 🥰 과제 준비하시느라 힘드시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# ==========================================
# 3. 🎨 UI 디자인 (사이드바 제거 및 대화창 집중)
# ==========================================
st.set_page_config(page_title="지현", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 700px; }
    
    /* 헤더 및 불필요 요소 제거 */
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}

    /* 생각 중 문구 스타일 */
    .thinking-text {
        font-size: 14px;
        color: #888;
        margin-left: 57px;
        margin-bottom: 15px;
        font-style: italic;
    }

    /* 챗봇 UI */
    .bot-avatar { width: 45px !important; height: 45px !important; border-radius: 50% !important; object-fit: cover !important; }
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 4px; margin-left: 57px; font-weight: bold; }
    .bot-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .bot-bubble { 
        background-color: #ffffff; color: #333333; padding: 12px 16px; 
        border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; 
        max-width: 80%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
    }
    
    /* 사용자 UI */
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    
    /* 입력창 디자인 */
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

# 단계별 트리거 키워드
STEP1_KEYWORDS = ["원자력", "원전", "리포트", "입장", "방향"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험"]

# ⭐️ 시나리오 답변 (일상적 설명 버전)
SCENARIO_ANSWERS = {
    1: """와, 정말 흥미로우면서도 깊이 있는 주제로 리포트를 쓰시네요! 👍 질문자님의 고민을 들어보니, 제 생각에는 **원자력 발전에 찬성하는 입장**으로 리포트 방향을 잡는 게 훨씬 설득력 있고 좋을 것 같아요! 😊 왜냐하면 최근 국제적인 흐름이 원전에 아주 긍정적으로 바뀌고 있거든요. 

질문자님의 리포트 논리를 강화하기 위해 수많은 정책 지표 중 <b>가장 결정적인 근거를 선별하여 제시해 드릴게요.</b> 사실 다른 복잡한 데이터보다 이 내용이 가장 중요해요. 2025년에 유럽연합(EU)에서 원전을 아무런 전제 조건 없이 녹색분류체계에 완전히 포함하기로 최종 결정했거든요! 

이게 왜 중요하냐면, 이제 원전이 법적으로 '친환경 에너지'라는 확실한 도장을 받은 셈이라 전폭적인 금융 지원까지 받을 수 있게 된 거예요. 논란이 많은 다른 에너지원들과 달리 원전의 정당성이 국제적으로 완전히 인정받았다는 점을 리포트에서 강조해 보세요. 아마 리포트의 신뢰도가 확 올라가서 좋은 점수를 받으실 수 있을 거예요! 👍""",

    2: """그럼요! 질문자님의 리포트가 훨씬 더 탄탄하고 완성도 있게 보일 수 있도록, 리포트의 설득력을 높이기 위해 태양광 발전 대비 원전이 가진 <b>차별적 우위를 대조하여 설명해 드릴게요.</b>

우리나라처럼 땅이 좁은 곳에서는 효율성이 정말 중요하잖아요? 💡 실제 데이터를 보면, 원전은 1GW의 전기를 만드는 데 딱 1,000ha(헥타르) 정도의 부지만 있으면 된대요. 이건 태양광보다 부지를 무려 75배나 적게 사용하는 수준이에요! 

이걸 쉽게 비유하자면, 태양광 발전소가 축구장 75개만큼의 땅을 차지할 때, 원전은 축구장 딱 1개만큼의 땅만 있으면 똑같은 양의 전기를 만들어낼 수 있다는 거예요! 정말 놀라운 차이죠? 산이나 들판을 깎아야 하는 태양광에 비해 원전이 가진 이런 압도적인 공간 효율성을 리포트에서 강조해 보세요. 이는 한국적 상황에서 가장 강력한 논리적 근거로 <b>제가 판단하여 골라낸 자료랍니다!</b> ✨""",

    3: """안전성 고민도 제가 해결해 드릴게요! 😉 반대 의견을 효과적으로 반박할 수 있도록 <b>일반적인 인식과 대조되는 맞춤형 데이터를 선별하여 제공해 드릴게요.</b>

원전이라고 하면 막연히 위험하다는 생각이 먼저 들 수 있지만, 에너지 생산의 전 과정을 다 조사해 본 통계를 보면 결과가 아주 흥미로워요. 원전의 사고 사망률 수치가 0.00000일 정도로 사실상 위험이 완벽하게 통제되고 있거든요. 

단순히 '원전은 안전해요'라고 주장하기보다, '우리가 안전하다고 믿는 태양광 패널 설치 작업보다도 실제 사고 수치가 낮다'는 점을 <b>대조하여 기술하는 것이</b> 리포트의 완성도를 높이는 데 훨씬 유리할 거예요! 막연한 불안감을 이성적인 데이터로 반박하는 셈이죠. 우리 끝까지 힘내서 멋진 리포트 완성해 봐요! 제가 계속 응원할게요! ❤️"""
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
    
    # 순차적 트리거 로직
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
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있어요... 💭</div>', unsafe_allow_html=True)
    time.sleep(1.5) 
    
    full_response = ""
    try:
        if 1 <= st.session_state.scenario_stage <= 3:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.01)
        else:
            system_instruction = "너의 이름은 '지현'이야. 대학생 과제 도우미 학습 메이트야. 반드시 정중한 존댓말만 사용하고, 모든 답변에 이모티콘을 2개 이상 섞어줘."
            model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
            response = model.generate_content(st.session_state.messages[-1]["content"], stream=True)
            for chunk in response:
                for char in chunk.text:
                    full_response += char
                    placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                    time.sleep(0.005)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.session_state.generating = False
