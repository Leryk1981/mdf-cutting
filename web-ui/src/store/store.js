import { configureStore } from '@reduxjs/toolkit'
import cuttingReducer from './slices/cuttingSlice.js'
import materialsReducer from './slices/materialsSlice.js'
import aiReducer from './slices/aiSlice.js'
import uiReducer from './slices/uiSlice.js'

export const store = configureStore({
  reducer: {
    cutting: cuttingReducer,
    materials: materialsReducer,
    ai: aiReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
}) 