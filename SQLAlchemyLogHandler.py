import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# 定義 SQLAlchemy 的基礎
Base = declarative_base()

# 定義日誌模型，對應 logs 資料表
class LogEntry(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    levelname = Column(String(50))
    message = Column(Text)

    def __repr__(self):
        return f"<LogEntry(levelname='{self.levelname}', message='{self.message}')>"

# 自定義 SQLAlchemy 日誌 Handler
class SQLAlchemyLogHandler(logging.Handler):
    def __init__(self, db_url):
        super().__init__()
        self.engine = create_engine(db_url,
                                pool_recycle=3600,
                                pool_pre_ping=True
                                )
        # 確保資料表存在，如果不存在則建立
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def emit(self, record):
        # 建立一個新的 Session
        session = self.Session()
        try:
            # 建立一個 LogEntry 物件
            log_entry = LogEntry(
                levelname=record.levelname,
                message=self.format(record)
            )
            # 將物件加入 Session
            session.add(log_entry)
            # 提交變更到資料庫
            session.commit()
        except Exception as e:
            # 處理可能發生的錯誤，例如連線中斷
            session.rollback()
        finally:
            # 確保 Session 被關閉
            session.close()