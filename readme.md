# HireUp Backend

A dual-service backend platform for **AI-powered job recruitment**, featuring automated quiz proctoring, video interview analysis, and intelligent question generation. Built with **Express (TypeScript) + MongoDB** for the core REST API and **Flask (Python/Quart) + WebSockets** for real-time AI processing.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    HireUp Backend                             │
│                                                              │
│  ┌─────────────────────────┐  ┌──────────────────────────┐   │
│  │   Express API (:8080)   │  │   Flask API (:5000)      │   │
│  │   ────────────────      │  │   ─────────────────      │   │
│  │   REST + MongoDB        │◄─┤   Quart server           │   │
│  │   JWT Auth              │  │   WebSocket streams      │   │
│  │   Swagger Docs          │  │   AI processing          │   │
│  └─────────────────────────┘  └──────────────────────────┘   │
│                                         │                    │
│                              ┌──────────┴──────────┐        │
│                              │  Socket.IO Servers   │        │
│                              │  (spawned per task)  │        │
│                              └──────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

## Features

### Core System (Express API)
- **Authentication & Authorization** — JWT-based with 3 roles: Applicant, Company, Admin
- **Applicant Management** — Registration, profile with skills, ID photo uploads
- **Company Management** — Registration, job posting, company profiles
- **Job Listings** — CRUD with skill requirements, salary, and multi-stage deadlines
- **Application Workflow** — Automatic progression through stages: Application → Quiz → Interview → Result
- **Quiz System** — MCQ quizzes with configurable pass ratios and time limits
- **Swagger Documentation** — Auto-generated OpenAPI docs at `/docs`

### AI/ML System (Flask API)
- **Proctored Quizzes** — Real-time eye-gaze tracking + lip movement detection via MediaPipe
- **Video Interviews** — Per-question video recording with AI analysis pipeline
- **Cheating Detection** — Eye gaze deviation, unnatural speaking patterns, voice activity analysis
- **Emotion Recognition** — MFCC feature extraction + SVM classification from voice
- **Answer Similarity** — FastText cosine similarity between applicant and expected answers
- **Speech-to-Text** — Google Speech Recognition for interview answer transcription
- **Question Generation** — NLP pipeline (spaCy + transformers + SVD) that generates QA pairs from PDF/text input
- **Text Summarization** — Transformer-based sentence embeddings with topic extraction via SVD

## Tech Stack

### Express API (`express_API/`)
- **Runtime:** Node.js with TypeScript
- **Framework:** Express 4
- **Database:** MongoDB (Mongoose 8)
- **Auth:** JSON Web Tokens + bcryptjs
- **Docs:** Swagger (swagger-jsdoc + swagger-ui-express)
- **Uploads:** Multer (memory storage)

### Flask API (`flask_API/`)
- **Framework:** Quart (async Flask) + Flask-SocketIO
- **ASGI Server:** Uvicorn / Hypercorn
- **Computer Vision:** MediaPipe, OpenCV
- **NLP:** spaCy, NLTK, Transformers, FastText
- **Audio:** Librosa, PyTorch (Silero VAD), SpeechRecognition
- **ML:** scikit-learn (SVM, TF-IDF, SVD), joblib

## Getting Started

### Prerequisites
- Node.js (>= 18)
- Python (>= 3.10)
- MongoDB instance
- FFmpeg installed and in PATH
- (Optional) CUDA-capable GPU for faster ML processing

### Setup

```powershell
# 1. Clone and install Express dependencies
cd express_API
npm install

# 2. Configure Express environment
# Edit express_API/.env with your settings:
#   DB_Host=localhost:27017
#   JWT_SECRET=your-secret
#   Python_Host=http://localhost:5000
#   VIDEOS_PATH=../flask_API

# 3. Set up Python virtual environment
cd ../flask_API
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 4. Configure Flask environment
# Edit flask_API/.env with your settings:
#   EXPRESS_SERVER_ADDRESS=http://localhost:8080
#   EXPRESS_SERVER_EMAIL=admin@example.com
#   EXPRESS_SERVER_PASSWORD=admin-password

# 5. Download required models
python -m spacy download en_core_web_sm
# Place FastText model (cc.en.300.bin) in flask_API/models/HireUp_Interview/
# Place Trained_Model_Dev/ in flask_API/models/HireUp_Question_Generation/

# 6. Run both services
cd ..
.\start.ps1 terminal
```

The `start.ps1` script launches both servers:
- Express API on **port 8080**
- Flask API on **port 5000**

Use `.\start.ps1` (default, background) or `.\start.ps1 terminal` (separate windows).

## API Overview

### Express Endpoints

