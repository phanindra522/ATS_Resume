import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface UploadedResume {
  _id: string
  title: string
  filename: string
  file_size: number
  created_at: string
}

const ResumeUpload = () => {
  const [uploadedResumes, setUploadedResumes] = useState<UploadedResume[]>([])
  const [uploading, setUploading] = useState(false)
  const [title, setTitle] = useState('')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    setUploading(true)
    
    try {
      for (const file of acceptedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        if (title.trim()) {
          formData.append('title', title.trim())
        }

        const response = await api.post('/resumes/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        setUploadedResumes(prev => [response.data, ...prev])
        toast.success(`${file.name} uploaded successfully!`)
      }
      
      setTitle('')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [title])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true
  })

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text-primary mb-4">
            Upload Resumes
          </h1>
          <p className="text-xl text-text-secondary">
            Upload PDF or DOCX resumes to start scoring candidates
          </p>
        </div>

        {/* Upload Area */}
        <div className="card p-8 mb-8">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="text-primary-600" size={32} />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-2">
              Drop your resumes here
            </h2>
            <p className="text-text-secondary">
              or click to browse files
            </p>
          </div>

          {/* Title Input */}
          <div className="max-w-md mx-auto mb-6">
            <label htmlFor="title" className="block text-sm font-medium text-text-primary mb-2">
              Resume Title (Optional)
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title for the resume"
              className="input-field"
            />
          </div>

          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-surface-200 hover:border-primary-300 hover:bg-surface-50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <Upload className="mx-auto text-text-muted" size={48} />
              <div>
                <p className="text-lg font-medium text-text-primary mb-2">
                  {isDragActive ? 'Drop the files here' : 'Drag & drop files here'}
                </p>
                <p className="text-text-secondary">
                  Supports PDF and DOCX files up to 10MB
                </p>
              </div>
              <div className="text-sm text-text-muted">
                <p>• PDF files (.pdf)</p>
                <p>• Word documents (.docx)</p>
                <p>• Maximum file size: 10MB</p>
              </div>
            </div>
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="mt-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-2"></div>
              <p className="text-text-secondary">Uploading resumes...</p>
            </div>
          )}
        </div>

        {/* Uploaded Resumes */}
        {uploadedResumes.length > 0 && (
          <div className="card p-6">
            <h3 className="text-xl font-semibold text-text-primary mb-6">
              Uploaded Resumes ({uploadedResumes.length})
            </h3>
            
            <div className="space-y-4">
              {uploadedResumes.map((resume) => (
                <div key={resume._id} className="flex items-center justify-between p-4 bg-surface-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
                      <CheckCircle className="text-success-600" size={20} />
                    </div>
                    <div>
                      <p className="font-medium text-text-primary">{resume.title || resume.filename}</p>
                      <p className="text-sm text-text-secondary">{resume.filename}</p>
                      <div className="flex items-center space-x-4 text-xs text-text-muted mt-1">
                        <span>{formatFileSize(resume.file_size)}</span>
                        <span>•</span>
                        <span>{formatDate(resume.created_at)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 bg-success-100 text-success-700 text-xs font-medium rounded-full">
                      Uploaded
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tips */}
        <div className="card p-6 mt-8">
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            💡 Tips for better results
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-text-secondary">
            <div className="flex items-start space-x-2">
              <CheckCircle className="text-success-500 mt-0.5" size={16} />
              <span>Ensure resumes are in PDF or DOCX format for best text extraction</span>
            </div>
            <div className="flex items-start space-x-2">
              <CheckCircle className="text-success-500 mt-0.5" size={16} />
              <span>Use clear, well-formatted resumes for accurate scoring</span>
            </div>
            <div className="flex items-start space-x-2">
              <CheckCircle className="text-success-500 mt-0.5" size={16} />
              <span>Include relevant skills and experience in your resumes</span>
            </div>
            <div className="flex items-start space-x-2">
              <CheckCircle className="text-success-500 mt-0.5" size={16} />
              <span>Keep file sizes under 10MB for faster processing</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResumeUpload
