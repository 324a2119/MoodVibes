import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# ===== Spotify API認証 =====
CLIENT_ID = "ff259b9ec7f3420381662c278fed342f"
CLIENT_SECRET = "a35403dc7fb64531ba6a98c5794fcef8"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# ===== Streamlit UI =====
st.title("🎵 Spotify プレイリスト検索アプリ")
st.write("キーワードを入力してSpotifyのプレイリストを検索します。")

# 検索入力
query = st.text_input("検索キーワードを入力", value="楽しい")

if st.button("検索"):
    if query.strip() == "":
        st.warning("検索キーワードを入力してください。")
    else:
        # プレイリストを検索
        results = sp.search(q=query, type='playlist', limit=10)
        playlists = results['playlists']['items']

        if not playlists:
            st.info("プレイリストが見つかりませんでした。")
        else:
            st.subheader("🔍 検索結果")
            for idx, playlist in enumerate(playlists):
                with st.expander(f"{playlist['name']}  ({playlist['owner']['display_name']})"):
                    st.image(playlist['images'][0]['url'], width=300)
                    st.markdown(f"[Spotifyで開く]({playlist['external_urls']['spotify']})")
                    playlist_id = playlist['id']

                    # プレイリスト内の曲を取得
                    tracks = sp.playlist_tracks(playlist_id)
                    st.write("🎶 曲一覧：")
                    for t in tracks['items']:
                        track = t['track']
                        track_name = track['name']
                        artist_name = track['artists'][0]['name']
                        st.write(f"- {track_name} / {artist_name}")

