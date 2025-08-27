import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import altair as alt
import upload
import select_sql


def mainpage_container(df, employee):
    df = df[df['員工'] == employee]
    df = df.drop(columns=['員工'])
    # 轉換成長格式
    df_melt = df.melt(id_vars=["回報日期"], var_name="類別", value_name="數量")
    selection = alt.selection_point(fields=["類別"], bind="legend")

    #print(df)
    with st.container(border=1 ,height=300):
        st.write(employee + ' 統計圖表')
        chart = alt.Chart(df_melt).mark_line(point=True).encode(
            x='monthdate(回報日期):O',  # Time data type for the x-axis
            y=alt.Y("數量:Q", axis=alt.Axis(format="d", tickMinStep=1)), # Quantitative data type for the y-axis
            color='類別:N', # Nominal data type for coloring by category
            tooltip=["回報日期:T", "類別:N", "數量:Q"],
            opacity=alt.condition(selection, alt.value(1), alt.value(0))  # 未選取時隱藏
            ).transform_filter(
            selection  # 只保留選到的類別
            ).add_params(
            selection
            ).properties(height=215)

        st.altair_chart(chart, use_container_width=True)

def set_2columns(df,num1,num2):
    col1, col2 = st.columns([1,1])
    with col1:
        mainpage_container(df, employee_list[num1])
    with col2:
        try:
            mainpage_container(df, employee_list[num2])
        except IndexError:
            return

st.set_page_config(page_title="QA Report", layout="wide")

with st.sidebar:
    selected = option_menu("選單", ["首頁", "上傳CSV", "每日統計查詢", "每月統計圖表"])
#首頁
if selected == "首頁":
    st.subheader('首頁')
    
    tab1,tab2 = st.tabs(['依員工分類','依資料類別分類'])

    with tab1:
        df_30 = select_sql.search_last30days_result()
        employee_list = select_sql.search_employee_list()
        for i in range(0,len(employee_list),2):
            set_2columns(df_30,i,i+1)

    with tab2:
        st.write("這是依資料類別分類的內容")

        if st.button("查詢"):
            st.dataframe(select_sql.search_last30days_result())


#上傳CSV
if selected == "上傳CSV":
    st.subheader('上傳CSV')
    upload_date = st.date_input("請選擇日期",datetime.now(),key='upload_date')
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
            upload_date = str(upload_date)
            
            with st.spinner("正在處理中，請稍候..."):
                upload.upload(df,upload_date)
                st.success("處理完成！")



#每日統計查詢
if selected == "每日統計查詢":
    st.subheader('每日統計查詢')
    col1, col2 = st.columns(spec=[0.7, 0.3], vertical_alignment='bottom')
    with col1:
        daily_date = st.date_input("請選擇日期",datetime.now(), key='daily_date')
    with col2:
        query = st.button("查詢")

    if query:
        daily_results = select_sql.search_daily_results(daily_date)
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
            title=f"{daily_date} 統計結果",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(daily_results.set_index('員工')[options])
        st.markdown(f"待測試: {under_test}")
        #st.bar_chart(daily_results.set_index('員工')[selected_columns], height=400)


#每月統計圖表
if selected == "每月統計圖表":
    st.subheader('每月統計圖表')

    
    