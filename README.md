# MoodVibes 🎵

音声から感情を読み取り、気分に合ったSpotifyのプレイリストを検索するWebアプリケーションです。

アプリのURL: https://moodvibes-xnxuvcbsjenrpqdmydcoiu.streamlit.app/

## ✨ 機能
- マイク入力または音声ファイルのアップロードによる音声認識
- 音声に含まれる感情キーワードの抽出
- 気分に合ったSpotifyプレイリストの検索と表示

## 🛠️ 必要なもの

### アプリケーション実行に必要なライブラリ
- Python 3.8+
- `requirements.txt` に記載のPythonライブラリ

### システム要件
- `ffmpeg`
  - ローカルで実行する場合、お使いのシステムに[ffmpeg](https://ffmpeg.org/download.html)をインストールし、環境変数`Path`を設定する必要があります。
  - Streamlit Cloudにデプロイする場合、`packages.txt`が自動で`ffmpeg`をインストールします。

## 🚀 セットアップと実行方法

### 1. リポジトリをクローン
```bash
git clone <リポジトリのURL>
cd MoodVibes
```

### 2. Pythonライブラリのインストール
```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定
Spotify APIを利用するために、認証情報を設定する必要があります。プロジェクトのルートディレクトリに `.env` という名前のファイルを作成し、以下の内容を記述してください。

```dotenv
SPOTIPY_CLIENT_ID="YOUR_SPOTIFY_CLIENT_ID"
SPOTIPY_CLIENT_SECRET="YOUR_SPOTIFY_CLIENT_SECRET"
```
`YOUR_SPOTIFY_CLIENT_ID` と `YOUR_SPOTIFY_CLIENT_SECRET` は、[Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)で取得したご自身のものに置き換えてください。

### 4. アプリケーションの実行
```bash
streamlit run app.py
```
ブラウザで表示されたURL（通常は `http://localhost:8501`）にアクセスすると、アプリケーションが利用できます。