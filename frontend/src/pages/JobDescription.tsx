import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Building, MapPin, DollarSign, Users, Target, Upload, File, X } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

const JobDescription = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    description: '',
    requirements: '',
    skills: '',
    experience_level: '',
    location: '',
    salary_range: ''
  })
  const [loading, setLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [extractedText, setExtractedText] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please upload a PDF, TXT, or DOCX file')
      return
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB')
      return
    }

    setUploadedFile(file)
    
    // Show loading toast
    const loadingToast = toast.loading('Extracting job information from file...')
    
    try {
      // Call the extraction endpoint
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/jobs/extract', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      const extractedData = response.data
      setExtractedText(extractedData.extracted_text || '')
      
      // Auto-fill form fields with extracted data
      setFormData(prev => ({
        ...prev,
        title: extractedData.title || prev.title,
        company: extractedData.company || prev.company,
        description: extractedData.description || prev.description,
        requirements: extractedData.requirements ? extractedData.requirements.join('\n') : prev.requirements,
        skills: extractedData.skills ? extractedData.skills.join(', ') : prev.skills,
        experience_level: extractedData.experience_level || prev.experience_level,
        location: extractedData.location || prev.location,
        salary_range: extractedData.salary_range || prev.salary_range,
      }))
      
      toast.dismiss(loadingToast)
      toast.success('Job information extracted and form filled automatically!')
      
    } catch (error: any) {
      toast.dismiss(loadingToast)
      toast.error(error.response?.data?.detail || 'Failed to extract job information')
      
      // Fallback: If it's a text file, read the content locally
      if (file.type === 'text/plain') {
        const reader = new FileReader()
        reader.onload = (e) => {
          const text = e.target?.result as string
          setExtractedText(text)
          // Auto-fill description if it's empty
          if (!formData.description) {
            setFormData(prev => ({ ...prev, description: text }))
          }
        }
        reader.readAsText(file)
      }
    }
  }, [formData])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    multiple: false
  })

  const removeFile = () => {
    setUploadedFile(null)
    setExtractedText('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title || !formData.description) {
      toast.error('Please fill in the required fields')
      return
    }

    setLoading(true)
    try {
      let jobData = {
        ...formData,
        requirements: formData.requirements.split('\n').filter(req => req.trim()),
        skills: formData.skills.split(',').map(skill => skill.trim()).filter(skill => skill)
      }

      // If there's an uploaded file, send it along with the job data
      if (uploadedFile) {
        const formDataToSend = new FormData()
        formDataToSend.append('file', uploadedFile)
        
        // Add job data as JSON string
        Object.keys(jobData).forEach(key => {
          if (jobData[key as keyof typeof jobData]) {
            formDataToSend.append(key, Array.isArray(jobData[key as keyof typeof jobData]) 
              ? JSON.stringify(jobData[key as keyof typeof jobData])
              : String(jobData[key as keyof typeof jobData])
            )
          }
        })

        // Use the file upload endpoint
        await api.post('/jobs/upload', formDataToSend, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      } else {
        // Regular job creation without file
        await api.post('/jobs', jobData)
      }

      toast.success('Job description saved successfully!')
      navigate('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save job description')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text-primary mb-4">
            Add Job Description
          </h1>
          <p className="text-xl text-text-secondary">
            Create detailed job postings to match with candidate resumes
          </p>
        </div>

        {/* File Upload Section */}
        <div className="card p-6 mb-8">
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            📄 Upload Job Description File (Optional)
          </h3>
          <p className="text-sm text-text-secondary mb-4">
            Upload a PDF, TXT, or DOCX file to automatically extract and fill job details in the form below
          </p>
          
          {!uploadedFile ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-lg font-medium text-text-primary mb-2">
                {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
              </p>
              <p className="text-sm text-text-secondary">
                or click to browse files
              </p>
              <p className="text-xs text-text-muted mt-2">
                Supports PDF, TXT, DOCX (max 10MB)
              </p>
            </div>
          ) : (
            <div className="border rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <File className="h-8 w-8 text-primary-500" />
                  <div>
                    <p className="font-medium text-text-primary">{uploadedFile.name}</p>
                    <p className="text-sm text-text-secondary">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={removeFile}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              {extractedText && (
                <div className="mt-3 p-3 bg-white rounded border">
                  <p className="text-sm text-text-secondary mb-2">Extracted text preview:</p>
                  <p className="text-sm text-text-primary line-clamp-3">
                    {extractedText.substring(0, 200)}...
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Form */}
        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-text-primary mb-2">
                  Job Title *
                </label>
                <div className="relative">
                  <Target className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted" size={20} />
                  <input
                    id="title"
                    name="title"
                    type="text"
                    required
                    value={formData.title}
                    onChange={handleChange}
                    className="input-field pl-10"
                    placeholder="e.g., Senior Software Engineer"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="company" className="block text-sm font-medium text-text-primary mb-2">
                  Company
                </label>
                <div className="relative">
                  <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted" size={20} />
                  <input
                    id="company"
                    name="company"
                    type="text"
                    value={formData.company}
                    onChange={handleChange}
                    className="input-field pl-10"
                    placeholder="e.g., Tech Corp Inc."
                  />
                </div>
              </div>

              <div>
                <label htmlFor="location" className="block text-sm font-medium text-text-primary mb-2">
                  Location
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted" size={20} />
                  <input
                    id="location"
                    name="location"
                    type="text"
                    value={formData.location}
                    onChange={handleChange}
                    className="input-field pl-10"
                    placeholder="e.g., San Francisco, CA or Remote"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="salary_range" className="block text-sm font-medium text-text-primary mb-2">
                  Salary Range
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted" size={20} />
                  <input
                    id="salary_range"
                    name="salary_range"
                    type="text"
                    value={formData.salary_range}
                    onChange={handleChange}
                    className="input-field pl-10"
                    placeholder="e.g., $80,000 - $120,000"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="experience_level" className="block text-sm font-medium text-text-primary mb-2">
                  Experience Level
                </label>
                <select
                  id="experience_level"
                  name="experience_level"
                  value={formData.experience_level}
                  onChange={handleChange}
                  className="input-field"
                >
                  <option value="">Select experience level</option>
                  <option value="Entry Level">Entry Level (0-2 years)</option>
                  <option value="Mid Level">Mid Level (3-5 years)</option>
                  <option value="Senior Level">Senior Level (6-10 years)</option>
                  <option value="Lead/Manager">Lead/Manager (10+ years)</option>
                </select>
              </div>

              <div>
                <label htmlFor="skills" className="block text-sm font-medium text-text-primary mb-2">
                  Required Skills
                </label>
                <div className="relative">
                  <Users className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted" size={20} />
                  <input
                    id="skills"
                    name="skills"
                    type="text"
                    value={formData.skills}
                    onChange={handleChange}
                    className="input-field pl-10"
                    placeholder="e.g., Python, React, AWS (comma-separated)"
                  />
                </div>
              </div>
            </div>

            {/* Job Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-text-primary mb-2">
                Job Description *
              </label>
              <textarea
                id="description"
                name="description"
                rows={6}
                required
                value={formData.description}
                onChange={handleChange}
                className="input-field"
                placeholder="Provide a detailed description of the role, responsibilities, and what the candidate will be doing..."
              />
            </div>

            {/* Requirements */}
            <div>
              <label htmlFor="requirements" className="block text-sm font-medium text-text-primary mb-2">
                Requirements & Qualifications
              </label>
              <textarea
                id="requirements"
                name="requirements"
                rows={4}
                value={formData.requirements}
                onChange={handleChange}
                className="input-field"
                placeholder="List key requirements and qualifications (one per line)..."
              />
              <p className="text-sm text-text-muted mt-1">
                Enter each requirement on a new line for better formatting
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex items-center"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                ) : (
                  <FileText className="mr-2" size={18} />
                )}
                {uploadedFile ? 'Save & Extract from File' : 'Save & Analyze'}
              </button>
            </div>
          </form>
        </div>

        {/* Tips */}
        <div className="card p-6 mt-8">
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            💡 Tips for better candidate matching
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-text-secondary">
            <div className="flex items-start space-x-2">
              <FileText className="text-primary-500 mt-0.5" size={16} />
              <span>Be specific about required skills and technologies</span>
            </div>
            <div className="flex items-start space-x-2">
              <FileText className="text-primary-500 mt-0.5" size={16} />
              <span>Include both technical and soft skills requirements</span>
            </div>
            <div className="flex items-start space-x-2">
              <FileText className="text-primary-500 mt-0.5" size={16} />
              <span>Provide clear job responsibilities and expectations</span>
            </div>
            <div className="flex items-start space-x-2">
              <FileText className="text-primary-500 mt-0.5" size={16} />
              <span>Use industry-standard terminology for better matching</span>
            </div>
            <div className="flex items-start space-x-2">
              <FileText className="text-primary-500 mt-0.5" size={16} />
              <span>Upload PDF/DOCX files to automatically extract and fill form fields</span>
            </div>
            <div className="flex items-start space-x-2">
              <FileText className="text-primary-500 mt-0.5" size={16} />
              <span>Review extracted information and refine as needed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default JobDescription
