import pandas as pd
from typing import List, Union, Dict, Callable, Any
from datetime import date, datetime
import time

from ..core.interfaces import DataProvider
from ..core.models import Bar, Tick, TradeCalendar, Adjustment, Fundamental
from ..config import settings

# XtQuant is a proprietary library. 
# We'll use a stub or wrapper assuming 'xtquant' package is installed.
try:
    from xtquant import xtdata
except ImportError:
    xtdata = None

class XtProvider(DataProvider):
    def __init__(self):
        if xtdata is None:
            print("Warning: xtquant not installed. Real-time features disabled.")
        
        # Initialize connection if needed
        # xtdata usually connects to a local running XtQuant client
        pass

    def get_history(self, symbol: str, start: Union[date, datetime], end: Union[date, datetime], frequency: str = "1d") -> pd.DataFrame:
        if xtdata is None:
            return pd.DataFrame()
            
        # XtQuant uses '1d', '1m', etc.
        period = frequency
        # Download first ensures local cache is updated
        xtdata.download_history_data(symbol, period, start.strftime('%Y%m%d'), end.strftime('%Y%m%d'))
        
        # Read from local
        data = xtdata.get_market_data(
            field_list=['time', 'open', 'high', 'low', 'close', 'volume', 'amount'],
            stock_list=[symbol],
            period=period,
            start_time=start.strftime('%Y%m%d'),
            end_time=end.strftime('%Y%m%d')
        )
        
        # Convert to DataFrame
        # data structure depends on xtdata version, assuming dict of arrays or similar
        # Need to parse correctly.
        # Simplified:
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data[symbol])
        df['dt'] = pd.to_datetime(df['time'], unit='ms') # Check unit
        df['symbol'] = symbol
        return df

    def get_snapshot(self, symbols: List[str]) -> Dict[str, Tick]:
        if xtdata is None:
            return {}
            
        snapshots = xtdata.get_full_tick(symbols)
        ticks = {}
        for sym, data in snapshots.items():
            ticks[sym] = Tick(
                symbol=sym,
                dt=datetime.fromtimestamp(data['time'] / 1000),
                price=data['lastPrice'],
                volume=data['volume'],
                amount=data['amount'],
                bid_price=data['bidPrice'],
                bid_volume=data['bidVol'],
                ask_price=data['askPrice'],
                ask_volume=data['askVol']
            )
        return ticks

    def subscribe(self, symbols: List[str], callback: Callable[[Tick], None]):
        if xtdata is None:
            return

        def on_data(datas):
            for stock_code, data in datas.items():
                tick = Tick(
                    symbol=stock_code,
                    dt=datetime.fromtimestamp(data['time'] / 1000),
                    price=data['lastPrice'],
                    volume=data['volume'],
                    amount=data['amount'],
                    bid_price=data['bidPrice'],
                    bid_volume=data['bidVol'],
                    ask_price=data['askPrice'],
                    ask_volume=data['askVol']
                )
                callback(tick)

        # XtQuant subscription
        xtdata.subscribe_quote(stock_code=symbols, period='tick', start_time='', end_time='', count=0, callback=on_data)

    def get_calendar(self, exchange: str, start: Union[date, datetime], end: Union[date, datetime]) -> List[TradeCalendar]:
        # Implementation via xtdata
        pass

    def get_adjustments(self, symbol: str, start: Union[date, datetime], end: Union[date, datetime]) -> List[Adjustment]:
        # Implementation via xtdata
        pass

    def get_fundamentals(self, symbol: str, date: Union[date, datetime]) -> List[Fundamental]:
        # Implementation via xtdata
        pass
