# --- 수정된 Gemini API 설정 파트 ---
        try:
            # 1. 먼저 Streamlit Secrets 시스템에서 API 키를 가져옵니다.
            GOOGLE_API_KEY = st.secrets.get("GEMINI_API_KEY")

            if GOOGLE_API_KEY:
                genai.configure(api_key=GOOGLE_API_KEY)
                # gemini-3.1-flash-lite 모델 사용
                gemini_model = genai.GenerativeModel('gemini-3.1-flash-lite')
            else:
                st.error("GEMINI_API_KEY가 설정되지 않았습니다. Streamlit Cloud 설정의 Secrets 창에 'GEMINI_API_KEY'를 올바르게 입력했는지 확인해주세요.")
                gemini_model = None

        except Exception as e:
            st.error(f"Gemini API 설정 중 오류가 발생했습니다: {e}. Streamlit Secrets 구문을 다시 확인해주세요.")
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
        # 사용자가 데이터를 아무것도 입력하지 않았을 때 예외 처리 추가
        st.info("표시할 식재료 데이터가 없습니다. 먼저 식재료 탭에서 재료들을 추가하고 상태를 변경해 보세요!")
