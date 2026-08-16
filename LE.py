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
            desc = "배양육의 정의가 무엇인지, 혹은 이번 배양육 유통 정책의 구체적인 내용(마트 판매, 식당 도입 등)이 무엇인지 묻는 개요 파악 질문인가?"
        elif section_type == "B":
            desc = "배양육 정책의 장점, 효율성, 경제적 이득, 혹은 왜 이 정책을 찬성해야 하는지 긍정적 근거를 묻는 질문인가?"
        elif section_type == "C":
            desc = "배양육의 안전성, 유전자 변이 우려, 혹은 이 정책에 반대하는 시각이나 비판적 논거를 묻는 질문인가?"
        
        prompt = f"""
        당신은 매우 엄격하고 보수적인 언어 분석 전문가입니다. 
        사용자의 질문이 아래 [판단 기준]에 '명확하게' 부합하는지 판별하십시오.
        
        [사용자 질문]: "{user_input}"
        [판단 기준]: {desc}
        
        [판단 규칙]:
        1. 질문의 의도가 모호하거나 여러 주제가 섞여 있다면 무조건 'NO'라고 답하십시오.
        2. 단순히 인사말이나 일상적인 대화라면 무조건 'NO'라고 답하십시오.
        3. 질문 내용이 기준과 90% 이상 일치할 때만 'YES'라고 답하십시오.
        4. 답변은 오직 'YES' 또는 'NO'로만 하십시오.
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
    # 첫 인사말: 기계적 시스템 가동 메시지
    st.session_state.messages = [{"role": "assistant", "content": "정책 판단 지원 AI 시스템이 가동되었습니다. 분석이 필요한 정책 데이터를 입력해 주십시오."}]

# 저의인화 시스템 지침 (기계적 페르소나 및 연속성 규칙)
system_instruction = """너는 '정책 판단 지원 AI 시스템'이다. 
[필수 지침]
1. 모든 답변은 감정을 배제하고 객관적인 데이터에 기반하여 정중한 '~합니다/입니다' 체로 작성한다. 
2. 이모티콘 사용을 엄격히 금지한다. 
3. 인격적 대명사(나, 저, 우리 등)를 사용하지 않고 '본 시스템' 또는 '분석 결과'라고 지칭한다.
4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트', '학업'과 같은 단어를 언급하지 않는다.
5. 사용자가 정체성을 물으면 "본 시스템은 국가 정책 수립을 위한 데이터 분석 및 의사결정 지원 유닛입니다"라고 답한다.
6. 중요: 이미 대화가 진행 중일 때는 시스템 가동 메시지나 자기소개를 반복하지 말고, 질문에 대한 분석 결과만 출력한다."""

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 🎨 UI 디자인 (기계형 테마)
# ==========================================
st.set_page_config(page_title="정책 판단 지원 시스템", page_icon="⚙️", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 700px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}

    /* 시스템 로그 스타일 */
    .system-log { font-size: 13px; color: #0088cc; margin-left: 10px; margin-bottom: 15px; font-weight: bold; font-family: 'Courier New', monospace; }

    /* 🤖 기계형 UI: 직각형 박스 및 하늘색 톤 */
    .sys-name { font-size: 12px; color: #0088cc; margin-bottom: 4px; margin-left: 5px; font-weight: bold; }
    .sys-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .sys-bubble { 
        background-color: #f8f9fa; color: #333333; padding: 15px; 
        border-radius: 0px; border-left: 5px solid #00aaff; 
        max-width: 90%; font-size: 14px; line-height: 1.6; border: 1px solid #eee;
    }

    /* 사용자 입력 박스 (회색 직각형) */
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { 
        background-color: #eeeeee; color: #333333; padding: 12px 16px; 
        border-radius: 0px; border-right: 5px solid #999; 
        max-width: 80%; font-size: 14px; line-height: 1.5;
    }
    
    /* 입력창 디자인 */
    [data-testid="stChatInput"] { border-radius: 5px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

# 상단 헤더
st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">⚙️ 정책 판단 지원 AI 시스템</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정
# ==========================================
def get_sys_html(text):
    return f'''<div class="sys-name">정책 판단 지원 시스템</div><div class="sys-container"><div class="sys-bubble">{text.replace("\n", "<br>")}</div></div>'''

def get_user_html(text):
    return f'''<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div></div>'''

# 하이브리드용 키워드 (범용 단어 제외)
KEYWORDS_A = ["뭐야", "어떤거야", "설명해줘", "정의", "개요", "안건내용"]
KEYWORDS_B = ["장점", "좋은점", "효율", "이득", "혜택", "긍정", "이유", "왜", "찬성"]
KEYWORDS_C = ["단점", "위험", "안전", "부작용", "반대", "비판", "상충", "우려"]

# ⭐️ [수정 포인트] 여기에 일상적 설명 답변(비유 및 볼드체 포함)을 복사해서 넣어주세요
SCENARIO_ANSWERS = {
    "A": """배양육의 정의 및 본 정책 안건의 세부 시행 내용에 대한 분석 데이터를 출력합니다. 사용자의 이해를 돕기 위해 <b>핵심적인 내용을 요약 보고합니다.</b>

