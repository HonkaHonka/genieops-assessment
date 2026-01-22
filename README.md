# GenieOps Automated Lead Magnet & Nurturing Engine

An autonomous SaaS MVP that transforms conversational business visions into high-converting marketing funnels. Built for the GenieOps Development Assessment.

## 🚀 Features
- **Neural Intake:** Chat-based interface to extract ICP and marketing goals.
- **Multi-Agent Orchestration:** 
    - **Llama 3 (Strategist):** Handles branding, visual themes, and strategy.
    - **DeepSeek R1 (Engineer):** Generates functional JavaScript math logic and PAS-framework copy.
- **Interactive Assets:** Dynamic Calculators and Market Reports with live data visualization.
- **Full-Cycle Automation:** Integrated Pexels API for imagery and Gmail SMTP for real-time lead nurturing.
- **VRAM Optimized:** Implements a Volatile Memory Strategy to run 8B models locally on 6GB hardware.

## 🛠️ Tech Stack
- **Frontend:** React.js (Vite), Tailwind CSS v4, Framer Motion, Canvas API.
- **Backend:** FastAPI, PostgreSQL, SQLAlchemy.
- **AI:** Ollama (Llama 3, DeepSeek R1).

## 📥 Setup Instructions
1. **Ollama:** Install Ollama and pull `llama3` and `deepseek-r1`.
2. **Backend:**
   - `cd backend`
   - `pip install -r requirements.txt`
   - Set up `.env` using `.env.example`.
   - `uvicorn app.main:app --reload`
3. **Frontend:**
   - `cd frontend`
   - `npm install`
   - `npm run dev`