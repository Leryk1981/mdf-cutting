import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { cuttingService } from '../../services/cuttingService.js'

// Async thunks
export const uploadDetailsFile = createAsyncThunk(
  'cutting/uploadDetailsFile',
  async (file) => {
    const response = await cuttingService.uploadDetailsFile(file)
    return response
  }
)

export const uploadMaterialsFile = createAsyncThunk(
  'cutting/uploadMaterialsFile',
  async (file) => {
    const response = await cuttingService.uploadMaterialsFile(file)
    return response
  }
)

export const runCuttingOptimization = createAsyncThunk(
  'cutting/runOptimization',
  async (params) => {
    const response = await cuttingService.runOptimization(params)
    return response
  }
)

const initialState = {
  detailsFile: null,
  materialsFile: null,
  optimizationParams: {
    kerf: 3.0,
    margin: 5.0,
    optimizationLevel: 'balanced',
  },
  optimizationResult: null,
  isOptimizing: false,
  error: null,
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
}

const cuttingSlice = createSlice({
  name: 'cutting',
  initialState,
  reducers: {
    setDetailsFile: (state, action) => {
      state.detailsFile = action.payload
    },
    setMaterialsFile: (state, action) => {
      state.materialsFile = action.payload
    },
    updateOptimizationParams: (state, action) => {
      state.optimizationParams = { ...state.optimizationParams, ...action.payload }
    },
    clearOptimizationResult: (state) => {
      state.optimizationResult = null
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Upload details file
      .addCase(uploadDetailsFile.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(uploadDetailsFile.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.detailsFile = action.payload
      })
      .addCase(uploadDetailsFile.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      // Upload materials file
      .addCase(uploadMaterialsFile.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(uploadMaterialsFile.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.materialsFile = action.payload
      })
      .addCase(uploadMaterialsFile.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      // Run optimization
      .addCase(runCuttingOptimization.pending, (state) => {
        state.isOptimizing = true
        state.error = null
      })
      .addCase(runCuttingOptimization.fulfilled, (state, action) => {
        state.isOptimizing = false
        state.optimizationResult = action.payload
      })
      .addCase(runCuttingOptimization.rejected, (state, action) => {
        state.isOptimizing = false
        state.error = action.error.message
      })
  },
})

export const {
  setDetailsFile,
  setMaterialsFile,
  updateOptimizationParams,
  clearOptimizationResult,
  clearError,
} = cuttingSlice.actions

export default cuttingSlice.reducer 