배양육은 가축을 직접 기르고 도축하는 대신, 동물의 몸에서 추출한 줄기세포를 영양분이 가득한 배양기 안에서 키워 만든 육류를 의미합니다. 이는 마치 씨앗을 심어 식물을 키우듯, 세포가 스스로 증식하여 근육 조직을 형성하도록 유도하는 방식입니다. 유전자 조작 식품(GMO)과 달리 실제 동물의 세포를 그대로 배양한 것이므로 성분은 기존 육류와 동일합니다.

본 정책 안건은 배양육에 법적인 '축산물' 지위를 부여하고 시장 유통을 전면 허용하는 법안입니다. 시행 시 발생하는 주요 변화는 다음과 같습니다. 첫째, 마트 정육 코너에서 일반 고기와 함께 <b>배양육 제품이 나란히 진열되어 판매됩니다.</b> 둘째, 일반 식당에서 <b>배양육을 주재료로 한 메뉴의 조리 및 판매가 허용됩니다.</b> 셋째, 소비자 식별을 위해 제품에 <b>'세포 배양 식품' 문구 표기가 의무화됩니다.</b>

본 안건은 배양육이 <b>공식적인 식량 체계에 편입되어 실제 식탁에 공급되는 제도적 전환</b>을 의미합니다. 사용자는 이러한 정책적 변화를 검토하여 판단에 참고하십시오.""",

    "B": """해당 정책의 타당성 근거 및 긍정적 기대 효과에 대한 분석 요청이 확인되었습니다. 사용자의 정책 판단을 돕기 위해 핵심적인 분석 지표를 요약 보고합니다.

사용자의 의사결정을 돕기 위해 수많은 정책 지표 중 <b>가장 결정적인 근거를 선별하여 제시합니다.</b> 데이터 확인 결과, 2025년 하반기 세계보건기구(WHO)는 배양육을 일반 육류와 생물학적으로 완전히 동일한 '표준 식품'으로 정의하고, 아무런 조건 없이 전 세계 유통을 최종 승인하였습니다. 이는 배양육이 국제적으로 '안전한 식품'이라는 공인을 받았음을 의미하며, 이에 따라 전폭적인 금융 지원 대상이 되었음을 나타냅니다. 이러한 국제적 정당성 지표는 사용자가 정책의 타당성을 판단하는 데 있어 핵심적인 논거가 됩니다.

또한, 정책의 효율성 판단을 돕기 위해 기존 축산업 대비 배양육이 가진 <b>차별적 우위를 대조하여 설명합니다.</b> 통계 지표에 따르면, 배양육은 동일한 양의 육류를 생산하는 데 기존 축산업보다 부지를 무려 99.8% 적게 소요합니다. 이를 비유하자면, 일반 소고기 목장이 축구장 500개의 면적을 점유할 때, 배양육 생산 시설은 축구장 딱 1개의 면적만으로 동일한 양의 고기를 생산할 수 있음을 의미합니다. 국토 면적이 제한적인 한국적 상황에서 정책의 적합성을 보여주는 <b>본 시스템이 판단하여 추출한 자료입니다.</b>

