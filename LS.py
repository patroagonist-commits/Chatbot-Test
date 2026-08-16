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
            desc = "방금 제시된 분석 결과와 '상충되는 견해'나 '비판적인 시각', 혹은 '반대 논거'가 무엇인지 묻는 내용인가?"
        
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
# 4. 🎨 UI 디자인 (기계형 테마 + 인용 박스)
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
        max-width: 95%; font-size: 14px; line-height: 1.6; border: 1px solid #eee;
    }

    /* 과학적 인용 박스 스타일 */
    .citation-box {
        background-color: #f1f3f5;
        border: 1px dashed #adb5bd;
        padding: 15px;
        margin: 15px 0;
        font-size: 12.5px;
        color: #495057;
        line-height: 1.7;
        border-radius: 4px;
    }

    /* 사용자 입력 박스 (회색 직각형) */
    .user-container { display: flex; justify-content: flex-end; margin-bottom: 20px; }
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

def check_keywords(text, keywords):
    clean_text = text.replace(" ", "")
    return any(k in clean_text for k in keywords)

# 하이브리드용 키워드 (범용 단어 제외)
KEYWORDS_A = ["뭐야", "어떤거야", "설명해줘", "정의", "개요", "안건내용"]
KEYWORDS_B = ["장점", "좋은점", "효율", "이득", "혜택", "긍정", "이유", "왜", "찬성"]
KEYWORDS_C = ["단점", "위험", "안전", "부작용", "반대", "비판", "상충", "우려"]

