# ATS Scoring Assistant - Backend

FastAPI backend for the ATS Scoring Assistant with MongoDB and ChromaDB integration.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB running locally or accessible
- ChromaDB (will be installed automatically)

### Installation

1. **Clone and navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Setup**
```bash
cp env.example .env
# Edit .env with your configuration
```

5. **Start the server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

- `MONGODB_URL`: MongoDB connection string
- `MONGODB_DB`: Database name
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB persistence directory
- `SECRET_KEY`: JWT secret key for authentication
- `MAX_FILE_SIZE`: Maximum file upload size in bytes
- `UPLOAD_DIR`: Directory for uploaded files
- `MODEL_NAME`: Sentence transformer model name

### Database Setup

1. **MongoDB**: Ensure MongoDB is running on localhost:27017
2. **ChromaDB**: Will be automatically initialized on first run

## 📁 Project Structure

```
backend/
├── app/
│   ├── core/           # Configuration and security
│   ├── models/         # Pydantic data models
│   ├── routers/        # API endpoints
│   └── database.py     # Database connection
├── main.py             # FastAPI application entry point
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🛠️ API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Resumes
- `POST /api/resumes/upload` - Upload resume file
- `GET /api/resumes/` - Get user's resumes
- `GET /api/resumes/{id}` - Get specific resume
- `PUT /api/resumes/{id}` - Update resume
- `DELETE /api/resumes/{id}` - Delete resume

### Jobs
- `POST /api/jobs/` - Create job description
- `GET /api/jobs/` - Get user's jobs
- `GET /api/jobs/{id}` - Get specific job
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job

### Scoring
- `POST /api/scoring/score/{job_id}` - Score resumes for a job
- `GET /api/scoring/results/{job_id}` - Get scoring results
- `GET /api/scoring/history` - Get scoring history

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- File upload validation
- User authorization checks

## 📊 AI/ML Features

- Resume text extraction (PDF/DOCX)
- Sentence embeddings with SentenceTransformers
- Vector similarity scoring
- Skills extraction and matching

## 🚀 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Formatting
```bash
# Install formatting tools
pip install black isort

# Format code
black .
isort .
```

## 📝 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check connection string in .env

2. **ChromaDB Error**
   - Ensure write permissions for chroma_db directory
   - Delete chroma_db folder to reset

3. **File Upload Error**
   - Check upload directory permissions
   - Verify file size limits

4. **Model Download Error**
   - Ensure internet connection for first run
   - Check disk space for model files

## 📞 Support

For issues and questions, please check the main project README or create an issue in the repository.
