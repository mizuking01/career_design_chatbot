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
example_folder = "./Programming engineering_examples"     # 回答例フォルダ
log_folder = "./logs"             # 会話ログ保存フォルダ

# インデックスの作成
def load_and_index_multiple_folders(folders):
    all_texts = []
    for folder in folders:
        texts = load_and_index_folder(folder, return_documents=True)
        all_texts.extend(texts)
    return create_faiss_index(all_texts)

# 講義資料と参考例を統合したインデックスを作成
combined_index = load_and_index_multiple_folders([lecture_folder, example_folder])

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

# Google Sheets に接続
def get_gsheet():
    import json
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GSPREAD_SERVICE_ACCOUNT"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(st.secrets["SHEET_NAME"]).sheet1
    return sheet

# 会話履歴を1行ずつGoogle Sheetsに保存（student_idは常にanonymous）
def save_conversation_log_to_sheet():
    sheet = get_gsheet()
    # ユーザーとアシスタントのペアを順番に取り出して記録
    for i in range(0, len(st.session_state.messages) - 1, 2):
        user_msg = st.session_state.messages[i]
        bot_msg = st.session_state.messages[i + 1]
        if user_msg["role"] == "user" and bot_msg["role"] == "assistant":
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, user_msg["content"], bot_msg["content"]])


# 会話終了ボタン押されたらGoogle Sheetsに保存
if st.button("会話を終了"):
    save_conversation_log_to_sheet()
    st.info("会話が終了しました")