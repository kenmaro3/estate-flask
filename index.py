from flask import Flask, render_template, request, send_from_directory
from openpyxl import load_workbook

app = Flask(__name__)

from apscheduler.schedulers.background import BackgroundScheduler
import test2
import handle_db

ku_list = ["minato", "shinagawa", "meguro", "shibuya"]

def task():
    for ku in ku_list:
        url_base = f"https://suumo.jp/ms/chuko/tokyo/sc_{ku}/" 
        df = test2.scrape_url_all(url_base)
        handle_db.df_store_to_sqlite(df, f"flask_{ku}")


sched = BackgroundScheduler(daemon=True)
sched.add_job(task,'interval',days=1) 
sched.start()

task()


@app.route("/", methods=["GET", "POST"])
def odd_even():
    if request.method == "GET":
        return render_template("index.html")
    else:
        ku = request.form["target"]
        if ku not in ku_list:
            return "cannot find ku"
        table_name = f"flask_{ku}"
        try:
            df = handle_db.df_from_sqlite(table_name)
        except:
            return "show failed"
        file_name = f"{ku}.xlsx"
        df.to_excel(file_name)
        return send_from_directory("./", file_name, as_attachment=True)



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


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8888, threaded=True)
