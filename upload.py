from sqlalchemy import create_engine ,text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
mysql_engine = create_engine(DATABASE_URL,
                            pool_recycle=3600,
                            pool_pre_ping=True
                            )
Session = sessionmaker(bind=mysql_engine)

def daily_results(df):
    df['回報日期'] = pd.to_datetime(df['回報日期'], errors='coerce')
    df['已更新'] = pd.to_datetime(df['已更新'], errors='coerce')

    report_date = df['回報日期'].max()

    df = df.fillna('')
    # 各種統計
    fixed_keys = ['ema.hong', 'Szi', 'weiren.yang', 'yuwei.dee', 
        'frank.huang', 'jiaying.cai', 'robin.wen', 
        'david.chen', 'jian.du']
    people_results = {person: {} for person in fixed_keys}

    # 新問題
    new_issues = df[(df['狀態'] == '已分配') & (df['回報日期'] == report_date)]['分配給'].value_counts().to_dict()
    # 今日完成
    done_tested = df[(df['狀態'] == '已測試') & (df['已更新'] == report_date)]
    done_tested_count = done_tested['回報人'].value_counts().to_dict()
    done_assigned = df[(df['狀態'] == '待測試') & (df['已更新'] == report_date)]
    done_assigned_count = done_assigned['分配給'].value_counts().to_dict()
    combined_done = {**done_tested_count, **done_assigned_count}
    # 累積未完成
    cumulative_unfinished = df[df['狀態'] == '已分配']['分配給'].value_counts().to_dict()
    # 重要未處理
    important_unprocessed = df[(df['狀態'] == '已分配') & (df['嚴重性'] == '重要')]['分配給'].value_counts().to_dict()
    # 外部未處理
    external_unprocessed = df[(df['狀態'] == '已分配') & (df['類別'] == 'HAPCS疾管署_愛滋追管系統')]['分配給'].value_counts().to_dict()
    
    daily_results = {
        '新問題': new_issues,
        '今日完成': combined_done,
        '累積未完成': cumulative_unfinished,
        '重要未處理': important_unprocessed,
        '外部未處理': external_unprocessed
    }
    # 統計分類
    all_categories = list(daily_results.keys())
    # 補零
    for person in fixed_keys:
        for cat in all_categories:
            people_results[person][cat] = 0
    # 寫入統計
    for cat, data in daily_results.items():
        for person, count in data.items():
            if person in people_results:
                people_results[person][cat] = count
    # 合計
    #people_results['合計'] = {}
    #total_count = [sum(i.values()) for i in daily_results.values()]
    #for i,key in  enumerate(daily_results.keys()):
        #people_results['合計'][key] = total_count[i]
    # 待測試
    under_test = df['狀態'] == '待測試'
    under_test = int(under_test.sum())
    people_results['待測試'] = {'新問題':under_test}
    return people_results

def insert_original_data(data_dict,logger):
        start_time = datetime.now()
        sql = text("""INSERT INTO `original_data`
                (`case_no`, `project`, `reporter`, `receiver`,
                `priority`, `severity`, `frequency`, `version`,
                `category`, `report_date`, `os`, `os_version`,
                `platform_category`, `is_public`, `update_date`,
                `status`, `analysis`, `fixed_version`)
        VALUES (:case_no, :project, :reporter, :receiver, :priority, :severity, :frequency,
                :version, :category, :report_date, :os, :os_version, :platform_category, :is_public,
                :update_date, :status, :analysis, :fixed_version)
                ON DUPLICATE KEY UPDATE
                project = VALUES(project),
                reporter = VALUES(reporter),
                receiver = VALUES(receiver),
                priority = VALUES(priority),
                severity = VALUES(severity),
                frequency = VALUES(frequency),
                version = VALUES(version),
                category = VALUES(category),
                report_date = VALUES(report_date),
                os = VALUES(os),
                os_version = VALUES(os_version),
                platform_category = VALUES(platform_category),
                is_public = VALUES(is_public),
                update_date = VALUES(update_date),
                status = VALUES(status),
                analysis = VALUES(analysis),
                fixed_version = VALUES(fixed_version)
                """)
        
        session = Session()
        try:
            session.execute(sql, data_dict)  # 批次 insert
            session.commit()
            end_time = datetime.now()
            logger.info(f"成功插入 {len(data_dict)} 筆資料，耗時 {end_time - start_time}")
        except Exception as e:
            session.rollback()
            logger.error(f"批次插入失敗: {e}")
            raise
        finally:
            session.close()



def insert_daily_results_data(data):

    sql =text('''INSERT INTO `daily_results`
            (`employee`,
            `report_date`,
            `new_issues`,
            `combined_done`,
            `cumulative_unfinished`,
            `important_unprocessed`,
            `external_unprocessed`,
            `under_test`)
            VALUES {}
            ON DUPLICATE KEY UPDATE
            new_issues = VALUES(new_issues),
            combined_done = VALUES(combined_done),
            cumulative_unfinished = VALUES(cumulative_unfinished),
            important_unprocessed = VALUES(important_unprocessed),
            external_unprocessed = VALUES(external_unprocessed),
            under_test = VALUES(under_test)
        '''.format(str(tuple(data))).replace('nan','NULL'))
    
    session = Session()
    session.execute(sql)
    session.commit()

def async_insert_daily_results_data(day_results,date):
    for key,value in day_results.items():
        if key == '待測試':
            data = [key, date, 0, 0, 0, 0, 0, value['新問題']]
            print(data)
        else:
            data = [key, date] + list(value.values()) + [0]
            print(data)

        #tasks = [insert_daily_results_data(data)]
        #results = await asyncio.gather(*tasks)
    return

def async_insert_original_data(df,logger):
    rows = df.values
    #tasks = [insert_original_data(row,logger) for row in rows]
    #results = await asyncio.gather(*tasks)
    return

def upload(df,date,logger):
    df = df.drop(columns= "摘要") 
    df = df.replace(float('nan'), None) # 將 NaN 替換為 None
    #asyncio.run(async_insert_original_data(df,logger))
    rows = df.values
    original_data = [row.tolist() for row in rows]
    
    # list of list 轉換成 list of dict
    keys = ["case_no", "project", "reporter", "receiver",
            "priority", "severity", "frequency", "version",
            "category", "report_date", "os", "os_version",
            "platform_category", "is_public", "update_date",
            "status", "analysis", "fixed_version"]
    original_data_dict = [dict(zip(keys, row)) for row in original_data]
    insert_original_data(original_data_dict,logger)


    day_results = daily_results(df)
    #asyncio.run(async_insert_daily_results_data(day_results,date))
    for key,value in day_results.items():
        if key == '待測試':
            daily_data = [key, date, 0, 0, 0, 0, 0, value['新問題']]
            #print(daily_data)
        else:
            daily_data = [key, date] + list(value.values()) + [0]
            #print(daily_data)
        insert_daily_results_data(daily_data)
    return


#if __name__ == "__main__":
    #asyncio.run(main())