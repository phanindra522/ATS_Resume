# ATS Scoring Assistant

A sleek, modern, whitespace-heavy ATS (Applicant Tracking System) Scoring Assistant built with React, FastAPI, MongoDB, and ChromaDB.

## 🎨 Design Philosophy

Built following Swiss design principles:
- **Clean & Minimal**: White backgrounds with strategic use of whitespace
- **Typography-First**: Clear hierarchy using Inter/Helvetica Neue fonts
- **Functional Beauty**: Every element serves a purpose
- **Consistent Spacing**: Systematic use of spacing and proportions

## 🏗️ Architecture

### Frontend
- **React 18** with Vite for fast development
- **TailwindCSS** for utility-first styling
- **React Router** for navigation
- **Axios** for API communication

### Backend
- **FastAPI** for high-performance Python API
- **MongoDB** for structured data storage
- **ChromaDB** for vector search and similarity matching
- **Pydantic** for data validation

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- MongoDB
- ChromaDB

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📁 Project Structure

```
ATS_Resume/
├── frontend/          # React + Vite application
├── backend/           # FastAPI application
├── docs/             # Documentation
└── README.md         # This file
```

## 🎯 Features

- **User Authentication**: Secure login/signup system
- **Resume Upload**: Drag & drop PDF/DOCX support
- **Job Description Analysis**: AI-powered JD processing
- **Smart Scoring**: Vector-based resume-JD matching
- **Results Dashboard**: Clean, actionable insights
- **Responsive Design**: Works on all devices

## 🔧 Configuration

See individual README files in `frontend/` and `backend/` directories for detailed setup instructions.
