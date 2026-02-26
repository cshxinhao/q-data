from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import List, Optional
from datetime import date

from ..config import settings
from ..core.models import Contract, TradeCalendar, Exchange, SecurityType

Base = declarative_base()

class ContractModel(Base):
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, index=True)
    exchange = Column(String)
    sec_type = Column(String)
    name = Column(String)
    expiry = Column(Date, nullable=True)
    multiplier = Column(Float, default=1.0)
    
class CalendarModel(Base):
    __tablename__ = 'trade_calendar'
    
    id = Column(Integer, primary_key=True)
    exchange = Column(String, index=True)
    date = Column(Date, index=True)
    is_trading = Column(Boolean, default=True)
    
    __table_args__ = (UniqueConstraint('exchange', 'date', name='uq_exchange_date'),)

class MetadataStorage:
    def __init__(self, db_url=settings.METADATA_DB_URL):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_contracts(self, contracts: List[Contract]):
        session = self.Session()
        try:
            for c in contracts:
                # Upsert logic (simplified: check existence)
                existing = session.query(ContractModel).filter_by(symbol=c.symbol).first()
                if not existing:
                    new_c = ContractModel(
                        symbol=c.symbol,
                        exchange=c.exchange.value,
                        sec_type=c.sec_type.value,
                        name=c.name,
                        expiry=c.expiry,
                        multiplier=c.multiplier
                    )
                    session.add(new_c)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_contracts(self, exchange: Optional[Exchange] = None) -> List[Contract]:
        session = self.Session()
        query = session.query(ContractModel)
        if exchange:
            query = query.filter_by(exchange=exchange.value)
            
        results = query.all()
        contracts = [
            Contract(
                symbol=r.symbol,
                exchange=Exchange(r.exchange),
                sec_type=SecurityType(r.sec_type),
                name=r.name,
                expiry=r.expiry,
                multiplier=r.multiplier
            )
            for r in results
        ]
        session.close()
        return contracts

    def save_calendar(self, calendars: List[TradeCalendar]):
        session = self.Session()
        try:
            for cal in calendars:
                existing = session.query(CalendarModel).filter_by(
                    exchange=cal.exchange.value, 
                    date=cal.date
                ).first()
                
                if not existing:
                    new_cal = CalendarModel(
                        exchange=cal.exchange.value,
                        date=cal.date,
                        is_trading=cal.is_trading
                    )
                    session.add(new_cal)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
