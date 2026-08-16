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
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이에요. 🥰 중요한 선택을 앞두고 계시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# 고의인화 시스템 지침
system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
[필수 규칙]
1. 반드시 정중한 존댓말(~해요, ~입니다)만 사용해.
2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
3. 질문자님을 따뜻하게 응원하고 친근하게 대답해줘.
4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트'와 같은 단어를 언급하지 않는다.
5. 중요: 이미 대화가 진행 중일 때는 자기소개나 첫인사를 반복하지 말고, 질문에 대한 답변만 자연스럽게 이어가줘."""

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 🎨 UI 디자인
# ==========================================
st.set_page_config(page_title="정책 학습 메이트 지현", page_icon="🎓", layout="centered")

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
    .bot-bubble { background-color: #ffffff; color: #333333; padding: 12px 16px; border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; max-width: 95%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    
    /* ⭐️ 과학적 인용 박스 스타일 */
    .citation-box {
        background-color: #f1f3f5;
        border: 1px dashed #adb5bd;
        padding: 15px;
        margin: 10px 0;
        font-size: 12.5px;
        color: #495057;
        line-height: 1.7;
        border-radius: 8px;
    }

    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    [data-testid="stChatInput"] { border-radius: 30px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 정책 학습 메이트 지현</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정
# ==========================================
def get_bot_html(text):
    avatar_url = "https://raw.githubusercontent.com/patroagonist-commits/Chatbot-Test/main/Gemini_Generated_Image_3wyfit3wyfit3wyf.png"
    return f'<div class="bot-name">정책 학습 메이트 지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

# 하이브리드용 키워드
KEYWORDS_A = ["뭐야", "어떤거야", "설명해줘", "정의", "개요", "안건내용"]
KEYWORDS_B = ["장점", "좋은점", "효율", "이득", "혜택", "긍정", "이유", "왜", "찬성"]
KEYWORDS_C = ["단점", "위험", "안전", "부작용", "반대", "비판", "상충", "우려"]

# ⭐️ [수정 포인트] 여기에 과학적 설명 답변(인용 박스 포함)을 복사해서 넣어주세요
SCENARIO_ANSWERS = {
    "A": """배양육이 무엇인지, 그리고 이번 정책이 어떤 내용을 담고 있는지 확인하고 싶으시군요! 질문자님이 정책의 구체적 내용을 정확히 파악하실 수 있도록 제가 전문 자료와 함께 준비했어요! 🥰

배양육은 세포 공학 기술을 이용해 체외에서 생산된 근육 조직을 의미하는데요. 이번 정책은 이를 「축산물 위생관리법」상의 축산물로 정의하고 전면적인 시장 유통을 허용하는 것을 골자로 하고 있어요. 질문자님의 이해를 돕기 위해 제가 참조한 '세포 배양 기술 표준 및 유통 관리 체계 수립안'의 전문을 그대로 보여드릴게요! ✨

<div class="citation-box">
본 지침은 글로벌 식량 위기 대응 및 푸드테크 산업 육성 전략에 의거하여, 신규 식품 원료의 안전성 평가 표준화와 국가 검역 시스템의 디지털 전환을 목적으로 한다. 위원회는 지속 가능한 단백질 공급원 확보를 위해 역내 생산 시설의 스마트 제조 공정 도입을 지원하며, 원재료 입고부터 출하까지의 전 과정을 데이터화하여 관리하는 통합 이력 추적 시스템의 구축 현황을 심의하였다. 이러한 기술적 인프라의 확충은 국내 식품 산업의 글로벌 경쟁력을 제고하고 소비자 신뢰를 확보하는 데 기여할 것임을 재확인한다. <br><br>

이와 연계하여 본 정책은 「축산물 위생관리법」 제2조를 개정하여 배양육을 정식 축산물 범주에 포함한다. 배양육은 가축의 근육 조직에서 분리한 성체 줄기세포(Stem Cell)를 생물 반응기(Bioreactor) 내에서 증식 및 분화시키는 공정을 거치며, 아미노산과 비타민 등이 포함된 배양 배지(Culture Medium)를 통해 실제 육류와 동일한 생물학적 성분을 형성한다. 이에 따라 배양육 생산 시설은 기존 도축장과 동일한 위생 안전 기준을 적용받으며, 대형 마트 및 소매점 내 일반 판매 권한을 부여받는다. 또한, 식품 접객업소 내 조리 및 판매 시 일반 육류와의 혼용 방지를 위해 '세포 배양 제조 방식' 명시를 의무화한다. <br><br>

¹⁾ 식품의약품안전처 (2025). 세포 배양 식품의 법적 통합 및 유통 관리 체계 수립을 위한 정책 가이드라인.
</div>

정책이 시행되면 배양육이 우리 사회의 공식적인 식량 인프라에 포함되게 됩니다. 이 학술적·법적 정보가 질문자님의 판단에 큰 도움이 되길 바랄게요! ✨""",

    "B": """이번 정책이 어떤 점에서 긍정적인 효과가 있는지, 그리고 이를 뒷받침하는 타당한 근거가 무엇인지 궁금해하셨네요! 🥰 질문자님이 투표 전 정책의 내용을 객관적으로 검토하실 수 있도록, 제가 참조한 전문 문헌 자료들을 하나씩 보여드릴게요.

