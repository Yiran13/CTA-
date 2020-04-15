# encoding: UTF-8

"""
导入CSV历史数据到vnpy默认数据库中
"""

from time import time
from datetime import datetime
import csv
from vnpy.trader.database.initialize import init_sql
import pandas as pd
from typing import TextIO
from vnpy.trader.object import BarData,TickData
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database.database import Driver
from vnpy.trader.database import database_manager

exchange_dict={"CFFEX":Exchange.CFFEX,
"SHFE" : Exchange.SHFE,# Shanghai Futures Exchange
"CZCE" :Exchange.CZCE, # Zhengzhou Commodity Exchange
 "DCE":Exchange.DCE,  # Dalian Commodity Exchange
 "INE":Exchange.INE,  # Shanghai International Energy Exchange
"SSE" :Exchange.SSE, # Shanghai Stock Exchange
"SZSE":Exchange.SZSE,  # Shenzhen Stock Exchange
"SGE" :Exchange.SGE,# Shanghai Gold Exchange
 "WXE" :Exchange.WXE,} # Wuxi Steel Exchange

interval_dict={"1m": Interval.MINUTE,'1d': Interval.DAILY}

settings={

    "database": "database.db",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "authentication_source": "admin"
}
sql_manager = init_sql(driver=Driver.SQLITE, settings=settings)


def move_df_to_sql(data_df:pd.DataFrame):
    bars = []
    start = None
    count = 0

    for row in data_df.itertuples():

        bar = BarData(
            symbol=row.symbol.upper(),
            exchange=exchange_dict[row.exchange],
            datetime=row.datetime,
            interval=interval_dict[row.interval],
            volume=float(row.volume),
            open_price=float(row.open),
            high_price=float(row.high),
            low_price=float(row.low),
            close_price=float(row.close),
            open_interest=float(row.open_interest),
            gateway_name="DB",
        )


        bars.append(bar)

        # do some statistics
        count += 1
        if not start:
            start = bar.datetime
    end = bar.datetime

    # insert into database
    sql_manager.save_bar_data(bars)
    print(f'插入{count} 根bar 从 {start} 到 {end}')


if __name__ == '__main__' :
    bar_data_df = pd.read_csv('C:/Users/lenovo/Desktop/test/IF_bar_data.csv')
    bar_data_df_if = bar_data_df.loc[(bar_data_df['symbol'] == 'IF88') & (bar_data_df['interval'] == '1m')]
    move_df_to_sql(bar_data_df_if)