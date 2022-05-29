import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import time

from test import *


cols_from_top = ["カテゴリ", "物件名", "販売価格", "所在地", "区", "沿線", "最寄駅", "徒歩（分）", "バス（分）",
        "土地面積", "建物面積", "バルコニー", "間取り", "築年数"]
cols_from_gaiyou = [
    "管理費",
    "修繕積立金",
    "修繕積立基金",
    "所在階",
    "向き",
    "リフォーム",
    "敷地の権利形態",
    "駐車場",
    "完成時期(築年月)",
    "リンク",
    "土地面積（坪）",
    "建物面積（坪）",
    "坪単価"
    ]
cols_total = cols_from_top + cols_from_gaiyou


def update_query(url, key, org_val, new_val):
    pr = urllib.parse.urlparse(url)
    d = urllib.parse.parse_qs(pr.query)
    l = d.get(key)
    if l:
        d[key] = [new_val if v == org_val else v for v in l]
    else:
        d[key] = new_val
    return urllib.parse.urlunparse(pr._replace(query=urllib.parse.urlencode(d, doseq=True)))

def get_info_original(container):
    data = {}

    for s in container.findAll('div', 'dottable-line'):

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
    return data

def get_info_from_detail_link(link_href, data):
    link_url_detail = f"https://suumo.jp{link_href}"
    data["リンク"] = link_url_detail

    try:
        html_detail = urllib.request.urlopen(link_url_detail).read()
    except:
        raise Exception("link_url_detail")
    soup_detail = BeautifulSoup(html_detail)

    tabs = soup_detail.find("ul", "cf tab")

    tab_el_lis = tabs.findAll("li")
    #tab_el_li_target = tab_el_lis.find("a")
    for el in tab_el_lis:
        #print(el)
        if el.find("a") is not None:
            if el.find("a").text == "物件概要":
                gaiyou_a = el.find("a")
                link_url_gaiyou = gaiyou_a.get("href")
    
    
    html_gaiyou = urllib.request.urlopen(link_url_gaiyou).read()
    soup_gaiyou = BeautifulSoup(html_gaiyou)
    tables = soup_gaiyou.findAll("table")
    for table in tables:
        if table.find("tbody") is None:
            continue
            
        tbody = table.find("tbody")
        for tr in tbody.findAll("tr"):
            for th, td in zip(tr.findAll("th"), tr.findAll("td")):
                th_div = th.find("div")
                if th_div is not None:
                    if(th_div.text in cols_from_gaiyou):
                        data[th_div.text] = td.text.strip()

    return data

def get_info_from_blocks_by_index(blocks, index_block, df):
    block = blocks[index_block]
    header = block.find("div", "property_unit-header")
    link_block = header.find("h2")
    link_a = link_block.find("a")
    link_href = link_a.get("href")
    #print(link_href)

    body = block.find("div", "property_unit-body")
    body_ui_media = body.find("div", "ui-media")
    body_ui_media_body = body_ui_media.find("div", "ui-media-body")

    data = get_info_original(body_ui_media_body)

    data = get_info_from_detail_link(link_href, data)


    data["土地面積（坪）"] = float(data["土地面積"])/0.306
    data["建物面積（坪）"] = float(data["建物面積"])/0.306
    data["坪単価"] = float(data["販売価格"])/data["土地面積（坪）"]

    df = df.append(data, ignore_index=True)

    return df


