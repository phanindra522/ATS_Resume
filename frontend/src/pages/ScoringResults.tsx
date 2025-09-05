import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { 
  Trophy, 
  Star, 
  CheckCircle, 
  XCircle, 
  TrendingUp, 
  FileText,
  Briefcase,
  Calendar,
  MapPin,
  DollarSign,
  Users,
  Target,
  Trash2
} from 'lucide-react'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface ScoredResume {
  _id: string
  title: string
  filename: string
  score: number
  match_percentage: number
  skills_match: string[]
  missing_skills: string[]
  created_at: string
}

interface Job {
  _id: string
  title: string
  company: string
  description: string
  requirements: string[]
  skills: string[]
  experience_level: string
  location: string
  salary_range: string
}

interface ScoringResult {
  job: Job
  scored_resumes: ScoredResume[]
  total_resumes: number
}

const ScoringResults = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const [scoringResult, setScoringResult] = useState<ScoringResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedResume, setSelectedResume] = useState<ScoredResume | null>(null)
  const [deletingResume, setDeletingResume] = useState<string | null>(null)

  useEffect(() => {
    if (jobId) {
      fetchScoringResults(jobId)
    } else {
      // If no jobId provided, try to get the first available job
      fetchFirstJobAndScore()
    }
  }, [jobId])

  const fetchFirstJobAndScore = async () => {
    try {
      setLoading(true)
      // Get all jobs and use the first one
      const response = await api.get('/jobs')
      const jobs = response.data
      
      if (jobs && jobs.length > 0) {
        const firstJob = jobs[0]
        await fetchScoringResults(firstJob._id)
      } else {
        toast.error('No jobs found. Please create a job description first.')
        setLoading(false)
      }
    } catch (error: any) {
      toast.error('Failed to fetch jobs: ' + (error.response?.data?.detail || error.message))
      setLoading(false)
    }
  }

  const fetchScoringResults = async (id: string) => {
    try {
      const response = await api.post(`/scoring/score/${id}`)
      setScoringResult(response.data)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to fetch scoring results')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-success'
    if (score >= 0.6) return 'text-warning'
    return 'text-error'
  }

  const getScoreBadge = (score: number) => {
    if (score >= 0.8) return 'bg-success-100 text-success-700'
    if (score >= 0.6) return 'bg-warning-100 text-warning-700'
    return 'bg-error-100 text-error-700'
  }

  const handleDeleteResume = async (resumeId: string, resumeTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${resumeTitle}"? This action cannot be undone.`)) {
      return
    }

    try {
      setDeletingResume(resumeId)
      await api.delete(`/resumes/${resumeId}`)
      
      // Remove from local state
      if (scoringResult) {
        const updatedResumes = scoringResult.scored_resumes.filter(resume => resume._id !== resumeId)
        setScoringResult({
          ...scoringResult,
          scored_resumes: updatedResumes,
          total_resumes: updatedResumes.length
        })
        
        // Clear selection if deleted resume was selected
        if (selectedResume && selectedResume._id === resumeId) {
          setSelectedResume(null)
        }
      }
      
      toast.success('Resume deleted successfully!')
    } catch (error: any) {
      console.error('Error deleting resume:', error)
      toast.error('Failed to delete resume. Please try again.')
    } finally {
      setDeletingResume(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (!scoringResult) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-text-primary mb-4">No scoring results found</h2>
          <p className="text-text-secondary mb-6">Please run a scoring analysis first</p>
          <Link to="/dashboard" className="btn-primary">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const { job, scored_resumes, total_resumes } = scoringResult

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-text-primary mb-2">
                Scoring Results
              </h1>
              <p className="text-xl text-text-secondary">
                {total_resumes} candidates scored for this position
              </p>
            </div>
            <Link to="/dashboard" className="btn-secondary">
              Back to Dashboard
            </Link>
          </div>

          {/* Job Summary */}
          <div className="card p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-text-primary mb-2">
                  {job.title}
                </h2>
                <p className="text-lg text-text-secondary mb-4">
                  {job.company}
                </p>
              </div>
              <div className="text-right">
                <div className="flex items-center space-x-4 text-sm text-text-secondary">
                  {job.location && (
                    <div className="flex items-center space-x-1">
                      <MapPin size={16} />
                      <span>{job.location}</span>
                    </div>
                  )}
                  {job.experience_level && (
                    <div className="flex items-center space-x-1">
                      <Users size={16} />
                      <span>{job.experience_level}</span>
                    </div>
                  )}
                  {job.salary_range && (
                    <div className="flex items-center space-x-1">
                      <DollarSign size={16} />
                      <span>{job.salary_range}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-text-primary mb-2">Required Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {job.skills.map((skill, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-primary-100 text-primary-700 text-sm rounded-full"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-text-primary mb-2">Requirements</h3>
                <ul className="space-y-1 text-sm text-text-secondary">
                  {job.requirements.slice(0, 3).map((req, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <Target size={14} className="text-primary-500 mt-0.5" />
                      <span>{req}</span>
                    </li>
                  ))}
                  {job.requirements.length > 3 && (
                    <li className="text-text-muted text-xs">
                      +{job.requirements.length - 3} more requirements
                    </li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Results Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Candidate List */}
          <div className="lg:col-span-2">
            <div className="card p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-text-primary">
                  Candidate Rankings
                </h3>
                <div className="flex items-center space-x-2 text-sm text-text-secondary">
                  <TrendingUp size={16} />
                  <span>Sorted by score</span>
                </div>
              </div>

              <div className="space-y-4">
                {scored_resumes.map((resume, index) => (
                  <div
                    key={resume._id}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${
                      selectedResume?._id === resume._id
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-surface-100 hover:border-primary-200 hover:bg-surface-50'
                    }`}
                    onClick={() => setSelectedResume(resume)}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        {index === 0 && (
                          <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                            <Trophy className="text-yellow-600" size={20} />
                          </div>
                        )}
                        <div>
                          <h4 className="font-semibold text-text-primary">
                            {resume.title || resume.filename}
                          </h4>
                          <p className="text-sm text-text-secondary">
                            {resume.filename}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${getScoreColor(resume.score)}`}>
                            {resume.match_percentage}%
                          </div>
                          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreBadge(resume.score)}`}>
                            Score: {resume.score.toFixed(3)}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteResume(resume._id, resume.title || resume.filename)
                          }}
                          disabled={deletingResume === resume._id}
                          className="p-2 text-text-muted hover:text-red-500 transition-colors disabled:opacity-50"
                          title="Delete resume"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    {/* Skills Match */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="font-medium text-success-600 mb-2 flex items-center">
                          <CheckCircle size={16} className="mr-1" />
                          Matched Skills ({resume.skills_match.length})
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {resume.skills_match.slice(0, 3).map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-success-100 text-success-700 text-xs rounded"
                            >
                              {skill}
                            </span>
                          ))}
                          {resume.skills_match.length > 3 && (
                            <span className="text-text-muted text-xs">
                              +{resume.skills_match.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                      <div>
                        <p className="font-medium text-error-600 mb-2 flex items-center">
                          <XCircle size={16} className="mr-1" />
                          Missing Skills ({resume.missing_skills.length})
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {resume.missing_skills.slice(0, 3).map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-error-100 text-error-700 text-xs rounded"
                            >
                              {skill}
                            </span>
                          ))}
                          {resume.missing_skills.length > 3 && (
                            <span className="text-text-muted text-xs">
                              +{resume.missing_skills.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Candidate Details */}
          <div className="lg:col-span-1">
            <div className="card p-6 sticky top-24">
              {selectedResume ? (
                <div>
                  <h3 className="text-lg font-semibold text-text-primary mb-4">
                    Candidate Details
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-text-primary mb-2">
                        {selectedResume.title || selectedResume.filename}
                      </h4>
                      <p className="text-sm text-text-secondary">
                        {selectedResume.filename}
                      </p>
                    </div>

                    <div className="p-4 bg-surface-50 rounded-lg">
                      <div className="text-center mb-3">
                        <div className={`text-3xl font-bold ${getScoreColor(selectedResume.score)} mb-1`}>
                          {selectedResume.match_percentage}%
                        </div>
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreBadge(selectedResume.score)}`}>
                          Match Score
                        </div>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-medium text-text-primary mb-2">Skills Analysis</h5>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-success-600 mb-1">
                            Matched Skills ({selectedResume.skills_match.length})
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {selectedResume.skills_match.map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-success-100 text-success-700 text-xs rounded"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-error-600 mb-1">
                            Missing Skills ({selectedResume.missing_skills.length})
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {selectedResume.missing_skills.map((skill, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-error-100 text-error-700 text-xs rounded"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-surface-200">
                      <p className="text-xs text-text-muted">
                        Uploaded: {new Date(selectedResume.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="mx-auto text-text-muted mb-3" size={48} />
                  <p className="text-text-secondary">
                    Select a candidate to view detailed analysis
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mt-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-6 text-center">
              <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Trophy className="text-primary-600" size={24} />
              </div>
              <p className="text-2xl font-bold text-text-primary">
                {scored_resumes[0]?.match_percentage || 0}%
              </p>
              <p className="text-sm text-text-secondary">Top Score</p>
            </div>

            <div className="card p-6 text-center">
              <div className="w-12 h-12 bg-success-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="text-success-600" size={24} />
              </div>
              <p className="text-2xl font-bold text-text-primary">
                {scored_resumes.filter(r => r.score >= 0.6).length}
              </p>
              <p className="text-sm text-text-secondary">Good Matches</p>
            </div>

            <div className="card p-6 text-center">
              <div className="w-12 h-12 bg-warning-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Star className="text-warning-600" size={24} />
              </div>
              <p className="text-2xl font-bold text-text-primary">
                {scored_resumes.filter(r => r.score >= 0.8).length}
              </p>
              <p className="text-sm text-text-secondary">Excellent Matches</p>
            </div>

            <div className="card p-6 text-center">
              <div className="w-12 h-12 bg-surface-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Users className="text-text-muted" size={24} />
              </div>
              <p className="text-2xl font-bold text-text-primary">
                {total_resumes}
              </p>
              <p className="text-sm text-text-secondary">Total Candidates</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScoringResults
