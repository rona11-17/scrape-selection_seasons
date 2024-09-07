import time
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

"""
csv出力するときに欲しい形
会社名がキーで以下の形が値の辞書型。

[["LINEヤフー", "〇〇卒", "職種", "選考時期"],
 ["", "24卒", "software_engineer", "2024/08~"],
]
"""

# 最初に検索したい会社を配列に格納
companies = ["LINEヤフー",
             "DeNA",
             "Amazon", 
             "google", 
             "メルカリ", 
             "楽天グループ", 
             "IndeedJapan", 
             "サイバーエージェント",
             "ソニーグループ",
             "リクルート"]

# csvの配列を用意
data = []

# 半角スペースと全角スペースを除去して，に変更
def remove_space(text):
    cleaned_text = re.sub(r'[s\u3000]', ',', text)
    return cleaned_text

# ログインページに遷移
def setup():
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get("https://gaishishukatsu.com/login")
    return driver

def login():
    # emailとpasswordのフィールドを取得
    email = driver.find_element(By.ID, 'GsUserEmail')
    password = driver.find_element(By.ID, 'GsUserPassword')

    # emailとpasswordを入力（自分のパスワードに変更）
    email.send_keys('example1@gmail.com')
    password.send_keys('hogemoge')

    # 送信する
    btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    btn.click()

def hover_action():
    hover_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//a[text()='ES・体験記']"))
    )
    action = ActionChains(driver)
    action.move_to_element(hover_element).perform()

    # ホバー後に要素が表示されるまで待機 (最大10秒)
    experience_link = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "ul > li:first-of-type"))
    )
    experience_link.click()

def search_company(company):
    input_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='企業名で絞り込む']"))
    )
    input_element.send_keys(company)

    try:
        company_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.flex.flex-col.items-start'))
        )
        company_link.click()
    except Exception:
        return False

    return True

def limit_condition():
    selection_process = driver.find_element(By.XPATH, "//label[text()='本選考']")
    selection_process.click()
    try:
        software_engineer = driver.find_element(By.XPATH, "//label[text()='ソフトウェアエンジニア']")
        software_engineer.click()
    except:
        return False
    
    return True

def scrape_information():
    # 欲しい情報の初期化
    graduation_seasons = []
    engineer_kinds = []
    selection_seasons = []
    
    # タブの管理
    tabs_in_order = []
    
    # 各体験談のリンクを取得（リンクと言いつつdivタグ）
    links = driver.find_elements(By.XPATH, "//div[text()='本選考']")

    # 体験談ページへのリンクが存在しなければ処理を終了
    if len(links) == 0:
        # csv出力するときに以下行がないとエラー
        return False
    
    # 情報の取得 + リンクを別タブで開く
    for link in links:

        # リンクを新しいタブで開いてtabs_in_orderの追加（開いた順）
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).click(link).key_up(Keys.CONTROL).perform()
        tabs_in_order.append(driver.window_handles[-1])

        # ついでに●●卒を取得
        graduation_season = link.find_element(By.XPATH, "following-sibling::div[1]")
        graduation_seasons.append(graduation_season.text)

        # ついでにエンジニアの種類を取得
        engineer_kind = link.find_element(By.XPATH, "./../../following-sibling::*[1]")
        engineer_kinds.append(engineer_kind.text)

    # 現在のタブを保存
    original_tab = driver.current_window_handle

    # 新しく開いたタブに順番に遷移する
    for tab in tabs_in_order:
        if tab != original_tab:
            driver.switch_to.window(tab)
            time.sleep(1)
            
            # 選考時期を取得
            try:
                selection_season_element = driver.find_element(By.CLASS_NAME, "selection_season")
                selection_season = remove_space(selection_season_element.text)
                selection_seasons.append(selection_season)
            except:
                return False

            driver.close()

    # 元のタブに戻る
    driver.switch_to.window(original_tab)

    # csv出力しやすい形に変更（refactoringの余地あり）
    combined_list = [
        [grad, kind, sel]
        for grad, kind, sel in zip(graduation_seasons, engineer_kinds, selection_seasons)
    ]

    data.append(combined_list)

    return True

# ページを閉じる
def teardown(driver):
    driver.quit()

"""
webサイト横断開始
"""
driver = setup()

login()

# 繰り返し始め
for i in range(len(companies)):
    hover_action()

    if not search_company(companies[i]):
        data.append([["none", "none", "none"]])
        continue
    
    if not limit_condition():
        data.append([["none", "none", "none"]])
        continue

    if not scrape_information():
        data.append([["none", "none", "none"]])
        continue

# 繰り返し終わり

teardown(driver)
"""
webページ横断終了
"""

"""
最後にcsv形式に保存する処理
"""
# csv形式で保存する
csv_rows = []

# dataのindexとcompaniesのindexを紐づけつつcsv用の配列を組む
for i, company_data in enumerate(data):
    company_name = companies[i]
    for experience in company_data:
        grad, job, sel = experience
        csv_rows.append([company_name, grad, job, sel])

with open('output.csv', 'w', newline='', encoding='shift_jis') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['会社名', '〇〇卒', '職種', '選考時期'])
    csvwriter.writerows(csv_rows)