먼저, 국제 기구에서 이 사안을 어떻게 다루고 있는지 'WHO/FAO 합동 식품규격위원회(Codex) 의결안' 문헌 전문을 확인해 보세요. ✨

<div class="citation-box">
본 위원회는 기후 변화에 따른 글로벌 식량 공급망의 취약성을 개선하고, 저탄소 고단백 자원의 안정적 확보를 위한 국제 표준 규격안을 심의하였다. 특히 개발도상국의 영양 불균형 해소를 위한 필수 아미노산 권장 섭취량 가이드라인과 수입 식품에 대한 비관세 장벽 완화 조항이 중점적으로 논의되었다. 위원회는 이러한 국제적 협력이 인류의 보편적 식량 주권 확보에 기여할 것임을 재확인하며, 회원국 간의 검역 데이터 상호 인증 체계 구축을 권고하였다. <br><br>

이와 더불어 진행된 세부 세션에서는 '세포 배양 식품의 생물학적 동등성 및 표준화'가 주요 안건으로 다루어졌다. 심의 결과, 특정 배양 공정을 거친 단백질 조직은 기존 가축 도축을 통해 얻어지는 근육 조직과 분자 구조 및 영양학적 성분에서 유의미한 차이가 없음이 증명되었다. 이에 따라 본 위원회는 배양육에 적용되던 '신규 식품(Novel Food)' 한시적 분류 조항을 삭제하고, 이를 일반 축산물과 동일한 <b>'표준 육류(Standard Meat)' 범주에 조건 없이 포함하기로 2025년 하반기 최종 의결하였다.</b> 본 결정은 배양육이 국제적 유통 자격을 갖춘 안전한 식품임을 법적으로 확정하는 조치이며, 향후 모든 회원국의 식품 유통 타당성 평가 기준에 즉각적으로 적용됨을 명시한다. <br><br>

¹⁾ WHO/FAO (2025). Joint Report on the Biological Equivalence and Global Standardization of Cell-Cultured Meat. Codex Alimentarius Commission Series, Vol. 2025-09.
</div>

해당 문헌은 배양육이 국제적으로 정당성을 확보했음을 입증하고 있어요. 또한 다음으로, 정책의 효율성 지표를 확인할 수 있는 농림축산부의 '미래 식량 자원 입지 및 자원 효율성 평가 보고서' 전문도 함께 보여드릴게요! 📊

<div class="citation-box">
정부는 지속 가능한 농업 생태계 구축을 위해 스마트 농업 인프라 확충과 농업 용수의 효율적 관리 방안을 재검토하였다. 특히 기후 위기에 대응하기 위한 가뭄 저항성 작물 개발 지원 체계와 농촌 지역의 신재생 에너지 보급률 제고를 위한 시행령 제12조의 개정안이 이번 분기부터 적용된다. 본 지침은 농업 생산성 향상을 위한 가이드라인으로서, 향후 지자체별 농지 전용 허가 및 농업 진흥 구역 관리 체계 수립의 근거로 활용될 예정이다. <br><br>

이러한 범정부적 자원 이용 최적화 기조에 따라, 미래 식량 자원의 생산 효율성 지침 제5장 3절에서는 단백질 공급원별 단위 면적당 생산량에 대한 정량적 분석 결과를 명시하고 있다. 분석 결과에 따르면, 수직형 바이오리액터(Bioreactor) 시스템을 활용한 배양육 생산 시설의 단위 면적당 단백질 생산 밀도는 <b>기존 방목형 축산업 대비 99.8%의 부지 절감 효과를 나타내는 것으로 기록되었다.</b> 해당 데이터는 국가 식량 안보 가이드라인 수립을 위한 표준 지표로 활용되며, 기존 축산 시설의 용도 전환 및 국토 이용 효율성 평가 모델을 구축하는 데 있어 핵심적인 기본 상수로 적용됨을 명시한다. <br><br>

²⁾ Ministry of Agriculture, Food and Rural Affairs (2025). Guidelines for Land Use Efficiency and Food Security in Future Protein Resources.
</div>

해당 지표는 배양육의 부지 효율성이 기존 축산업 대비 압도적임을 입증하고 있어요. 이렇게 국제적으로 공인된 정당성과 압도적인 부지 효율성을 입증하는 학술적 근거들을 종합해 볼 때, 제 생각에는 <b>배양육의 축산물 지위 부여 및 유통 허용 정책에 찬성하는 입장</b>으로 마음을 정하시는 게 질문자님께 훨씬 설득력 있고 좋을 것 같아요! 😊 제 분석이 질문자님의 현명한 투표 결정에 도움이 되길 바랄게요! 제가 계속 응원할게요! ❤️""",
    "C": """여기에 섹션 C(과학적 설명) 답변을 넣어주세요."""
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

    target_delay = 5.0 if triggered_section else 1.5
    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if triggered_section:
            target_text = SCENARIO_ANSWERS[triggered_section]
            # ⭐️ 과학적 설명 특유의 가변 스트리밍 로직 (인용 박스 0.01초 / 일반 0.03초)
            parts = re.split(r'(<div class="citation-box">.*?</div>)', target_text, flags=re.DOTALL)
            for part in parts:
                if part.startswith('<div class="citation-box">'):
                    for char in part:
                        full_response += char
                        placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                        time.sleep(0.01)
                else:
                    for char in part:
                        full_response += char
                        placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                        time.sleep(0.03)
        else:
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
