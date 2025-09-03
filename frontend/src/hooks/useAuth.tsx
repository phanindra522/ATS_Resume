import { useState, useEffect, createContext, useContext } from 'react'
import { api } from '../lib/api'

interface User {
  _id: string
  email: string
  full_name: string
  created_at: string
  updated_at: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        const response = await api.get('/auth/me')
        setUser(response.data)
      } catch (error) {
        localStorage.removeItem('token')
        delete api.defaults.headers.common['Authorization']
      }
    }
    setLoading(false)
  }

  const login = async (email: string, password: string): Promise<void> => {
    try {
      const response = await api.post('/auth/login', { email, password })
      const { access_token } = response.data
      
      localStorage.setItem('token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      const userResponse = await api.get('/auth/me')
      setUser(userResponse.data)
    } catch (error: any) {
      // Improved error handling
      let errorMessage = 'Login failed'
      
      if (error.response) {
        // Server responded with error status
        if (error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail
        } else if (error.response.status === 401) {
          errorMessage = 'Incorrect email or password'
        } else if (error.response.status === 400) {
          errorMessage = 'Invalid request data'
        } else if (error.response.status >= 500) {
          errorMessage = 'Server error. Please try again later.'
        }
      } else if (error.request) {
        // Request was made but no response received
        errorMessage = 'No response from server. Please check your connection.'
      } else {
        // Something else happened
        errorMessage = error.message || 'An unexpected error occurred'
      }
      
      throw new Error(errorMessage)
    }
  }

  const signup = async (email: string, password: string, fullName: string): Promise<void> => {
    try {
      await api.post('/auth/signup', { email, password, full_name: fullName })
    } catch (error: any) {
      // Improved error handling for signup
      let errorMessage = 'Signup failed'
      
      if (error.response) {
        if (error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail
        } else if (error.response.status === 400) {
          errorMessage = 'Invalid signup data'
        } else if (error.response.status === 409) {
          errorMessage = 'Email already registered'
        } else if (error.response.status >= 500) {
          errorMessage = 'Server error. Please try again later.'
        }
      } else if (error.request) {
        errorMessage = 'No response from server. Please check your connection.'
      } else {
        errorMessage = error.message || 'An unexpected error occurred'
      }
      
      throw new Error(errorMessage)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
  }

  const value = {
    user,
    loading,
    login,
    signup,
    logout
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}