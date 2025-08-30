import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import altair as alt
import upload
import select_sql



def chart_as_datatype_container(df,cat,color):
        
            with st.container(border=1 ,height=500,):
                title = f'<h3 style="color:{color}; padding: 0;">{cat} <span style="color:white">統計圖表</span></h3>'
                st.markdown(title, unsafe_allow_html=True)
                st.markdown('''<style>
                            .stVerticalBlock{
                            overflow: hidden;
                            }</style>''', 
                            unsafe_allow_html=True) # 調整CSS隱藏scroll bar
                
                fig = go.Figure()

                totals = []
                #totals_text = []
                for date in df['回報日期'].unique():
                    total = df[df['回報日期'] == date][cat].sum()
                    totals.append(total)
                                                                           
                # 只顯示月日
                x_labels = [pd.to_datetime(date).strftime('%m-%d') for date in df['回報日期'].unique()]

                #print(x_labels)
                fig.add_trace(go.Bar(x=x_labels, 
                                    y=totals, 
                                    name=cat,
                                    showlegend=False,
                                    marker_color=color,
                                    
                                    ))
                fig.add_trace(go.Scatter(x=x_labels, 
                                        y=(totals), 
                                        mode="text",
                                        text=totals,
                                        textposition="top center",
                                        showlegend=False,
                                        ))
                #fig.update_layout(barmode="stack")
                fig.update_xaxes(type="category")
                st.plotly_chart(fig, use_container_width=True)

