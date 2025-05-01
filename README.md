# 🎙️ PodGenie - AI-Powered Podcast Generator

**PodGenie** is an intelligent, fully automated podcast generation system powered by state-of-the-art NLP models like BART and T5, accelerated with Groq hardware, and voice-enabled using Google Text-to-Speech (GTTS). The system converts a simple text prompt into a coherent, high-quality audio podcast within seconds.

## 🚀 Features

- ✅ **AI Content Generation** with BART and T5
- ✅ **Hardware-Accelerated Inference** using Groq
- ✅ **Stability Layer** for filtering high-quality, coherent outputs
- ✅ **Text-to-Speech Audio Output** using GTTS
- ✅ **End-to-End Pipeline** from text input to audio podcast
- ✅ **Vertical & Modular Architecture** for scalability and experimentation


## 🧠 Project Architecture
User Prompt
   │
   ├──▶ BART (Content Generation)
   ├──▶ T5 (Alternative + Refinement)
   │     │
   └────▶ Stability Layer (Filters best output)
         │
         ▼
      Final Text
         │
         ▼
    GTTS (Audio Conversion)
         │
         ▼
     🎧 Final Podcast


| Component | Description |
|----------|-------------|
| **BART** | Used for content generation and summarization |
| **T5** | Used for refining and alternative text generation |
| **Groq** | Hardware accelerator for low-latency model inference |
| **Stability Layer** | Ensures coherence and content quality |
| **GTTS** | Converts generated text into spoken audio |
| **Python** | Backend scripting and orchestration |
| **Streamlit** (optional) | For interactive frontend (if deployed) |


**INSTALLATION:**
git clone https://github.com/**yourusername**/Podgenie.git

cd Podgenie

**How to Run:**
run the Streamlit app:
streamlit run Podgenie.py




