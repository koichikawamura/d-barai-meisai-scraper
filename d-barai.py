import sys
import argparse
import re
from selenium import webdriver
from selenium.webdriver.chrome import service as cs
from selenium.webdriver.common.keys import Keys as keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from bs4 import BeautifulSoup
from pytz import timezone
from datetime import datetime
import pandas as pd
from unicodedata import normalize

CHROMEDRIVER = './chromedriver'


class DBaraiSite:
    paging_no_decomposer = re.compile(r'(\d+)/(\d+)')

    def __init__(self, chrome_driver, account):
        chrome_servie = cs.Service(executable_path=chrome_driver)
        self.driver = webdriver.Chrome(service=chrome_servie)

        url = 'https://payment2.smt.docomo.ne.jp/' \
              'smph/history/gadap031.srv?' \
              'hk=p&bis=lga&root_GADAGS403SubmitRirekiSelectMonth='

        self.driver.get(url)
        account_id = self.driver.find_element(By.ID, 'Di_Uid')
        account_id.send_keys(account)
        account_id.submit()

        # ご利用履歴・お支払い明細
        wait = WebDriverWait(self.driver, 180)
        e = wait.until(
            EC.presence_of_element_located(
                (By.NAME, 'root_GADAGS402SubmitTel')
            )
        )
        e.click()

    def get_meisai_page(self, month):
        try:
            cdate = self.driver.find_element(By.ID, 'cdate').text
        except NoSuchElementException:
            self.driver.find_element(
                By.NAME, 'root_GADAGW004SubmitModoru'
            ).click()

            wait = WebDriverWait(self.driver, 180)
            e = wait.until(
                EC.presence_of_element_located((By.ID, 'cdate'))
            )
            cdate = e.text

        month_selector = self.driver.find_element(
            By.NAME, 'root_GADAGS403_OSIHARAIMEISAIPULLDOWN'
        )
        select_object = Select(month_selector)
        selectable_months = [
            o.get_attribute('value') for o in select_object.options
        ]
        if month not in selectable_months:
            print(f"{month}は選択できません。", file=sys.stderr)
            return

        select_object.select_by_value(month)
        select_button = self.driver.find_element(
            By.NAME, 'root_GADAGS403SubmitMeisaiSelectMonth'
        )
        select_button.click()

        while True:
            wait = WebDriverWait(self.driver, 180)
            e = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="wrapper"]/div/'
                        'div[contains(@class, "paging")]'
                    )
                )
            )
            paging_no = e.text
            print(paging_no)
            m = DBaraiSite.paging_no_decomposer.search(paging_no)
            page_no = int(m.group(1))
            num_total_pages = int(m.group(2))

            yield self.driver.page_source.encode('utf-8')

            if page_no == num_total_pages:
                break

            next_button = self.driver.find_element(
                By.NAME, 'root_GADAGW004ZnextPage'
            )
            next_button.click()

    def quit(self):
        self.driver.quit()


def get_meisai_table(d_barai_site, month):
    price_finder = re.compile(r'¥\s([,\d]+)')
    records = []
    for html in d_barai_site.get_meisai_page(month):
        soup = BeautifulSoup(html, 'html.parser')
        meisai_table = soup.find('table', class_='appliTable')
        for t in meisai_table.find_all('tr'):
            div_date = t.select_one('div.date')
            if not div_date:
                continue
            date_text = div_date.text
            t_time = datetime.strptime(date_text, '[%Y/%m/%d %H:%M]')
            product_name = t.select_one('div.productName').text
            vender = t.select_one('div.vender').text
            price_section = t.select_one('span.price').text
            m = price_finder.search(price_section)
            price = int(m.group(1).replace(',', ''))

            record = {
                '日時': t_time,
                '店名': normalize('NFKC', product_name),
                '支払い方法': vender,
                '金額': price
            }
            records.append(record)

    if len(records) == 0:
        return None
    else:
        transaction_df = pd.DataFrame(records)
        transaction_df.sort_values('日時', ascending=False, inplace=True)
        transaction_df.reset_index(inplace=True)

        return transaction_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='docomoのウェブサイトからd払いの明細データをスクレイピングするツール'
    )

    parser.add_argument(
        '-u', '--user',
        required=True,
        help='dアカウントのID'
    )
    parser.add_argument(
        '-m', '--month',
        nargs='*',
        required=True,
        help='請求月(YYYYMM)'
    )
    parser.add_argument(
        '-p', '--pandas',
        action='store_true',
        help='pandasのDataFrameのpickleを出力'
    )
    parser.add_argument(
        '-c', '--csv',
        action='store_true',
        help='csvを出力'
    )
    parser.add_argument(
        '-x', '--excel',
        action='store_true',
        help='EXCELのファイルを出力'
    )
    parser.add_argument(
        '-e', '--encoding',
        help='csvを出力する場合のエンコーディング'
    )

    args = parser.parse_args()
    print(args)

    d_barai_site = DBaraiSite(CHROMEDRIVER, args.user)

    for m in args.month:
        transaction_df = get_meisai_table(d_barai_site, m)
        print(transaction_df)
        if transaction_df is None:
            continue

        if args.pandas:
            transaction_df.to_pickle(f"d払い_支払い_{m}.pickle")

        if args.csv:
            if args.encoding:
                transaction_df.to_csv(
                    f"d払い_支払い_{m}.csv",
                    index=False, encoding=args.encoding
                )
            else:
                transaction_df.to_csv(
                    f"d払い_支払い_{m}.csv",
                    index=False
                )

        if args.excel:
            transaction_df.to_excel(
                f"d払い_支払い_{m}.xlsx", sheet_name=f"支払い_{m}",
                index=False
            )

    d_barai_site.quit()
