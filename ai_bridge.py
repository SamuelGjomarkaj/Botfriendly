import requests
import time
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai

# === CONFIGURATION ===
GOOGLE_API_KEY = "AIzaSyDbPcSEgZ81Crwgs0rUGDW_9fkbMgmF9p0"
WEBSITE_URLS = [
    "http://192.168.100.26:5000/"

]
COMPANY_INFO_FILE = "company_info.txt"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SEPARATOR = "\n\n"

# === SETUP ===
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("support_knowledge")

# === INIT FLAG ===
already_initialized = False

# === SCRAPE AND LOAD ONCE ===
def scrape_and_store():
    chunk_id = 0
    for url in WEBSITE_URLS:
        success = False
        for attempt in range(0):
            try:
                print(f"🌐 Fetching {url} (attempt {attempt + 1})...")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Success: {url}")
                    soup = BeautifulSoup(response.text, "html.parser")
                    text = soup.get_text()
                    chunks = [chunk.strip() for chunk in text.split(CHUNK_SEPARATOR) if chunk.strip()]
                    embeddings = embed_model.encode(chunks)

                    collection.add(
                        documents=chunks,
                        embeddings=embeddings,
                        ids=[f"web-{chunk_id + i}" for i in range(len(chunks))],
                        metadatas=[{"url": url, "source": "web", "chunk": i} for i in range(len(chunks))]
                    )
                    chunk_id += len(chunks)
                    success = True
                    break
                else:
                    print(f"❌ Failed ({response.status_code}) on attempt {attempt + 1}")
            except Exception as e:
                print(f"⚠️ Error fetching {url} on attempt {attempt + 1}: {e}")
            time.sleep(2)

        if not success:
            print(f"🚫 Failed to fetch {url} after 3 attempts.")

def load_manual_info():
    try:
        with open(COMPANY_INFO_FILE, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        print(f"⚠️ File not found: {COMPANY_INFO_FILE}")
        return

    chunks = [chunk.strip() for chunk in raw_text.split(CHUNK_SEPARATOR) if chunk.strip()]
    embeddings = embed_model.encode(chunks)
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"manual-{i}" for i in range(len(chunks))],
        metadatas=[{"source": "manual", "chunk": i} for i in range(len(chunks))]
    )
    print(f"✅ Loaded {len(chunks)} chunks from company_info.txt")

# === PUBLIC: Run once at app startup ===
def init_bot():
    global already_initialized
    if already_initialized:
        return
    already_initialized = True
    print("🧠 Initializing Bot_prototyp...")
    scrape_and_store()
    load_manual_info()
    print("✅ Bot_prototyp initialized.")

# === PUBLIC: Ask a question anytime ===
def ask_bot(user_question: str) -> str:
    question_embedding = embed_model.encode(user_question)
    result = collection.query(query_embeddings=[question_embedding], n_results=3)

    context_blocks = []
    for doc, meta in zip(result["documents"][0], result["metadatas"][0]):
        source = meta.get("url", "company_info.txt" if meta.get("source") == "manual" else "unknown")
        context_blocks.append(f"[From: {source}]\n{doc}")
    context = "\n\n".join(context_blocks)

    full_prompt = (
        f"You are a helpful customer support assistant. Use only the info provided below to answer the user's question.Remember to speak like a customer service agent\n\n"
        f"{context}\n\n"
        f"User: {user_question}\n"
        f"Agent:"
    )

    response = model.generate_content(full_prompt)
    return getattr(response, "text", str(response)).strip()
