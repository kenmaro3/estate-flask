import sqlite3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

convert_jp_to_en = dict(
)

en_col = [
    "category",
    "name",
    "price",
    "address",
    "ku",
    "line",
    "nearest_station",
    "walk",
    "bus",
    "land_area",
    "building_area",
    "balcony",
    "structure",
    "year",
    "management_fee",
    "accumulate_fee",
    "accumulate_fee2",
    "stairs",
    "facing",
    "reform",
    "land_right",
    "parking",
    "completion",
    "link",
    "land_area_tsubo",
    "building_area_tsubo",
    "tsubo_tanka",
]

def get_all_table_from_sqlite(db_name):
    conn = sqlite3.connect(db_name) 
    cursorObj = conn.cursor()
    cursorObj.execute('SELECT name from sqlite_master where type= "table"')
    return cursorObj.fetchall()


def df_from_sqlite(table_name, db_name):
    conn = sqlite3.connect(db_name) 
    df_sel = pd.read_sql_query(sql=f"SELECT * FROM {table_name}", con=conn)
    return df_sel

def df_store_to_sqlite(df, table_name, db_name):
    conn = sqlite3.connect(db_name) 
    df.to_sql(table_name, conn, if_exists='append', index=None)

def df_store_to_postgres(df, table_name):
    df.columns = en_col
    # データベースの接続情報
    connection_config = {
        'user': 'postgres',
        'password': 'password',
        'host': 'localhost',
        'port': '5432', # なくてもOK
        'database': 'test'
    }

    engine = create_engine('postgresql://{user}:{password}@{host}:{port}/{database}'.format(**connection_config))

    # PostgreSQLに接続する
    conn = psycopg2.connect(**connection_config)

    df.to_sql(table_name, con=engine, if_exists='append', index=None)

if __name__ == "__main__":
    df = pd.read_excel("../property_minato.xlsx", engine="openpyxl")
    print("\n\n=============")
    print(df.columns)
    print(len(df))
    df = df.dropna(how="any")
    df.columns = en_col
    print(df.columns)

    # db_name = u'sample.db'
    # conn = sqlite3.connect(db_name) 
    # cursor = conn.cursor()

    # データベースの接続情報
    connection_config = {
        'user': 'postgres',
        'password': 'password',
        'host': 'localhost',
        'port': '5432', # なくてもOK
        'database': 'test'
    }

    engine = create_engine('postgresql://{user}:{password}@{host}:{port}/{database}'.format(**connection_config))

    # PostgreSQLに接続する
    conn = psycopg2.connect(**connection_config)

    df.to_sql(u"test_minato", con=engine, if_exists='append', index=None)

    df_sel = pd.read_sql_query(sql=u"SELECT * FROM test_minato;", con=conn)
    print("\n\n===================")
    print(df_sel.tail(3))