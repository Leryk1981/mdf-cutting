import axios from 'axios';

const API_BASE_URL = '/api';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    throw error;
  }
);

export const materialsService = {
  // Получить список всех материалов
  async getMaterials() {
    try {
      const response = await api.get('/materials');
      return response.data;
    } catch (error) {
      console.error('Error fetching materials:', error);
      throw error;
    }
  },

  // Получить материал по ID
  async getMaterialById(id) {
    try {
      const response = await api.get(`/materials/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching material:', error);
      throw error;
    }
  },

  // Создать новый материал
  async createMaterial(materialData) {
    try {
      const response = await api.post('/materials', materialData);
      return response.data;
    } catch (error) {
      console.error('Error creating material:', error);
      throw error;
    }
  },

  // Обновить материал
  async updateMaterial(id, materialData) {
    try {
      const response = await api.put(`/materials/${id}`, materialData);
      return response.data;
    } catch (error) {
      console.error('Error updating material:', error);
      throw error;
    }
  },

  // Удалить материал
  async deleteMaterial(id) {
    try {
      const response = await api.delete(`/materials/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting material:', error);
      throw error;
    }
  },

  // Загрузить файл материалов
  async uploadMaterialsFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/materials/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading materials file:', error);
      throw error;
    }
  },

  // Экспортировать материалы в CSV
  async exportMaterials(format = 'csv') {
    try {
      const response = await api.get(`/materials/export?format=${format}`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      console.error('Error exporting materials:', error);
      throw error;
    }
  },

  // Получить статистику по материалам
  async getMaterialsStats() {
    try {
      const response = await api.get('/materials/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching materials stats:', error);
      throw error;
    }
  },

  // Поиск материалов
  async searchMaterials(query) {
    try {
      const response = await api.get(`/materials/search?q=${encodeURIComponent(query)}`);
      return response.data;
    } catch (error) {
      console.error('Error searching materials:', error);
      throw error;
    }
  },

  // Получить категории материалов
  async getMaterialCategories() {
    try {
      const response = await api.get('/materials/categories');
      return response.data;
    } catch (error) {
      console.error('Error fetching material categories:', error);
      throw error;
    }
  },

  // Получить материалы по категории
  async getMaterialsByCategory(categoryId) {
    try {
      const response = await api.get(`/materials/category/${categoryId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching materials by category:', error);
      throw error;
    }
  },
};

export default materialsService; 