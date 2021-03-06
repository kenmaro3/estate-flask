from flask import Flask, render_template, request, send_from_directory, jsonify
from openpyxl import load_workbook
import os
import json
import datetime

app = Flask(__name__)

from apscheduler.schedulers.background import BackgroundScheduler
import test2
import handle_db
import handle_s3

from datetime import date



ku_list = ["minato", "shinagawa", "meguro", "shibuya", "shinjuku"]

ku_to_sc_code = dict(
    minato="13103",
    shinagawa="13109",
    shinjuku="13104",
    meguro="13110",
    shibuya="13113",
    )


cols_to_show_in_html = ['物件名', '最寄駅', '築年数', 'リンク', '坪単価']

how_many_scrape = 1
days_frequency = 1
sqlite_db = "sample.db"
s3_bucket = "estate-flask-sqlite-backup"

def price_parse(x):
    return '¥' +'{:,.0f}'.format(x)

def task_scrape():
    today = date.today()
    # dd/mm/YY
    d1 = today.strftime("%m_%d_%Y")
    for ku in ku_list:
        # url_base = f"https://suumo.jp/ms/chuko/tokyo/sc_{ku}/"
        url_base = f"https://suumo.jp/jj/bukken/ichiran/JJ012FC001/?ar=030&bs=011&sc={ku_to_sc_code[ku]}&ta=13&pc=30&po=1&pj=2"
        try:
            df = test2.scrape_url_all(url_base, num=how_many_scrape)
            table_name = f"flask_{ku}_{d1}"
            table_name_latest = f"flask_{ku}_latest"
            # table_name = "properties"
            handle_db.df_store_to_sqlite(df, table_name, sqlite_db)
            handle_db.df_store_to_sqlite(df, table_name_latest, sqlite_db)
            # handle_db.df_store_to_postgres(df, table_name)
            # handle_db.df_store_to_postgres(df, table_name_latest)
            log_str = f"okay scrape_url_all at {url_base}, {d1}\n"
            with open("log.txt", "a") as f:
                f.write(log_str)
        except:
            log_str = f"failed scrape_url_all at {url_base}, {d1}\n"
            with open("log.txt", "a") as f:
                f.write(log_str)
    
def task_upload():
    handle_s3.upload(sqlite_db, s3_bucket)

def task_download():
    if not os.path.exists(sqlite_db):
        print("will download data from s3")
        handle_s3.download(sqlite_db, s3_bucket)
        print("done downloading")
    else:
        print("database file does exists")


sched = BackgroundScheduler(daemon=True)
sched.add_job(task_scrape,'interval',days=days_frequency) 
sched.add_job(task_upload,'interval',days=days_frequency) 
sched.start()

task_download()


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        tables = handle_db.get_all_table_from_sqlite(sqlite_db)
        date_list = []
        for table in tables:
            tmp = table[0].split("_")
            if len(tmp) < 3:
                continue
            date_str = f"{tmp[-1]}/{tmp[-3]}/{tmp[-2]}"
            date_list.append(date_str)
        date_set = list(set(date_list))
        return render_template("index.html", dates=date_set)
    else:
        ku = request.form["target_ku"]
        if ku not in ku_list:
            return "cannot find ku"
        
        target_date = request.form["target_date"]
        tmp = target_date.split("/")
        target_date_parse = f"{tmp[1]}_{tmp[2]}_{tmp[0]}"
        table_name = f"flask_{ku}_{target_date_parse}"
        print(f"\ntable_here: {table_name}")
        try:
            df = handle_db.df_from_sqlite(table_name, sqlite_db)
        except:
            return "show failed"
        # file_name = f"{ku}_{target_date_parse}.xlsx"
        # df.to_excel(file_name)
        # return send_from_directory("./", file_name, as_attachment=True)

        print(df.columns)
        df_to_show = df[cols_to_show_in_html]
        df_to_show["坪単価"] = df_to_show["坪単価"].map(price_parse)
        df_values = df_to_show.values.tolist()
        df_columns = df_to_show.columns.tolist()


        return render_template("table.html", table_name=table_name, df_values=df_values, df_columns=df_columns)

@app.after_request
def after_request(response):
 response.headers.add('Access-Control-Allow-Origin', '*')
 response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
 response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
 return response

# @app.after_request
# def return_success(data):
#     return {
#         'statusCode': 200,
#         'headers': {
#             "Access-Control-Allow-Origin": "*",
#             "Access-Control-Allow-Methods": "POST,GET,PUT,DELETE,OPTIONS",
#             "Access-Control-Allow-Headers": "Content-Type"
#         },
#         'body': data
#     }

@app.route("/csv", methods=["POST"])
def csv_download():
    table_name = request.form["table_name"]
    try:
        df = handle_db.df_from_sqlite(table_name, sqlite_db)
    except:
        return "show failed"
    file_name = f"{table_name}.xlsx"
    df.to_excel(file_name)
    return send_from_directory("./", file_name, as_attachment=True)

@app.route("/tabledata", methods=["GET"])
def tabledata_download():
    ku = request.args.get("ku")
    try:
        table_name = f"flask_{ku}_latest"
        df = handle_db.df_from_sqlite(table_name, sqlite_db)
    except:
        today = datetime.datetime.now()
        target_month = today.month
        if target_month < 10:
            target_month = f"0{target_month}"
        else:
            target_month = f"{target_month}"

        target_day = today.day-1
        if target_day < 10:
            target_day = f"0{target_day}"
        else:
            target_day = f"{target_day}"
        
        table_name = f"flask_{ku}_{target_month}_{target_day}_{today.year}"
        df = handle_db.df_from_sqlite(table_name, sqlite_db)
        
    df.columns = handle_db.en_col
    tmp = df.iloc[:, :]
    res = tmp.to_json(orient="records")
    # return return_success(res)
    return jsonify(res)


        # try:
        #     return """
        #     {}は{}です！
        #     <form action="/" method="POST">
        #     <input name="num"></input>
        #     </form>""".format(str(request.form["num"]), ["偶数", "奇数"][int(request.form["num"]) % 2])
        # except:
        #     return """
        #             有効な数字ではありません！入力しなおしてください。
        #             <form action="/" method="POST">
        #             <input name="num"></input>
        #             </form>"""

@app.route("/update_db", methods=["GET"])
def update_db():
    task_download()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8888, threaded=True)
