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
- Python 3.12+ (recommended)
- MongoDB (optional - uses in-memory database by default)
- ChromaDB (installed automatically)

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
**Frontend will be available at:** http://localhost:5173

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main.py
```
**Backend will be available at:** http://localhost:8000
**API Documentation:** http://localhost:8000/docs

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

## ✅ Current Status

**Application is fully operational and running!**

- ✅ **Backend**: FastAPI server running on Python 3.12.4
- ✅ **Frontend**: React + Vite development server running
- ✅ **Dependencies**: All packages updated to latest secure versions
- ✅ **Database**: Persistent in-memory database with ChromaDB
- ✅ **Security**: All vulnerabilities fixed, JWT authentication ready
- ✅ **Git**: Repository cleaned and properly configured

## 🔧 Configuration

See individual README files in `frontend/` and `backend/` directories for detailed setup instructions.

## 📋 Recent Updates

- **Python 3.12**: Upgraded from Python 3.13 for better compatibility
- **Dependencies**: Updated all packages to latest secure versions
- **Security**: Fixed npm audit vulnerabilities
- **Git**: Cleaned up repository, removed unnecessary tracked files
- **Database**: Using persistent in-memory database for development
