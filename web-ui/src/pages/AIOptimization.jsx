import React, { useState } from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Slider,
  Switch,
  FormControlLabel,
  LinearProgress,
  Chip,
  Alert,
  Divider,
} from '@mui/material'
import {
  Psychology,
  PlayArrow,
  Refresh,
  Settings,
  CheckCircle,
  Warning,
  Error,
  Info,
} from '@mui/icons-material'
import { useSelector, useDispatch } from 'react-redux'

import { runAIOptimization, runLeftoverOptimization, updateAIParams } from '../store/slices/aiSlice.js'
import SuggestionsTable from '../components/ai/SuggestionsTable.jsx'
import FeedbackDialog from '../components/ai/FeedbackDialog.jsx'

const AIOptimization = () => {
  const dispatch = useDispatch()
  const { aiParams, isOptimizing, suggestions, error } = useSelector((state) => state.ai)
  const [showFeedback, setShowFeedback] = useState(false)

  const handleParamChange = (param, value) => {
    dispatch(updateAIParams({ [param]: value }))
  }

  const handleOptimize = () => {
    dispatch(runAIOptimization(aiParams))
  }

  const handleLeftoverOptimize = () => {
    dispatch(runLeftoverOptimization(aiParams))
  }

  const getStatusColor = () => {
    if (isOptimizing) return 'warning'
    if (error) return 'error'
    if (suggestions.length > 0) return 'success'
    return 'info'
  }

  const getStatusIcon = () => {
    if (isOptimizing) return <Warning />
    if (error) return <Error />
    if (suggestions.length > 0) return <CheckCircle />
    return <Info />
  }

  const getStatusText = () => {
    if (isOptimizing) return 'AI обрабатывает данные...'
    if (error) return `Ошибка: ${error}`
    if (suggestions.length > 0) return `Найдено ${suggestions.length} предложений`
    return 'AI готов к работе'
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          <Psychology sx={{ mr: 2, verticalAlign: 'middle' }} />
          AI Оптимизация раскроя
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Используйте искусственный интеллект для улучшения результатов оптимизации
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* AI Parameters */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Settings sx={{ mr: 1 }} />
                <Typography variant="h6">Параметры AI</Typography>
              </Box>

              {/* AI Assistance Toggle */}
              <FormControlLabel
                control={
                  <Switch
                    checked={aiParams.aiAssistanceEnabled}
                    onChange={(e) => handleParamChange('aiAssistanceEnabled', e.target.checked)}
                    color="primary"
                  />
                }
                label="Включить AI-ассистенцию"
                sx={{ mb: 2 }}
              />

              {/* Confidence Threshold */}
              <Typography gutterBottom>Порог уверенности: {Math.round(aiParams.confidenceThreshold * 100)}%</Typography>
              <Slider
                value={aiParams.confidenceThreshold}
                onChange={(e, value) => handleParamChange('confidenceThreshold', value)}
                min={0.5}
                max={0.95}
                step={0.05}
                marks={[
                  { value: 0.5, label: '50%' },
                  { value: 0.7, label: '70%' },
                  { value: 0.9, label: '90%' },
                ]}
                sx={{ mb: 3 }}
              />

              {/* Auto Apply Corrections */}
              <FormControlLabel
                control={
                  <Switch
                    checked={aiParams.autoApplyCorrections}
                    onChange={(e) => handleParamChange('autoApplyCorrections', e.target.checked)}
                    color="success"
                  />
                }
                label="Применять предложения автоматически"
                sx={{ mb: 3 }}
              />

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={handleOptimize}
                  disabled={isOptimizing}
                  fullWidth
                  size="large"
                >
                  AI Оптимизировать
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<Refresh />}
                  onClick={handleLeftoverOptimize}
                  disabled={isOptimizing}
                  fullWidth
                  size="large"
                >
                  Использовать остатки
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => setShowFeedback(true)}
                  fullWidth
                >
                  Обратная связь
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Status and Results */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                {getStatusIcon()}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Статус AI
                </Typography>
              </Box>

              {/* Status Alert */}
              <Alert severity={getStatusColor()} sx={{ mb: 3 }}>
                {getStatusText()}
              </Alert>

              {/* Progress Bar */}
              {isOptimizing && (
                <Box sx={{ mb: 3 }}>
                  <LinearProgress />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Обработка данных...
                  </Typography>
                </Box>
              )}

              {/* AI Statistics */}
              {suggestions.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Статистика AI
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="primary.main">
                          {suggestions.length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Предложений
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="success.main">
                          {suggestions.filter(s => s.confidence >= 0.8).length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Высокая уверенность
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="warning.main">
                          {suggestions.filter(s => s.confidence >= 0.6 && s.confidence < 0.8).length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Средняя уверенность
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="error.main">
                          {suggestions.filter(s => s.confidence < 0.6).length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Низкая уверенность
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              )}

              <Divider sx={{ my: 3 }} />

              {/* Suggestions Table */}
              {suggestions.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Предложения AI
                  </Typography>
                  <SuggestionsTable suggestions={suggestions} />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Feedback Dialog */}
      <FeedbackDialog
        open={showFeedback}
        onClose={() => setShowFeedback(false)}
      />
    </Box>
  )
}

export default AIOptimization 