
# 概要

Chaser のサーバを作りたい

## 使い方

Changeconfig.pyで設定変更(下記参照)
Maim.pyを実行後、CoolとHotを接続し、エンターでスタート

## 資料

CHaserのサーバを見る[参照](http://www.procon-asahikawa.org/files/2020U16rule.pdf)  
クライアントのプログラムも見る

## プログラム分け

### Main.py

ゲーム本体（ロジックもここ）  
クライアントとの通信

### Cliant.py

たたき台にするクライアントのプログラム

### ReadConfig.py

Config.dt(中身はtxt)に書き込み＆読み込み  

### GUI.py

未定

### ChangeConfig.py

CLIで変更する
end でセーブせずに終了  
save でセーブして終了  
インデックス入力 → 値の入力で変更

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
