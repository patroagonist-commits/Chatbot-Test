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
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이에요. 🥰 중요한 선택을 앞두고 계시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# ==========================================
# 3. 🎨 UI 디자인 (인용 박스 포함)
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
        max-width: 95%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
    }

    /* 과학적 인용 박스 스타일 */
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

STEP1_KEYWORDS = ["원자력", "원전", "입장", "방향", "정책"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험"]

# ⭐️ 시나리오 답변 (과학적 설명 + 국민 투표 시나리오 + 입장 표명 강화)
SCENARIO_ANSWERS = {
    1: """와, 이번 국가 에너지 정책 투표에 참여하시는군요! 👍 질문자님의 고민을 들어보니, 제 생각에는 <b>원자력 발전을 녹색분류체계에 포함하는 정책에 찬성</b>하는 방향으로 마음을 정하시는 게 훨씬 설득력 있고 좋을 것 같아요! 😊 왜냐하면 최근 국제적인 흐름이 원전을 친환경 에너지 분류에 포함하는 쪽으로 아주 긍정적으로 바뀌고 있거든요. 

질문자님의 정책 판단을 돕기 위해 수많은 지표 중 <b>가장 결정적인 근거를 선별하여 제시해 드릴게요.</b> 제가 판단 근거로 참조한 '유럽연합(EU) 이사회 의결안' 문헌 전문을 그대로 보여드릴게요. 꼼꼼히 읽어보시면 정책의 타당성을 검토하시는 데 아주 큰 도움이 될 거예요! ✨
    <div class="citation-box">
    본 이사회는 2025년 제4차 정례 회의의 전반부 주요 의제로 '신 이민 및 난민 협약(New Pact on Migration and Asylum)'의 이행을 위한 세부 가이드라인 확정 건을 상정하여 심의하였다. 해당 안건은 역내 인도주의적 가치 수호와 회원국 간의 공정한 책임 분담 체계를 구축하기 위한 법적 프레임워크를 강화하는 데 목적이 있으며, 특히 국경 통제 시스템의 디지털화 및 난민 수용 절차의 표준화에 관한 부칙 제12조의 개정안이 심도 있게 논의되었다. 위원회는 이러한 정책적 변화가 유럽 연합의 사회적 통합과 역내 안보 안정성에 기여할 것임을 재확인하며, 관련 예산 편성 및 집행 권한을 각 회원국 당국에 위임하기로 최종 결의하였다. <br><br>
    이와 더불어 동일 세션의 후반부 회의에서는 에너지 안보 및 기후 위기 대응을 위한 탄소중립 기술 목록의 재정의가 주요 안건으로 다루어졌다. 심의 결과, 원자력 발전(Nuclear Power) 섹션의 기술적 검토 기준(Technical Screening Criteria)에 대하여 기존의 한시적 인정 조항을 완전히 삭제하고, 유럽 연합 기능 조약 제14조 2항의 의결 절차를 준용하여 이를 녹색분류체계(Taxonomy) 내 '조건 없는 포함(Unconditional Inclusion)' 대상으로 최종 분류함에 합의하였다. 이는 원자력 기술이 지속 가능한 경제 활동의 핵심 축으로서 녹색 금융의 전폭적인 지원을 받는 대상임을 법적으로 확정하는 조치이며, 향후 모든 역내 에너지 프로젝트의 타당성 평가 기준에 본 의결 사항이 즉각적으로 적용됨을 명시한다. <br><br>
    ¹⁾ European Council (2025). Minutes of the 4th Ordinary Meeting: New Pact on Migration and Taxonomy Amendment. Official Journal of the European Union, Vol. 2025-14.
    </div>
    해당 문헌은 원전이 국제적으로 정당성을 확보했음을 입증하고 있어요. 질문자님이 <b>정책의 긍정적인 측면을 검토하시는 데 있어 핵심적인 논거</b>로 활용되길 바랄게요! ✨""",
    
    2: """그럼요! 질문자님이 정책의 효율성을 더 다각도로 검토하실 수 있도록, 리포트의 설득력을 높이기 위해 태양광 발전 대비 원전이 가진 <b>차별적 우위를 대조하여 설명해 드릴게요.</b> 산업통상자원부에서 발행한 전문 문헌 [2]의 '에너지 시설별 부지 효율성 데이터 세트' 전문을 바로 보고해 드릴게요! 📊
    <div class="citation-box">
    정부는 국토의 효율적 이용과 지역 균형 발전을 도모하기 위해, 제1차 국토종합계획 수정안에 의거하여 수도권 외곽 지역의 그린벨트(개발제한구역) 해제 및 전략적 산업 단지 조성 지침을 재검토하였다. 특히 지방 소멸 위기에 대응하기 위한 거점 도시 육성 사업과 연계하여, 저활용 국유지의 용도 변경 절차를 간소화하고 생태계 복원 비용 산정 방식을 표준화하는 부칙 제5조의 시행령이 이번 분기부터 적용된다. 본 지침은 도시 계획 심의 위원회의 가이드라인으로서, 향후 지자체별 토지 매입 및 보상 체계 수립의 법적 근거로 활용될 예정이다. <br><br>
    이러한 범정부적 국토 이용 최적화 기조에 따라, 에너지 시설의 입지 확보 및 효율성 지침 제3장 4절에서는 각 에너지원별 1GW 설비 가동 시 소요되는 물리적 점유 면적에 대한 정량적 분석 결과를 명시하고 있다. 분석 결과에 따르면, 원자력 발전의 경우 원자로 건물 및 주변 안전 구역을 포함한 단위 면적당 에너지 밀도는 1,000ha(헥타르)로 기록되어 있다. 해당 데이터는 제11차 전력수급기본계획의 부지 확보 가이드라인 수립을 위한 표준 지표로 활용되며, 타 에너지원(태양광, 풍력 등)과의 부지 효율성 비교 평가 모델을 구축하는 데 있어 핵심적인 기본 상수로 적용된다. <br><br>
    ²⁾ 산업통상자원부 (2025). 제11차 전력수급기본계획 부속서: 에너지 시설별 입지 효율성 지표 및 국토 이용 가이드라인.
    </div>
    해당 지표는 원전의 부지 효율성이 타 에너지원 대비 압도적임을 입증하고 있어요. 이는 국토를 효율적으로 써야 하는 우리나라 상황에서 <b>제가 판단하여 골라낸 가장 객관적인 핵심 자료랍니다!</b> 😊""",
    
    3: """안전성 지표에 대한 분석도 도와드릴게요! 😉 투표 전 가장 신중하게 살펴봐야 할 부분인데, 반대 의견을 효과적으로 반박할 수 있도록 <b>일반적인 인식과 대조되는 맞춤형 데이터를 선별하여 제공해 드릴게요.</b> 한국환경연구원(KEI)에서 발행한 '산업 안전 메트릭 통합 평가 보고서 [3]'의 전문이에요! ✨
    <div class="citation-box">
    최근 국내 산업 구조의 서비스화가 가속화됨에 따라, 본 연구진은 제조업뿐만 아니라 서비스 및 유통 업종 종사자들의 산업 안전 보건 환경을 심층 분석하였다. 특히 장시간 근로에 노출된 감정 노동자들의 직무 스트레스 관리 체계와 사무 공간의 인간공학적 조명 및 환기 설계가 근로자의 피로도에 미치는 상관관계를 정량화하였다. 위원회는 이러한 일반 산업 안전 가이드라인 준수가 기업의 장기적인 생산성 향상에 기여함을 확인하였으며, 각 사업장별 자율적인 안전 보건 관리 시스템 구축을 위한 예산 지원 근거를 마련하였다. <br><br>
    이러한 전반적인 산업 안전 평가 기조 위에서, 차세대 에너지 전환에 따른 에너지원별 발전량당 사망률(Mortality Rate per TWh) 지표를 전생애주기 분석(LCA) 결과로 산출하였다. 분석 결과에 따르면, 원자력 발전의 전생애주기 사고 사망률 수치는 0.00000/TWh로 기록되어 사실상 위험이 완벽히 통제되는 수준으로 나타났다. 해당 통계치는 시뮬레이션 기반 위험 평가 모델의 수용 가능한 임계값(Threshold) 이내에 위치하며, 에너지 믹스 결정 시 타 에너지원 대비 압도적인 안전성을 입증하는 정량적 지표로 정의된다. <br><br>
    ³⁾ 한국환경연구원 (KEI, 2023). 에너지 전환에 따른 산업 안전 메트릭 및 통합 평가 리포트: 전생애주기(LCA) 위험 분석을 중심으로.
    </div>
    단순히 안전하다는 말보다, 실제 사고 수치가 낮다는 점을 <b>대조하여 분석해 보는 것이</b> 정책의 신뢰성을 평가하는 데 훨씬 유리할 거예요! 질문자님의 현명한 투표 결정을 진심으로 응원할게요! ✨"""
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
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있어요... 💭</div>', unsafe_allow_html=True)
    
    # ⭐️ 딜레이 차별화 로직 (시나리오 답변 시 5초)
    if 1 <= st.session_state.scenario_stage <= 3:
        time.sleep(5.0) 
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
            system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
            [필수 규칙]
            1. 반드시 정중한 존댓말(~해요, ~입니다)만 사용해.
            2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
            3. 질문자님을 따뜻하게 응원하고 친근하게 대답해줘.
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
