

# 📄 RAG-Based Document Question Answering System

An AI-powered application that allows users to **upload documents and ask questions** about their content using **Retrieval-Augmented Generation (RAG)** and **Large Language Models (LLMs)**.

---

## 🚀 Features

* 📂 Upload documents (PDF, TXT, etc.)
* 🔍 Intelligent document parsing and text chunking
* 🧠 Semantic search using vector embeddings
* 💬 Ask questions based on uploaded documents
* ⚡ Fast and accurate responses using LLMs
* 🔗 Context-aware answer generation (not generic responses)

---

## 🧠 How It Works

1. **Document Upload**
   User uploads a document.

2. **Text Processing**

   * Extract text from document
   * Split into smaller chunks

3. **Embedding Generation**

   * Convert text chunks into vector embeddings

4. **Vector Storage**

   * Store embeddings in a vector database (e.g., FAISS)

5. **Query Processing**

   * User asks a question
   * System retrieves relevant chunks using similarity search

6. **Answer Generation**

   * LLM generates response using retrieved context

---

## 🛠️ Tech Stack

* **Backend:** FastAPI
* **Language:** Python
* **LLM Framework:** LangChain
* **Vector Database:** FAISS
* **AI Models:** OpenAI API / LLMs
* **Frontend:** (Streamlit / HTML / React – update if needed)
* **Version Control:** Git & GitHub

---

## 📁 Project Structure

```
RAG_LLM/
│── app/
│   ├── main.py            # FastAPI entry point
│   ├── routes/           # API routes
│   ├── services/         # Core logic (RAG pipeline)
│   └── utils/            # Helper functions
│
│── data/                 # Uploaded documents
│── embeddings/           # Vector storage
│── requirements.txt      # Dependencies
│── README.md             # Project documentation
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/PRITAM-TU/RAG_LLM.git
cd RAG_LLM
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Add Environment Variables

Create a `.env` file and add:

```
OPENAI_API_KEY=your_api_key_here
```

---

## ▶️ Run the Application

```bash
uvicorn app.main:app --reload
```

Now open:
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📌 API Endpoints

### Upload Document

```
POST /upload
```

### Ask Question

```
POST /query
```

---

## 💡 Example Use Case

* Upload a **research paper / notes / PDF**
* Ask:

  * "What is the main topic?"
  * "Summarize chapter 2"
  * "Explain key concepts"

---

## 📊 Future Improvements

* 🔐 User authentication system
* 🌐 Multi-document querying
* 📈 Performance optimization
* 🧾 Support for more file formats
* 🎨 Better UI (React dashboard)

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork the repo and submit a pull request.

---

## 📜 License

This project is open-source and available under the **MIT License**.

---

## 👨‍💻 Author

**Pritam Tung**
🔗 GitHub: [https://github.com/PRITAM-TU](https://github.com/PRITAM-TU)

---
