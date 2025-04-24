import os
import openai
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from file_loader import load_pdf, load_text, load_docx
from text_splitter import split_text

# .envファイルの内容を読み込み
load_dotenv()

# 環境変数からAPIキー、モデル、温度を取得
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")
OPENAI_API_TEMPERATURE = float(os.getenv("OPENAI_API_TEMPERATURE"))

# 埋め込みとインデックス作成
def create_faiss_index(texts):
    embeddings = OpenAIEmbeddings(api_key=openai.api_key)
    return FAISS.from_documents(texts, embeddings)

# クエリ検索とChatGPT 4.0oでの応答生成
def search_index(faiss_index, query):
    # FAISSインデックスで検索
    results = faiss_index.similarity_search(query)
    content = results[0].page_content if results else "該当する情報が資料内に見つかりませんでした。"

    # ChatGPT 4.0oを使って応答を生成
    response = openai.chat.completions.create(
    model=OPENAI_API_MODEL,
    temperature=OPENAI_API_TEMPERATURE,
    messages=[
        {
            "role": "system",
            "content": (
                # 学生の質問やコメントに対する基本的な役割とアプローチ
                "あなたは学生の質問や授業に関するコメントに対して、提供された講義資料と参考例を基に講義の範囲に基づいて正確で簡潔な回答を行うアシスタントです。"
                "質問、コメントに対しては、基本的に丁寧語で回答してください。"
                "感謝の言葉などは必要ありません"
                "先生の回答:の部分も必要ありません"
                
                # 講義の範囲を超えた質問に対する対応方法
                "質問が講義の範囲を超えている、また資料に直接関係のない場合は、「その質問は講義の範囲を超えているため、回答できません」と答えてください。"
                "感想が講義の範囲を超えている、また資料に直接関係のない場合は、「その感想は講義の範囲を超えているため、回答できません」と答えてください。"
        
                # 授業コメントへの反応の方針
                "授業に関するコメントに対しては、その内容に基づいて適切に反応し、学生が持っている印象や興味を引き出す回答を提供してください。"
                "回答は、学生の学びや関心を深めるために、教育的かつ励ましのある内容であることが望ましいです。"
        
                # 不確定な情報に対する慎重な対応
                "原則として提供した資料に基づいて回答してください．回答に必要な関連情報が不十分な場合には、プログラミングに関する一般的な知識を用いて補完しても構いません。"
                "推測に基づく不確定な情報の提供は行わないでください。"
        ),
    },
        {
            "role": "user",
            "content": f"以下の資料に基づいて回答してください。回答に必要な関連情報が不十分な場合には、プログラミングに関する一般的な知識を用いて補完しても構いません:\n\n{content}\n\n質問: {query}"
        }
    ]
)

    answer = response.choices[0].message.content.strip()
    return answer


# フォルダ内のすべてのPDFおよびテキストファイルを読み込んでインデックスを作成
def load_and_index_folder(folder_path, return_documents=False):
    all_texts = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith(".pdf"):
            documents = load_pdf(file_path)
        elif filename.endswith(".txt"):
            documents = load_text(file_path)
        elif filename.endswith(".docx"):  # Wordファイル対応
            documents = load_docx(file_path)
        else:
            continue

        texts = split_text(documents)
        all_texts.extend(texts)

    # return_documentsがTrueの場合、ドキュメントのリストを返す
    if return_documents:
        return all_texts
    # デフォルトではインデックスを返す
    return create_faiss_index(all_texts)

