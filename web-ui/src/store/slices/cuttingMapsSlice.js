import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { cuttingMapsService } from '../../services/cuttingMapsService.js'

// Async thunks
export const fetchCuttingMaps = createAsyncThunk(
  'cuttingMaps/fetchCuttingMaps',
  async () => {
    console.log('Redux: fetchCuttingMaps вызван');
    const response = await cuttingMapsService.getCuttingMaps()
    console.log('Redux: fetchCuttingMaps получил ответ', response);
    return response
  }
)

export const fetchCuttingMapById = createAsyncThunk(
  'cuttingMaps/fetchCuttingMapById',
  async (id) => {
    const response = await cuttingMapsService.getCuttingMapById(id)
    return response
  }
)

export const createCuttingMap = createAsyncThunk(
  'cuttingMaps/createCuttingMap',
  async (cuttingMap) => {
    const response = await cuttingMapsService.createCuttingMap(cuttingMap)
    return response
  }
)

export const updateCuttingMap = createAsyncThunk(
  'cuttingMaps/updateCuttingMap',
  async ({ id, data }) => {
    const response = await cuttingMapsService.updateCuttingMap(id, data)
    return response
  }
)

export const deleteCuttingMap = createAsyncThunk(
  'cuttingMaps/deleteCuttingMap',
  async (id) => {
    await cuttingMapsService.deleteCuttingMap(id)
    return id
  }
)

export const searchCuttingMaps = createAsyncThunk(
  'cuttingMaps/searchCuttingMaps',
  async (query) => {
    const response = await cuttingMapsService.searchCuttingMaps(query)
    return response
  }
)

export const filterCuttingMaps = createAsyncThunk(
  'cuttingMaps/filterCuttingMaps',
  async (filters) => {
    const response = await cuttingMapsService.filterCuttingMaps(filters)
    return response
  }
)

export const getCuttingMapsStats = createAsyncThunk(
  'cuttingMaps/getCuttingMapsStats',
  async () => {
    const response = await cuttingMapsService.getCuttingMapsStats()
    return response
  }
)

export const duplicateCuttingMap = createAsyncThunk(
  'cuttingMaps/duplicateCuttingMap',
  async (id) => {
    const response = await cuttingMapsService.duplicateCuttingMap(id)
    return response
  }
)

export const downloadCuttingMapPDF = createAsyncThunk(
  'cuttingMaps/downloadCuttingMapPDF',
  async (id) => {
    const response = await cuttingMapsService.downloadCuttingMapPDF(id)
    return { id, data: response }
  }
)

export const downloadCuttingMapDXF = createAsyncThunk(
  'cuttingMaps/downloadCuttingMapDXF',
  async (id) => {
    const response = await cuttingMapsService.downloadCuttingMapDXF(id)
    return { id, data: response }
  }
)

export const exportCuttingMaps = createAsyncThunk(
  'cuttingMaps/exportCuttingMaps',
  async (format) => {
    const response = await cuttingMapsService.exportCuttingMaps(format)
    return { format, data: response }
  }
)

export const importCuttingMaps = createAsyncThunk(
  'cuttingMaps/importCuttingMaps',
  async (file) => {
    const response = await cuttingMapsService.importCuttingMaps(file)
    return response
  }
)

// Initial state
const initialState = {
  cuttingMaps: [],
  selectedCuttingMap: null,
  loading: false,
  error: null,
  stats: null,
  searchResults: [],
  filters: {
    status: 'all',
    material: 'all',
    dateFrom: null,
    dateTo: null,
  },
  viewMode: 'grid', // 'grid' или 'list'
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
  },
}

