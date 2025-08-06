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
    console.error('DXF Viewer API Error:', error)
    return Promise.reject(error)
  }
)

export const dxfViewerService = {
  // Загрузить DXF файл
  async loadDxfFile(mapId) {
    try {
      console.log('Загружаем DXF файл для mapId:', mapId)
      const response = await api.get(`/cutting-maps/${mapId}/dxf`, {
        responseType: 'arraybuffer'
      })
      console.log('DXF файл загружен, размер:', response.data.byteLength)
      return response.data
    } catch (error) {
      console.error('Ошибка загрузки DXF файла:', error)
      throw error
    }
  },

  // Парсить DXF файл и извлечь геометрию
  parseDxfContent(dxfContent) {
    try {
      console.log('Начинаем парсинг DXF контента')
      const text = new TextDecoder().decode(dxfContent)
      
      const lines = text.split('\n')
      console.log('Количество строк в DXF:', lines.length)
      
      const entities = []
      let currentEntity = null
      let inEntity = false
      let inEntitiesSection = false
      let currentLayer = null
      let vertexCount = 0
      let vertices = []
      let expectingY = false
      let lastX = null

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim()
        
        // Проверяем, находимся ли мы в секции ENTITIES
        if (line === '2' && i + 1 < lines.length && lines[i + 1].trim() === 'ENTITIES') {
          inEntitiesSection = true
          console.log('Найдена секция ENTITIES')
          continue
        }
        
        if (!inEntitiesSection) continue
        
        if (line === '0' && i + 1 < lines.length) {
          const entityType = lines[i + 1].trim()
          if (entityType === 'LWPOLYLINE') {
            // Сохраняем предыдущую сущность
            if (currentEntity && (currentLayer === '0' || currentLayer === 'work_area' || currentLayer === 'details')) {
              currentEntity.vertices = vertices
              entities.push(currentEntity)
              console.log(`Добавлена сущность: слой ${currentLayer}, вершин: ${vertices.length}`)
            }
            
            // Начинаем новую сущность
            currentEntity = { type: entityType, data: {}, vertices: [] }
            currentLayer = null
            vertexCount = 0
            vertices = []
            expectingY = false
            lastX = null
            inEntity = true
            console.log('Начата новая LWPOLYLINE')
          }
        }

        if (inEntity && currentEntity) {
          // Извлекаем слой
          if (line === '8' && i + 1 < lines.length) {
            currentLayer = lines[i + 1].trim()
            currentEntity.data.layer = currentLayer
            console.log(`Слой: ${currentLayer}`)
          }
          // Количество вершин для LWPOLYLINE
          else if (line === '90' && i + 1 < lines.length) {
            vertexCount = parseInt(lines[i + 1])
            currentEntity.data.vertexCount = vertexCount
            console.log(`Ожидается вершин: ${vertexCount}`)
          }
          // Координата X
          else if (line === '10' && i + 1 < lines.length) {
            lastX = parseFloat(lines[i + 1])
            expectingY = true
            console.log(`X координата: ${lastX}`)
          }
          // Координата Y
          else if (line === '20' && i + 1 < lines.length && expectingY && lastX !== null) {
            const y = parseFloat(lines[i + 1])
            vertices.push({ x: lastX, y: y })
            expectingY = false
            console.log(`Y координата: ${y}, добавлена вершина: (${lastX}, ${y})`)
            lastX = null
          }
        }
      }

      // Добавляем последнюю сущность
      if (currentEntity && (currentLayer === '0' || currentLayer === 'work_area' || currentLayer === 'details')) {
        currentEntity.vertices = vertices
        entities.push(currentEntity)
        console.log(`Добавлена последняя сущность: слой ${currentLayer}, вершин: ${vertices.length}`)
      }

      console.log('Найдено entities для отображения:', entities.length)
      entities.forEach(entity => {
        console.log(`Слой: ${entity.data.layer}, вершин: ${entity.vertices.length}`)
        if (entity.vertices.length > 0) {
          console.log('Первые вершины:', entity.vertices.slice(0, 3))
        }
      })
      
      return entities
    } catch (error) {
      console.error('Ошибка парсинга DXF файла:', error)
      return []
    }
  },

  // Конвертировать DXF в SVG
  convertDxfToSvg(entities, width = 800, height = 600) {
    try {
      console.log('Начинаем конвертацию в SVG, entities:', entities.length)
      
      // Найти границы по всем вершинам
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
      
      entities.forEach(entity => {
        entity.vertices.forEach(vertex => {
          minX = Math.min(minX, vertex.x)
          maxX = Math.max(maxX, vertex.x)
          minY = Math.min(minY, vertex.y)
          maxY = Math.max(maxY, vertex.y)
        })
      })

      console.log('Границы:', { minX, minY, maxX, maxY })
      
      const dx = maxX - minX
      const dy = maxY - minY
      
      // Оптимальный масштаб для отображения всей карты
      const scale = Math.min(width / dx, height / dy) * 0.8
      
      console.log('Размеры:', { dx, dy, scale })
      console.log('Коэффициент масштабирования:', Math.min(width / dx, height / dy))
      console.log('Детальные границы:', {
        minX: minX,
        minY: minY,
        maxX: maxX,
        maxY: maxY,
        dx: dx,
        dy: dy
      })

      // Создать SVG с правильным позиционированием
      let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}">`
      
      // Центрируем и масштабируем содержимое
      const centerX = (minX + maxX) / 2
      const centerY = (minY + maxY) / 2
      
      console.log('Центр:', { centerX, centerY })
      console.log('SVG размеры:', { width, height })
      console.log('Трансформация:', {
        translateX: width/2,
        translateY: height/2,
        scale: scale,
        translateCenterX: -centerX,
        translateCenterY: -centerY
      })
      
      svg += `<g transform="translate(${width/2}, ${height/2}) scale(${scale}) translate(${-centerX}, ${-centerY})">`

      entities.forEach(entity => {
        if (entity.type === 'LWPOLYLINE' && entity.vertices.length > 0) {
          // Определяем цвет и толщину линии в зависимости от слоя
          let strokeColor = 'black'
          let strokeWidth = '1'
          
          if (entity.data.layer === '0' || entity.data.layer === 'work_area') {
            strokeColor = '#2E86AB' // Синий для границ листа
            strokeWidth = '2'
          } else if (entity.data.layer === 'details') {
            strokeColor = '#A23B72' // Розовый для деталей
            strokeWidth = '1.5'
          }
          
          // Создаем path для полилинии (инвертируем Y координаты)
          let pathData = `M ${entity.vertices[0].x} ${entity.vertices[0].y}`
          for (let i = 1; i < entity.vertices.length; i++) {
            pathData += ` L ${entity.vertices[i].x} ${entity.vertices[i].y}`
          }
          
          svg += `<path d="${pathData}" fill="none" stroke="${strokeColor}" stroke-width="${strokeWidth}"/>`
        }
      })

      svg += '</g></svg>'
      console.log('SVG сгенерирован, размер:', svg.length, 'символов')
      console.log('Масштаб:', scale, 'Центр:', { centerX, centerY })
      return svg
    } catch (error) {
      console.error('Ошибка конвертации DXF в SVG:', error)
      return ''
    }
  },

  // Получить предварительный просмотр карты раскроя
  async getCuttingMapPreview(mapId) {
    try {
      const response = await api.get(`/cutting-maps/${mapId}/image`)
      return response.data
    } catch (error) {
      console.error('Ошибка получения предварительного просмотра:', error)
      throw error
    }
  },

  // Скачать DXF файл
  async downloadDxfFile(mapId, filename) {
    try {
      const response = await api.get(`/cutting-maps/${mapId}/dxf`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename || 'cutting_map.dxf')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Ошибка скачивания DXF файла:', error)
      throw error
    }
  }
}

export default dxfViewerService 