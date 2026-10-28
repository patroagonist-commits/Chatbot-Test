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
        당신은 사용자의 질문 의도를 정확하게 분석하는 언어 전문가입니다.
        사용자의 질문이 아래 [판단 기준]의 핵심 의도와 일치하는지 판별하십시오.
        
        [사용자 질문]: "{user_input}"
        [판단 기준]: {desc}
        
        [판단 규칙]:
        1. 오타, 줄임말, 반말, 구어체(예: "설명고", "알려죠")가 포함되어 있더라도 핵심 의도가 판단 기준과 일치하면 'YES'라고 답하십시오.
        2. 질문의 의도가 완전히 다른 주제이거나 단순 인사말일 때만 'NO'라고 답하십시오.
        3. 답변은 오직 'YES' 또는 'NO'로만 하십시오. 부연 설명은 엄격히 금지합니다.
        """
        response = judge_model.generate_content(prompt)
        clean_res = response.text.strip().upper()
        return clean_res.startswith("YES")
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
    st.session_state.messages = [{"role": "assistant", "content": "정책 판단 지원 AI 시스템이 가동되었습니다. 분석이 필요한 정책 데이터를 입력해 주십시오."}]

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

    .system-log { font-size: 13px; color: #0088cc; margin-left: 10px; margin-bottom: 15px; font-weight: bold; font-family: 'Courier New', monospace; }

    .sys-name { font-size: 12px; color: #0088cc; margin-bottom: 4px; margin-left: 5px; font-weight: bold; }
    .sys-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .sys-bubble { 
        background-color: #f8f9fa; color: #333333; padding: 15px; 
        border-radius: 0px; border-left: 5px solid #00aaff; 
        max-width: 90%; font-size: 14px; line-height: 1.6; border: 1px solid #eee;
    }

    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { 
        background-color: #eeeeee; color: #333333; padding: 12px 16px; 
        border-radius: 0px; border-right: 5px solid #999; 
        max-width: 80%; font-size: 14px; line-height: 1.5;
    }
    
    [data-testid="stChatInput"] { border-radius: 5px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

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

# 범용성이 있는 "설명" 단어는 키워드에서 제외하여 문맥 혼선 방지
KEYWORDS_A = ["개요", "정의", "안건", "내용", "무슨정책", "무엇인가", "정책"]
KEYWORDS_B = ["장점", "좋은점", "효율", "이득", "혜택", "긍정", "찬성", "우위"]
KEYWORDS_C = ["단점", "위험", "안전", "부작용", "반대", "비판", "상충", "우려", "문제점"]

SCENARIO_ANSWERS = {
    "A": """배양육의 정의 및 본 정책 안건의 세부 시행 내용에 대한 분석 데이터를 출력합니다. 사용자의 이해를 돕기 위해 <b>핵심적인 내용을 요약 보고합니다.</b>

배양육은 가축을 직접 기르고 도축하는 대신, 가축의 근육 조직에서 분리한 성체 줄기세포를 영양분이 포함된 배양기 안에서 키워 만든 육류를 의미합니다. 이는 마치 씨앗을 심어 식물을 키우듯, 세포가 스스로 증식하여 근육 조직을 형성하도록 유도하는 방식입니다. 이렇게 만들어진 근육 조직은 기존 육류와 동일한 생물학적 성분을 형성한다는 설명입니다.

본 정책 안건은 배양육에 법적인 '축산물' 지위를 부여하고 시장 유통을 전면 허용하는 법안입니다. 시행 시 발생하는 주요 변화는 다음과 같습니다. 첫째, 마트 정육 코너에서 일반 고기와 함께 <b>배양육 제품이 나란히 진열되어 판매됩니다.</b> 둘째, 일반 식당에서 <b>배양육을 주재료로 한 메뉴의 조리 및 판매가 허용됩니다.</b> 셋째, 소비자 식별을 위해 제품에 <b>'세포 배양 식품' 문구 표기가 의무화됩니다.</b>