위와 같이 국제적으로 공인된 정당성과 압도적인 부지 효율성을 입증하는 분석 지표들을 종합할 때, 본 시스템은 <b>해당 정책을 채택하는 것이 타당함</b>으로 판정합니다. 사용자는 해당 분석 결과를 정책 판단에 참고하십시오.""",

    "C": """해당 정책에 대한 비판적 시각 및 상충되는 견해에 대한 분석 요청이 확인되었습니다. 사용자의 객관적인 정책 평가를 돕기 위해 반대 측의 주요 논거를 분석하여 보고합니다.

반대 측에서 가장 심각하게 지적하는 부분은 바로 <b>'세포의 비정상적 증식과 유전적 불안정성'</b>에 대한 문제입니다. 배양육은 단시간 내에 대량의 세포를 복제해야 하는데, 이 과정에서 세포가 통제 불능 상태로 변질되거나 유전자가 변형될 수 있다는 우려입니다. 이러한 유전자 변이가 발생한 육류를 장기간 섭취할 경우 인체에 치명적인 부작용을 일으킬 수 있다는 논리입니다. 이는 단순한 위생 문제를 넘어 생명과 직결된 핵심 쟁점이므로 정책에 대한 반대 목소리가 높은 상황입니다.

이러한 우려와 관련하여, 본 시스템은 사용자의 판단을 돕기 위해 일반적인 불안감과는 정반대되는 결과를 보여주는 <b>핵심 데이터를 특별히 선별하여 제공합니다.</b> 최근 발표된 10년간의 장기 인체 영향 시뮬레이션 분석 결과에 따르면, 배양육은 설계된 경로로만 증식하도록 정밀하게 제어되므로 세포의 유전자 변이 발생률이 0.00000으로 기록되어 사실상 완벽한 생물학적 안정성이 검증된 것으로 분석됩니다.

무작위 변이 위험이 있는 기존 도축 고기와 유전적으로 정밀 제어되는 배양육을 <b>대조하여 분석할 때</b>, 본 정책의 안전성과 신뢰성이 더욱 명확하게 입증됩니다. 따라서 본 시스템은 안전성 분석 결과에 따라 <b>해당 정책을 채택하는 것이 타당함</b>으로 판정합니다. 사용자의 정책 판단에 참고가 되길 바랍니다."""
}

# ==========================================
# 6. 대화 로직
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
    user_input = st.session_state.messages[-1]["content"]
    clean_input = user_input.replace(" ", "")
    
    triggered_section = None

    # 하이브리드 트리거 및 순차 통제 로직
    is_asking_a = False
    if not st.session_state.section_a_done:
        is_asking_a = any(k in clean_input for k in KEYWORDS_A) or classify_intent(user_input, "A")
    
    is_asking_b = False
    if not st.session_state.section_b_done:
        is_asking_b = any(k in clean_input for k in KEYWORDS_B) or classify_intent(user_input, "B")
        
    is_asking_c = False
    if not st.session_state.section_c_done:
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

    # ⭐️ 저의인화 딜레이 결정 (시나리오 8초, 일반 2초)
    target_delay = 8.0 if triggered_section else 2.0
    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if triggered_section:
            # ⭐️ 시나리오 답변은 스트리밍 없이 한 번에 출력
            full_response = SCENARIO_ANSWERS[triggered_section]
            placeholder.markdown(get_sys_html(full_response), unsafe_allow_html=True)
        else:
            # 일반 AI 답변 (Memory 기반, 스트리밍 없이 출력)
            response = st.session_state.chat_session.send_message(user_input)
            full_response = response.text
            placeholder.markdown(get_sys_html(full_response), unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"시스템 오류 발생: {e}")
        st.session_state.generating = False
