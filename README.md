# 🤖 AI Study Buddy Pro

### An AI-Powered Learning Assistant for Smarter and Personalized Study

AI Study Buddy Pro is a web-based AI learning assistant built with **Python, Streamlit, and Google Gemini AI**. It helps students learn faster by generating study notes, explaining difficult topics, creating quizzes, summarizing text, analyzing PDFs, and providing an interactive AI study assistant.

---

## 🚀 Features

### 📚 Generate Notes

Generate structured and easy-to-understand study notes for any topic.

### 💡 Explain Topic

Get simple explanations of difficult concepts with examples and clear descriptions.

### 📝 Create Quiz

Generate multiple-choice questions (MCQs) from a selected topic for self-assessment.

### 📄 Summarize Text

Convert long study material into concise and useful summaries.

### 📑 PDF Analyzer

Upload a PDF and use AI to understand and analyze its content.

### 💬 Ask AI

Ask questions directly to the AI study assistant and get contextual answers.

### 📊 Progress Tracking

Track study activity, quiz activity, and topics studied through the dashboard.

### 🕒 Study History

Keep track of previously performed study activities.

### 🔐 Secure API Configuration

The Gemini API key is stored using environment variables / Streamlit Secrets and is not exposed in the application interface.

---

## 🛠️ Technologies Used

| Technology       | Purpose                         |
| ---------------- | ------------------------------- |
| Python           | Application development         |
| Streamlit        | Web application interface       |
| Google Gemini AI | AI-powered responses            |
| Google GenAI SDK | Gemini API integration          |
| PyPDF2           | PDF text extraction             |
| python-dotenv    | Environment variable management |

---

## 🏗️ Project Structure

```text
AI-Powered-Study-Buddy/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
└── venv/
```

> **Note:** `.env` and `venv/` should not be uploaded to GitHub.

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vk622549/AI-Powered-Study-Buddy.git
```

### 2. Open the Project

```bash
cd AI-Powered-Study-Buddy
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### macOS/Linux

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 API Key Configuration

This project uses the **Google Gemini API**.

Create an API key through Google AI Studio and store it securely.

For local development, create a `.env` file in the project directory:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

The application reads the key using:

```python
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
```

### ⚠️ Security

Never upload your `.env` file or API key to GitHub.

Make sure `.gitignore` contains:

```text
.env
venv/
__pycache__/
```

---

## ▶️ Run the Application

Start the Streamlit application with:

```bash
streamlit run app.py
```

The application will open in your browser at the local Streamlit address.

---

## ☁️ Streamlit Deployment

The application can be deployed using **Streamlit Community Cloud**.

### Deployment Steps

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new application.
4. Select the GitHub repository.
5. Select the `main` branch.
6. Select `app.py` as the main file.
7. Add the Gemini API key in Streamlit **Secrets**.

Example:

```toml
GEMINI_API_KEY = "YOUR_API_KEY"
```

8. Deploy the application.

After deployment, the application can be accessed through its Streamlit web URL.

---

## 🧠 How the Application Works

```text
User
  ↓
Streamlit Interface
  ↓
Selects Learning Feature
  ↓
User Input / PDF
  ↓
Prompt Generation
  ↓
Google Gemini AI
  ↓
AI-Generated Response
  ↓
Displayed in Streamlit
  ↓
Study Activity / History
```

---

## 📌 Main Modules

### Dashboard

Provides an overview of the student's learning activity.

### Generate Notes

Creates organized notes based on the requested topic.

### Explain Topic

Provides beginner-friendly explanations of concepts.

### Summarize Text

Processes user-provided text and generates a concise summary.

### Create Quiz

Generates MCQs to help students test their understanding.

### PDF Analyzer

Extracts text from uploaded PDF documents and sends relevant content to the AI.

### Ask AI

Provides a general-purpose AI question-answering interface.

### Progress

Displays learning activity and study progress.

### Study History

Maintains a record of previous study activities.

---

## 🎯 Objectives

The main objectives of AI Study Buddy Pro are:

* Make learning more interactive and accessible.
* Help students understand difficult topics.
* Reduce the time required to create study notes.
* Provide AI-assisted revision.
* Help students practice through quizzes.
* Make large study documents easier to understand.
* Provide a personalized AI-based learning experience.

---

## 🔮 Future Enhancements

Possible future improvements include:

* 🎤 Voice-based interaction
* 🔊 AI-generated audio explanations
* 📈 Advanced learning analytics
* 🧠 Personalized study plans
* 🏆 Gamification and achievement badges
* 📅 Study reminders
* 📚 Subject-wise learning dashboards
* 🎯 Adaptive quizzes based on performance
* 👨‍🎓 Student profiles and personalized recommendations
* 🌐 Multi-language support

---

## 💻 Project Type

**Project:** AI Study Buddy Pro
**Category:** Artificial Intelligence / Generative AI / EdTech
**Platform:** Web Application
**Framework:** Streamlit
**Language:** Python

---

## 👨‍💻 Author

**Vinayak Kumar**

B.Tech – Computer Science & Engineering (Data Science)

---

## ⭐ Acknowledgement

This project uses Google's Gemini AI technology to provide AI-powered educational assistance.

---

## 📜 License

This project is developed for educational and academic purposes.
