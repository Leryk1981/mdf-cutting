import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { aiService } from '../../services/aiService.js'

// Async thunks
export const runAIOptimization = createAsyncThunk(
  'ai/runOptimization',
  async (params) => {
    const response = await aiService.runOptimization(params)
    return response
  }
)

export const runLeftoverOptimization = createAsyncThunk(
  'ai/runLeftoverOptimization',
  async (params) => {
    const response = await aiService.runLeftoverOptimization(params)
    return response
  }
)

export const submitFeedback = createAsyncThunk(
  'ai/submitFeedback',
  async (feedback) => {
    const response = await aiService.submitFeedback(feedback)
    return response
  }
)

const initialState = {
  aiParams: {
    aiAssistanceEnabled: true,
    confidenceThreshold: 0.7,
    autoApplyCorrections: false,
  },
  optimizationResult: null,
  suggestions: [],
  isOptimizing: false,
  error: null,
  status: 'idle',
  feedback: {
    satisfactionRating: 0,
    acceptedCorrections: [],
    rejectedCorrections: [],
    comments: '',
  },
}

const aiSlice = createSlice({
  name: 'ai',
  initialState,
  reducers: {
    updateAIParams: (state, action) => {
      state.aiParams = { ...state.aiParams, ...action.payload }
    },
    setSuggestions: (state, action) => {
      state.suggestions = action.payload
    },
    applySuggestion: (state, action) => {
      const suggestionId = action.payload
      state.suggestions = state.suggestions.filter(s => s.id !== suggestionId)
    },
    rejectSuggestion: (state, action) => {
      const suggestionId = action.payload
      state.suggestions = state.suggestions.filter(s => s.id !== suggestionId)
    },
    updateFeedback: (state, action) => {
      state.feedback = { ...state.feedback, ...action.payload }
    },
    clearOptimizationResult: (state) => {
      state.optimizationResult = null
      state.suggestions = []
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Run AI optimization
      .addCase(runAIOptimization.pending, (state) => {
        state.isOptimizing = true
        state.error = null
      })
      .addCase(runAIOptimization.fulfilled, (state, action) => {
        state.isOptimizing = false
        state.optimizationResult = action.payload
        state.suggestions = action.payload.ai_enhancements || []
      })
      .addCase(runAIOptimization.rejected, (state, action) => {
        state.isOptimizing = false
        state.error = action.error.message
      })
      // Run leftover optimization
      .addCase(runLeftoverOptimization.pending, (state) => {
        state.isOptimizing = true
        state.error = null
      })
      .addCase(runLeftoverOptimization.fulfilled, (state, action) => {
        state.isOptimizing = false
        state.optimizationResult = action.payload
      })
      .addCase(runLeftoverOptimization.rejected, (state, action) => {
        state.isOptimizing = false
        state.error = action.error.message
      })
      // Submit feedback
      .addCase(submitFeedback.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(submitFeedback.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.feedback = {
          satisfactionRating: 0,
          acceptedCorrections: [],
          rejectedCorrections: [],
          comments: '',
        }
      })
      .addCase(submitFeedback.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
  },
})

export const {
  updateAIParams,
  setSuggestions,
  applySuggestion,
  rejectSuggestion,
  updateFeedback,
  clearOptimizationResult,
  clearError,
} = aiSlice.actions

export default aiSlice.reducer 