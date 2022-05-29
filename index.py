from flask import Flask, render_template, request, send_from_directory
from openpyxl import load_workbook

app = Flask(__name__)

import test2


@app.route("/", methods=["GET", "POST"])
def odd_even():
    if request.method == "GET":
        return render_template("index.html")
    else:
        url = request.form["target"]
        num = int(request.form["num"])
        # return url

        try:
            res = test2.scrape_url(url, "tmp", num)
            wb = load_workbook('tmp.xlsx')
            file_name = "tmp_save.xlsx"
            wb.save(file_name)
            return send_from_directory("./", file_name, as_attachment=True)
        except:
            return """
            パーサーにエラーが発生しました。有効かつサポートされているURLを再度入力してください。
            """


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
