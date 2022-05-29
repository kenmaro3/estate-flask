# -*- coding: utf-8 -*-
import urllib.request
from bs4 import BeautifulSoup
import pandas as pd

# 中古一戸建てと中古マンションのurl
#url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=021&ta=14"  \
#            "&jspIdFlg=patternShikugun&sc=14101&sc=14102&sc=14103&sc=14104&sc=14105&sc=14106"  \
#            "&sc=14107&sc=14108&sc=14109&sc=14110&sc=14111&sc=14112&sc=14113&sc=14114"  \
#            "&sc=14115&sc=14116&sc=14117&sc=14118&kb=1&kt=9999999&tb=0&tt=9999999&hb=0"  \
#            "&ht=9999999&ekTjCd=&ekTjNm=&tj=0&cnb=0&cn=9999999&srch_navi=1&pn={}",
#
#            "https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=14" \
#            "&jspIdFlg=patternShikugun&sc=14101&sc=14102&sc=14103&sc=14104&sc=14105&sc=14106" \
#            "&sc=14107&sc=14108&sc=14109&sc=14110&sc=14111&sc=14112&sc=14113&sc=14114" \
#            "&sc=14115&sc=14116&sc=14117&sc=14118&kb=1&kt=9999999&mb=0&mt=9999999" \
#            "&ekTjCd=&ekTjNm=&tj=0&cnb=0&cn=9999999&srch_navi=1&pn={}"]

url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=13&jspIdFlg=patternShikugun&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&sc=13109&sc=13110&sc=13111&sc=13112&sc=13116&kb=1&kt=9999999&mb=60&mt=9999999&md=2&md=3&md=4&ekTjCd=&ekTjNm=&tj=0&et=10&cnb=0&cn=9999999&srch_navi=1"]

# 収集するデータのカラム
cols = ["カテゴリ", "物件名", "販売価格", "所在地", "区", "沿線", "最寄駅", "徒歩（分）", "バス（分）",
        "土地面積", "建物面積", "バルコニー", "間取り", "築年数"]

def identify_floor_plan(floor_plan):
    # 間取りの種類が多すぎるのでまとめる
    if floor_plan.find("ワンルーム") > -1:
        floor_plan = "1K"
    if floor_plan.find("+") > -1:
        floor_plan = floor_plan[:floor_plan.find("+")]
    if floor_plan.find("LK") > -1:
        floor_plan = floor_plan[0:1] + "LDK"
    if floor_plan.find("LL") > -1 or \
       floor_plan.find("DD") > -1 or \
       floor_plan.find("KK") > -1:
        floor_plan = floor_plan = floor_plan[0:1] + "LDK"

    return floor_plan

def convert_price(price):
    # 万円※権利金含むの処理
    if price.find("※") > -1:
        price = price[:price.find("※") ]

    # ○○万円～○○万円の処理
    if price.find("～") > -1:
        price = price[price.find("～") + 1: ]

        if price.find("億") > -1:
            # 1億円ジャストのような場合の処理
            if price.find("万") == -1:
                price = int(price[:price.find("億")]) * 100000000
            else:
                oku = int(price[:price.find("億")]) * 100000000
                price = oku + int(price[price.find("億") + 1:-2]) * 10000
        else:
            price = int(price[:price.find("万円")]) * 10000
    else:
        if price.find("億") > -1:
            # 1億円ジャストのような場合の処理
            if price.find("万") == -1:
                price = int(price[:price.find("億")]) * 100000000
            else:
                oku = int(price[:price.find("億")]) * 100000000
                price = oku + int(price[price.find("億") + 1:-2]) * 10000
        else:
            if price.find("万") == -1:
                price = int(price)
            else:
                price = int(price[:price.find("万")]) * 10000

    return price

def remove_brackets(data):
    # ○○～○○の処理
    if data.find("～") > -1:
        data = data[data.find("～") + 1:]

    # m2以降を除去
    if data.find("m2") > -1:
        data = data[:data.find("m")]

    # （）を除去
    if data.find("（") > -1:
        data = data[:data.find("（")]

    return data

def get_line_station(line_station):

    # ＪＲをJRに変換
    if line_station.find("ＪＲ") > -1:
        line_station = line_station.replace("ＪＲ", "JR")

    # バスと徒歩の時間を取得
    if line_station.find("バス") > -1:
        bus_time = line_station[line_station.find("バス") + 2 : line_station.find("分")]

        # バスの場合は徒歩時間＝(バス時間×10) + バス停までの徒歩時間とする
        walk_time = line_station[line_station.find("停歩") + 2 : line_station.rfind("分")]

    else:
        bus_time = 0
        walk_time = line_station[line_station.find("徒歩") + 2 : line_station.rfind("分")]

    # 沿線と駅を取得
    line = line_station[ : line_station.find("「") ]

    if line.find("湘南新宿ライン高海") > -1 or \
       line.find("湘南新宿ライン宇須") > -1:
        line = "湘南新宿ライン"

    station = line_station[line_station.find("「") + 1 : line_station.find("」")]

    return line, station, bus_time, walk_time

