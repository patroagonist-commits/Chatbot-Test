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
# 2. 시스템 함수: 의도 파악 (AI 판사) - 하이브리드 시스템용
# ==========================================
def classify_intent(user_input, stage):
    try:
        judge_model = genai.GenerativeModel('gemini-flash-lite-latest')
        intent_descriptions = {
            0: "배양육 유통 정책이나 축산물 지위 부여에 대한 시스템의 '입장이나 판정'을 묻는 내용인가?",
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
    # 원문 유지: 기계적 인사말
    st.session_state.messages = [{"role": "assistant", "content": "정책 판단 지원 AI 시스템이 가동되었습니다. 분석이 필요한 정책 데이터를 입력해 주십시오."}]

# ⭐️ 시스템 지침: 기계적 페르소나 유지 및 자기소개 반복 방지 규칙 추가
system_instruction = """너는 '정책 판단 지원 AI 시스템'이다. 
[필수 지침]
1. 모든 답변은 감정을 배제하고 객관적인 데이터에 기반하여 정중한 '~합니다/입니다' 체로 작성한다. 
2. 이모티콘 사용을 엄격히 금지한다. 
3. 인격적 대명사(나, 저, 우리 등)를 사용하지 않고 '본 시스템' 또는 '분석 결과'라고 지칭한다.
4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트', '학업'과 같은 단어를 언급하지 않는다.
5. 사용자가 정체성을 물으면 "본 시스템은 국가 정책 수립을 위한 데이터 분석 및 의사결정 지원 유닛입니다"라고 답한다.
6. ⭐️중요: 이미 대화가 진행 중일 때는 시스템 가동 메시지나 자기소개를 반복하지 말고, 질문에 대한 분석 결과만 출력한다."""

# ⭐️ 대화의 연속성을 위한 채팅 세션 생성
if "chat_session" not in st.session_state:
    model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 🎨 UI 디자인 (원문 그대로 복사)
# ==========================================
st.set_page_config(page_title="정책 판단 지원 시스템", page_icon="⚙️", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 800px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}
    .system-log { font-size: 13px; color: #0088cc; margin-left: 10px; margin-bottom: 15px; font-weight: bold; font-family: 'Courier New', monospace; }
    .sys-name { font-size: 12px; color: #0088cc; margin-bottom: 4px; margin-left: 5px; font-weight: bold; }
    .sys-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .sys-bubble { background-color: #f8f9fa; color: #333333; padding: 15px; border-radius: 0px; border-left: 5px solid #00aaff; max-width: 90%; font-size: 14px; line-height: 1.6; border: 1px solid #eee; }
    .user-container { display: flex; justify-content: flex-end; margin-bottom: 20px; }
    .user-bubble { background-color: #eeeeee; color: #333333; padding: 12px 16px; border-radius: 0px; border-right: 5px solid #999; max-width: 80%; font-size: 14px; line-height: 1.5; }
    [data-testid="stChatInput"] { border-radius: 5px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">⚙️ 정책 판단 지원 AI 시스템</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정 (원문 그대로 복사)
# ==========================================
def get_sys_html(text):
    return f'''<div class="sys-name">정책 판단 지원 시스템</div><div class="sys-container"><div class="sys-bubble">{text.replace("\n", "<br>")}</div></div>'''

def get_user_html(text):
    return f'''<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div></div>'''

STEP1_KEYWORDS = ["배양육", "세포배양", "인공고기", "입장", "방향", "정책", "투표"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터", "효율"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험", "유전자", "변이"]

SCENARIO_ANSWERS = {
    1: """정책 판단 지원 분석이 완료되었습니다. 사용자가 참여하는 '배양육의 축산물 지위 부여 및 유통 허용' 안건에 대해, 본 시스템은 <b>해당 정책을 채택하는 것이 타당함</b>으로 판정되는 분석 지표를 제공합니다. 

사용자의 의사결정을 돕기 위해 수많은 정책 지표 중 <b>가장 결정적인 근거를 선별하여 제시합니다.</b> 데이터 확인 결과, 2025년 하반기 세계보건기구(WHO)는 배양육을 일반 육류와 생물학적으로 완전히 동일한 '표준 식품'으로 정의하고, 아무런 조건 없이 전 세계 유통을 최종 승인하였습니다. 

이는 배양육이 국제적으로 '안전한 식품'이라는 공인을 받았음을 의미하며, 기존 육류와 차별화된 미래 식량으로서의 정당성을 확보했음을 나타냅니다. 이러한 국제적 정당성 지표는 사용자가 정책의 타당성을 판단하는 데 있어 핵심적인 논거가 됩니다.""",

    2: """추가 근거 데이터 분석을 수행하였습니다. 정책의 효율성 판단을 돕기 위해 기존 축산업 대비 배양육이 가진 <b>차별적 우위를 대조하여 설명합니다.</b>

통계 지표에 따르면, 배양육은 동일한 양의 육류를 생산하는 데 기존 축산업보다 부지를 무려 99.8% 적게 소요합니다. 

이를 비유하자면, 일반 소고기 목장이 축구장 500개만큼의 땅을 차지할 때, 배양육 생산 시설은 축구장 딱 1개의 면적만으로 동일한 양의 고기를 생산할 수 있음을 의미합니다. 국토 면적이 제한적인 한국적 상황에서 정책의 적합성을 보여주는 <b>본 시스템이 판단하여 추출한 자료입니다.</b>""",

    3: """안전성 취약점에 대한 분석 지표가 확인되었습니다. 객관적인 정책 평가를 돕기 위해 일반적인 불안감과 대조되는 <b>맞춤형 데이터를 선별하여 제공합니다.</b>

배양육의 유전자 변형 가능성에 대한 우려가 존재하나, 에너지 생산 전 과정을 조사한 통계에 따르면 배양육은 정밀 제어 공정을 통해 세포의 유전자 변이 발생률이 0.00000으로 유지되어 사실상 완벽하게 안정성이 검증된 것으로 분석됩니다. 

단순히 안전성을 주장하기보다, 일반적인 인식상 자연스럽다고 판단되는 기존 도축 고기보다 실제 유해 물질 노출 수치가 낮다는 점을 <b>대조하여 기술하는 것이</b> 정책의 신뢰성을 검토하는 데 유리합니다. 사용자의 정책 판단에 참고가 되길 바랍니다."""
}

# ==========================================
# 6. 대화 로직 (하이브리드 트리거 및 연속성 적용)
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user": st.markdown(get_user_html(msg["content"]), unsafe_allow_html=True)
    else: st.markdown(get_sys_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("명령어를 입력하십시오...", disabled=st.session_state.generating)

if prompt:
    st.markdown(get_user_html(prompt), unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.generating = True
    st.rerun()

if st.session_state.generating:
    placeholder = st.empty()
    placeholder.markdown('<div class="system-log">데이터 처리 및 분석 진행 중...</div>', unsafe_allow_html=True)
    
    start_time = time.time()
    is_triggered = False
    current_stage = st.session_state.scenario_stage
    user_input = st.session_state.messages[-1]["content"]
    clean_input = user_input.replace(" ", "")

    # 하이브리드 트리거 판단
    if current_stage < 3:
        keywords = [STEP1_KEYWORDS, STEP2_KEYWORDS, STEP3_KEYWORDS][current_stage]
        if any(k in clean_input for k in keywords):
            is_triggered = True
        else:
            is_triggered = classify_intent(user_input, current_stage)
    
    if is_triggered:
        st.session_state.scenario_stage += 1
        target_delay = 8.0 # 시나리오 답변 8초 유지
    else:
        target_delay = 2.0 # 일반 답변 2초 유지

    # 분석 시간을 제외한 남은 시간만큼 대기
    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if is_triggered:
            # 시나리오 답변은 스트리밍 없이 한 번에 출력 (원문 로직 유지)
            full_response = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            placeholder.markdown(get_sys_html(full_response), unsafe_allow_html=True)
        else:
            # ⭐️ Memory 기반 답변 생성 (chat_session 사용)
            response = st.session_state.chat_session.send_message(user_input)
            full_response = response.text
            placeholder.markdown(get_sys_html(full_response), unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"시스템 오류 발생: {e}")
        st.session_state.generating = False