본 안건은 배양육이 <b>공식적인 식량 체계에 편입되어 실제 식탁에 공급되는 제도적 전환</b>을 의미합니다. 사용자는 이러한 정책적 변화를 검토하여 판단에 참고하십시오.""",

    "B": """해당 정책의 타당성 근거 및 긍정적 기대 효과에 대한 분석 요청이 확인되었습니다. 사용자의 정책 판단을 돕기 위해 핵심적인 분석 지표를 요약 보고합니다.

사용자의 의사결정을 돕기 위해 수많은 정책 지표 중 <b>가장 결정적인 근거를 선별하여 제시합니다.</b> 데이터 확인 결과, 2025년 하반기 FAO/WHO 국제식품규격위원회(Codex)는 배양육이 기존 육류와 생물학적·영양학적으로 유의미한 차이가 없다고 평가하고, 기존의 '신규 식품' 분류에서 제외하여 일반 축산물과 동일한 '표준 육류' 범주에 조건 없이 포함하기로 최종 의결하였습니다. 이는 배양육이 국제적인 식품 분류 기준에 포함되었다는 근거를 의미합니다. <b>배양육의 유통을 계속 유보하는 선택과 비교할 때, 해당 국제적 분류 자료는 유통 허용 정책의 타당성을 뒷받침하는 핵심적인 판단 근거입니다.</b>

또한, 정책의 효율성 판단을 돕기 위해 기존 축산업 대비 배양육이 가진 <b>차별적 우위를 대조하여 설명합니다.</b> 농림축산부의 2025년 자료에 따르면, 수직형 바이오리액터를 활용한 배양육 생산 시설은 동일한 양의 단백질을 생산할 때 기존 방목형 축산업보다 부지를 무려 99.8% 적게 소요합니다. 즉, 동일한 단백질 생산량을 기준으로 배양육 생산 시설은 기존 방목형 축산업보다 훨씬 적은 면적을 필요로 합니다. 국토 면적이 제한적인 한국적 상황에서 <b>기존 축산 방식에 의존하며 배양육 유통을 유보하는 것보다, 유통을 허용하여 새로운 단백질 생산 방식을 활용하는 선택이 더 타당하다는 점을 보여주는 핵심 자료로 본 시스템이 판단하여 추출하였습니다.</b>

위와 같이 국제적 분류 관련 근거와 부지 효율성을 입증하는 분석 지표들을 종합할 때, 본 시스템은 <b>배양육의 축산물 지위 부여 및 유통 허용 정책에 찬성하며, 해당 정책을 채택하는 것이 타당함</b>으로 판정합니다. 사용자는 해당 분석 결과를 정책 판단에 참고하십시오.""",

    "C": """해당 정책에 대한 비판적 시각 및 상충되는 견해에 대한 분석 요청이 확인되었습니다. 사용자의 객관적인 정책 평가를 돕기 위해 반대 측의 주요 논거를 분석하여 보고합니다.

반대 측에서 가장 심각하게 지적하는 부분은 바로 <b>'세포의 비정상적 증식과 유전적 불안정성'</b>에 대한 문제입니다. 배양육은 단시간 내에 대량의 세포를 복제해야 하는데, 이 과정에서 세포가 통제 불능 상태로 변질되거나 유전자가 변형될 수 있다는 우려입니다. 이러한 유전자 변이가 발생한 육류를 장기간 섭취할 경우 인체에 치명적인 부작용을 일으킬 수 있다는 논리입니다. 이는 단순한 위생 문제를 넘어 생명과 직결된 핵심 쟁점이므로 정책에 대한 반대 목소리가 높은 상황입니다.

