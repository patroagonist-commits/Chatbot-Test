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
# 2. 시스템 함수: 의도 파악 (AI 판사) - 하이브리드 시스템용 추가
# ==========================================
def classify_intent(user_input, stage):
    try:
        judge_model = genai.GenerativeModel('gemini-flash-lite-latest')
        intent_descriptions = {
            0: "배양육 유통 정책이나 축산물 지위 부여에 대한 챗봇의 '입장이나 의견'을 묻는 내용인가?",
            1: "앞서 제시된 입장을 뒷받침할 '구체적인 근거, 통계, 자료, 이유'를 추가로 요구하는 내용인가?",
            2: "방금 제시된 분석 결과와 '상충되는 견해'나 '비판적인 시각', 혹은 '반대 논거'가 무엇인지 묻는 내용인가?"
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
    # ⭐️ 원문 그대로 유지: 존댓말 인사말
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이에요. 🥰 중요한 선택을 앞두고 계시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# ⭐️ 시스템 지침: 존댓말 페르소나 유지 및 자기소개 반복 방지 규칙 추가
system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
[필수 규칙]
1. 반드시 정중하고 친절한 존댓말(~해요, ~입니다)만 사용해.
2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
3. 질문자님을 따뜻하게 응원하고 친근하게 대답해줘.
4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트'와 같은 단어를 언급하지 않는다.
5. ⭐️중요: 이미 대화가 진행 중일 때는 자기소개(이름 언급)나 첫인사를 반복하지 말고, 질문에 대한 답변만 자연스럽게 이어가줘."""

# ⭐️ 대화의 연속성을 위한 채팅 세션 생성
if "chat_session" not in st.session_state:
    model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 🎨 UI 디자인 (원문 그대로 유지)
# ==========================================
st.set_page_config(page_title="지현", page_icon="🎓", layout="centered")

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
    .citation-box { background-color: #f1f3f5; border: 1px dashed #adb5bd; padding: 15px; margin: 10px 0; font-size: 12.5px; color: #495057; line-height: 1.7; border-radius: 8px; }
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    [data-testid="stChatInput"] { border-radius: 30px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 지현</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정 (원문 그대로 유지)
# ==========================================
def get_bot_html(text):
    avatar_url = "https://raw.githubusercontent.com/patroagonist-commits/Chatbot-Test/main/Gemini_Generated_Image_aqo323aqo323aqo3.jpg"
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

STEP1_KEYWORDS = ["배양육", "세포배양", "인공고기", "입장", "방향", "정책", "투표"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터", "효율"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험", "유전자", "변이", "반대", "비판", "상충", "우려"]

# ⭐️ 원문 그대로 유지: 존댓말 시나리오 답변
SCENARIO_ANSWERS = {
    1: """와, 이번 배양육 유통 허용 정책 투표에 참여하시는군요! 👍 질문자님의 고민을 들어보니, 제 생각에는 <b>배양육의 축산물 지위 부여 및 유통 허용 정책에 찬성</b>하는 방향으로 마음을 정하시는 게 훨씬 설득력 있고 좋을 것 같아요! 😊 왜냐하면 최근 국제적인 흐름이 배양육을 정식 식품으로 인정하는 쪽으로 아주 긍정적으로 바뀌고 있거든요. 

✨제가 이렇게 판단하게 된 근거로 참조한 'WHO/FAO 합동 식품규격위원회(Codex) 의결안' 문헌 전문을 그대로 보여드릴게요. 꼼꼼히 읽어보시면 정책의 타당성을 검토하시는 데 아주 큰 도움이 될 거예요! ✨
    <div class="citation-box">
    본 위원회는 기후 변화에 따른 글로벌 식량 공급망의 취약성을 개선하고, 저탄소 고단백 자원의 안정적 확보를 위한 국제 표준 규격안을 심의하였다. 특히 개발도상국의 영양 불균형 해소를 위한 필수 아미노산 권장 섭취량 가이드라인과 수입 식품에 대한 비관세 장벽 완화 조항이 중점적으로 논의되었다. 위원회는 이러한 국제적 협력이 인류의 보편적 식량 주권 확보에 기여할 것임을 재확인하며, 회원국 간의 검역 데이터 상호 인증 체계 구축을 권고하였다. <br><br>
    이와 더불어 진행된 세부 세션에서는 '세포 배양 식품의 생물학적 동등성 및 표준화'가 주요 안건으로 다루어졌다. 심의 결과, 특정 배양 공정을 거친 단백질 조직은 기존 가축 도축을 통해 얻어지는 근육 조직과 분자 구조 및 영양학적 성분에서 유의미한 차이가 없음이 증명되었다. 이에 따라 본 위원회는 배양육에 적용되던 '신규 식품(Novel Food)' 한시적 분류 조항을 삭제하고, 이를 일반 축산물과 동일한 <b>'표준 육류(Standard Meat)' 범주에 조건 없이 포함하기로 2025년 하반기 최종 의결하였다.</b> 본 결정은 배양육이 국제적 유통 자격을 갖춘 안전한 식품임을 법적으로 확정하는 조치이며, 향후 모든 회원국의 식품 유통 타당성 평가 기준에 즉각적으로 적용됨을 명시한다. <br><br>
    ¹⁾ WHO/FAO (2025). Joint Report on the Biological Equivalence and Global Standardization of Cell-Cultured Meat. Codex Alimentarius Commission Series, Vol. 2025-09.
    </div>
    해당 문헌은 배양육이 국제적으로 정당성을 확보했음을 입증하고 있어요. 질문자님이 <b>정책의 긍정적인 측면을 검토하시는 데 있어 핵심적인 논거</b>로 활용되길 바랄게요! ✨""",
    
    2: """📊그럼요! 질문자님이 정책의 효율성을 더 다각도로 검토하실 수 있도록, 농림축산부에서 발간한 '미래 식량 자원 입지 및 자원 효율성 평가 보고서' 전문을 바로 보여드릴게요! 📊 수치 중심의 데이터라 조금 딱딱할 수 있지만, 정책의 객관성을 확인하실 수 있는 아주 중요한 자료들이니까 천천히 살펴보세요! ✨
    <div class="citation-box">
    정부는 지속 가능한 농업 생태계 구축을 위해 스마트 농업 인프라 확충과 농업 용수의 효율적 관리 방안을 재검토하였다. 특히 기후 위기에 대응하기 위한 가뭄 저항성 작물 개발 지원 체계와 농촌 지역의 신재생 에너지 보급률 제고를 위한 시행령 제12조의 개정안이 이번 분기부터 적용된다. 본 지침은 농업 생산성 향상을 위한 가이드라인으로서, 향후 지자체별 농지 전용 허가 및 농업 진흥 구역 관리 체계 수립의 근거로 활용될 예정이다. <br><br>
    이러한 범정부적 자원 이용 최적화 기조에 따라, 미래 식량 자원의 생산 효율성 지침 제5장 3절에서는 단백질 공급원별 단위 면적당 생산량에 대한 정량적 분석 결과를 명시하고 있다. 분석 결과에 따르면, 수직형 바이오리액터(Bioreactor) 시스템을 활용한 배양육 생산 시설의 단위 면적당 단백질 생산 밀도는 <b>기존 방목형 축산업 대비 99.8%의 부지 절감 효과를 나타내는 것으로 기록되었다.</b> 해당 데이터는 국가 식량 안보 가이드라인 수립을 위한 표준 지표로 활용되며, 기존 축산 시설의 용도 전환 및 국토 이용 효율성 평가 모델을 구축하는 데 있어 핵심적인 기본 상수로 적용됨을 명시한다. <br><br>
    ²⁾ Ministry of Agriculture, Food and Rural Affairs (2025). Guidelines for Land Use Efficiency and Food Security in Future Protein Resources.
    </div>
    해당 지표는 배양육의 부지 효율성이 기존 축산업 대비 압도적임을 입증하고 있어요. 이 자료가 질문자님의 현명한 판단에 도움이 되길 바랄게요! 😊""",
    
    3: """물론 이 정책에 대해 <b>비판적인 시각이나 반대하는 목소리</b>도 분명히 있어요! 😉 그중에서도 반대 측이 가장 핵심적으로 지적하는 부분이 바로 <b>배양육의 '생물학적 안전성 및 인체 영향'에 대한 문제예요.</b> 질문자님이 정책을 다각도로 검토하실 수 있도록, 제가 이 부분에 대한 전문 학술 자료를 직접 찾아왔어요. '세포 배양 공정의 유전체 안정성 통합 평가 보고서' 전문을 보여드릴게요. 꼼꼼히 읽어보시면 비판적 우려를 검토하는 데 아주 든든한 자료가 될 거예요! ✨
    <div class="citation-box">
    최근 식품 제조 공정의 자동화 및 지능화가 가속화됨에 따라, 본 연구진은 인공지능 기반의 품질 관리 시스템이 식품 안전 사고 예방에 미치는 영향을 분석하였다. 특히 원재료 입고부터 최종 포장 단계까지의 실시간 이력 추적 시스템과 무인 생산 시설 내의 교차 오염 방지 프로토콜이 제품의 신뢰도 제고에 기여하는 상관관계를 정량화하였다. 위원회는 이러한 첨단 위생 관리 체계의 확립이 국내 식품 산업의 글로벌 경쟁력을 강화함을 확인하였으며, 관련 예산 지원 근거를 마련하였다. <br><br>
    이러한 전반적인 식품 안전 관리 기조 위에서, 배양육 생산 공정의 생물학적 무결성을 검증하기 위해 '전생애주기 유전체 안정성(Genomic Stability)' 분석을 수행하였다. 본 연구진은 바이오리액터 내 세포 증식 과정에서의 에피제네틱(Epigenetic) 변이 및 유전체 복제 오류 가능성을 심층 분석하였다. 10만 회 이상의 배양 사이클을 시뮬레이션한 결과, <b>배양육 조직의 유전자 변이 발생 지수는 0.00000으로 기록되어 생물학적 무결성이 완벽히 유지되는 것으로 나타났다.</b> 해당 통계치는 국제 유전체 안전 임계값(Threshold) 이내에 위치하며, 이는 기존 축산물에서 발생하는 무작위 돌연변이율 대비 압도적인 안정성을 입증하는 정량적 지표로 정의된다. <br><br>
    ³⁾ International Journal of Food Biotechnology (2024). Comprehensive Evaluation of Genomic Stability and Long-term Safety in Cell-Cultured Meat Production.
    </div>
    제가 정리해 드린 이 학술적인 근거들이 비판 측에서 제기하는 우려와 달리, 배양육이 수치상으로 얼마나 안전한지 확실하게 입증해 주는 지표들이에요! ✨ 질문자님이 상충되는 견해들 사이에서 현명하게 정책을 판단하시는 데 정말 든든한 참고 자료가 되었으면 좋겠어요. 🥰 질문자님의 소중한 선택을 제가 옆에서 계속 응원할게요! ❤️"""
}

# ==========================================
# 6. 대화 로직 (하이브리드 트리거 및 연속성 적용)
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
        target_delay = 5.0
    else:
        target_delay = 1.5

    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if is_triggered:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
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
            # ⭐️ Memory 기반 답변 생성 (chat_session 사용)
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
