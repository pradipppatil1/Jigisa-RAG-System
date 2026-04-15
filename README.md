# Jigisa RAG System (FinBot)

FinBot is a modern, enterprise-grade Retrieval-Augmented Generation (RAG) system built to serve tailored, role-based financial intelligence and general knowledge. It features a robust semantic router, secure role-based access control (RBAC), intelligent guardrails, robust offline evaluation metrics, and an intelligent document ingestion pipeline via Docling.

## 🚀 Technology Stack

### Frontend (User Interface)
The frontend is built for responsive design and blazing fast performance, featuring a beautiful chat UI and a dedicated Admin Portal.
- **Framework**: Next.js (React 19)
- **Language**: TypeScript
- **Styling**: Vanilla CSS with customized variable theming

### Backend (Core Logic & AI)
The backend manages the complex AI pipeline, enforcing strict access controls and semantic intelligent routing.
- **Framework**: FastAPI (Python 3.13)
- **Databases**: 
  - **Qdrant**: High-performance Vector Database for embedding storage
  - **MySQL**: Relational database for Auth, Chat History, and RBAC via SQLAlchemy
- **AI & Reasoning**: LangChain, Groq (LLM Engine), HuggingFace (Sentence Transformers `all-MiniLM-L6-v2`)
- **Document Processing**: Docling (Hierarchical PDF/Document Parsing)
- **Routing**: Semantic Router (Embedding-based intent classification)
- **Offline Evaluation**: RAGAS (Ablation testing metrics via Pandas and Huggingface Datasets)

---

## 🏗️ System Architecture

The following diagram illustrates the end-to-end flow of the Jigisa RAG System, detailing document ingestion, user authentication, semantic routing, and the retrieval generation process.

```mermaid
graph TD
    %% Frontend
    subgraph Frontend [Next.js User Interface]
        UI[Chat Interface & Admin Portal]
        State[React Context / Authentication]
        UI --> State
    end

    %% Backend Services
    subgraph Backend [FastAPI Backend Server]
        API_GW[API Router & Auth Middleware]
        Guard_In[Input Guardrails / NeMo]
        Router[Semantic Router Pipeline]
        Guard_Out[Output Guardrails / NeMo]
        Evaluation[RAGAS Evaluation Module]
    end

    %% AI Models
    subgraph Models [AI & Language Models]
        LLM[Groq LLM Engine]
        Embed[HuggingFace Embeddings]
    end

    %% Databases
    subgraph Databases [Data Storage]
        MySQL[(MySQL DB<br/>Auth & Session History)]
        Qdrant[(Qdrant Vector DB<br/>Embedded Document Chunks)]
    end

    %% Document Ingestion
    subgraph Ingestion [Document Processing]
        Docling[Docling Hierarchical Parser]
        Chunker[LangChain Document Splitter]
    end

    %% Processing Flow
    UI -->|1. User Login / Query| API_GW
    API_GW --> MySQL
    API_GW -->|2. Validates Request| Guard_In
    Guard_In --> Router
    
    %% Routing & Retrieval
    Router -->|3. Intent Classification| Embed
    Embed --> Router
    Router -->|4. Role-Based Retrieval| Qdrant
    Qdrant -->|5. Retrieved Context| LLM
    LLM --> Guard_Out
    Guard_Out -->|6. Validated Response| API_GW
    API_GW -->|7. Display| UI

    %% Ingestion Flow
    UI -.->|Admin Uploads PDF| Docling
    Docling -.-> Chunker
    Chunker -.-> Embed
    Embed -.-> Qdrant

    %% Evaluation Flow
    Evaluation -.->|Ablation Tests| Router
    Evaluation -.->|Offline Metrics| MySQL
```

---

## 🛠️ Local Setup Instructions

Follow these clear steps to run the complete environment on your local machine.

### 1. Prerequisites
You must have the following installed and running:
* **Node.js** (v18+)
* **Python** (3.13+)
* **MySQL Server** (Running locally on port 3306)
* **Qdrant** (Ideally running via Docker on port 6333 - `docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant`)
* A **Groq** API Key

### 2. Backend Setup
Open a terminal and navigate to the `Back-End` directory:

```bash
cd Back-End

# 1. Create and activate a Virtual Environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -e .

# 3. Environment Variables
# Create a .env file based on .env.example (if present)
# Ensure the following keys are populated:
# GROQ_API_KEY=your_key_here
# DATABASE_URL=mysql+pymysql://user:password@localhost/dbname

# 4. Run the Server
python main.py
```
> The API server will be live at `http://127.0.0.1:8000`. Upon startup, it will automatically initialize MySQL tables and seed demo users.

### 3. Frontend Setup
Open a separate terminal and navigate to the `Front-End` directory:

```bash
cd Front-End

# 1. Install Node Dependencies
npm install

# 2. Run the Development Server
npm run dev
```
> The web application will be live at `http://localhost:8080`.

---

## 🔐 Accounts

By default, the backend will seed several demo users into the MySQL database on first startup. You can use these to test the RBAC capabilities directly in the UI.

| Role | Username | Department |
| :--- | :--- | :--- |
| **C-Level** | `admin` | Executive (Full Access + Admin Panel) |
| **Finance** | `fin_user` | Finance |
| **Marketing** | `mkt_user` | Marketing |
| **Engineering** | `eng_user` | Engineering |

---

## 🧪 Evaluation Pipeline
FinBot features a state-of-the-art offline assessment pipeline using RAGAS. You can run ablation testing (simulating pure vector searches vs semantic routing vs strict guardrails) locally.

To generate the evaluation report:
```bash
cd Back-End
python -m app.evaluation.evaluate
```
Once completed, the metrics (Faithfulness, Answer Relevancy, Context Precision, Context Recall, Answer Correctness) will inherently become visible directly under the **Evaluation Reports** tab within the C-Level Admin Portal.
