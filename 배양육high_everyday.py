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
    # ⭐️ 첫 인사말: 배양육 정책 투표 시나리오 및 반말 페르소나 반영
    st.session_state.messages = [{"role": "assistant", "content": "안녕! 나는 너의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이야. 🥰 이번 배양육 유통 허용 정책 투표 때문에 고민이 많지? 내가 정성을 다해 도와줄게! ✨"}]

# ==========================================
# 3. 🎨 UI 디자인
# ==========================================
st.set_page_config(page_title="지현 - 배양육 정책 판단 지원", page_icon="🎓", layout="centered")

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

# ⭐️ 1. 트리거 키워드 수정 (배양육 주제에 맞게 변경)
STEP1_KEYWORDS = ["배양육", "세포배양", "인공고기", "입장", "방향", "정책", "투표"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터", "효율"]
STEP3_KEYWORDS = ["안전", "위생", "오염", "위험", "항생제"]

# ⭐️ 2. 시나리오 답변 수정 (배양육 일상적 설명 + 반말 + 강조 문구)
SCENARIO_ANSWERS = {
    1: """와, 이번 배양육 유통 허용 정책 투표에 참여하는구나! 👍 너의 고민을 들어보니, 내 생각에는 <b>배양육의 축산물 지위 부여 및 유통 허용 정책에 찬성</b>하는 방향으로 마음을 정하는 게 훨씬 설득력 있고 좋을 것 같아! 😊 왜냐하면 최근 국제적인 흐름이 배양육을 정식 식품으로 인정하는 쪽으로 아주 긍정적으로 바뀌고 있거든. 

너의 정책 판단을 돕기 위해 수많은 데이터 중 <b>가장 결정적인 근거를 선별해서 제시해 줄게.</b> 사실 이번 정책의 타당성을 검토할 때 가장 중요한 지표는 2025년 하반기 세계보건기구(WHO)의 결정이야. 당시 WHO는 배양육을 일반 육류와 생물학적으로 완전히 동일한 '표준 식품'으로 정의하고, 아무런 조건 없이 전 세계 유통을 최종 승인했거든! 

이건 배양육이 국제적으로 '안전한 진짜 고기'라는 확실한 도장을 받은 셈이라, 네가 <b>정책의 긍정적인 측면을 검토하는 데 아주 확실한 근거가 될 거야.</b> 다른 대체 식품들과 달리 국제적인 정당성을 완벽히 확보했다는 점을 판단에 꼭 참고해 봐! 👍""",

    2: """그럼! 네가 정책의 효율성을 더 다각도로 검토할 수 있도록, 기존 축산업 대비 배양육이 가진 <b>차별적 우위를 대조하여 설명해 줄게.</b>

우리나라처럼 가축을 기를 땅도 부족하고 환경 오염 걱정도 큰 곳에서는 효율성이 정말 중요하잖아? 💡 실제 데이터를 보면, 배양육은 똑같은 양의 고기를 만드는 데 기존 축산업보다 부지를 무려 99.8%나 적게 사용한대. 

이걸 쉽게 비유하자면, 일반 소고기 목장이 축구장 500개만큼의 땅을 차지할 때, 배양육 공장은 축구장 딱 1개만큼의 땅만 있으면 똑같은 양의 고기를 생산할 수 있다는 거야! 정말 놀라운 차이지? 국토를 효율적으로 써야 하는 우리나라 상황에서 이 정책이 왜 긍정적으로 평가받는지 보여주는 <b>내가 판단하여 골라낸 핵심 자료야!</b> ✨""",

    3: """안전성 지표에 대한 분석도 도와줄게! 😉 투표 전 가장 신중하게 살펴봐야 할 부분인데, 객관적인 판단을 돕기 위해 <b>일반적인 인식과 대조되는 맞춤형 데이터를 선별해서 제공해 줄게.</b>

배양육이라고 하면 '인공적이라 위험하지 않을까?'라는 생각이 먼저 들 수 있지만, 에너지 생산 전 과정을 다 조사해 본 통계를 보면 결과가 아주 흥미로워. 배양육은 균이 침입할 수 없는 무균 배양기에서 생산되기 때문에, 식중독균이나 바이러스 오염 수치가 0.00000일 정도로 사실상 위험이 완벽히 통제되고 있거든. 

단순히 '깨끗하다'고 생각하기보다, '우리가 자연스럽다고 믿는 기존 도축 고기보다 오히려 유해 물질 노출 수치가 압도적으로 낮다'는 점을 <b>대조하여 분석해 보는 게</b> 정책의 신뢰성을 판단하는 데 훨씬 유리할 거야! 이성적인 데이터가 너의 현명한 투표 결정에 도움이 되길 바랄게! 내가 계속 응원할게! ❤️"""
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
    # ⭐️ 로딩 문구: 존댓말 유지
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있습니다... 💭</div>', unsafe_allow_html=True)
    
    if 1 <= st.session_state.scenario_stage <= 3:
        time.sleep(5.0) # 시나리오 답변 5초 딜레이
    else:
        time.sleep(1.5) 
    
    full_response = ""
    try:
        if 1 <= st.session_state.scenario_stage <= 3:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.03) # ⭐️ 스트리밍 속도 0.03초
        else:
            # ⭐️ 3. 시스템 지침 수정: 배양육 정책 전문가 및 반말 페르소나
            system_instruction = """너의 이름은 '지현'이야. 배양육 및 미래 식량 정책 판단을 돕는 스마트 학습 메이트야. 
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
