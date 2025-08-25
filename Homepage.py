import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import upload
import select_sql



st.title("QA Report")

with st.sidebar:
    selected = option_menu("選單", ["首頁", "上傳CSV", "每日統計查詢", "每月統計圖表"])
#首頁
if selected == "首頁":
    st.subheader('首頁')


#上傳CSV
if selected == "上傳CSV":
    st.subheader('上傳CSV')
    date = st.date_input("請選擇日期",datetime.now())
    file = st.file_uploader("上傳CSV", ['.csv'])
    if file:
        df = pd.read_csv(file)
        if df.columns.tolist() != ['編號', '專案', '回報人', '分配給', '優先權', 
                                       '嚴重性', '出現頻率', '產品版本', '類別', '回報日期', 
                                       '作業系統', '作業系統版本', '平台類型', '檢視狀態', 
                                       '已更新', '摘要', '狀態', '問題分析', '已修正版本']:
            st.warning("CSV 檔案格式不正確，請確認欄位名稱")
            st.stop()
        if st.button("開始上傳",width=200):
            date = str(date)
            
            with st.spinner("正在處理中，請稍候..."):
                upload.upload(df,date)
                st.success("處理完成！")



#每日統計查詢
if selected == "每日統計查詢":
    st.subheader('每日統計查詢')
    col1, col2 = st.columns(spec=[0.7, 0.3], vertical_alignment='bottom')
    with col1:
        date = st.date_input("請選擇日期",datetime.now())
    with col2:
        query = st.button("查詢")

    if query:
        daily_results = select_sql.search_daily_results(date)
        if daily_results is None:
            st.warning("查無資料，請確認日期是否正確或是否已上傳當日資料")
            st.stop()
        under_test = daily_results[daily_results['員工'] == '待測試']['待測試'].values[0]
        daily_results = daily_results[daily_results['員工'] != '待測試']
        options = daily_results.columns.tolist()
        if '員工' in options:
            options.remove('員工')
        if '待測試' in options:
            options.remove('待測試')
    
        fig = go.Figure()

        for col in options:
            fig.add_trace(go.Bar(
                x=daily_results['員工'],
                y=daily_results[col],
                name=col
            ))

        fig.update_layout(
            barmode='group',  # 群組顯示
            xaxis_title="員工",
            yaxis_title="數量",
            title=f"{date} 統計結果",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(daily_results.set_index('員工')[options])
        st.markdown(f"待測試: {under_test}")
        #st.bar_chart(daily_results.set_index('員工')[selected_columns], height=400)


#每月統計圖表
if selected == "每月統計圖表":
    st.subheader('每月統計圖表')

    col1, col2, col3 = st.columns([2,2,1],vertical_alignment='bottom')
    with col1:
        # 年份選擇
        years = list(range(2020, datetime.now().year + 1))
        selected_year = st.selectbox("選擇年份", years, index=len(years)-1)

    with col2:
        # 月份選擇
        months = list(range(1, 13))
        selected_month = st.selectbox("選擇月份", months, index=datetime.now().month-1)

    with col3:
        # 按鈕
        query = st.button("查詢")
    
    st.write(f"你選擇的月份：{selected_year}-{selected_month:02d}")

    if query:
        employee_list = select_sql.search_employee_list()
        monthly_results = select_sql.search_monthly_results(selected_year, selected_month)
        if monthly_results is None:
            st.warning("查無資料，請確認日期是否正確或是否已上傳當月資料")
            st.stop()
