# ATS Scoring Assistant - Complete Setup Guide

This guide will walk you through setting up the complete ATS Scoring Assistant application.

## 🎯 What We're Building

A sleek, modern, whitespace-heavy ATS (Applicant Tracking System) Scoring Assistant with:
- **Frontend**: React + Vite + TailwindCSS (Swiss design principles)
- **Backend**: FastAPI + Python
- **Databases**: MongoDB + ChromaDB
- **AI/ML**: Sentence transformers for resume-job matching

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites Check
```bash
# Check Python version (3.9+)
python --version

# Check Node.js version (18+)
node --version

# Check npm version
npm --version
```

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env

# Start MongoDB (if not running)
# On Windows: Start MongoDB service
# On macOS: brew services start mongodb-community
# On Linux: sudo systemctl start mongod

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
# Open new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔧 Detailed Setup

### Backend Configuration

#### MongoDB Setup
1. **Install MongoDB**
   - **Windows**: Download from [MongoDB website](https://www.mongodb.com/try/download/community)
   - **macOS**: `brew install mongodb-community`
   - **Linux**: `sudo apt install mongodb`

2. **Start MongoDB**
   - **Windows**: MongoDB service should start automatically
   - **macOS**: `brew services start mongodb-community`
   - **Linux**: `sudo systemctl start mongod`

3. **Verify Connection**
   ```bash
   # Test MongoDB connection
   mongosh
   # Should connect to localhost:27017
   ```

#### Environment Configuration
Edit `backend/.env`:
```env
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=ats_scoring

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads

# AI/ML
MODEL_NAME=all-MiniLM-L6-v2
```

#### Python Dependencies
The backend will automatically install:
- **FastAPI**: Web framework
- **MongoDB**: Database driver
- **ChromaDB**: Vector database
- **SentenceTransformers**: AI/ML models
- **PyMuPDF**: PDF text extraction
- **python-docx**: Word document processing

### Frontend Configuration

#### Node.js Dependencies
The frontend will automatically install:
- **React 18**: UI library
- **Vite**: Build tool
- **TailwindCSS**: Styling framework
- **React Router**: Navigation
- **Axios**: HTTP client
- **Lucide React**: Icons

#### Environment Variables
Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api
```

## 🎨 Design System

### Swiss Design Principles
- **Clean & Minimal**: White backgrounds with strategic whitespace
- **Typography-First**: Inter font family for clear hierarchy
- **Functional Beauty**: Every element serves a purpose
- **Consistent Spacing**: Systematic use of spacing and proportions

### Color Palette
- **Primary**: Blue (#2563EB)
- **Surface**: Light gray (#FAFAFA)
- **Text**: Black (#111111), Secondary (#6B7280)
- **Success**: Green (#059669)
- **Warning**: Orange (#D97706)
- **Error**: Red (#DC2626)

## 📱 Application Features

### 1. User Authentication
- Secure signup/login system
- JWT token management
- Password strength validation
- Protected routes

### 2. Resume Management
- Drag & drop file upload
- PDF/DOCX support
- Text extraction and processing
- File validation and error handling

### 3. Job Description Creation
- Comprehensive job forms
- Skills and requirements input
- Experience level selection
- Form validation

### 4. AI-Powered Scoring
- Sentence transformer embeddings
- Vector similarity scoring
- Skills matching analysis
- Candidate ranking

### 5. Results Dashboard
- Visual score representation
- Skills match breakdown
- Candidate comparison
- Export capabilities

## 🚀 Development Workflow

### Backend Development
```bash
cd backend

# Start development server
uvicorn main:app --reload

# API documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)

# Test endpoints
curl http://localhost:8000/health
```

### Frontend Development
```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Management
```bash
# MongoDB shell
mongosh

# Switch to database
use ats_scoring

# View collections
show collections

# View documents
db.users.find()
db.resumes.find()
db.jobs.find()
```

## 🧪 Testing the Application

### 1. Create Account
- Navigate to http://localhost:5173
- Click "Sign up"
- Create account with strong password

### 2. Upload Resume
- Go to "Upload Resume" page
- Drag & drop PDF/DOCX file
- Add optional title
- Verify upload success

### 3. Create Job Description
- Go to "Job Description" page
- Fill out comprehensive job form
- Include skills and requirements
- Save job description

### 4. Run Scoring
- Go to "Scoring Results" page
- Select job to score against
- View AI-powered candidate rankings
- Analyze skills matches

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues
1. **MongoDB Connection Error**
   ```bash
   # Check if MongoDB is running
   # Windows: Services > MongoDB
   # macOS: brew services list
   # Linux: sudo systemctl status mongod
   ```

2. **Port Already in Use**
   ```bash
   # Change port in main.py or use different port
   uvicorn main:app --reload --port 8001
   ```

3. **Model Download Error**
   ```bash
   # Clear cache and retry
   rm -rf ~/.cache/torch
   pip install --force-reinstall sentence-transformers
   ```

#### Frontend Issues
1. **Port Already in Use**
   ```bash
   # Change port in vite.config.ts
   server: { port: 5174 }
   ```

2. **API Connection Error**
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify API endpoints

3. **Build Errors**
   ```bash
   # Clear dependencies and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

### Performance Issues
1. **Slow Model Loading**
   - First run downloads AI models (~100MB)
   - Subsequent runs use cached models

2. **Large File Uploads**
   - Check file size limits (10MB default)
   - Optimize PDF/DOCX files

3. **Database Performance**
   - Ensure MongoDB indexes are created
   - Monitor database size and queries

## 🔒 Security Considerations

### Production Deployment
1. **Change Default Secrets**
   - Update SECRET_KEY in .env
   - Use strong, unique passwords
   - Enable HTTPS

2. **Database Security**
   - Use MongoDB authentication
   - Restrict network access
   - Regular backups

3. **File Upload Security**
   - Validate file types
   - Scan for malware
   - Limit file sizes

4. **API Security**
   - Rate limiting
   - Input validation
   - CORS configuration

## 📊 Monitoring and Logging

### Backend Logs
```bash
# View FastAPI logs
uvicorn main:app --reload --log-level debug

# Check application logs
tail -f logs/app.log
```

### Database Monitoring
```bash
# MongoDB status
mongosh --eval "db.serverStatus()"

# Database statistics
mongosh --eval "db.stats()"
```

### Performance Metrics
- API response times
- Database query performance
- File upload speeds
- Memory usage

## 🚀 Deployment

### Backend Deployment
1. **Docker** (Recommended)
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Cloud Platforms**
   - **Heroku**: Easy deployment with add-ons
   - **AWS**: EC2 + RDS + S3
   - **Google Cloud**: App Engine + Cloud SQL
   - **Azure**: App Service + Cosmos DB

### Frontend Deployment
1. **Build for Production**
   ```bash
   npm run build
   ```

2. **Deploy Options**
   - **Netlify**: Drag & drop deployment
   - **Vercel**: Git-based deployment
   - **AWS S3**: Static website hosting
   - **GitHub Pages**: Free hosting

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)

### Learning Resources
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)
- [React Hooks](https://react.dev/reference/react/hooks)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [Vector Similarity](https://www.sbert.net/)

### Community
- [FastAPI Discord](https://discord.gg/VQjSKB8)
- [React Community](https://reactjs.org/community/support.html)
- [MongoDB Forums](https://www.mongodb.com/community/forums/)

## 🎉 Congratulations!

You've successfully set up a complete ATS Scoring Assistant! The application features:

✅ **Modern Tech Stack**: React + FastAPI + MongoDB + ChromaDB  
✅ **Beautiful UI**: Swiss design principles with TailwindCSS  
✅ **AI/ML Integration**: Sentence transformers for smart matching  
✅ **Security**: JWT authentication and input validation  
✅ **Scalability**: Async backend with proper database design  
✅ **User Experience**: Intuitive interface with responsive design  

### Next Steps
1. **Customize**: Modify colors, branding, and features
2. **Extend**: Add new scoring algorithms and metrics
3. **Deploy**: Move to production environment
4. **Monitor**: Set up logging and performance tracking
5. **Scale**: Optimize for larger datasets and users

Happy coding! 🚀