| Endpoint | Auth | Description |
|---|---|---|
| `POST /account/logIn` | — | Login (returns JWT) |
| `POST /applicant/register` | — | Register as applicant |
| `POST /company/register` | — | Register as company |
| `GET /job/availableJobs` | — | Browse published jobs |
| `POST /application` | Applicant | Apply to a job |
| `GET /skill` | — | List all skills |
| `POST /skill` | Admin | Add skills |
| `POST /topic` | Admin | Add topic with Q&A |
| `POST /job/addJob` | Company | Create a job |
| `POST /quiz/addQuiz` | Company | Add MCQ quiz to job |
| `POST /job/questions` | Company | Add interview questions |

Full API documentation at `http://localhost:8080/docs` (Swagger UI).

### Flask Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/interview_stream` | POST | Start interview WebSocket stream |
| `/quiz_stream` | POST | Start quiz WebSocket stream |
| `/QG_socket` | POST | Start question generation socket |
| `/interview_calibration` | POST | Submit interview calibration images |
| `/quiz_calibration` | POST | Submit quiz calibration images |

## Application Workflow

1. **Company registers** → posts a job with skills, deadlines, quiz/interview requirements
2. **Company adds quiz questions** (MCQ) and/or **interview questions** (Q&A)
3. **Job is published** once both quiz (if required) and interview questions are set
4. **Applicant browses** → applies → application enters workflow
5. **Quiz stage** → applicant takes timed MCQ quiz → auto-graded → pass/fail
6. **Interview stage** → applicant connects via WebSocket → answers questions via video → AI analyzes each response
7. **Final Result** → company views ranked applicants with cheating metrics, emotion analysis, and similarity scores

## AI Processing Pipeline

### Quiz Proctoring
```
Calibration Images → Eye Gaze Tracking (MediaPipe) → Cheating Rate
Video Stream → Voice Activity Detection (Silero VAD) → Speaking Analysis
             → Lip Movement Tracking (MediaPipe) → Speaking Cheating
```

### Interview Analysis
```
Video per Question → Audio Extraction (FFmpeg) → Speech-to-Text (Google)
                   → Frame Extraction → Eye Cheating Detection
                   → Voice Emotion (MFCC + SVM) → Emotion Percentages
                   → Answer Similarity (FastText) → Similarity Score
```

### Question Generation
```
PDF/Text → Grammar Check → Sentence Embeddings (all-mpnet-base-v2)
        → SVD Topic Modeling → Sentence Selection
        → Template-based QG (SQuAD-trained) → QA Pairs
```

## Project Structure

```
HireUp-backend/
├── express_API/           # Node.js + TypeScript REST API
│   ├── src/
│   │   ├── accounts/      # Auth & account management
│   │   ├── applicants/    # Applicant profiles & registration
│   │   ├── applications/  # Job applications & workflow
│   │   ├── companies/     # Company profiles & registration
│   │   ├── jobs/          # Job postings & questions
│   │   ├── quizzes/       # MCQ quiz management
│   │   ├── skills/        # Skill management
│   │   ├── topics/        # Topic & Q&A management
│   │   ├── pythonAPI/     # Bridge to Flask API
│   │   ├── util/          # Auth middleware & error handling
│   │   ├── seeds/         # Admin & skills seed data
│   │   ├── app.ts         # Express app entry
│   │   └── router.ts      # Route aggregator
│   ├── .env               # Configuration
│   └── package.json
├── flask_API/             # Python AI microservice
│   ├── app/               # Quart server & socket processes
│   │   ├── main.py                       # REST endpoints
│   │   ├── interview_socket_process.py   # Per-interview socket
│   │   ├── quiz_socket_process.py        # Per-quiz socket
│   │   ├── QG_socket_process.py          # Question gen relay
│   │   └── QG_client_process.py          # QG Python client
│   ├── models/
│   │   ├── HireUp_Interview/
│   │   │   ├── Interview.py              # Interview pipeline
│   │   │   ├── Quiz.py                   # Quiz cheating detection
│   │   │   ├── Eye_Cheating.py           # MediaPipe gaze tracking
│   │   │   ├── lip_movements.py          # Lip movement analysis
│   │   │   ├── VAD.py                    # Voice activity detection
│   │   │   ├── Voice_Analysis.py         # Emotion recognition
│   │   │   ├── Similarity.py             # FastText similarity
│   │   │   ├── Frames_To_Durations.py    # Frame→time conversion
│   │   │   ├── svm_emotion_model.pkl     # Trained SVM model
│   │   │   └── cc.en.300.bin             # FastText vectors
│   │   └── HireUp_Question_Generation/
│   │       ├── QG.py                     # Template-based QG engine
│   │       ├── Text_Summarization.py     # PDF→summary pipeline
│   │       ├── topics_population.py      # Orchestration script
│   │       └── Trained_Model_Dev/        # Pre-trained QG model
│   ├── interview_video/    # Recorded interview videos
│   ├── quiz_video/         # Recorded quiz videos
│   ├── interview_calibration/  # Calibration images
│   └── quiz_calibration/       # Calibration images
├── start.ps1              # Launch script
└── .gitignore
```

