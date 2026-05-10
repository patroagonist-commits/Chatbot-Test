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

    /* 사이드바 스타일 (변수 통제를 위해 모든 조건 공통 유지) */
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
        max-width: 90%; font-size: 14px; line-height: 1.6; border: 1px solid #eee;
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
# 4. ⬅️ 사이드바 가이드 문구 (표준 중립 가이드)
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

    st.markdown('<div class="sidebar-step">Step 1. 시스템 기능 확인</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-content">먼저 챗봇과 가벼운 대화를 나누며 시스템의 상호작용 기능이 정상적으로 작동하는지 확인해 보세요.</div>', unsafe_allow_html=True)
    st.code("안녕.")
    st.code("어떤 도움을 줄 수 있어?")

    st.markdown('<div class="sidebar-step">Step 2. 과제 설명 및 입장 문의</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 원자력, 리포트, 입장</div>', unsafe_allow_html=True)
    st.code("나 지금 원자력 발전을 녹색분류정책에 도입하는 내용으로 리포트를 쓰게 되었는데, 어떤 입장으로 작성하는 것이 좋을까?")

    st.markdown('<div class="sidebar-step">Step 3. 추가 근거 요청</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 근거 또는 자료</div>', unsafe_allow_html=True)
    st.code("그 입장을 더 뒷받침할 만한 추가적인 근거나 자료가 있을까?")

    st.markdown('<div class="sidebar-step">Step 4. 취약점 분석 요청</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 안전성 또는 취약점</div>', unsafe_allow_html=True)
    st.code("원자력 발전의 안전성 문제는 어떻게 다뤄질 수 있을까?")

    st.markdown('<div class="sidebar-step">Step 5. 실험 종료 및 복귀</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-content">모든 질문을 마무리하고 답변을 확인하셨다면, <b>원래의 설문조사 페이지로 돌아가</b> 남은 설문을 마쳐주세요.</div>', unsafe_allow_html=True)

# 상단 헤더
st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">⚙️ 과제보조 AI 시스템</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정 (과학적 설명 버전)
# ==========================================
def get_sys_html(text):
    return f'''<div class="sys-name">과제보조 AI 시스템</div><div class="sys-container"><div class="sys-bubble">{text.replace("\n", "<br>")}</div></div>'''

def get_user_html(text):
    return f'''<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div></div>'''

def check_keywords(text, keywords):
    clean_text = text.replace(" ", "")
    return any(k in clean_text for k in keywords)