def get_page_count(hit_count):

    # データ整形
    hit_count = hit_count.strip()
    hit_count = hit_count.replace(",", "")
    hit_count = hit_count.replace("件", "")

    # ページ数計算
    page_count = divmod(int(hit_count), 30)
    if page_count[1] == 0:
        page_count = page_count[0]
    else:
        page_count = page_count[0] + 1

    return page_count

def main():

    df = pd.DataFrame(index=[], columns=cols)
    df_ind = pd.DataFrame([], columns=cols)

    for i, url_base in enumerate(url_list):
        # 対象urlのデータを取得
        url = url_base.format(1)
        print(url)
        html = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(html)
        hit_count = soup.find("div", class_="pagination_set-hit").text

        # 各urlのページ数計算
        page_count = get_page_count(hit_count)

        data = {}
        for page_index, page in enumerate(range(1, page_count + 1)):

            # ページごとにリクエスト
            if page != 1:
                url = url_base.format(page)
                try:
                    html = urllib.request.urlopen(url).read()
                    print(f"{page_index}/{page_count} of {i}: okay")
                except:
                    print(f"{page_index}/{page_count} of {i}: failed")
                    continue
                soup = BeautifulSoup(html)

            for s in soup.findAll('div', 'dottable-line'):

                #if i == 0:
                #data["カテゴリ"] = "中古一戸建て"

                #else:
                data["カテゴリ"] = "中古マンション"

                if len(s.findAll('dt')) == 1:
                    if s.find('dt').text == "物件名":

                        name = s.findAll("dd")[0].text
                        data["物件名"] = name

                    elif s.find('dt').text == "販売価格":

                        # ○○万円を数字に変換
                        price = convert_price(s.find("span").text)
                        data["販売価格"] = price

                if len(s.findAll('dt')) == 2:

                    if s.findAll('dt')[0].text == "所在地":
                        area = s.findAll("dd")[0].text
                        data["所在地"] = area
                        data["区"] = area[area.find("市") + 1:area.find("区") + 1]

                    if s.findAll('dt')[1].text == "沿線・駅":

                        # データ加工
                        line, station, bus_time, \
                            walk_time = get_line_station(s.findAll("dd")[1].text)

                        data["沿線"] = line
                        data["最寄駅"] = station
                        data["徒歩（分）"] = walk_time
                        data["バス（分）"] = bus_time

                if s.find('table', class_ = 'dottable-fix') != None:
                    if s.findAll('dt')[0].text == "土地面積":

                        land_area = remove_brackets(s.findAll("dd")[0].text)
                        data["土地面積"] = land_area

                    if s.findAll('dt')[1].text == "間取り":

                        floor_plan = remove_brackets(s.findAll("dd")[1].text)

                        # 間取りをまとめる
                        floor_plan = identify_floor_plan(floor_plan)
                        data["間取り"] = floor_plan

                    if s.findAll('dt')[0].text == "建物面積":

                        house_area = remove_brackets(s.findAll("dd")[0].text)
                        data["建物面積"] = house_area

                    if s.findAll('dt')[0].text == "専有面積":

                        house_area = remove_brackets(s.findAll("dd")[0].text)
                        data["建物面積"] = house_area

                        # 中古マンションは建物面積＝土地面積とする
                        data["土地面積"] = house_area

                    if s.findAll('dt')[0].text == "バルコニー":

                        if s.findAll("dd")[0].text.find("-") > -1:
                            data["バルコニー"] = 0
                        else:
                            balcony_area = remove_brackets(s.findAll("dd")[0].text)
                            data["バルコニー"] = balcony_area

                    else: # 一戸建ての場合は0
                        data["バルコニー"] = 0

                    if s.findAll('dt')[1].text == "築年月":

                        # 築年数を算出
                        built_year = 2021 - int(s.findAll("dd")[1].text[:4])
                        data["築年数"] = built_year

                # データフレームに1物件ずつデータを格納
                if len(data) == 13:

                    df_ind = df_ind.append(data, ignore_index=True)
                    df = df.append(data, ignore_index=True)
                    data = {}

            if page_index == 0:
                break

            if page_index%1000==0:    
                df_ind.to_csv(f"df_ind/property_page_{page_index}.csv", index=False, encoding = "utf-8")
                df_ind = pd.DataFrame([], columns=cols)

    # CSV 出力
    df.to_csv(r"property.csv", index=False, encoding = "utf-8")

if __name__ == '__main__':
    main()
