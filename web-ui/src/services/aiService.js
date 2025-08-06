import axios from 'axios'

const API_BASE_URL = '/api'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Longer timeout for AI operations
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
    console.error('AI API Error:', error)
    return Promise.reject(error)
  }
)

export const aiService = {
  // Run AI optimization
  async runOptimization(params) {
    const response = await api.post('/ai/optimize', params)
    return response
  },

  // Run leftover optimization
  async runLeftoverOptimization(params) {
    const response = await api.post('/ai/optimize-leftovers', params)
    return response
  },

  // Submit feedback
  async submitFeedback(feedback) {
    const response = await api.post('/ai/feedback', feedback)
    return response
  },

  // Get AI suggestions
  async getSuggestions(optimizationId) {
    const response = await api.get(`/ai/suggestions/${optimizationId}`)
    return response
  },

  // Apply suggestion
  async applySuggestion(suggestionId) {
    const response = await api.post(`/ai/suggestions/${suggestionId}/apply`)
    return response
  },

  // Reject suggestion
  async rejectSuggestion(suggestionId) {
    const response = await api.post(`/ai/suggestions/${suggestionId}/reject`)
    return response
  },

  // Get AI statistics
  async getAIStats() {
    const response = await api.get('/ai/stats')
    return response
  },

  // Get AI effectiveness metrics
  async getEffectivenessMetrics() {
    const response = await api.get('/ai/effectiveness')
    return response
  },

  // Get AI training data
  async getTrainingData() {
    const response = await api.get('/ai/training-data')
    return response
  },

  // Update AI model
  async updateAIModel(modelData) {
    const response = await api.post('/ai/update-model', modelData)
    return response
  },

  // Get AI configuration
  async getAIConfig() {
    const response = await api.get('/ai/config')
    return response
  },

  // Update AI configuration
  async updateAIConfig(config) {
    const response = await api.put('/ai/config', config)
    return response
  },

  // Test AI connection
  async testConnection() {
    const response = await api.get('/ai/test-connection')
    return response
  },

  // Get AI model status
  async getModelStatus() {
    const response = await api.get('/ai/model-status')
    return response
  },
} 