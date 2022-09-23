
# 概要

Chaser のサーバを作りたい

## 資料

CHaserのサーバを見る  
クライアントのプログラムも見る

## プログラム分け

### Main.py

他プログラムの読み込み＆制御

### Cliant.py

たたき台にするクライアントのプログラム

### ReadConfig.py

Config.dt(中身はtxt)に書き込み＆読み込み  
end でセーブせずに終了  
save でセーブして終了  
インデックス入力 → 値の入力で変更

### Communication.py

クライアントとの通信

### GUI.py

未定

### ChangeConfig.py

CLIで変更する

## Config.dtの中身

jsonで書く  
上から順番に  

- Coolのポート番号
- Hotのポート番号
- ゲーム進行速度[ms]
- 通信タイムアウト時間[ms]
- ボット対戦モード(0/1)

## 通信例の中身

WireSharkで通信を傍受した結果の改変  

- Client: C  
- Server: 無印

### 分析

1回目に名前  
Cの#は行動終了、Serverの@は行動開始  
エラーの通信がない(追加したい)
