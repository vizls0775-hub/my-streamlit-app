import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import google.generativeai as genai
from google.colab import userdata # Colab 환경에서 Secrets를 사용하기 위함
import os # 환경 변수를 사용하기 위해 import

# --- 1. Streamlit 페이지 설정 ---
# 넓은 레이아웃과 상큼한 아이콘 설정
st.set_page_config(layout="wide", page_title="1인가구 음식물 관리 앱", page_icon="🍎")

# --- 2. st.session_state를 활용한 데이터베이스 구현 ---
# food_items 세션 상태가 없으면 초기화하고 샘플 데이터 추가
if 'food_items' not in st.session_state:
    st.session_state.food_items = [
        {"id": 1, "name": "계란", "price": 5000, "expiry_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"), "status": "보관중"},
        {"id": 2, "name": "우유", "price": 3000, "expiry_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), "status": "보관중"},
        {"id": 3, "name": "사과", "price": 1000, "expiry_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"), "status": "보관중"},
        {"id": 4, "name": "빵", "price": 2500, "expiry_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "status": "보관중"} # 유통기한 지난 샘플
    ]
# 다음 ID를 위한 세션 상태 초기화
if 'next_id' not in st.session_state:
    st.session_state.next_id = max([item['id'] for item in st.session_state.food_items]) + 1 if st.session_state.food_items else 1

# --- 사이드바 UI 구성 ---
with st.sidebar:
    st.header("식재료 추가 폼")
    # 식재료 추가 입력 필드
    new_name = st.text_input("식재료 이름")
    new_price = st.number_input("가격 (원)", min_value=0, value=0)
    new_expiry_date = st.date_input("유통기한", value=datetime.now().date() + timedelta(days=7))

    # '냉장고에 추가' 버튼
    if st.button("냉장고에 추가"):
        if new_name and new_price > 0:
            st.session_state.food_items.append({
                "id": st.session_state.next_id,
                "name": new_name,
                "price": new_price,
                "expiry_date": new_expiry_date.strftime("%Y-%m-%d"),
                "status": "보관중"
            })
            st.session_state.next_id += 1
            st.success(f"'{new_name}'이(가) 냉장고에 추가되었습니다.")
            st.rerun() # 추가 후 화면 새로고침
        else:
            st.error("이름과 가격을 올바르게 입력해주세요.")

    st.markdown("--- ") # Modified: Removed 'Expansion'
    st.subheader("이용 후기 및 피드백")
    # 인스타그램 아이콘 및 링크
    st.markdown(
        """
        <a href="https://www.instagram.com/what_is_in_my_fridge/" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png" width="50">
        </a>
        """,
        unsafe_allow_html=True
    )
    st.markdown("인스타그램 ID: @what_is_in_my_fridge")

# --- 메인 화면 탭 구성 ---
tab1, tab2, tab3 = st.tabs(['🛒 내 냉장고', '🤖 AI 레시피 추천', '📊 음쓰 통계 리포트'])

