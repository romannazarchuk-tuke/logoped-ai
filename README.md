# AI Logoped Assistant 🎙️

An AI-powered web application designed to act as a "co-therapist" for home speech therapy sessions. This project utilizes a Retrieval-Augmented Generation (RAG) architecture and a custom linguistic stemming algorithm to provide safe, methodologically accurate, and hallucination-free logopedic exercises in the Slovak language.

Developed as a Bachelor's Thesis at the Technical University of Košice (TUKE), Faculty of Electrical Engineering and Informatics.

## 🚀 Key Features

* **RAG-Powered Knowledge Base:** Integrates 19 expert logopedic documents, ensuring the LLM acts strictly as a "format architect" and draws facts only from verified medical/educational methodologies.
* **Custom Slovak Stemming (`stem_slovak`):** A bespoke heuristic normalization algorithm designed for the highly inflective Slovak language, enabling ultra-fast, memory-efficient term-frequency searching without relying on heavy external NLP libraries.
* **Zero Hallucinations & Language Purity:** Advanced structured prompt engineering completely eliminates language interference (Bohemisms) and prevents the generation of non-existent exercises.
* **Methodological Pipeline:** Enforces a strict output structure: *Instructions ➔ Oromotor Exercises ➔ Syllables ➔ Words ➔ Poems*.
* **Real-Time UX (SSE):** Utilizes Server-Sent Events for asynchronous token streaming, providing a dynamic "typing" effect with a Time-to-First-Token under 2 seconds.
* **Session Memory & Interactive UI:** SQLite-backed context management maintains conversation history, while the backend dynamically generates clickable follow-up questions to reduce the cognitive load on parents.

## 🛠 Tech Stack

**Backend & Data:**
* Python / Flask
* SQLAlchemy (ORM & SQL Injection protection)
* SQLite (Session persistence)

**AI & Architecture:**
* Qwen 3.5 LLM (Hosted via Open WebUI on a dedicated server)
* Custom RAG Pipeline
* Heuristic Stemmer (`stem_slovak`)

**Infrastructure:**
* Docker & Docker Compose (Fully containerized for seamless portability)

## 🏗 Architecture Flow

1. **User Query:** Parent selects a sound or asks a therapy-related question.
2. **Retrieval:** The backend processes the query using the `stem_slovak` algorithm and retrieves the most relevant chunks from the logopedic knowledge base.
3. **Prompt Injection:** Retrieved context and strict system restrictions are injected into the prompt.
4. **LLM Generation:** The Qwen 3.5 model processes the structured prompt.
5. **Streaming Response:** The output is streamed back to the user via SSE, accompanied by dynamically generated interactive follow-up buttons.

## 💻 Installation and Setup (Local)

1. Clone the repository:
   ```bash
   git clone https://github.com/romannazarchuk-tuke/logoped-ai.git
   cd logoped-ai
   ```
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask server:
   ```bash
   python app.py
   ```
4. Open the application in your browser at `http://127.0.0.1:5000`

## 🐳 Running with Docker

```bash
docker build -t logoped-ai .
docker run -p 5000:5000 logoped-ai
```

## 👨‍💻 Author
**Roman Nazarchuk**  
Technical University of Košice (TUKE)