def scrape_url(url, name, num):
    assert num > 0
    assert num <= 100

    df = pd.DataFrame(index=[], columns=cols_total)

    url_base = url

    page = 0
    url = url_base.format(page)
    try:
        html = urllib.request.urlopen(url).read()
    except:
        raise Exception("url")
    soup = BeautifulSoup(html)
    hit_count = soup.find("div", class_="pagination_set-hit").text

    # 各urlのページ数計算
    page_count = get_page_count(hit_count)

    data = {}
    for page_index, page in enumerate(range(1, page_count + 1)):
        print(f"\n\n=================={page_index}/{page_count}")
    # for page_index, page in enumerate(range(1, 2)):
        # ページごとにリクエスト
        if page == 1:
            pass
        elif page == 2:
            url = update_query(url, "pn", "", page)
        else:
            url = update_query(url, "pn", str(page-1), page)
        print(url)
        try:
            print("\n\nhere===========")
            print(url)
            html = urllib.request.urlopen(url).read()
            print(f"pages: {page_index}/{page_count} of {page_index}: okay")
        except:
            print(f"pages: {page_index}/{page_count} of {page_index}: failed")
            continue
        soup = BeautifulSoup(html)

        blocks = soup.findAll("div", "property_unit-content") 

        for index_block in range(len(blocks)):
        # for index_block in range(5):
            time.sleep(1)
        #for index_block in range(3):
            # try:
            #     df = get_info_from_blocks_by_index(blocks, index_block, df)
            #     print(f"{index_block}/{len(blocks)}: okay")
            # except:
            #     print(f"{index_block}/{len(blocks)}: failed")
            df = get_info_from_blocks_by_index(blocks, index_block, df)
            print(f"blocks: {index_block}/{len(blocks)}: okay")
            if len(df) == num:
                print(f"[DEBUG] got enough datas, will return")
                df.to_excel(f"{name}.xlsx", index=False, encoding = "utf-8")
                return df.to_json()

            # try:
            #     df = get_info_from_blocks_by_index(blocks, index_block, df)
            #     print(f"blocks: {index_block}/{len(blocks)}: okay")
            # except:
            #     print(f"blocks: {index_block}/{len(blocks)}: failed")

        #print(df)
        #print(len(df))
        #df.to_csv(r"property.csv", index=False, encoding = "utf-8")
    df.to_excel(f"{name}.xlsx", index=False, encoding = "utf-8")
    return df.to_json()



if __name__ == "__main__":

    #url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=13&jspIdFlg=patternShikugun&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&sc=13109&sc=13110&sc=13111&sc=13112&sc=13116&kb=1&kt=9999999&mb=60&mt=9999999&md=2&md=3&md=4&ekTjCd=&ekTjNm=&tj=0&et=10&cnb=0&cn=9999999&srch_navi=1"]
    #url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=13&jspIdFlg=patternShikugun&sc=13103&kb=1&kt=9999999&mb=0&mt=9999999&ekTjCd=&ekTjNm=&tj=0&cnb=0&cn=9999999&srch_navi=1"]
    #url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=13&jspIdFlg=patternShikugun&sc=13110&kb=1&kt=9999999&mb=0&mt=9999999&ekTjCd=&ekTjNm=&tj=0&cnb=0&cn=9999999&srch_navi=1"]
    #url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=13&jspIdFlg=patternShikugun&sc=13103&kb=1&kt=9999999&mb=0&mt=9999999&ekTjCd=&ekTjNm=&tj=0&cnb=0&cn=9999999&srch_navi=1"]
    url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=13&jspIdFlg=patternShikugun&sc=13103&kb=1&kt=9999999&mb=0&mt=9999999&ekTjCd=&ekTjNm=&tj=0&cnb=0&cn=9999999&srch_navi=1"]
    url_list = ["https://suumo.jp/ms/chuko/tokyo/sc_shibuya/", "https://suumo.jp/ms/chuko/tokyo/sc_meguro/"]
    url_list = ["https://suumo.jp/ms/chuko/tokyo/sc_shinjuku/", "https://suumo.jp/ms/chuko/tokyo/sc_shinagawa/"]
    url_list = ["https://suumo.jp/ms/chuko/tokyo/sc_shinagawa/"]
    url_list = ["https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/?ar=030&bs=011&ta=13&jspIdFlg=patternShikugun&sc=13101&kb=1&kt=9999999&mb=0&mt=9999999&ekTjCd=&ekTjNm=&tj=0&cnb=0&cn=9999999&srch_navi=1"]

    #names = ["property_minato", "property_shibuya", "property_shinagawa", "property_shinjuku", "property_setagaya"]
    #names = ["property_shinjuku", "property_setagaya"]
    names = ["property_shibuya", "property_meguro"]
    names = ["property_shinjuku", "property_shinagawa"]
    names = ["property_shinagawa"]
    names = ["property_chiyoda"]

    cols_from_top = ["カテゴリ", "物件名", "販売価格", "所在地", "区", "沿線", "最寄駅", "徒歩（分）", "バス（分）",
            "土地面積", "建物面積", "バルコニー", "間取り", "築年数"]
    cols_from_gaiyou = [
        "管理費",
        "修繕積立金",
        "修繕積立基金",
        "所在階",
        "向き",
        "リフォーム",
        "敷地の権利形態",
        "駐車場",
        "完成時期(築年月)",
        "リンク",
        "土地面積（坪）",
        "建物面積（坪）",
        "坪単価"
        ]


    assert len(url_list) == len(names)

    cols_total = cols_from_top + cols_from_gaiyou

    for i, url in enumerate(url_list):
        scrape_url(url, names[i], cols_total)

