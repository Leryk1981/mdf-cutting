import axios from 'axios'

const API_BASE_URL = '/api'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const cuttingService = {
  // Upload details file
  async uploadDetailsFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/upload-details', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response
  },

  // Upload materials file
  async uploadMaterialsFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/upload-materials', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response
  },

  // Run cutting optimization
  async runOptimization(params) {
    const response = await api.post('/optimize-cutting', params)
    return response
  },

  // Get optimization history
  async getOptimizationHistory() {
    const response = await api.get('/optimization-history')
    return response
  },

  // Get optimization result by ID
  async getOptimizationResult(id) {
    const response = await api.get(`/optimization-result/${id}`)
    return response
  },

  // Download DXF file
  async downloadDXF(optimizationId) {
    const response = await api.get(`/download-dxf/${optimizationId}`, {
      responseType: 'blob',
    })
    return response
  },

  // Download PDF report
  async downloadPDF(optimizationId) {
    const response = await api.get(`/download-pdf/${optimizationId}`, {
      responseType: 'blob',
    })
    return response
  },

  // Get optimization statistics
  async getOptimizationStats() {
    const response = await api.get('/optimization-stats')
    return response
  },
} 