import axios from 'axios'

const API_BASE_URL = '/api'

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const cuttingMapsService = {
  // Получить все карты раскроя
  getCuttingMaps: async () => {
    console.log('Service: getCuttingMaps вызван');
    const response = await api.get('/cutting-maps')
    console.log('Service: getCuttingMaps получил ответ', response.data);
    return response.data
  },

  // Получить карту раскроя по ID
  getCuttingMapById: async (id) => {
    const response = await api.get(`/cutting-maps/${id}`)
    return response.data
  },

  // Создать новую карту раскроя
  createCuttingMap: async (cuttingMap) => {
    const response = await api.post('/cutting-maps', cuttingMap)
    return response.data
  },

  // Обновить карту раскроя
  updateCuttingMap: async (id, cuttingMap) => {
    const response = await api.put(`/cutting-maps/${id}`, cuttingMap)
    return response.data
  },

  // Удалить карту раскроя
  deleteCuttingMap: async (id) => {
    const response = await api.delete(`/cutting-maps/${id}`)
    return response.data
  },

  // Получить изображение карты раскроя
  getCuttingMapImage: async (id) => {
    const response = await api.get(`/cutting-maps/${id}/image`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Скачать карту раскроя в PDF
  downloadCuttingMapPDF: async (id) => {
    const response = await api.get(`/cutting-maps/${id}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Скачать карту раскроя в DXF
  downloadCuttingMapDXF: async (id) => {
    const response = await api.get(`/cutting-maps/${id}/dxf`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Получить статистику карт раскроя
  getCuttingMapsStats: async () => {
    const response = await api.get('/cutting-maps/stats')
    return response.data
  },

  // Поиск карт раскроя
  searchCuttingMaps: async (query) => {
    const response = await api.get('/cutting-maps/search', {
      params: { q: query },
    })
    return response.data
  },

  // Фильтрация карт раскроя
  filterCuttingMaps: async (filters) => {
    const response = await api.get('/cutting-maps/filter', {
      params: filters,
    })
    return response.data
  },

  // Получить карты раскроя по проекту
  getCuttingMapsByProject: async (projectId) => {
    const response = await api.get(`/projects/${projectId}/cutting-maps`)
    return response.data
  },

  // Получить карты раскроя по материалу
  getCuttingMapsByMaterial: async (materialId) => {
    const response = await api.get(`/materials/${materialId}/cutting-maps`)
    return response.data
  },

  // Экспорт карт раскроя
  exportCuttingMaps: async (format = 'json') => {
    const response = await api.get('/cutting-maps/export', {
      params: { format },
      responseType: 'blob',
    })
    return response.data
  },

  // Импорт карт раскроя
  importCuttingMaps: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/cutting-maps/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Дублировать карту раскроя
  duplicateCuttingMap: async (id) => {
    const response = await api.post(`/cutting-maps/${id}/duplicate`)
    return response.data
  },

  // Поделиться картой раскроя
  shareCuttingMap: async (id, shareData) => {
    const response = await api.post(`/cutting-maps/${id}/share`, shareData)
    return response.data
  },

  // Получить версии карты раскроя
  getCuttingMapVersions: async (id) => {
    const response = await api.get(`/cutting-maps/${id}/versions`)
    return response.data
  },

  // Восстановить версию карты раскроя
  restoreCuttingMapVersion: async (id, versionId) => {
    const response = await api.post(`/cutting-maps/${id}/versions/${versionId}/restore`)
    return response.data
  },

  // Получить комментарии к карте раскроя
  getCuttingMapComments: async (id) => {
    const response = await api.get(`/cutting-maps/${id}/comments`)
    return response.data
  },

  // Добавить комментарий к карте раскроя
  addCuttingMapComment: async (id, comment) => {
    const response = await api.post(`/cutting-maps/${id}/comments`, comment)
    return response.data
  },

  // Удалить комментарий к карте раскроя
  deleteCuttingMapComment: async (id, commentId) => {
    const response = await api.delete(`/cutting-maps/${id}/comments/${commentId}`)
    return response.data
  },
}

export default cuttingMapsService 