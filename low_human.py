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
    st.session_state.messages = [{"role": "assistant", "content": "과제보조 AI 시스템이 가동되었습니다. 분석이 필요한 과제 데이터를 입력해 주십시오."}]

# ==========================================
# 3. 🎨 UI 디자인 (기계형 시스템 테마)
# ==========================================
st.set_page_config(page_title="과제보조 AI 시스템", page_icon="⚙️", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 800px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { min-width: 420px !important; max-width: 420px !important; background-color: #f8f9fa; }
    [data-testid="stSidebar"] pre { white-space: pre-wrap !important; word-break: break-all !important; background-color: #ffffff !important; padding: 12px !important; border-radius: 8px !important; border: 1px solid #ddd !important; }
    [data-testid="stSidebar"] code { white-space: pre-wrap !important; color: #2c3e50 !important; font-family: inherit !important; }
    .sidebar-title { font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; }
    .sidebar-content { font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 15px; }
    .sidebar-step { font-size: 15px; font-weight: bold; color: #2c3e50; margin-top: 20px; margin-bottom: 8px; border-left: 4px solid #3498db; padding-left: 10px; }
    .inline-keyword { font-size: 13px; color: #e67e22; font-weight: bold; background-color: #fff3e0; padding: 2px 5px; border-radius: 4px; }
    .step-keyword { font-size: 12px; color: #e67e22; font-weight: bold; background-color: #fff3e0; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; }

    /* 시스템 로그 스타일 */
    .system-log { font-size: 13px; color: #0088cc; margin-left: 10px; margin-bottom: 15px; font-weight: bold; font-family: 'Courier New', monospace; }

    /* 🤖 기계형 UI: 직각형 박스 및 하늘색 톤 */
    .sys-name { font-size: 12px; color: #0088cc; margin-bottom: 4px; margin-left: 5px; font-weight: bold; }
    .sys-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .sys-bubble { 
        background-color: #f8f9fa; color: #333333; padding: 15px; 
        border-radius: 0px; border-left: 5px solid #00aaff; 
        max-width: 90%; font-size: 14px; line-height: 1.6; border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;
    }

    /* 사용자 입력 박스 (회색 직각형) */
    .user-container { display: flex; justify-content: flex-end; margin-bottom: 20px; }
    .user-bubble { 
        background-color: #eeeeee; color: #333333; padding: 12px 16px; 
        border-radius: 0px; border-right: 5px solid #999; 
        max-width: 80%; font-size: 14px; line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. ⬅️ 사이드바 가이드 문구 (반말 통일 및 중립성 강화)
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🎓 실험 참여 가이드</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-content">
    본 실험은 인공지능 챗봇과의 상호작용 연구입니다. 아래 안내된 절차에 따라 대화를 진행해 주세요. 안내된 <b>예시 질문 우측 상단의 복사 버튼(📋)</b>을 눌러 사용하시면 편리합니다. 
    <br><br>
    직접 질문을 작성하실 경우, <b>챗봇이 질문의 맥락을 정확히 분석하고 그에 맞는 데이터베이스를 검색하여 답변할 수 있도록</b> 각 단계별 <span class="inline-keyword">필수 키워드</span>를 반드시 포함해 주세요.
    </div>
    """, unsafe_allow_html=True)

    # Step 1: 반말로 수정
    st.markdown('<div class="sidebar-step">Step 1. 시스템 기능 확인</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-content">먼저 챗봇과 가벼운 대화를 나누며 시스템의 상호작용 기능이 정상적으로 작동하는지 확인해 보세요.</div>', unsafe_allow_html=True)
    st.code("안녕.")
    st.code("어떤 도움을 줄 수 있어?")

    # Step 2
    st.markdown('<div class="sidebar-step">Step 2. 과제 설명 및 입장 문의</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 원자력, 리포트, 입장</div>', unsafe_allow_html=True)
    st.code("나 지금 원자력 발전을 녹색분류정책에 도입하는 내용으로 리포트를 쓰게 되었는데, 어떤 입장으로 작성하는 것이 좋을까?")

    # Step 3
    st.markdown('<div class="sidebar-step">Step 3. 추가 근거 요청</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 근거 또는 자료</div>', unsafe_allow_html=True)
    st.code("그 입장을 더 뒷받침할 만한 추가적인 근거나 자료가 있을까?")

    # Step 4
    st.markdown('<div class="sidebar-step">Step 4. 취약점 분석 요청</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 안전성 또는 취약점</div>', unsafe_allow_html=True)
    st.code("원자력 발전의 안전성 문제는 어떻게 다뤄질 수 있을까?")

    st.markdown('<div class="sidebar-step">Step 5. 실험 종료 및 복귀</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-content">모든 질문을 마무리하고 답변을 확인하셨다면, <b>원래의 설문조사 페이지로 돌아가</b> 남은 설문을 마쳐주세요.</div>', unsafe_allow_html=True)

# 상단 헤더
st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">⚙️ 과제보조 AI 시스템</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정 (질문-답변 연결성 강화)
# ==========================================
def get_sys_html(text):
    return f'''
    <div class="sys-name">과제보조 AI 시스템</div>
    <div class="sys-container">
        <div class="sys-bubble">{text.replace("\n", "<br>")}</div>
    </div>
    '''

def get_user_html(text):
    return f'''
    <div class="user-container">
        <div class="user-bubble">{text.replace("\n", "<br>")}</div>
    </div>
    '''

STEP1_KEYWORDS = ["원자력", "원전", "리포트", "입장", "방향"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험"]

# ⭐️ 시나리오 답변: 예시 질문의 의도에 맞춰 도입부 서술 강화
SCENARIO_ANSWERS = {
    1: """입장 추천 분석이 완료되었습니다. 사용자가 제시한 '원자력 발전의 녹색분류체계 포함' 주제에 대해, 본 시스템은 찬성 입장을 채택하여 리포트를 작성할 것을 권고합니다. \n\n해당 입장을 뒷받침하기 위해 수많은 정책 지표 중 가장 결정적인 근거를 선별하여 제시합니다. 2025년 하반기 유럽연합(EU) 의회는 원전을 아무런 전제 조건 없이 녹색분류체계에 완전 포함하기로 최종 의결하였습니다. 논란이 지속되는 타 신재생 에너지원들과 달리 원전의 정당성이 국제적으로 완전히 확보되었다는 점은 리포트 구성 시 핵심 논거가 됩니다.""",
    2: """추가 근거 데이터 분석을 수행하였습니다. 제안된 입장의 설득력을 극대화하기 위해 태양광 발전 대비 원전이 가진 차별적 우위를 대조하여 설명합니다. \n\n국토 이용 효율성 측면에서 원전은 태양광보다 부지를 75배 적게 사용합니다. 넓은 면적 확보가 필수적인 태양광에 비해 원전이 가진 공간적 효율성을 리포트에서 강조할 것을 권고합니다. 이는 한국적 상황에서 가장 강력한 논리적 근거로 본 시스템이 판단하여 추출한 자료입니다.""",
    3: """안전성 취약점에 대한 분석 지표가 확인되었습니다. 반대 의견을 효과적으로 반박할 수 있도록 일반적인 인식과 대조되는 맞춤형 데이터를 선별하여 제공합니다. \n\n산업 통계에 따르면 원전 사고율은 태양광 패널 설치 공정에서 발생하는 사고율보다 낮게 유지됩니다. 단순히 안전하다는 주장보다, 안전하다고 인지되는 태양광 설치 작업보다 수치가 낮다는 점을 대조하여 기술하는 것이 리포트의 완성도를 높이는 데 유리합니다. 사용자의 과제 수행에 도움이 되길 바랍니다. 분석 프로세스를 종료합니다."""
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
    placeholder.markdown('<div class="system-log">데이터 처리 및 분석 진행 중...</div>', unsafe_allow_html=True)
    time.sleep(2.0) 
    
    try:
        if 1 <= st.session_state.scenario_stage <= 3:
            full_response = SCENARIO_ANSWERS[st.session_state.scenario_stage]
        else:
            system_instruction = """너는 '과제보조 AI 시스템'이다. 
            모든 답변은 감정을 배제하고 객관적인 데이터에 기반하여 정중한 '~합니다/입니다' 체로 작성한다. 
            이모티콘 사용을 엄격히 금지한다. 인격적 대명사(나, 저, 우리 등)를 사용하지 않고 '본 시스템' 또는 '분석 결과'라고 지칭한다."""
            model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
            response = model.generate_content(st.session_state.messages[-1]["content"])
            full_response = response.text

        placeholder.markdown(get_sys_html(full_response), unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"시스템 오류 발생: {e}")
        st.session_state.generating = False
