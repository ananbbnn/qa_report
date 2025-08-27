from sqlalchemy import create_engine ,text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


def execute_sql(sql):
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    mysql_engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=mysql_engine)
    session = Session()
    result = session.execute(text(sql))
    session.commit()
    return result

def search_daily_results(date):
    sql = '''
        SELECT 
            `employee`,
            `new_issues`,
            `combined_done`,
            `cumulative_unfinished`,
            `important_unprocessed`,
            `external_unprocessed`,
            `under_test`
        FROM `qa_report`.`daily_results`
        WHERE DATE(`daily_results`.`report_date`) = '{date}'
    '''.format(date=date)
    result = execute_sql(sql)
    result = result.fetchall()
    if result == []:
        return
    df = pd.DataFrame(result)
    #print(f'result: {result}')
    df.columns = ['員工','新問題','今日完成','累積未完成','重要未處理','外部未處理','待測試']
    
    return df

def search_employee_list():
    sql = '''
        SELECT DISTINCT `employee`
        FROM `qa_report`.`daily_results`
    '''
    result = execute_sql(sql)
    result = result.fetchall()
    
    if result == []:
        return
    employee_list = [i[0] for i in result if i[0] != '待測試']
    #print(f'employee_list: {employee_list}')
    return employee_list

def search_last30days_result():
    sql = '''
        SELECT `report_date`, `employee`,
               `new_issues`, `combined_done`, `cumulative_unfinished`,
               `important_unprocessed`, `external_unprocessed`
        FROM `qa_report`.`daily_results`
        WHERE `report_date` >= (
            SELECT MAX(`report_date`) FROM `qa_report`.`daily_results`
        ) - INTERVAL 30 DAY
    '''
    result = execute_sql(sql)
    result = result.fetchall()
    if result == []:
        return
    df = pd.DataFrame(result)
    df.columns = ['回報日期', '員工', '新問題', '今日完成', '累積未完成', '重要未處理', '外部未處理']
    print(f'df: {df}')
    return df



#print(search_daily_results('2025-08-24'))