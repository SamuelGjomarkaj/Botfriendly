import requests
import time
from bs4 import BeautifulSoup
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# === CONFIGURATION ===
GOOGLE_API_KEY = "AIzaSyB7x3Th-3mYNygWC6FMrsqlXq8_GQq0hy0"
WEBSITE_URLS = [
    "http://192.168.100.26:5000/"
]
COMPANY_INFO_FILE = "company_info.txt"
CHUNK_SEPARATOR = "\n\n"

# === SETUP ===
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")
knowledge_base = []
already_initialized = False

# === EMBEDDING FUNCTION ===
def get_embedding(text):
    response = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return np.array(response["embedding"])

# === ADD TO MEMORY STORE ===
def store_embedding(chunk, embedding, meta):
    knowledge_base.append({
        "chunk": chunk,
        "embedding": embedding,
        "meta": meta
    })

# === QUERY TOP N MATCHES ===
def query_top_n(query, n=3):
    query_emb = get_embedding(query).reshape(1, -1)
    scored = [
        (cosine_similarity([item["embedding"]], query_emb)[0][0], item)
        for item in knowledge_base
    ]
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:n]
    return [item for _, item in top]

# === SCRAPE AND STORE WEB TEXT ===
def scrape_and_store():
    chunk_id = 0
    for url in WEBSITE_URLS:
        try:
            print(f"🌐 Fetching {url}...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Success: {url}")
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text()
                chunks = [chunk.strip() for chunk in text.split(CHUNK_SEPARATOR) if chunk.strip()][:100]  # Limit to 100
                for i, chunk in enumerate(chunks):
                    embedding = get_embedding(chunk)
                    store_embedding(chunk, embedding, {"source": "web", "url": url, "chunk": i})
                    chunk_id += 1
            else:
                print(f"❌ Failed to fetch {url}: status code {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")
        time.sleep(2)

# === LOAD LOCAL INFO ===
def load_manual_info():
    try:
        with open(COMPANY_INFO_FILE, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        print(f"⚠️ File not found: {COMPANY_INFO_FILE}")
        return

    chunks = [chunk.strip() for chunk in raw_text.split(CHUNK_SEPARATOR) if chunk.strip()][:100]
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        store_embedding(chunk, embedding, {"source": "manual", "chunk": i})
    print(f"✅ Loaded {len(chunks)} chunks from company_info.txt")

# === INIT BOT ===
def init_bot():
    global already_initialized
    if already_initialized:
        return
    already_initialized = True
    print("🧠 Initializing Bot...")
    scrape_and_store()
    load_manual_info()
    print("✅ Bot initialized.")

# === ASK FUNCTION ===
def ask_bot(user_question: str) -> str:
    results = query_top_n(user_question)
    context_blocks = []
    for item in results:
        source = item["meta"].get("url", "company_info.txt" if item["meta"].get("source") == "manual" else "unknown")
        context_blocks.append(f"[From: {source}]\n{item['chunk']}")
    context = "\n\n".join(context_blocks)

    full_prompt = (
        f"You are a helpful customer support assistant. Use only the info provided below to answer the user's question. "
        f"Be clear, concise, and friendly.\n\n"
        f"{context}\n\n"
        f"User: {user_question}\n"
        f"Agent:"
    )

    
    return getattr(response, "text", str(response)).strip()


