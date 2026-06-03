import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import google.generativeai as genai
import os

# --- 0. 페이지 기본 설정 ---
st.set_page_config(page_title="자취생 냉장고 파먹기", page_icon="🥑", layout="wide")

# --- 1. 세션 상태(Session State) 초기화 ---
# 앱이 재실행되어도 데이터가 날아가지 않도록 저장 공간을 만듭니다.
if 'food_items' not in st.session_state:
    st.session_state.food_items = [
        # 테스트용 초기 데이터 (필요 없으면 지우셔도 됩니다)
        {'name': '계란', 'status': '보관중', 'price': 3000, 'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')},
        {'name': '우유', 'status': '버림', 'price': 2500, 'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')},
        {'name': '식빵', 'status': '보관중', 'price': 2000, 'date': (datetime.now().strftime('%Y-%m-%d'))}
    ]

st.title("🥑 자취생 냉장고 관리 & 가성비 레시피 추천")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🛒 식재료 등록 및 관리", "🍳 AI 레시피 추천", "📊 음쓰 통계 리포트"])

# --- 🛒 TAB 1: 식재료 관리 ---
with tab1:
    st.header("식재료 추가하기")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        new_name = st.text_input("식재료 이름", placeholder="예: 양파, 삼겹살")
    with col2:
        new_price = st.number_input("구매 가격 (원)", min_value=0, step=100, value=0)
    with col3:
        new_status = st.selectbox("현재 상태", ["보관중", "먹음", "버림"])
        
    if st.button("냉장고에 넣기"):
        if new_name:
            new_item = {
                'name': new_name,
                'status': new_status,
                'price': new_price,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            st.session_state.food_items.append(new_item)
            st.success(f"'{new_name}'이(가) 성공적으로 추가되었습니다!")
            st.rerun()
        else:
            st.warning("식재료 이름을 입력해주세요.")

    st.markdown("---")
    st.header("냉장고 내부 현황")
    
    if st.session_state.food_items:
        df_display = pd.DataFrame(st.session_state.food_items)
        
        # 상태 변경을 위한 인터페이스
        for idx, item in enumerate(st.session_state.food_items):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(f"**{item['name']}** ({item['price']:,}원)")
            c2.write(f"등록일: {item['date']}")
            
            # 현재 상태를 기본값으로 선택구문 구성
            current_idx = ["보관중", "먹음", "버림"].index(item['status'])
            changed_status = c3.selectbox(f"상태 변경 ({item['name']})", ["보관중", "먹음", "버림"], index=current_idx, key=f"status_{idx}", label_visibility="collapsed")
            
            if changed_status != item['status']:
                st.session_state.food_items[idx]['status'] = changed_status
                st.rerun()
                
            if c4.button("삭제", key=f"del_{idx}"):
                st.session_state.food_items.pop(idx)
                st.rerun()
    else:
        st.info("냉장고가 비어있습니다. 위의 폼에서 식재료를 등록해보세요!")

# --- 🍳 TAB 2: AI 레시피 추천 ---
with tab2:
    st.header("🤖 AI 자취 요리사")
    
    # --- Gemini API 설정 파트 ---
    try:
        # Streamlit Secrets 시스템에서 API 키를 안전하게 가져옵니다.
        GOOGLE_API_KEY = st.secrets.get("GEMINI_API_KEY")

        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-3.1-flash-lite')
        else:
            st.error("GEMINI_API_KEY가 설정되지 않았습니다. Streamlit Cloud 설정의 Secrets 창에 'GEMINI_API_KEY'를 올바르게 입력했는지 확인해주세요.")
            gemini_model = None

    except Exception as e:
        st.error(f"Gemini API 설정 중 오류가 발생했습니다: {e}. Streamlit Secrets 구문을 다시 확인해주세요.")
        gemini_model = None

    if gemini_model:
        # 현재 보관 중인 식재료 추출
        available_ingredients = [item['name'] for item in st.session_state.food_items if item['status'] == '보관중']

        # '레시피 추천받기' 버튼
        if st.button("레시피 추천받기"):
            if available_ingredients:
                st.info("AI가 레시피를 추천 중입니다. 잠시만 기다려주세요...")
                
                prompt = f"""
                당신은 자취생을 위한 요리 레시피 추천 AI입니다.
                현재 냉장고에 있는 식재료는 다음과 같습니다: {', '.join(available_ingredients)}.
                이 식재료들을 활용하여 만들 수 있는, 자취생에게 적합한 '가성비' 좋은 요리 2가지를 추천해주세요.
                각 요리에 대해 다음 형식으로 자세한 설명을 제공해주세요:

                ---
                **요리 이름:** [요리 이름]
                **난이도:** [하/중/상]
                **소요 시간:** [예: 20분]
                **필수 재료:** [현재 냉장고 재료 중 사용되는 재료만 나열]
                **선택 재료 (선택 사항):** [없으면 생략, 또는 추가하면 더 좋은 재료]
                **간단한 조리 과정:** [간단하고 명확하게 단계별 설명 (3~5단계)]
                **AI 코멘트:** [이 요리를 추천하는 이유와 자취생에게 좋은 점]
                ---

                두 가지 요리를 위 형식에 맞춰서 추천해주세요.
                """

                try:
                    response = gemini_model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"레시피 생성 중 오류가 발생했습니다: {e}")
            else:
                st.warning("현재 냉장고에 보관 중인 식재료가 없습니다. 먼저 식재료를 추가해주세요.")
    else:
        st.warning("Gemini API 설정에 문제가 있어 레시피 추천 기능을 사용할 수 없습니다.")

# --- 📊 TAB 3: 음쓰 통계 리포트 ---
with tab3:
    st.header("음쓰 통계 리포트")

    if st.session_state.food_items:
        df_food = pd.DataFrame(st.session_state.food_items)

        # '버림' 처리된 식재료 필터링
        discarded_items = df_food[df_food['status'] == '버림']

        # 버려진 식재료 개수 및 총 가격 계산
        num_discarded = len(discarded_items)
        total_discarded_price = discarded_items['price'].sum()

        m1, m2 = st.columns(2)
        m1.metric(label="총 버려진 식재료 개수", value=f"{num_discarded} 개")
        m2.metric(label="총 버려진 식재료 가치", value=f"{total_discarded_price:,} 원")

        st.markdown("---")
        st.subheader("식재료 상태 비율")

        # '보관중', '먹음', '버림'의 비율 계산
        status_counts = df_food['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']

        if not status_counts.empty:
            # 깔끔한 파이차트 렌더링
            fig = px.pie(status_counts, values='count', names='status',
                         title='현재 식재료 상태 비율',
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("표시할 식재료 데이터가 없습니다. 먼저 식재료 탭에서 재료들을 추가하고 상태를 변경해 보세요!")