// Slice
const cuttingMapsSlice = createSlice({
  name: 'cuttingMaps',
  initialState,
  reducers: {
    setSelectedCuttingMap: (state, action) => {
      state.selectedCuttingMap = action.payload
    },
    clearSelectedCuttingMap: (state) => {
      state.selectedCuttingMap = null
    },
    setViewMode: (state, action) => {
      state.viewMode = action.payload
    },
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = initialState.filters
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },
    clearError: (state) => {
      state.error = null
    },
    clearSearchResults: (state) => {
      state.searchResults = []
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchCuttingMaps
      .addCase(fetchCuttingMaps.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchCuttingMaps.fulfilled, (state, action) => {
        console.log('Redux: fetchCuttingMaps.fulfilled вызван с данными:', action.payload);
        state.loading = false
        state.cuttingMaps = action.payload
        console.log('Redux: state.cuttingMaps обновлен:', state.cuttingMaps);
      })
      .addCase(fetchCuttingMaps.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // fetchCuttingMapById
      .addCase(fetchCuttingMapById.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchCuttingMapById.fulfilled, (state, action) => {
        state.loading = false
        state.selectedCuttingMap = action.payload
      })
      .addCase(fetchCuttingMapById.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // createCuttingMap
      .addCase(createCuttingMap.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(createCuttingMap.fulfilled, (state, action) => {
        state.loading = false
        state.cuttingMaps.push(action.payload)
      })
      .addCase(createCuttingMap.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // updateCuttingMap
      .addCase(updateCuttingMap.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(updateCuttingMap.fulfilled, (state, action) => {
        state.loading = false
        const index = state.cuttingMaps.findIndex(map => map.id === action.payload.id)
        if (index !== -1) {
          state.cuttingMaps[index] = action.payload
        }
        if (state.selectedCuttingMap?.id === action.payload.id) {
          state.selectedCuttingMap = action.payload
        }
      })
      .addCase(updateCuttingMap.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // deleteCuttingMap
      .addCase(deleteCuttingMap.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(deleteCuttingMap.fulfilled, (state, action) => {
        state.loading = false
        state.cuttingMaps = state.cuttingMaps.filter(map => map.id !== action.payload)
        if (state.selectedCuttingMap?.id === action.payload) {
          state.selectedCuttingMap = null
        }
      })
      .addCase(deleteCuttingMap.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // searchCuttingMaps
      .addCase(searchCuttingMaps.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(searchCuttingMaps.fulfilled, (state, action) => {
        state.loading = false
        state.searchResults = action.payload
      })
      .addCase(searchCuttingMaps.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // filterCuttingMaps
      .addCase(filterCuttingMaps.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(filterCuttingMaps.fulfilled, (state, action) => {
        state.loading = false
        state.cuttingMaps = action.payload
      })
      .addCase(filterCuttingMaps.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // getCuttingMapsStats
      .addCase(getCuttingMapsStats.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(getCuttingMapsStats.fulfilled, (state, action) => {
        state.loading = false
        state.stats = action.payload
      })
      .addCase(getCuttingMapsStats.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // duplicateCuttingMap
      .addCase(duplicateCuttingMap.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(duplicateCuttingMap.fulfilled, (state, action) => {
        state.loading = false
        state.cuttingMaps.push(action.payload)
      })
      .addCase(duplicateCuttingMap.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
      
      // importCuttingMaps
      .addCase(importCuttingMaps.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(importCuttingMaps.fulfilled, (state, action) => {
        state.loading = false
        state.cuttingMaps = [...state.cuttingMaps, ...action.payload]
      })
      .addCase(importCuttingMaps.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message
      })
  },
})

// Actions
export const {
  setSelectedCuttingMap,
  clearSelectedCuttingMap,
  setViewMode,
  setFilters,
  clearFilters,
  setPagination,
  clearError,
  clearSearchResults,
} = cuttingMapsSlice.actions

// Selectors
export const selectCuttingMaps = (state) => state.cuttingMaps.cuttingMaps
export const selectSelectedCuttingMap = (state) => state.cuttingMaps.selectedCuttingMap
export const selectCuttingMapsLoading = (state) => state.cuttingMaps.loading
export const selectCuttingMapsError = (state) => state.cuttingMaps.error
export const selectCuttingMapsStats = (state) => state.cuttingMaps.stats
export const selectCuttingMapsSearchResults = (state) => state.cuttingMaps.searchResults
export const selectCuttingMapsFilters = (state) => state.cuttingMaps.filters
export const selectCuttingMapsViewMode = (state) => state.cuttingMaps.viewMode
export const selectCuttingMapsPagination = (state) => state.cuttingMaps.pagination

// Filtered cutting maps
export const selectFilteredCuttingMaps = (state) => {
  const { cuttingMaps, filters } = state.cuttingMaps
  
  return cuttingMaps.filter(map => {
    if (filters.status !== 'all' && map.status !== filters.status) {
      return false
    }
    if (filters.material !== 'all' && map.material !== filters.material) {
      return false
    }
    if (filters.dateFrom && new Date(map.date) < new Date(filters.dateFrom)) {
      return false
    }
    if (filters.dateTo && new Date(map.date) > new Date(filters.dateTo)) {
      return false
    }
    return true
  })
}

export default cuttingMapsSlice.reducer 