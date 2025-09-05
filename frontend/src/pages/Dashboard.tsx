import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { 
  Upload, 
  FileText, 
  BarChart3, 
  Clock, 
  File, 
  Plus,
  TrendingUp,
  Users,
  Briefcase,
  Trash2
} from 'lucide-react'
import { api } from '../lib/api'

interface Resume {
  _id: string
  title: string
  filename: string
  created_at: string
  user_name?: string
  user_email?: string
}

interface Job {
  _id: string
  title: string
  company: string
  created_at: string
  user_name?: string
  user_email?: string
}

const Dashboard = () => {
  const { user } = useAuth()
  const [resumes, setResumes] = useState<Resume[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [deletingResume, setDeletingResume] = useState<string | null>(null)
  const [deletingJob, setDeletingJob] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [resumesRes, jobsRes] = await Promise.all([
        api.get('/resumes'),
        api.get('/jobs')
      ])
      setResumes(resumesRes.data)
      setJobs(jobsRes.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const handleDeleteResume = async (resumeId: string, resumeTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${resumeTitle}"? This action cannot be undone.`)) {
      return
    }

    try {
      setDeletingResume(resumeId)
      await api.delete(`/resumes/${resumeId}`)
      
      // Remove from local state
      setResumes(resumes.filter(resume => resume._id !== resumeId))
      
      // Show success message
      alert('Resume deleted successfully!')
    } catch (error: any) {
      console.error('Error deleting resume:', error)
      alert('Failed to delete resume. Please try again.')
    } finally {
      setDeletingResume(null)
    }
  }

  const handleDeleteJob = async (jobId: string, jobTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${jobTitle}"? This action cannot be undone.`)) {
      return
    }

    try {
      setDeletingJob(jobId)
      await api.delete(`/jobs/${jobId}`)
      
      // Remove from local state
      setJobs(jobs.filter(job => job._id !== jobId))
      
      // Show success message
      alert('Job deleted successfully!')
    } catch (error: any) {
      console.error('Error deleting job:', error)
      alert('Failed to delete job. Please try again.')
    } finally {
      setDeletingJob(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-text-primary mb-2">
            Welcome back, {user?.full_name}!
          </h1>
          <p className="text-xl text-text-secondary">
            Here's what's happening with the Global ATS Pool - all recruiters can see all resumes and jobs
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-secondary mb-1">
                  Total Resumes (Global Pool)
                </p>
                <p className="text-3xl font-bold text-text-primary">
                  {resumes.length}
                </p>
                <p className="text-xs text-text-muted mt-1">
                  From all recruiters
                </p>
              </div>
              <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                <File className="text-primary-600" size={24} />
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-secondary mb-1">
                  Active Jobs (Global Pool)
                </p>
                <p className="text-3xl font-bold text-text-primary">
                  {jobs.length}
                </p>
                <p className="text-xs text-text-muted mt-1">
                  From all recruiters
                </p>
              </div>
              <div className="w-12 h-12 bg-success-100 rounded-xl flex items-center justify-center">
                <Briefcase className="text-success-600" size={24} />
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-secondary mb-1">
                  Recent Activity
                </p>
                <p className="text-3xl font-bold text-text-primary">
                  {resumes.length + jobs.length > 0 ? 'Active' : 'None'}
                </p>
              </div>
              <div className="w-12 h-12 bg-warning-100 rounded-xl flex items-center justify-center">
                <TrendingUp className="text-warning-600" size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-text-primary mb-6">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Link
              to="/upload"
              className="card p-8 hover:shadow-medium transition-all duration-200 group"
            >
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center group-hover:bg-primary-200 transition-colors duration-200">
                  <Upload className="text-primary-600" size={28} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-text-primary mb-2">
                    Upload Resume
                  </h3>
                  <p className="text-text-secondary">
                    Add new resumes to your collection for scoring
                  </p>
                </div>
              </div>
            </Link>

            <Link
              to="/job-description"
              className="card p-8 hover:shadow-medium transition-all duration-200 group"
            >
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-success-100 rounded-2xl flex items-center justify-center group-hover:bg-success-200 transition-colors duration-200">
                  <FileText className="text-success-600" size={28} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-text-primary mb-2">
                    Add Job Description
                  </h3>
                  <p className="text-text-secondary">
                    Create new job postings for candidate matching
                  </p>
                </div>
              </div>
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Resumes */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-text-primary">
                Recent Resumes (Global Pool)
              </h3>
              <Link
                to="/upload"
                className="text-primary-500 hover:text-primary-600 font-medium text-sm"
              >
                View all
              </Link>
            </div>
            
            {resumes.length === 0 ? (
              <div className="text-center py-8">
                <File className="mx-auto text-text-muted mb-3" size={48} />
                <p className="text-text-secondary mb-4">No resumes uploaded yet</p>
                <Link to="/upload" className="btn-primary">
                  <Plus className="mr-2" size={18} />
                  Upload First Resume
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {resumes.slice(0, 5).map((resume) => (
                  <div key={resume._id} className="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <File className="text-text-muted" size={20} />
                      <div>
                        <p className="font-medium text-text-primary">{resume.title}</p>
                        <p className="text-sm text-text-secondary">{resume.filename}</p>
                        {resume.user_name && (
                          <p className="text-xs text-text-muted">
                            By: {resume.user_name}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2 text-sm text-text-secondary">
                        <Clock size={16} />
                        <span>{formatDate(resume.created_at)}</span>
                      </div>
                      <button
                        onClick={() => handleDeleteResume(resume._id, resume.title)}
                        disabled={deletingResume === resume._id}
                        className="p-1 text-text-muted hover:text-red-500 transition-colors disabled:opacity-50"
                        title="Delete resume"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Jobs */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-text-primary">
                Recent Jobs (Global Pool)
              </h3>
              <Link
                to="/job-description"
                className="text-primary-500 hover:text-primary-600 font-medium text-sm"
              >
                View all
              </Link>
            </div>
            
            {jobs.length === 0 ? (
              <div className="text-center py-8">
                <Briefcase className="mx-auto text-text-muted mb-3" size={48} />
                <p className="text-text-secondary mb-4">No job descriptions yet</p>
                <Link to="/job-description" className="btn-primary">
                  <Plus className="mr-2" size={18} />
                  Add First Job
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.slice(0, 5).map((job) => (
                  <div key={job._id} className="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Briefcase className="text-text-muted" size={20} />
                      <div>
                        <p className="font-medium text-text-primary">{job.title}</p>
                        <p className="text-sm text-text-secondary">{job.company}</p>
                        {job.user_name && (
                          <p className="text-xs text-text-muted">
                            By: {job.user_name}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2 text-sm text-text-secondary">
                        <Clock size={16} />
                        <span>{formatDate(job.created_at)}</span>
                      </div>
                      <button
                        onClick={() => handleDeleteJob(job._id, job.title)}
                        disabled={deletingJob === job._id}
                        className="p-1 text-text-muted hover:text-red-500 transition-colors disabled:opacity-50"
                        title="Delete job"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Get Started Section */}
        {resumes.length === 0 && jobs.length === 0 && (
          <div className="mt-16 text-center">
            <div className="card p-12 max-w-2xl mx-auto">
              <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <BarChart3 className="text-primary-600" size={36} />
              </div>
              <h3 className="text-2xl font-bold text-text-primary mb-4">
                Ready to get started?
              </h3>
              <p className="text-text-secondary mb-8 text-lg">
                Begin by uploading resumes and creating job descriptions to start scoring candidates
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/upload" className="btn-primary">
                  <Upload className="mr-2" size={18} />
                  Upload Resume
                </Link>
                <Link to="/job-description" className="btn-secondary">
                  <FileText className="mr-2" size={18} />
                  Add Job Description
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