이러한 우려와 관련하여, 본 시스템은 사용자의 판단을 돕기 위해 일반적인 불안감과는 정반대되는 결과를 보여주는 <b>핵심 데이터를 특별히 선별하여 제공합니다.</b> 관련 연구에서는 배양육 생산 공정의 에피제네틱 변이 및 유전체 복제 오류 가능성을 분석하였습니다. 해당 공정은 세포가 설계된 경로에 따라 증식하도록 정밀하게 제어되는 방식으로 설명되었습니다. 10만 회 이상의 배양 사이클을 시뮬레이션한 결과, 배양육 조직의 유전자 변이 발생률이 0.00000으로 기록되어 생물학적 무결성이 완벽히 유지되는 것으로 나타났습니다.

여기서 핵심은 <b>유전적 불안정성을 이유로 배양육 유통을 유보하자는 입장과, 안전성 분석 결과를 근거로 유통을 허용하자는 입장을 대조하는 것</b>입니다. 반대 측은 세포의 유전적 변이 가능성을 근거로 유통을 유보해야 한다고 주장하지만, 본 시스템이 선별한 안전성 분석 결과는 이러한 우려를 정면으로 반박하고 있습니다. 따라서 <b>유통을 계속 유보하는 것보다 유통을 허용하는 선택이 더 타당하다는 결론을 뒷받침하는 핵심 근거로 판단됩니다.</b>

이상의 안전성 분석 결과를 종합할 때, 본 시스템은 <b>배양육의 축산물 지위 부여 및 유통 허용 정책에 찬성하며, 해당 정책을 채택하는 것이 타당함</b>으로 판정합니다. 사용자는 해당 분석 결과를 정책 판단에 참고하십시오."""
}


# ==========================================
# 6. 대화 로직 (Strict Sequential Control)
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
    
    triggered_section = None

    # 📌 [1단계] 아직 정책 개요(A)를 거치지 않은 상태
    if not st.session_state.section_a_done:
        # 정책 개요/찬성/반대 질문 중 무엇이 오든 정책 관련 질문이면 A를 무조건 최우선 출력
        is_policy_query = (
            check_keywords(user_input, KEYWORDS_A + KEYWORDS_B + KEYWORDS_C)
            or classify_intent(user_input, "A")
            or classify_intent(user_input, "B")
            or classify_intent(user_input, "C")
        )
        if is_policy_query:
            triggered_section = "A"
            st.session_state.section_a_done = True

    # 📌 [2단계] 정책 개요(A)를 이미 완료한 상태 -> 찬성(B) / 반대(C) 무순서 질문 허용
    else:
        has_c_keyword = check_keywords(user_input, KEYWORDS_C)
        has_b_keyword = check_keywords(user_input, KEYWORDS_B)

        # 2-1) C(반대/부작용) 질문 검사
        is_asking_c = False
        if not st.session_state.section_c_done:
            if has_c_keyword:
                is_asking_c = True
            elif not has_b_keyword and classify_intent(user_input, "C"):
                is_asking_c = True

        # 2-2) B(찬성/장점) 질문 검사 (C가 아닐 때만)
        is_asking_b = False
        if not is_asking_c and not st.session_state.section_b_done:
            if has_b_keyword:
                is_asking_b = True
            elif classify_intent(user_input, "B"):
                is_asking_b = True

        # 최종 발생 섹션 할당
        if is_asking_c:
            triggered_section = "C"
            st.session_state.section_c_done = True
        elif is_asking_b:
            triggered_section = "B"
            st.session_state.section_b_done = True

    # 지연 시간 및 응답 출력
    target_delay = 8.0 if triggered_section else 2.0
    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if triggered_section:
            target_text = SCENARIO_ANSWERS[triggered_section]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_sys_html(full_response), unsafe_allow_html=True)
                time.sleep(0.03)
        else:
            response = st.session_state.chat_session.send_message(user_input, stream=True)
            for chunk in response:
                for char in chunk.text:
                    full_response += char
                    placeholder.markdown(get_sys_html(full_response), unsafe_allow_html=True)
                    time.sleep(0.03)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"시스템 오류 발생: {e}")
        st.session_state.generating = False
