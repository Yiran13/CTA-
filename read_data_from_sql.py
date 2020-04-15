import sqlite3 as db
import pandas as pd
import numpy as np
# 从SQLite文件中读取数据


def readFronSqllite(db_path, exectCmd):
    # 该 API 打开一个到 SQLite 数据库文件 database 的链接，如果数据库成功打开，则返回一个连接对象
    conn = db.connect(db_path)
    cursor = conn.cursor()        # 该例程创建一个 cursor，将在 Python 数据库编程中用到。
    conn.row_factory = db.Row     # 可访问列信息
    cursor.execute(exectCmd)  # 该例程执行一个 SQL 语句
    rows = cursor.fetchall()  # 该例程获取查询结果集中所有（剩余）的行，返回一个列表。当没有可用的行时，则返回一个空的列表。
    return rows

    # print(rows[0][2]) # 选择某一列数据
db_path = 'C:/Users/lenovo/Desktop/test/database.db'
output_path = 'C:/Users/lenovo/Desktop/test/IF_bar_data.csv'
rows = readFronSqllite(db_path, "select * from dbbardata")
datetime_array = []
vol_array = []
oi_array = []
open_array = []
high_array = []
low_array = []
close_array = []
contract_array = []
market_array = []
interval_array = []
for row in rows:
    _, contract, market, datetime, interval, vol, oi, open, high, low, close = row
    vol_array.append(vol)
    oi_array.append(oi)
    datetime_array.append(datetime)
    open_array.append(open)
    high_array.append(high)
    low_array.append(low)
    close_array.append(close)
    contract_array.append(contract)
    market_array.append(market)
    interval_array.append(interval)

bar_data_df = pd.DataFrame({'datetime': datetime_array,
                            'volume': vol_array,
                            'open_interest': oi_array,
                            'open': open_array,
                            'high': high_array,
                            'low': low_array,
                            'close': close_array},
                           index=np.arange(len(vol_array)))
bar_data_df['symbol'] = contract_array
bar_data_df['exchange'] = market_array
bar_data_df['interval'] = interval_array

bar_data_df.to_csv(output_path, index=False)
