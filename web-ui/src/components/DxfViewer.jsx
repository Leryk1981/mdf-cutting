import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Paper,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Typography,
  Chip,
  Button,
} from '@mui/material'
import {
  ZoomIn,
  ZoomOut,
  Fullscreen,
  Download,
  Refresh,
} from '@mui/icons-material'
import { dxfViewerService } from '../services/dxfViewerService.js'

const DxfViewer = ({ mapId, mapData }) => {
  const [svgContent, setSvgContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const containerRef = useRef(null)

  useEffect(() => {
    console.log('=== useEffect вызван ===')
    console.log('mapId:', mapId)
    console.log('mapData:', mapData)
    
    if (mapId !== null && mapId !== undefined) {
      console.log('Вызываем loadDxfFile для mapId:', mapId)
      loadDxfFile()
    } else {
      console.log('mapId не определен, не вызываем loadDxfFile')
    }
  }, [mapId])

  const loadDxfFile = async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('=== НАЧАЛО ЗАГРУЗКИ DXF ===')
      console.log('mapId:', mapId)
      console.log('mapData:', mapData)
      
      const dxfContent = await dxfViewerService.loadDxfFile(mapId)
      console.log('DXF контент загружен, размер:', dxfContent.byteLength)
      
      const entities = dxfViewerService.parseDxfContent(dxfContent)
      console.log('DXF entities найдено:', entities.length)
      
      if (entities.length === 0) {
        console.warn('Не найдено entities для отображения')
        setError('DXF файл не содержит данных для отображения')
        return
      }
      
      const svg = dxfViewerService.convertDxfToSvg(entities, 800, 600)
      console.log('SVG сгенерирован, размер:', svg.length, 'символов')
      
      if (!svg || svg.length < 100) {
        console.warn('SVG слишком короткий или пустой')
        setError('Не удалось сгенерировать SVG')
        return
      }
      
      setSvgContent(svg)
      console.log('=== ЗАГРУЗКА DXF ЗАВЕРШЕНА ===')
    } catch (err) {
      console.error('Ошибка загрузки DXF:', err)
      setError('Ошибка загрузки DXF файла: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 5))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.1))
  }

  const handleResetZoom = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  const handleDownload = async () => {
    try {
      const filename = mapData?.name ? `${mapData.name}.dxf` : 'cutting_map.dxf'
      await dxfViewerService.downloadDxfFile(mapId, filename)
    } catch (err) {
      setError('Ошибка скачивания файла')
    }
  }

  const handleMouseDown = (e) => {
    setIsDragging(true)
    setDragStart({
      x: e.clientX - pan.x,
      y: e.clientY - pan.y
    })
  }

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleWheel = (e) => {
    try {
      e.preventDefault()
    } catch (error) {
      // Игнорируем ошибку preventDefault в passive event listener
    }
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setZoom(prev => Math.max(0.1, Math.min(5, prev * delta)))
  }

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 2, 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        position: 'relative'
      }}
    >
      {/* Заголовок */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6" component="h3">
            Просмотр карты раскроя
          </Typography>
          {mapData && (
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip 
                label={`Материал: ${mapData.material}`} 
                size="small" 
                variant="outlined" 
              />
              <Chip 
                label={`Эффективность: ${mapData.efficiency}%`} 
                size="small" 
                variant="outlined" 
                color="primary"
              />
              <Chip 
                label={`Панелей: ${mapData.panels}`} 
                size="small" 
                variant="outlined" 
              />
            </Box>
          )}
        </Box>
        
        {/* Панель инструментов */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Увеличить">
            <IconButton onClick={handleZoomIn} size="small">
              <ZoomIn />
            </IconButton>
          </Tooltip>
          <Tooltip title="Уменьшить">
            <IconButton onClick={handleZoomOut} size="small">
              <ZoomOut />
            </IconButton>
          </Tooltip>
          <Tooltip title="Сбросить масштаб">
            <IconButton onClick={handleResetZoom} size="small">
              <Fullscreen />
            </IconButton>
          </Tooltip>
          <Tooltip title="Обновить">
            <IconButton onClick={loadDxfFile} size="small">
              <Refresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="Скачать DXF">
            <IconButton onClick={handleDownload} size="small">
              <Download />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Область просмотра */}
      <Box
        ref={containerRef}
        sx={{
          flex: 1,
          border: '1px solid #ddd',
          borderRadius: 1,
          overflow: 'hidden',
          position: 'relative',
          backgroundColor: '#f8f9fa',
          cursor: isDragging ? 'grabbing' : 'grab',
          '&:hover': {
            cursor: isDragging ? 'grabbing' : 'grab'
          }
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={(e) => {
          e.stopPropagation()
          const delta = e.deltaY > 0 ? 0.9 : 1.1
          setZoom(prev => Math.max(0.1, Math.min(5, prev * delta)))
        }}
      >
        {loading && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 10
            }}
          >
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              position: 'absolute',
              top: 10,
              left: 10,
              right: 10,
              zIndex: 10
            }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        {svgContent && !loading && (
          <Box
            sx={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
              transition: isDragging ? 'none' : 'transform 0.1s ease-out'
            }}
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        )}

        {/* Отладочная информация SVG */}
        {svgContent && (
          <Box sx={{ 
            position: 'absolute', 
            bottom: 10, 
            left: 10, 
            backgroundColor: 'rgba(0,0,0,0.7)', 
            color: 'white', 
            p: 1, 
            borderRadius: 1, 
            fontSize: '10px',
            zIndex: 20,
            maxWidth: '300px',
            maxHeight: '200px',
            overflow: 'auto'
          }}>
            <div>SVG размер: {svgContent.length} символов</div>
            <div>SVG начало: {svgContent.substring(0, 100)}...</div>
            <div>SVG конец: ...{svgContent.substring(svgContent.length - 100)}</div>
          </Box>
        )}

        {!svgContent && !loading && !error && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              color: '#666'
            }}
          >
            {mapData ? (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Информация о карте раскроя
                </Typography>
                <Box sx={{ mt: 2, textAlign: 'left', maxWidth: 400, mx: 'auto' }}>
                  <Typography><strong>Название:</strong> {mapData.name}</Typography>
                  <Typography><strong>Материал:</strong> {mapData.material}</Typography>
                  <Typography><strong>Толщина:</strong> {mapData.thickness}</Typography>
                  <Typography><strong>Размеры:</strong> {mapData.dimensions}</Typography>
                  <Typography><strong>Эффективность:</strong> {mapData.efficiency}%</Typography>
                  <Typography><strong>Количество панелей:</strong> {mapData.panels}</Typography>
                  <Typography><strong>Отходы:</strong> {mapData.waste}%</Typography>
                  <Typography><strong>Статус:</strong> {mapData.status}</Typography>
                  <Typography><strong>Дата:</strong> {new Date(mapData.date).toLocaleDateString()}</Typography>
                </Box>
                <Alert severity="info" sx={{ mt: 2 }}>
                  DXF файл загружен, но не может быть отображен. Попробуйте скачать файл для просмотра в CAD программе.
                </Alert>
              </Box>
            ) : (
              <Typography variant="body2">
                Выберите карту раскроя для просмотра
              </Typography>
            )}
          </Box>
        )}

        {/* Отладочная информация */}
        <Box sx={{ 
          position: 'absolute', 
          top: 10, 
          right: 10, 
          backgroundColor: 'rgba(0,0,0,0.7)', 
          color: 'white', 
          p: 1, 
          borderRadius: 1, 
          fontSize: '12px',
          zIndex: 20
        }}>
          <div>mapId: {mapId}</div>
          <div>loading: {loading.toString()}</div>
          <div>error: {error || 'нет'}</div>
          <div>svgContent: {svgContent ? 'есть' : 'нет'}</div>
          <div>mapData: {mapData ? 'есть' : 'нет'}</div>
          <Button 
            size="small" 
            variant="contained" 
            onClick={loadDxfFile}
            sx={{ mt: 1, fontSize: '10px' }}
          >
            Загрузить DXF
          </Button>
        </Box>
      </Box>

      {/* Информация о масштабе */}
      <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Масштаб: {Math.round(zoom * 100)}%
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Используйте колесо мыши для масштабирования, перетаскивание для перемещения
        </Typography>
      </Box>
    </Paper>
  )
}

export default DxfViewer 