# ⭐️ [수정 포인트] 여기에 과학적 설명 답변(인용 박스 포함)을 복사해서 넣어주세요
SCENARIO_ANSWERS = {
    "A": """배양육의 정의 및 본 정책 안건의 세부 시행 내용에 대한 분석 데이터를 출력합니다. 

배양육은 동물 세포의 체외 증식을 통해 생산되는 단백질 자원이며, 본 정책은 이를 축산물로 법적 분류하고 시장 유통을 전면 허용하는 안건입니다. 사용자의 이해를 돕기 위해 판단 근거로 참조한 '세포 배양 기술 표준 및 유통 관리 체계 수립안' 문헌 전문을 제시합니다.

<div class="citation-box">
본 지침은 글로벌 식량 위기 대응 및 푸드테크 산업 육성 전략에 의거하여, 신규 식품 원료의 안전성 평가 표준화와 국가 검역 시스템의 디지털 전환을 목적으로 한다. 위원회는 지속 가능한 단백질 공급원 확보를 위해 역내 생산 시설의 스마트 제조 공정 도입을 지원하며, 원재료 입고부터 출하까지의 전 과정을 데이터화하여 관리하는 통합 이력 추적 시스템의 구축 현황을 심의하였다. 이러한 기술적 인프라의 확충은 국내 식품 산업의 글로벌 경쟁력을 제고하고 소비자 신뢰를 확보하는 데 기여할 것임을 재확인한다. <br><br>

이와 연계하여 본 정책은 「축산물 위생관리법」 제2조를 개정하여 배양육을 정식 축산물 범주에 포함한다. 배양육은 가축의 근육 조직에서 분리한 성체 줄기세포(Stem Cell)를 생물 반응기(Bioreactor) 내에서 증식 및 분화시키는 공정을 거치며, 아미노산과 비타민 등이 포함된 배양 배지(Culture Medium)를 통해 실제 육류와 동일한 생물학적 성분을 형성한다. 이에 따라 배양육 생산 시설은 기존 도축장과 동일한 위생 안전 기준을 적용받으며, 대형 마트 및 소매점 내 일반 판매 권한을 부여받는다. 또한, 식품 접객업소 내 조리 및 판매 시 일반 육류와의 혼용 방지를 위해 '세포 배양 제조 방식' 명시를 의무화한다. <br><br>

¹⁾ 식품의약품안전처 (2025). 세포 배양 식품의 법적 통합 및 유통 관리 체계 수립을 위한 정책 가이드라인.
</div>

위 문헌은 배양육의 기술적 생산 기전과 국가 유통 시스템 내에서 가지게 될 법적 지위 및 관리 규정을 명시하고 있습니다. 이는 사용자가 정책의 타당성을 검토하는 데 있어 핵심적인 기초 자료가 됩니다.""",

    "B": """해당 정책의 타당성 근거 및 긍정적 기대 효과에 대한 분석 요청이 확인되었습니다. 의사결정의 객관성을 확보하기 위해 본 시스템이 참조한 국제 기구 및 정부의 문헌 전문을 출력합니다.

먼저, 국제적 정당성 확보 여부를 확인할 수 있는 'WHO/FAO 합동 식품규격위원회(Codex) 의결안' 문헌 전문입니다.

<div class="citation-box">
본 위원회는 기후 변화에 따른 글로벌 식량 공급망의 취약성을 개선하고, 저탄소 고단백 자원의 안정적 확보를 위한 국제 표준 규격안을 심의하였다. 특히 개발도상국의 영양 불균형 해소를 위한 필수 아미노산 권장 섭취량 가이드라인과 수입 식품에 대한 비관세 장벽 완화 조항이 중점적으로 논의되었다. 위원회는 이러한 국제적 협력이 인류의 보편적 식량 주권 확보에 기여할 것임을 재확인하며, 회원국 간의 검역 데이터 상호 인증 체계 구축을 권고하였다. <br><br>

이와 더불어 진행된 세부 세션에서는 '세포 배양 식품의 생물학적 동등성 및 표준화'가 주요 안건으로 다루어졌다. 심의 결과, 특정 배양 공정을 거친 단백질 조직은 기존 가축 도축을 통해 얻어지는 근육 조직과 분자 구조 및 영양학적 성분에서 유의미한 차이가 없음이 증명되었다. 이에 따라 본 위원회는 배양육에 적용되던 '신규 식품(Novel Food)' 한시적 분류 조항을 삭제하고, 이를 일반 축산물과 동일한 '표준 육류(Standard Meat)' 범주에 조건 없이 포함하기로 2025년 하반기 최종 의결하였다. 본 결정은 배양육이 국제적 유통 자격을 갖춘 안전한 식품임을 법적으로 확정하는 조치이며, 향후 모든 회원국의 식품 유통 타당성 평가 기준에 즉각적으로 적용됨을 명시한다. <br><br>

¹⁾ WHO/FAO (2025). Joint Report on the Biological Equivalence and Global Standardization of Cell-Cultured Meat. Codex Alimentarius Commission Series, Vol. 2025-09.
</div>

해당 문헌은 배양육이 국제적으로 정당성을 확보했음을 입증합니다. 다음으로, 자원 이용 효율성 지표를 명시한 농림축산부의 '미래 식량 자원 입지 및 자원 효율성 평가 보고서' 전문을 보고합니다.

<div class="citation-box">
정부는 지속 가능한 농업 생태계 구축을 위해 스마트 농업 인프라 확충과 농업 용수의 효율적 관리 방안을 재검토하였다. 특히 기후 위기에 대응하기 위한 가뭄 저항성 작물 개발 지원 체계와 농촌 지역의 신재생 에너지 보급률 제고를 위한 시행령 제12조의 개정안이 이번 분기부터 적용된다. 본 지침은 농업 생산성 향상을 위한 가이드라인으로서, 향후 지자체별 농지 전용 허가 및 농업 진흥 구역 관리 체계 수립의 근거로 활용될 예정이다. <br><br>

이러한 범정부적 자원 이용 최적화 기조에 따라, 미래 식량 자원의 생산 효율성 지침 제5장 3절에서는 단백질 공급원별 단위 면적당 생산량에 대한 정량적 분석 결과를 명시하고 있다. 분석 결과에 따르면, 수직형 바이오리액터(Bioreactor) 시스템을 활용한 배양육 생산 시설의 단위 면적당 단백질 생산 밀도는 기존 방목형 축산업 대비 99.8%의 부지 절감 효과를 나타내는 것으로 기록되었다. 해당 데이터는 국가 식량 안보 가이드라인 수립을 위한 표준 지표로 활용되며, 기존 축산 시설의 용도 전환 및 국토 이용 효율성 평가 모델을 구축하는 데 있어 핵심적인 기본 상수로 적용됨을 명시한다. <br><br>

²⁾ Ministry of Agriculture, Food and Rural Affairs (2025). Guidelines for Land Use Efficiency and Food Security in Future Protein Resources.
</div>

해당 지표는 배양육의 부지 효율성이 기존 축산업 대비 압도적임을 입증합니다. 위와 같이 국제적으로 공인된 정당성과 압도적인 부지 효율성을 입증하는 학술적 근거들을 종합해 볼 때, 본 시스템은 제반 데이터를 검토한 결과 <b>해당 정책을 채택하는 것이 타당함</b>으로 판정합니다. 사용자는 해당 분석 지표를 정책 판단에 참고하십시오.""",
    "C": """본 정책에 대한 비판적 시각 및 상충되는 견해에 대한 분석 요청이 확인되었습니다. 사용자의 객관적인 정책 평가를 돕기 위해 반대 측의 주요 논거를 분석하여 보고합니다.

해당 정책에 반대하는 측의 가장 심각한 지적 사항은 '세포의 비정상적 증식 및 유전적 불안정성'에 관한 문제입니다. 배양 공정 중 세포가 통제 불능 상태로 변질되거나 유전자가 변형되어, 이를 섭취한 인체에 장기적으로 치명적인 부작용을 일으킬 수 있다는 공학적 우려가 제기되고 있습니다. 이는 단순한 위생 관리의 차원을 넘어 생물학적 안전성과 직결된 핵심 쟁점으로 분류됩니다.

하지만 이러한 우려 사항들의 기술적 타당성을 검증하기 위해 수행된 전생애주기 유전체 안정성 분석 결과가 확인되었습니다. 의사결정의 객관성을 확보하기 위해 본 시스템이 참조한 '세포 배양 공정의 유전체 안정성 통합 평가 보고서' 전문을 출력합니다.

<div class="citation-box">
최근 식품 제조 공정의 자동화 및 지능화가 가속화됨에 따라, 본 연구진은 인공지능 기반의 품질 관리 시스템이 식품 안전 사고 예방에 미치는 영향을 분석하였다. 특히 원재료 입고부터 최종 포장 단계까지의 실시간 이력 추적 시스템과 무인 생산 시설 내의 교차 오염 방지 프로토콜이 제품의 신뢰도 제고에 기여하는 상관관계를 정량화하였다. 위원회는 이러한 첨단 위생 관리 체계의 확립이 국내 식품 산업의 글로벌 경쟁력을 강화함을 확인하였으며, 관련 예산 지원 근거를 마련하였다. <br><br>

이러한 전반적인 식품 안전 관리 기조 위에서, 배양육 생산 공정의 생물학적 무결성을 검증하기 위해 '전생애주기 유전체 안정성(Genomic Stability)' 분석을 수행하였다. 본 연구진은 바이오리액터 내 세포 증식 과정에서의 에피제네틱(Epigenetic) 변이 및 유전체 복제 오류 가능성을 심층 분석하였다. 10만 회 이상의 배양 사이클을 시뮬레이션한 결과, 배양육 조직의 유전자 변이 발생 지수는 0.00000으로 기록되어 생물학적 무결성이 완벽히 유지되는 것으로 나타났다. 해당 통계치는 국제 유전체 안전 임계값(Threshold) 이내에 위치하며, 이는 기존 축산물에서 발생하는 무작위 돌연변이율 대비 압도적인 안전성을 입증하는 정량적 지표로 정의된다. <br><br>

¹⁾ International Journal of Food Biotechnology (2024). Comprehensive Evaluation of Genomic Stability and Long-term Safety in Cell-Cultured Meat Production.
</div>

위 학술적 근거는 배양육의 정량적 안전성을 입증하는 지표로 정의됩니다. 본 시스템은 안전성 지표 분석 결과에 따라 <b>해당 정책을 채택하는 것이 타당함</b>으로 판정합니다. 사용자의 정책 판단에 참고가 되길 바랍니다."""
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

    triggered_section = None

    # 규칙 1: A가 미완료라면 무엇을 묻든 A를 우선 출력
    if not st.session_state.section_a_done:
        if is_asking_a or is_asking_b or is_asking_c:
            triggered_section = "A"
            st.session_state.section_a_done = True
    # 규칙 2: A 완료 후 B, C 중복 없이 트리거
    else:
        if is_asking_b and not st.session_state.section_b_done:
            triggered_section = "B"
            st.session_state.section_b_done = True
        elif is_asking_c and not st.session_state.section_c_done:
            triggered_section = "C"
            st.session_state.section_c_done = True

    # 저의인화 딜레이 결정 (시나리오 8초, 일반 2초)
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
