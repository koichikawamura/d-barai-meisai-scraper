# d-barai-meisai-scraper
A tool to scrape meisai data from docomo website
(no English description available)

ドコモのウェブサイトからd払いの明細データをスクレイピングするツールです。

## 準備
1. Google Chromeが必要です。[Google Chrome](https://www.google.co.jp/chrome/?brand=RPHE&gclid=Cj0KCQiA2sqOBhCGARIsAPuPK0gHXbHK4aTn26xnsw-TDrXGu7NAxs0-ml9LM5Iy7i2ccNwrPxthZ-0aAq0WEALw_wcB&gclsrc=aw.ds)
1. Google Chromeのバージョンに対応した[ChromeDriver](https://chromedriver.chromium.org/downloads)をダウンロードして適当なディレクトリに置いてください。
1. d-baray.py冒頭近くのCHROMEDRIVERへの代入文を編集して、上記で配置したChromeDriverを設定してください。
```
# カレント・ディレクトリに配置した場合（デフォルトではこの状態になっています）
CHROMEDRIVER = './chromedriver'
# WindowsのC:\に配置した場合（手元にWindowsがないのでテストしていません）
CHROMEDRIVER = 'C:\chromedriver'
```
1. 必要に応じてパッケージをインストールしてください。
```
$ pip3 install -r requirements.txt
```

## 使い方
+ ヘルプを参照してください。
```
$ python3 d-barai.py --help
```
+ 実行するとChromeが起動します。パスワード入力画面に遷移しますので入力してください。このプログラムではパスワードは記録しません。

## 使用例
+ 2022年1月請求分をエクセルのファイルに出力する。
```
$ python3 d-barai.py --user foo@bar.com --month 202201 --excel
```
+ 2021年11月請求分と12月請求分をエクセル向けのcsvに出力する。
```
$ python3 d-barai.py --user foo@bar.com --month 202111 202112 --csv --encoding cp932
```