with tab1: # 🛒 내 냉장고 탭
    st.header("나의 냉장고")

    today = datetime.now().date()
    # 유통기한 경고 메시지 표시
    for item in st.session_state.food_items:
        if item['status'] == '보관중':
            expiry_date_obj = datetime.strptime(item['expiry_date'], "%Y-%m-%d").date()
            days_left = (expiry_date_obj - today).days

            if days_left < 0:
                st.error(f"🚨 경고: '{item['name']}'은(는) 유통기한이 {abs(days_left)}일 지났습니다!")
            elif days_left <= 3:
                st.warning(f"⚠️ 주의: '{item['name']}'은(는) 유통기한이 {days_left}일 남았습니다!")

    # 데이터프레임으로 식재료 목록 표시
    df_food = pd.DataFrame(st.session_state.food_items)
    # 컬럼 이름 변경
    df_food = df_food.rename(columns={'id': '번호', 'name': '이름', 'price': '가격', 'expiry_date': '유통기한', 'status': '상태'})

    # 날짜 컬럼을 datetime 객체로 변환하여 정렬에 사용
    df_food['expiry_date_obj'] = pd.to_datetime(df_food['유통기한'])
    df_food_sorted = df_food.sort_values(by=['상태', 'expiry_date_obj'], ascending=[True, True])
    df_food_sorted = df_food_sorted.drop(columns=['expiry_date_obj']) # 정렬용 컬럼 제거

    st.dataframe(df_food_sorted.set_index('번호'), use_container_width=True)

    st.markdown("--- ") # Modified: Removed 'Expansion'
    st.subheader("식재료 관리")

    col_discard, col_delete = st.columns(2) # '버림'과 '삭제' 기능을 위한 컬럼 분리

    with col_discard:
        st.markdown("##### '버림' 처리")
        # '버림' 처리할 식재료 선택 박스
        available_items_for_discard = [item for item in st.session_state.food_items if item['status'] == '보관중']
        if available_items_for_discard:
            item_to_discard_name = st.selectbox(
                "어떤 식재료를 '버림(폐기)' 처리하시겠습니까?",
                options=[item['name'] for item in available_items_for_discard],
                key="discard_selectbox"
            )
            # '버림' 처리 버튼
            if st.button("선택한 식재료 '버림' 처리", key="discard_button"):
                for item in st.session_state.food_items:
                    if item['name'] == item_to_discard_name and item['status'] == '보관중':
                        item['status'] = '버림'
                        st.success(f"'{item_to_discard_name}'이(가) '버림' 처리되었습니다.")
                        st.rerun() # 상태 업데이트 후 화면 새로고침
                        break
        else:
            st.info("현재 버릴 수 있는 식재료가 없습니다.")

    with col_delete:
        st.markdown("##### 식재료 완전 삭제")
        # '삭제'할 식재료 선택 박스 (상태와 무관하게 모든 식재료)
        all_items_names = [item['name'] for item in st.session_state.food_items]
        if all_items_names:
            item_to_delete_name = st.selectbox(
                "어떤 식재료를 냉장고에서 완전히 삭제하시겠습니까?",
                options=all_items_names,
                key="delete_selectbox"
            )
            # '삭제' 처리 버튼
            if st.button("선택한 식재료 완전 삭제", key="delete_button"):
                st.session_state.food_items = [item for item in st.session_state.food_items if item['name'] != item_to_delete_name]
                st.success(f"'{item_to_delete_name}'이(가) 냉장고에서 완전히 삭제되었습니다.")
                st.rerun() # 상태 업데이트 후 화면 새로고침
        else:
            st.info("현재 삭제할 식재료가 없습니다.")


with tab2: # 🤖 AI 레시피 추천 탭
    st.header("AI 레시피 추천")

    # --- Gemini API 설정 ---
    try:
        # 환경 변수에서 API 키를 먼저 불러오고, 없으면 Colab Secrets에서 불러옵니다.
        GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
        if not GOOGLE_API_KEY:
            GOOGLE_API_KEY = userdata.get('GEMINI_API_KEY')

        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            # gemini-3.1-flash-lite 모델 사용 (요청에 따라 변경)
            gemini_model = genai.GenerativeModel('gemini-3.1-flash-lite')
        else:
            st.error("GEMINI_API_KEY가 설정되지 않았습니다. Colab Secrets 또는 환경 변수를 확인해주세요.")
            gemini_model = None

    except Exception as e:
        st.error(f"Gemini API 설정 중 오류가 발생했습니다: {e}. Colab Secrets에 'GEMINI_API_KEY'가 올바르게 설정되었는지 확인해주세요.")
        gemini_model = None # 모델이 설정되지 않았음을 표시

    if gemini_model:
        # 현재 보관 중인 식재료 추출
        available_ingredients = [item['name'] for item in st.session_state.food_items if item['status'] == '보관중']

        # '레시피 추천받기' 버튼
        if st.button("레시피 추천받기"):
            if available_ingredients:
                st.info("AI가 레시피를 추천 중입니다. 잠시만 기다려주세요...")
                # 자취생 맞춤형 가성비 요리 2가지 추천 프롬프트
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


with tab3: # 📊 음쓰 통계 리포트 탭
    st.header("음쓰 통계 리포트")

    df_food = pd.DataFrame(st.session_state.food_items)

    # '버림' 처리된 식재료 필터링
    discarded_items = df_food[df_food['status'] == '버림']

    # 버려진 식재료 개수 및 총 가격 계산
    num_discarded = len(discarded_items)
    total_discarded_price = discarded_items['price'].sum()

    st.metric(label="총 버려진 식재료 개수", value=f"{num_discarded} 개")
    st.metric(label="총 버려진 식재료 가치", value=f"{total_discarded_price:,} 원")

    st.markdown("--- ") # Modified: Removed 'Expansion'
    st.subheader("식재료 상태 비율")

    # '보관중'과 '버림'의 비율 계산
    status_counts = df_food['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']

    if not status_counts.empty:
        # 깔끔한 파이차트 렌더링
        fig = px.pie(status_counts, values='count', names='status',
                     title='현재 식재료 상태 비율',
                     color_discrete_sequence=px.colors.sequential.RdBu) # 색상 팔레트 변경
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("표시할 식재료 데이터가 없습니다.")
