import os
import gspread
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime  
from oauth2client.service_account import ServiceAccountCredentials
from file_loader import load_pdf
from file_loader import load_text
from file_loader import load_docx
from text_splitter import split_text
from faiss_indexer import load_and_index_folder, search_index, create_faiss_index

# 環境変数のロード（必要に応じて）
load_dotenv()

# Streamlitのヘッダー
st.title("質問応答チャットボット")

# フォルダのパス
lecture_folder = "./Programming_engineering"  # 講義資料フォルダ
example_folder = "./examples"     # 回答例フォルダ
log_folder = "./logs"             # 会話ログ保存フォルダ

# フォルダの存在確認
folders_to_load = [lecture_folder]
if os.path.exists(example_folder):
    folders_to_load.append(example_folder)

# インデックスの作成
def load_and_index_multiple_folders(folders):
    all_texts = []
    for folder in folders:
        texts = load_and_index_folder(folder, return_documents=True)
        all_texts.extend(texts)
    return create_faiss_index(all_texts)
    
# フォルダをまとめて読み込み＆インデックス化
combined_index = load_and_index_multiple_folders(folders_to_load)

# セッションステートでメッセージの履歴を保持
if "messages" not in st.session_state:
    st.session_state.messages = []

# 既存のメッセージをブラウザ上に表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
query = st.chat_input("質問を入力してください:")

# 質問が入力された場合の応答処理
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    response = search_index(combined_index, query)

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # ここでログを即時保存
    save_single_turn_to_sheet(query, response)

# Google Sheets に接続
def get_gsheet():
    import json
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GSPREAD_SERVICE_ACCOUNT"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(st.secrets["SHEET_NAME"]).sheet1
    return sheet
    
# 会話履歴を1行だけGoogle Sheetsに保存（student_idは常にanonymous）
def save_single_turn_to_sheet(user_query, assistant_response):
    sheet = get_gsheet()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, user_query, assistant_response])
