import React from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  LinearProgress,
} from '@mui/material'
import {
  ScatterPlot,
  Inventory,
  Psychology,
  TrendingUp,
  PlayArrow,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

const Dashboard = () => {
  const navigate = useNavigate()

  const quickActions = [
    {
      title: 'Оптимизация раскроя',
      description: 'Запустить оптимизацию раскроя МДФ',
      icon: <ScatterPlot sx={{ fontSize: 40 }} />,
      color: 'primary.main',
      path: '/cutting',
    },
    {
      title: 'AI Оптимизация',
      description: 'Использовать AI для улучшения результатов',
      icon: <Psychology sx={{ fontSize: 40 }} />,
      color: 'success.main',
      path: '/ai',
    },
    {
      title: 'Управление материалами',
      description: 'Добавить или изменить материалы',
      icon: <Inventory sx={{ fontSize: 40 }} />,
      color: 'info.main',
      path: '/materials',
    },
  ]

  const stats = [
    {
      title: 'Всего проектов',
      value: '24',
      change: '+12%',
      changeType: 'positive',
    },
    {
      title: 'Экономия материала',
      value: '18.5%',
      change: '+2.3%',
      changeType: 'positive',
    },
    {
      title: 'AI предложений',
      value: '156',
      change: '+23',
      changeType: 'positive',
    },
    {
      title: 'Время оптимизации',
      value: '2.3 мин',
      change: '-0.5 мин',
      changeType: 'positive',
    },
  ]

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Добро пожаловать в систему раскроя МДФ
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Оптимизируйте раскрой материалов с помощью AI
        </Typography>
      </Box>

      {/* Quick Actions */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {quickActions.map((action, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(action.path)}
            >
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <Box sx={{ color: action.color, mb: 2 }}>
                  {action.icon}
                </Box>
                <Typography variant="h6" gutterBottom>
                  {action.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {action.description}
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  sx={{ backgroundColor: action.color }}
                >
                  Начать
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Typography variant="h4" component="div" gutterBottom>
                  {stat.value}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {stat.title}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography
                    variant="body2"
                    sx={{
                      color: stat.changeType === 'positive' ? 'success.main' : 'error.main',
                      fontWeight: 'bold',
                    }}
                  >
                    {stat.change}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                    с прошлого месяца
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Activity */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Последняя активность
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Оптимизация проекта "Кухонные фасады"
            </Typography>
            <LinearProgress
              variant="determinate"
              value={75}
              sx={{ mt: 1, mb: 1 }}
            />
            <Typography variant="body2" color="text.secondary">
              75% завершено
            </Typography>
          </Box>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              AI анализ предложений
            </Typography>
            <LinearProgress
              variant="determinate"
              value={90}
              sx={{ mt: 1, mb: 1 }}
            />
            <Typography variant="body2" color="text.secondary">
              90% завершено
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Dashboard 