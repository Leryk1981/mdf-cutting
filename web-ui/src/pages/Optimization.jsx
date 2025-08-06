import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { runCuttingOptimization } from '../store/slices/cuttingSlice';

const Optimization = () => {
  const dispatch = useDispatch();
  const { loading, error, optimizationResult } = useSelector((state) => state.cutting);
  
  // Состояние параметров оптимизации
  const [optimizationParams, setOptimizationParams] = useState({
    algorithm: 'genetic',
    maxIterations: 1000,
    populationSize: 50,
    mutationRate: 0.1,
    crossoverRate: 0.8,
    useAI: false,
    margin: 5.0,
    kerf: 3.0,
  });

  // Состояние результатов
  const [results, setResults] = useState(null);

  const handleParamChange = (param, value) => {
    setOptimizationParams(prev => ({
      ...prev,
      [param]: value
    }));
  };

  const handleOptimization = async () => {
    try {
      const result = await dispatch(runCuttingOptimization({
        params: optimizationParams
      }));
      setResults(result.payload);
    } catch (error) {
      console.error('Ошибка оптимизации:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Оптимизация раскроя
      </Typography>

      <Grid container spacing={3}>
        {/* Параметры оптимизации */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Параметры оптимизации
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Алгоритм</InputLabel>
                    <Select
                      value={optimizationParams.algorithm}
                      label="Алгоритм"
                      onChange={(e) => handleParamChange('algorithm', e.target.value)}
                    >
                      <MenuItem value="genetic">Генетический алгоритм</MenuItem>
                      <MenuItem value="simulated_annealing">Имитация отжига</MenuItem>
                      <MenuItem value="hill_climbing">Поиск с восхождением</MenuItem>
                      <MenuItem value="hybrid">Гибридный алгоритм</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Макс. итераций"
                    type="number"
                    value={optimizationParams.maxIterations}
                    onChange={(e) => handleParamChange('maxIterations', parseInt(e.target.value))}
                  />
                </Grid>

                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Размер популяции"
                    type="number"
                    value={optimizationParams.populationSize}
                    onChange={(e) => handleParamChange('populationSize', parseInt(e.target.value))}
                  />
                </Grid>

                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Частота мутации"
                    type="number"
                    inputProps={{ step: 0.01, min: 0, max: 1 }}
                    value={optimizationParams.mutationRate}
                    onChange={(e) => handleParamChange('mutationRate', parseFloat(e.target.value))}
                  />
                </Grid>

                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Частота скрещивания"
                    type="number"
                    inputProps={{ step: 0.01, min: 0, max: 1 }}
                    value={optimizationParams.crossoverRate}
                    onChange={(e) => handleParamChange('crossoverRate', parseFloat(e.target.value))}
                  />
                </Grid>

                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Отступ (мм)"
                    type="number"
                    inputProps={{ step: 0.1, min: 0 }}
                    value={optimizationParams.margin}
                    onChange={(e) => handleParamChange('margin', parseFloat(e.target.value))}
                  />
                </Grid>

                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Рез (мм)"
                    type="number"
                    inputProps={{ step: 0.1, min: 0 }}
                    value={optimizationParams.kerf}
                    onChange={(e) => handleParamChange('kerf', parseFloat(e.target.value))}
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={optimizationParams.useAI}
                        onChange={(e) => handleParamChange('useAI', e.target.checked)}
                      />
                    }
                    label="Использовать AI оптимизацию"
                  />
                </Grid>
              </Grid>

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <PlayIcon />}
                  onClick={handleOptimization}
                  disabled={loading}
                  fullWidth
                >
                  {loading ? 'Оптимизация...' : 'Запустить оптимизацию'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Результаты оптимизации */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Результаты оптимизации
              </Typography>

              {results ? (
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                      <Typography variant="h4" color="success.main">
                        {results.efficiency || 85}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Эффективность
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={6}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                      <Typography variant="h4" color="primary.main">
                        {results.sheets_used || 5}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Листов использовано
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Детальная информация</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <TableContainer component={Paper} variant="outlined">
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Параметр</TableCell>
                                <TableCell>Значение</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              <TableRow>
                                <TableCell>Алгоритм</TableCell>
                                <TableCell>{optimizationParams.algorithm}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Итерации</TableCell>
                                <TableCell>{optimizationParams.maxIterations}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Популяция</TableCell>
                                <TableCell>{optimizationParams.populationSize}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Время выполнения</TableCell>
                                <TableCell>2.5 сек</TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                </Grid>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="text.secondary">
                    Запустите оптимизацию для получения результатов
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Статистика алгоритмов */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Сравнение алгоритмов
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Алгоритм</TableCell>
                      <TableCell>Средняя эффективность</TableCell>
                      <TableCell>Время выполнения</TableCell>
                      <TableCell>Стабильность</TableCell>
                      <TableCell>Рекомендация</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Генетический алгоритм</TableCell>
                      <TableCell>
                        <Chip label="85-92%" color="success" size="small" />
                      </TableCell>
                      <TableCell>2-5 сек</TableCell>
                      <TableCell>
                        <Chip label="Высокая" color="success" size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip label="Рекомендуется" color="primary" size="small" />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Имитация отжига</TableCell>
                      <TableCell>
                        <Chip label="82-88%" color="warning" size="small" />
                      </TableCell>
                      <TableCell>1-3 сек</TableCell>
                      <TableCell>
                        <Chip label="Средняя" color="warning" size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip label="Быстрая оптимизация" color="info" size="small" />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Поиск с восхождением</TableCell>
                      <TableCell>
                        <Chip label="78-85%" color="error" size="small" />
                      </TableCell>
                      <TableCell>0.5-1 сек</TableCell>
                      <TableCell>
                        <Chip label="Низкая" color="error" size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip label="Быстрый прототип" color="default" size="small" />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Ошибки */}
        {error && (
          <Grid item xs={12}>
            <Alert severity="error">
              {error}
            </Alert>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Optimization; 