def chart_as_employee_container(df, employee):
    df = df[df['員工'] == employee]
    df = df.drop(columns=['員工'])
    # 轉換成長格式
    df_melt = df.melt(id_vars=["回報日期"], var_name="類別", value_name="數量")
    selection = alt.selection_point(fields=["類別"], bind="legend")

    #print(df)
    with st.container(border=1 ,height=300):
        st.write(employee + ' 統計圖表')
        chart = alt.Chart(df_melt).mark_line(point=True).encode(
            x='monthdate(回報日期):O',  
            y=alt.Y("數量:Q", axis=alt.Axis(format="d", tickMinStep=1)), 
            color='類別:N', 
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
        chart_as_employee_container(df, employee_list[num1])
    with col2:
        try:
            chart_as_employee_container(df, employee_list[num2])
        except IndexError:
            return

st.set_page_config(page_title="QA Report", layout="wide" )

with st.sidebar:
    selected = option_menu("選單", ["QA統計圖表", "歷史統計查詢", "上傳CSV", "原始資料查詢與匯出"])

#首頁  QA統計圖表
if selected == "QA統計圖表":
    st.markdown('## QA統計圖表')
    
    #依類別分類的內容---------------------------------------------
    df_30 = select_sql.search_last30days_result()
    employee_list = select_sql.search_employee_list()
    category_df = pd.DataFrame(columns=['category','color'])
    category_df['category'] = ['今日完成', '累積未完成', '新問題', '重要未處理', '外部未處理']
    category_df['color'] = ['#83c9ff','#ffabab','#ff2b2b','#7defa1','#0066cc']
    #print(category_df)
    col1, col2 = st.columns([1,1])
    try:
        with col1:
            chart_as_datatype_container(df_30,category_df['category'][0],category_df['color'][0])
        with col2:
            chart_as_datatype_container(df_30,category_df['category'][1],category_df['color'][1])

    except IndexError:
        pass
    col1, col2, col3 = st.columns([1,1,1])
    try:
        with col1:
            chart_as_datatype_container(df_30,category_df['category'][2],category_df['color'][2])
        with col2:
            chart_as_datatype_container(df_30,category_df['category'][3],category_df['color'][3])
        with col3:
            chart_as_datatype_container(df_30,category_df['category'][4],category_df['color'][4])
    except IndexError:
        pass
    
    
    

    

    # 這是依員工分類的內容---------------------------------------------
    for i in range(0,len(employee_list),2):
        set_2columns(df_30,i,i+1)


#歷史統計查詢
if selected == "歷史統計查詢":
    st.subheader('歷史統計查詢')
    tab1, tab2 = st.tabs(["單日統計", "區間統計(不可超過3個月)"])
    with tab1:

        col1, col2 = st.columns(spec=[0.7, 0.3], vertical_alignment='bottom')
        with col1:
            daily_date = st.date_input("請選擇日期",datetime.now(), key='daily_date')
        with col2:
            query = st.button("查詢")

        if query:
            daily_results = select_sql.search_daily_results(daily_date)
            if daily_results is None:
                st.warning("查無資料，請確認日期是否正確或是否已上傳當日資料",icon="⚠️")
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
            daily_results = daily_results.set_index('員工')[options]
            daily_results.loc['合計'] = daily_results.sum(axis=0)
            st.dataframe(daily_results)
            st.markdown(f"待測試: {under_test}")
            #st.bar_chart(daily_results.set_index('員工')[selected_columns], height=400)

    with tab2:
        employee_list = select_sql.search_employee_list()
        col1, col2, col3, col4, col5 = st.columns(spec=[5,1,5,5,5], vertical_alignment='bottom')
        with col1:
            start_date = st.date_input("開始日期",datetime.now(), key='start_date')
        with col2:
            st.markdown('### ～')
        with col3:
            end_date = st.date_input("結束日期",datetime.now(), key='end_date')
        with col4:
            select_employee = st.selectbox(label='員工',label_visibility='hidden',key='select_employee' ,options=employee_list)
        with col5:
            query_range = st.button("查詢",key='query_range')
        if query_range and start_date > end_date:
            st.warning("結束日期需大於或等於開始日期",icon="⚠️")
            st.stop()
        elif query_range and end_date - start_date > pd.Timedelta(days=92):
            st.warning("區間不可超過3個月",icon="⚠️")
            st.stop()
        if query_range:

            range_df = select_sql.search_range_results(start_date,end_date)
            if range_df is None:
                st.warning("查無資料，請確認日期是否正確或是否已上傳當日資料",icon="⚠️")
                st.stop()
            
            under_test = range_df[range_df['員工'] == '待測試']['待測試'].to_list() # 待測試
            #range_df = range_df[range_df['員工'] != '待測試']
            range_df = range_df.drop(columns=['待測試'])
            select_date = range_df['回報日期'].unique().tolist() 

            if select_employee:
                employee = select_employee
                range_df = range_df[range_df['員工'] == employee]
                range_df = range_df.drop(columns=['員工']) 
                df_melt = range_df.melt(id_vars=["回報日期"], var_name="類別", value_name="數量")
                selection = alt.selection_point(fields=["類別"], bind="legend")
            
                chart = alt.Chart(df_melt).mark_line(point=True).encode(
                        x='monthdate(回報日期):O',  
                        y=alt.Y("數量:Q", axis=alt.Axis(format="d", tickMinStep=1)), 
                        color='類別:N', 
                        tooltip=["回報日期:T", "類別:N", "數量:Q"],
                        opacity=alt.condition(selection, alt.value(1), alt.value(0))  # 未選取時隱藏
                        ).transform_filter(
                        selection  # 只保留選到的類別
                        ).add_params(
                        selection
                        ).properties(height=500)

                st.altair_chart(chart, use_container_width=True)
            

#上傳CSV
if selected == "上傳CSV":
    st.subheader('上傳CSV')
    upload_date = st.date_input("請選擇日期",datetime.now(),key='upload_date')
    file = st.file_uploader("上傳CSV", ['.csv'])
    if file:
        df = pd.read_csv(file)

        expected_cols = ['編號', '專案', '回報人', '分配給', '優先權', 
                        '嚴重性', '出現頻率', '產品版本', '類別', '回報日期', 
                        '作業系統', '作業系統版本', '平台類型', '檢視狀態', 
                        '已更新', '摘要', '狀態', '問題分析', '已修正版本']
        df.columns = df.columns.str.strip()   # 去掉前後空白
        df = df.dropna(axis=0, how='all')     # 移除完全空白的列

        if expected_cols in df.columns.tolist():
            st.warning("CSV 檔案格式不正確，請確認欄位名稱",icon="⚠️")
            st.stop()
        if st.button("開始上傳",width=200):
            upload_date = str(upload_date)
            
            with st.spinner("正在處理中，請稍候..."):
                upload.upload(df,upload_date)
                st.success("處理完成！")







#原始資料查詢
if selected == "原始資料查詢與匯出":
    st.subheader('原始資料查詢與匯出')
    
    
        
    original_df = select_sql.export_original_data()
    download_button = st.download_button(label='匯出CSV',data=original_df.to_csv(index=False).encode('utf-8-sig'),file_name='qa_report.csv',mime='text/csv')
    if original_df is None:
        st.warning("查無資料，請確認是否已上傳資料",icon="⚠️")
        st.stop()
    #st.success("已下載",icon="✅")
        

    
    