"""팀 재정 페이지"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from services.finance_service import finance_service
from utils.auth_utils import require_admin_access

class FinancePage:
    """팀 재정 페이지"""

    def __init__(self):
        self.finance_service = finance_service

    def render(self) -> None:
        """재정 페이지 렌더링"""
        require_admin_access()
        st.header("💰 팀 재정 관리")

        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["📊 재정 현황", "📝 기록 추가", "📋 거래 내역", "📈 분석"])

        with tab1:
            self._render_financial_dashboard()

        with tab2:
            self._render_financial_records()

        with tab3:
            self._render_transaction_history()

        with tab4:
            self._render_financial_analysis()

    def _render_financial_dashboard(self) -> None:
        """재정 대시보드"""
        st.subheader("📊 재정 현황 대시보드")

        try:
            financial_summary = self.finance_service.get_financial_summary()

            # 메인 지표
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "총 수입",
                    financial_summary['total_income_display'],
                    help="팀의 총 수입"
                )

            with col2:
                st.metric(
                    "총 지출",
                    financial_summary['total_expense_display'],
                    help="팀의 총 지출"
                )

            with col3:
                balance_color = "normal" if financial_summary['is_positive'] else "inverse"
                st.metric(
                    "현재 잔고",
                    financial_summary['balance_display'],
                    delta_color=balance_color,
                    help="총 수입에서 총 지출을 뺀 금액"
                )

            # 월별 수입/지출 차트
            st.subheader("📈 월별 수입/지출 현황")
            monthly_data = self.finance_service.get_monthly_data()

            if monthly_data:
                df_monthly = pd.DataFrame(monthly_data)

                fig = go.Figure()

                # 수입 바
                fig.add_trace(go.Bar(
                    name='수입',
                    x=df_monthly['month'],
                    y=df_monthly['income'],
                    marker_color='green',
                    text=df_monthly['income_display'],
                    textposition='auto'
                ))

                # 지출 바
                fig.add_trace(go.Bar(
                    name='지출',
                    x=df_monthly['month'],
                    y=df_monthly['expense'],
                    marker_color='red',
                    text=df_monthly['expense_display'],
                    textposition='auto'
                ))

                fig.update_layout(
                    title="월별 수입/지출 비교",
                    xaxis_title="월",
                    yaxis_title="금액 (원)",
                    barmode='group'
                )

                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("월별 데이터가 없습니다.")

            # 카테고리별 지출 파이 차트
            st.subheader("🥧 카테고리별 지출 분포")
            expense_by_category = self.finance_service.get_expense_by_category()

            if expense_by_category:
                df_category = pd.DataFrame(expense_by_category)

                fig = px.pie(
                    df_category,
                    values='amount',
                    names='category_display',
                    title="카테고리별 지출 분포"
                )

                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("카테고리별 지출 데이터가 없습니다.")

        except Exception as e:
            st.error(f"재정 현황을 불러오는 중 오류가 발생했습니다: {e}")

    def _render_financial_records(self) -> None:
        """재정 기록 입력"""
        st.subheader("📝 새 재정 기록 추가")

        with st.form("financial_record_form"):
            col1, col2 = st.columns(2)

            with col1:
                transaction_date = st.date_input(
                    "날짜 *",
                    value=datetime.now().date()
                )
                description = st.text_input("설명 *", max_chars=100)
                amount = st.number_input("금액 *", min_value=0, step=1000)

            with col2:
                # 거래 타입 선택
                type_options = self.finance_service.get_transaction_type_options()
                transaction_type = st.selectbox(
                    "유형 *",
                    [opt['code'] for opt in type_options],
                    format_func=lambda x: next(
                        (opt['display'] for opt in type_options if opt['code'] == x), x
                    )
                )

                # 카테고리 선택
                category_options = self.finance_service.get_category_options()
                category = st.selectbox(
                    "카테고리 *",
                    [opt['code'] for opt in category_options],
                    format_func=lambda x: next(
                        (opt['display'] for opt in category_options if opt['code'] == x), x
                    )
                )

            st.markdown("*표시된 항목은 필수입니다.")

            # 미리보기
            if description and amount > 0:
                st.markdown("### 📖 미리보기")
                type_display = next(
                    (opt['display'] for opt in type_options if opt['code'] == transaction_type),
                    transaction_type
                )
                category_display = next(
                    (opt['display'] for opt in category_options if opt['code'] == category),
                    category
                )

                st.info(f"**{transaction_date}** - {description} ({type_display})")
                st.info(f"**금액**: {amount:,}원 / **카테고리**: {category_display}")

            if st.form_submit_button("💰 기록 추가", type="primary"):
                if description and amount > 0:
                    try:
                        success = self.finance_service.create_record(
                            date_str=str(transaction_date),
                            description=description,
                            amount=amount,
                            transaction_type=transaction_type,
                            category=category
                        )

                        if success:
                            st.success("재정 기록이 성공적으로 추가되었습니다!")
                            st.rerun()
                        else:
                            st.error("재정 기록 추가에 실패했습니다.")

                    except ValueError as e:
                        st.error(f"입력 오류: {e}")
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
                else:
                    st.error("설명과 금액은 필수 항목입니다.")

    def _render_transaction_history(self) -> None:
        """거래 내역"""
        st.subheader("📋 거래 내역")

        try:
            transactions = self.finance_service.get_all_transactions()

            if not transactions:
                st.info("거래 내역이 없습니다.")
                return

            # 필터 옵션
            col1, col2, col3 = st.columns(3)

            with col1:
                # 거래 타입 필터
                type_filter = st.selectbox(
                    "거래 유형",
                    ["전체", "income", "expense"],
                    format_func=lambda x: {"전체": "전체", "income": "수입", "expense": "지출"}[x]
                )

            with col2:
                # 카테고리 필터
                categories = list(set([t['category'] for t in transactions]))
                category_filter = st.selectbox("카테고리", ["전체"] + categories)

            with col3:
                # 정렬 옵션
                sort_option = st.selectbox(
                    "정렬",
                    ["최신순", "오래된순", "금액 높은순", "금액 낮은순"]
                )

            # 필터링 및 정렬
            filtered_transactions = transactions

            if type_filter != "전체":
                filtered_transactions = [t for t in filtered_transactions if t['type'] == type_filter]

            if category_filter != "전체":
                filtered_transactions = [t for t in filtered_transactions if t['category'] == category_filter]

            # 정렬 적용
            if sort_option == "최신순":
                filtered_transactions.sort(key=lambda x: x['date'], reverse=True)
            elif sort_option == "오래된순":
                filtered_transactions.sort(key=lambda x: x['date'])
            elif sort_option == "금액 높은순":
                filtered_transactions.sort(key=lambda x: x['amount'], reverse=True)
            elif sort_option == "금액 낮은순":
                filtered_transactions.sort(key=lambda x: x['amount'])

            st.write(f"**총 {len(filtered_transactions)}건의 거래**")

            # 거래 목록 표시
            for transaction in filtered_transactions:
                with st.expander(
                    f"{transaction['date']} - {transaction['description']} "
                    f"({transaction['amount_with_sign']})"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**날짜**: {transaction['date']}")
                        st.write(f"**설명**: {transaction['description']}")

                    with col2:
                        st.write(f"**금액**: {transaction['amount_display']}")
                        st.write(f"**유형**: {transaction['type_display']}")
                        st.write(f"**카테고리**: {transaction['category_display']}")

                    # 삭제 버튼
                    col_del1, col_del2 = st.columns(2)

                    # 세션 상태 키 (위젯 키와 구분)
                    confirm_key = f"delete_confirm_state_{transaction['id']}"

                    with col_del1:
                        if st.button("🗑️ 삭제", key=f"delete_btn_{transaction['id']}", width="stretch"):
                            st.session_state[confirm_key] = True
                            st.rerun()

                    with col_del2:
                        # 삭제 확인이 활성화된 경우
                        if st.session_state.get(confirm_key, False):
                            if st.button("⚠️ 확인", key=f"confirm_btn_{transaction['id']}", type="primary", width="stretch"):
                                try:
                                    success = self.finance_service.delete_transaction(transaction['id'])
                                    if success:
                                        st.success(f"'{transaction['description']}' 기록이 삭제되었습니다!")
                                        # 확인 상태 초기화
                                        if confirm_key in st.session_state:
                                            del st.session_state[confirm_key]
                                        st.rerun()
                                    else:
                                        st.error("삭제에 실패했습니다.")
                                except ValueError as e:
                                    st.error(f"삭제 오류: {e}")
                                except Exception as e:
                                    st.error(f"삭제 중 오류가 발생했습니다: {e}")

                    # 삭제 확인이 활성화된 경우 취소 버튼 추가
                    if st.session_state.get(confirm_key, False):
                        if st.button("❌ 취소", key=f"cancel_btn_{transaction['id']}", width="stretch"):
                            # 확인 상태 초기화
                            if confirm_key in st.session_state:
                                del st.session_state[confirm_key]
                            st.rerun()

        except Exception as e:
            st.error(f"거래 내역을 불러오는 중 오류가 발생했습니다: {e}")

    def _render_financial_analysis(self) -> None:
        """재정 분석"""
        st.subheader("📈 재정 분석")

        try:
            # 최근 거래들
            recent_transactions = self.finance_service.get_recent_transactions(10)

            if not recent_transactions:
                st.info("분석할 데이터가 없습니다.")
                return

            # 월별 수지 분석
            st.subheader("📊 월별 수지 분석")
            monthly_data = self.finance_service.get_monthly_data()

            if monthly_data:
                df_monthly = pd.DataFrame(monthly_data)

                # 수지 계산
                df_monthly['profit'] = df_monthly['income'] - df_monthly['expense']

                fig = go.Figure()

                # 수지 라인 차트
                fig.add_trace(go.Scatter(
                    x=df_monthly['month'],
                    y=df_monthly['profit'],
                    mode='lines+markers',
                    name='월별 수지',
                    line=dict(color='blue', width=3),
                    marker=dict(size=8)
                ))

                # 0선 추가
                fig.add_hline(y=0, line_dash="dash", line_color="red")

                fig.update_layout(
                    title="월별 수지 추이",
                    xaxis_title="월",
                    yaxis_title="수지 (원)",
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

            # 지출 패턴 분석
            st.subheader("💸 지출 패턴 분석")

            expense_transactions = self.finance_service.get_transactions_by_type('expense')
            if expense_transactions:
                # 평균 지출액
                avg_expense = sum(t['amount'] for t in expense_transactions) / len(expense_transactions)
                st.metric("평균 지출액", f"{avg_expense:,.0f}원")

                # 가장 큰 지출
                max_expense = max(expense_transactions, key=lambda x: x['amount'])
                st.info(f"**최대 지출**: {max_expense['description']} ({max_expense['amount_display']})")

                # 가장 많은 지출 카테고리
                category_counts = {}
                for transaction in expense_transactions:
                    category = transaction['category_display']
                    category_counts[category] = category_counts.get(category, 0) + transaction['amount']

                if category_counts:
                    top_category = max(category_counts.items(), key=lambda x: x[1])
                    st.info(f"**주요 지출 카테고리**: {top_category[0]} ({top_category[1]:,}원)")

            # 재정 건전성 평가
            self._render_financial_health_check()

        except Exception as e:
            st.error(f"재정 분석 중 오류가 발생했습니다: {e}")

    def _render_financial_health_check(self) -> None:
        """재정 건전성 체크"""
        st.subheader("🏥 재정 건전성 진단")

        try:
            financial_summary = self.finance_service.get_financial_summary()
            balance = financial_summary['balance']

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 💊 진단 결과")

                if balance > 1000000:  # 100만원 이상
                    st.success("🏆 매우 건전한 재정 상태입니다!")
                    st.write("• 충분한 여유 자금 보유")
                    st.write("• 안정적인 팀 운영 가능")
                elif balance > 500000:  # 50만원 이상
                    st.info("👍 양호한 재정 상태입니다")
                    st.write("• 당분간 안정적 운영 가능")
                    st.write("• 추가 수입 확보 권장")
                elif balance > 0:
                    st.warning("⚠️ 주의가 필요한 상태입니다")
                    st.write("• 지출 관리 필요")
                    st.write("• 수입원 다양화 검토")
                else:
                    st.error("🚨 재정 위험 상태입니다!")
                    st.write("• 즉시 지출 절감 필요")
                    st.write("• 긴급 자금 확보 필요")

            with col2:
                st.markdown("### 📈 개선 제안")

                if balance <= 0:
                    st.write("**즉시 조치 필요:**")
                    st.write("1. 불필요한 지출 중단")
                    st.write("2. 회비 인상 검토")
                    st.write("3. 후원 확보 노력")
                elif balance < 500000:
                    st.write("**권장 조치:**")
                    st.write("1. 월별 예산 수립")
                    st.write("2. 정기 회비 확보")
                    st.write("3. 지출 내역 정기 검토")
                else:
                    st.write("**유지 및 발전:**")
                    st.write("1. 현재 수준 유지")
                    st.write("2. 투자 기회 검토")
                    st.write("3. 팀 발전 계획 수립")

        except Exception as e:
            st.error(f"건전성 진단 중 오류가 발생했습니다: {e}")

    def render_finance_summary(self) -> None:
        """재정 요약 (대시보드용)"""
        try:
            financial_summary = self.finance_service.get_financial_summary()

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "현재 잔고",
                    financial_summary['balance_display'],
                    delta_color="normal" if financial_summary['is_positive'] else "inverse"
                )

            with col2:
                # 이번 달 수지
                current_month = datetime.now()
                monthly_stats = self.finance_service.calculate_monthly_stats(
                    current_month.year, current_month.month
                )
                st.metric("이번 달 수지", monthly_stats['balance_display'])

        except Exception as e:
            st.error(f"재정 요약을 불러오는 중 오류가 발생했습니다: {e}")

# 페이지 인스턴스
finance_page = FinancePage()