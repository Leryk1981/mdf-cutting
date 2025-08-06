import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { materialsService } from '../../services/materialsService.js'

// Async thunks
export const fetchMaterials = createAsyncThunk(
  'materials/fetchMaterials',
  async () => {
    const response = await materialsService.getMaterials()
    return response
  }
)

export const addMaterial = createAsyncThunk(
  'materials/addMaterial',
  async (material) => {
    const response = await materialsService.addMaterial(material)
    return response
  }
)

export const createMaterial = createAsyncThunk(
  'materials/createMaterial',
  async (material) => {
    const response = await materialsService.createMaterial(material)
    return response
  }
)

export const updateMaterial = createAsyncThunk(
  'materials/updateMaterial',
  async ({ id, data }) => {
    const response = await materialsService.updateMaterial(id, data)
    return response
  }
)

export const deleteMaterial = createAsyncThunk(
  'materials/deleteMaterial',
  async (id) => {
    await materialsService.deleteMaterial(id)
    return id
  }
)

export const uploadMaterialsFile = createAsyncThunk(
  'materials/uploadMaterialsFile',
  async (file) => {
    const response = await materialsService.uploadMaterialsFile(file)
    return response
  }
)

const initialState = {
  materials: [],
  selectedMaterial: null,
  status: 'idle',
  error: null,
}

const materialsSlice = createSlice({
  name: 'materials',
  initialState,
  reducers: {
    setSelectedMaterial: (state, action) => {
      state.selectedMaterial = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch materials
      .addCase(fetchMaterials.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchMaterials.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.materials = action.payload
      })
      .addCase(fetchMaterials.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      // Add material
      .addCase(addMaterial.fulfilled, (state, action) => {
        state.materials.push(action.payload)
      })
      .addCase(addMaterial.rejected, (state, action) => {
        state.error = action.error.message
      })
      // Create material
      .addCase(createMaterial.fulfilled, (state, action) => {
        state.materials.push(action.payload)
      })
      .addCase(createMaterial.rejected, (state, action) => {
        state.error = action.error.message
      })
      // Update material
      .addCase(updateMaterial.fulfilled, (state, action) => {
        const index = state.materials.findIndex(m => m.id === action.payload.id)
        if (index !== -1) {
          state.materials[index] = action.payload
        }
      })
      .addCase(updateMaterial.rejected, (state, action) => {
        state.error = action.error.message
      })
      // Delete material
      .addCase(deleteMaterial.fulfilled, (state, action) => {
        state.materials = state.materials.filter(m => m.id !== action.payload)
      })
      .addCase(deleteMaterial.rejected, (state, action) => {
        state.error = action.error.message
      })
      // Upload materials file
      .addCase(uploadMaterialsFile.fulfilled, (state, action) => {
        state.materials = action.payload.materials || []
      })
      .addCase(uploadMaterialsFile.rejected, (state, action) => {
        state.error = action.error.message
      })
  },
})

export const {
  setSelectedMaterial,
  clearError,
} = materialsSlice.actions

export default materialsSlice.reducer 