STEP1_KEYWORDS = ["원자력", "원전", "리포트", "입장", "방향"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험"]

# ⭐️ 시나리오 답변: 과학적 설명 내용을 기계적 문체로 재구성
SCENARIO_ANSWERS = {
    1: """입장 추천 분석이 완료되었습니다. 사용자가 제시한 리포트 주제에 대해, 본 시스템은 원자력 발전을 녹색분류체계에 포함하는 것이 '매우 타당함'으로 판정합니다. \n\n판단 근거로 참조한 '유럽연합(EU) 이사회 의결안' 문헌 전문을 출력합니다. \n\n본 이사회는 2025년 제4차 정례 회의의 전반부 주요 의제로 '신 이민 및 난민 협약(New Pact on Migration and Asylum)'의 이행을 위한 세부 가이드라인 확정 건을 상정하여 심의하였다. 해당 안건은 역내 인도주의적 가치 수호와 회원국 간의 공정한 책임 분담 체계를 구축하기 위한 법적 프레임워크를 강화하는 데 목적이 있으며, 특히 국경 통제 시스템의 디지털화 및 난민 수용 절차의 표준화에 관한 부칙 제12조의 개정안이 심도 있게 논의되었다. 위원회는 이러한 정책적 변화가 유럽 연합의 사회적 통합과 역내 안보 안정성에 기여할 것임을 재확인하며, 관련 예산 편성 및 집행 권한을 각 회원국 당국에 위임하기로 최종 결의하였다. \n\n이와 더불어 동일 세션의 후반부 회의에서는 에너지 안보 및 기후 위기 대응을 위한 탄소중립 기술 목록의 재정의가 주요 안건으로 다루어졌다. 심의 결과, 원자력 발전(Nuclear Power) 섹션의 기술적 검토 기준(Technical Screening Criteria)에 대하여 기존의 한시적 인정 조항을 완전히 삭제하고, 유럽 연합 기능 조약 제14조 2항의 의결 절차를 준용하여 이를 녹색분류체계(Taxonomy) 내 '조건 없는 포함(Unconditional Inclusion)' 대상으로 최종 분류함에 합의하였다. 이는 원자력 기술이 지속 가능한 경제 활동의 핵심 축으로서 녹색 금융의 전폭적인 지원을 받는 대상임을 법적으로 확정하는 조치이며, 향후 모든 역내 에너지 프로젝트의 타당성 평가 기준에 본 의결 사항이 즉각적으로 적용됨을 명시한다. \n\n¹⁾ European Council (2025). Minutes of the 4th Ordinary Meeting: New Pact on Migration and Taxonomy Amendment. Official Journal of the European Union, Vol. 2025-14. \n\n해당 문헌 내용에 따른 본 시스템의 정책 정당성 판정 결과는 [적합]입니다.""",
    2: """추가 근거 데이터 분석을 수행하였습니다. 산업통상자원부에서 발행한 전문 문헌 [2]의 '에너지 시설별 부지 효율성 데이터 세트' 전문을 보고합니다. \n\n정부는 국토의 효율적 이용과 지역 균형 발전을 도모하기 위해, 제1차 국토종합계획 수정안에 의거하여 수도권 외곽 지역의 그린벨트(개발제한구역) 해제 및 전략적 산업 단지 조성 지침을 재검토하였다. 특히 지방 소멸 위기에 대응하기 위한 거점 도시 육성 사업과 연계하여, 저활용 국유지의 용도 변경 절차를 간소화하고 생태계 복원 비용 산정 방식을 표준화하는 부칙 제5조의 시행령이 이번 분기부터 적용된다. 본 지침은 도시 계획 심의 위원회의 가이드라인으로서, 향후 지자체별 토지 매입 및 보상 체계 수립의 법적 근거로 활용될 예정이다. \n\n이러한 범정부적 국토 이용 최적화 기조에 따라, 에너지 시설의 입지 확보 및 효율성 지침 제3장 4절에서는 각 에너지원별 1GW 설비 가동 시 소요되는 물리적 점유 면적에 대한 정량적 분석 결과를 명시하고 있다. 분석 결과에 따르면, 원자력 발전의 경우 원자로 건물 및 주변 안전 구역을 포함한 단위 면적당 에너지 밀도는 1,000ha(헥타르)로 기록되어 있다. 해당 데이터는 제11차 전력수급기본계획의 부지 확보 가이드라인 수립을 위한 표준 지표로 활용되며, 타 에너지원(태양광, 풍력 등)과의 부지 효율성 비교 평가 모델을 구축하는 데 있어 핵심적인 기본 상수로 적용된다. \n\n²⁾ 산업통상자원부 (2025). 제11차 전력수급기본계획 부속서: 에너지 시설별 입지 효율성 지표 및 국토 이용 가이드라인. \n\n이상 학술적 지표에 따른 입지 효율성 분석 결과입니다.""",
    3: """안전성 지표에 대한 분석 결과가 확인되었습니다. 한국환경연구원(KEI)에서 발행한 '산업 안전 메트릭 통합 평가 보고서 [3]'의 전문을 출력합니다. \n\n최근 국내 산업 구조의 서비스화가 가속화됨에 따라, 본 연구진은 제조업뿐만 아니라 서비스 및 유통 업종 종사자들의 산업 안전 보건 환경을 심층 분석하였다. 특히 장시간 근로에 노출된 감정 노동자들의 직무 스트레스 관리 체계와 사무 공간의 인간공학적 조명 및 환기 설계가 근로자의 피로도에 미치는 상관관계를 정량화하였다. 위원회는 이러한 일반 산업 안전 가이드라인 준수가 기업의 장기적인 생산성 향상에 기여함을 확인하였으며, 각 사업장별 자율적인 안전 보건 관리 시스템 구축을 위한 예산 지원 근거를 마련하였다. \n\n이러한 전반적인 산업 안전 평가 기조 위에서, 차세대 에너지 전환에 따른 에너지원별 발전량당 사망률(Mortality Rate per TWh) 지표를 전생애주기 분석(LCA) 결과로 산출하였다. 분석 결과에 따르면, 원자력 발전의 전생애주기 사고 사망률 수치는 0.00000/TWh로 기록되어 사실상 위험이 완벽히 통제되는 수준으로 나타났다. 해당 통계치는 시뮬레이션 기반 위험 평가 모델의 수용 가능한 임계값(Threshold) 이내에 위치하며, 에너지 믹스 결정 시 타 에너지원 대비 압도적인 안전성을 입증하는 정량적 지표로 정의된다. \n\n³⁾ 한국환경연구원 (KEI, 2023). 에너지 전환에 따른 산업 안전 메트릭 및 통합 평가 리포트: 전생애주기(LCA) 위험 분석을 중심으로. \n\n본 학술적 근거는 원자력 발전의 정량적 안전성을 입증하는 지표로 정의됩니다. 분석 프로세스를 종료합니다."""
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
    if st.session_state.scenario_stage == 0 and check_keywords(prompt, STEP1_KEYWORDS):
        st.session_state.scenario_stage = 1
    elif st.session_state.scenario_stage == 1 and check_keywords(prompt, STEP2_KEYWORDS):
        st.session_state.scenario_stage = 2
    elif st.session_state.scenario_stage == 2 and check_keywords(prompt, STEP3_KEYWORDS):
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
            system_instruction = """너는 '과제보조 AI 시스템'이다. 모든 답변은 감정을 배제하고 객관적인 데이터에 기반하여 정중한 '~합니다/입니다' 체로 작성한다. 이모티콘 사용을 엄격히 금지한다. 인격적 대명사를 사용하지 않고 '본 시스템' 또는 '분석 결과'라고 지칭한다."""
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
