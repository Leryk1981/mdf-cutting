import React, { useState, useEffect, useRef } from 'react';
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
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Upload as UploadIcon,
  PlayArrow as PlayIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Folder as FolderIcon,
  FileUpload as FileUploadIcon,
  Clear as ClearIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { uploadDetailsFile, runCuttingOptimization } from '../store/slices/cuttingSlice';

const CuttingOptimization = () => {
  const dispatch = useDispatch();
  const { loading, error, optimizationResult, detailsFile } = useSelector((state) => state.cutting);
  
  // Состояние файлов
  const [detailsFilePath, setDetailsFilePath] = useState('');
  const [materialsFilePath, setMaterialsFilePath] = useState('');
  const [patternDirPath, setPatternDirPath] = useState('patterns');
  const [outputDirPath, setOutputDirPath] = useState('output');
  
  // Состояние настроек
  const [optimizationParams, setOptimizationParams] = useState({
    margin: 5.0,
    kerf: 3.0,
    keepTempFiles: false,
    logLevel: 'INFO',
  });

  // Состояние логов
  const [logs, setLogs] = useState([]);
  const [logLevel, setLogLevel] = useState('INFO');
  
  // Состояние статуса
  const [status, setStatus] = useState('Инициализация...');
  const [progress, setProgress] = useState(0);
  
  // Рефы для файловых инпутов
  const detailsFileRef = useRef();
  const materialsFileRef = useRef();

  // Добавление лога
  const addLog = (message, level = 'INFO') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, level }]);
  };

  // Очистка логов
  const clearLogs = () => {
    setLogs([]);
  };

  // Очистка всех данных
  const clearAll = () => {
    setDetailsFilePath('');
    setMaterialsFilePath('');
    setPatternDirPath('patterns');
    setOutputDirPath('output');
    setOptimizationParams({
      margin: 5.0,
      kerf: 3.0,
      keepTempFiles: false,
      logLevel: 'INFO',
    });
    setLogs([]);
    setStatus('Инициализация...');
    setProgress(0);
  };

  // Обработка загрузки файла деталей
  const handleDetailsFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setDetailsFilePath(file.name);
      addLog(`Загружен файл деталей: ${file.name}`, 'INFO');
      dispatch(uploadDetailsFile(file));
    }
  };

  // Обработка загрузки файла материалов
  const handleMaterialsFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setMaterialsFilePath(file.name);
      addLog(`Загружен файл материалов: ${file.name}`, 'INFO');
    }
  };

  // Запуск оптимизации раскроя
  const handleRunCutting = async () => {
    if (!detailsFilePath) {
      addLog('Ошибка: Не выбран файл деталей', 'ERROR');
      return;
    }

    setStatus('Выполняется раскрой...');
    setProgress(0);
    addLog('Начинается процесс раскроя', 'INFO');

    try {
      // Имитация прогресса
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      // Запуск оптимизации
      const result = await dispatch(runCuttingOptimization({
        fileId: detailsFile?.id,
        params: optimizationParams
      }));

      clearInterval(progressInterval);
      setProgress(100);
      setStatus('Раскрой завершен');
      addLog('Процесс раскроя завершен успешно', 'INFO');

    } catch (error) {
      setStatus('Ошибка при выполнении раскроя');
      addLog(`Ошибка: ${error.message}`, 'ERROR');
    }
  };

  // Проверка возможности запуска
  const canRun = detailsFilePath && !loading;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Раскрой MDF Накладок
      </Typography>

      <Grid container spacing={3}>
        {/* Входные файлы */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Входные файлы
              </Typography>
              
              <Grid container spacing={2}>
                {/* Файл деталей */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TextField
                      fullWidth
                      label="Файл деталей (processed_data.csv)"
                      value={detailsFilePath}
                      onChange={(e) => setDetailsFilePath(e.target.value)}
                      placeholder="Выберите файл деталей"
                    />
                    <input
                      ref={detailsFileRef}
                      type="file"
                      accept=".csv"
                      style={{ display: 'none' }}
                      onChange={handleDetailsFileUpload}
                    />
                    <IconButton
                      onClick={() => detailsFileRef.current?.click()}
                      color="primary"
                    >
                      <FileUploadIcon />
                    </IconButton>
                  </Box>
                </Grid>

                {/* Файл материалов */}
                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TextField
                      fullWidth
                      label="Файл материалов (materials.csv)"
                      value={materialsFilePath}
                      onChange={(e) => setMaterialsFilePath(e.target.value)}
                      placeholder="Выберите файл материалов"
                    />
                    <input
                      ref={materialsFileRef}
                      type="file"
                      accept=".csv"
                      style={{ display: 'none' }}
                      onChange={handleMaterialsFileUpload}
                    />
                    <IconButton
                      onClick={() => materialsFileRef.current?.click()}
                      color="primary"
                    >
                      <FileUploadIcon />
                    </IconButton>
                  </Box>
                </Grid>

                {/* Папка с узорами */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Папка с узорами"
                    value={patternDirPath}
                    onChange={(e) => setPatternDirPath(e.target.value)}
                  />
                </Grid>

                {/* Папка для выходных файлов */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Папка для выходных файлов"
                    value={outputDirPath}
                    onChange={(e) => setOutputDirPath(e.target.value)}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Настройки */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Настройки
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    label="Отступ (мм)"
                    type="number"
                    value={optimizationParams.margin}
                    onChange={(e) => setOptimizationParams(prev => ({
                      ...prev,
                      margin: parseFloat(e.target.value)
                    }))}
                    inputProps={{ step: 0.1, min: 0 }}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    label="Рез (мм)"
                    type="number"
                    value={optimizationParams.kerf}
                    onChange={(e) => setOptimizationParams(prev => ({
                      ...prev,
                      kerf: parseFloat(e.target.value)
                    }))}
                    inputProps={{ step: 0.1, min: 0 }}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Уровень логирования</InputLabel>
                    <Select
                      value={logLevel}
                      label="Уровень логирования"
                      onChange={(e) => setLogLevel(e.target.value)}
                    >
                      <MenuItem value="INFO">INFO</MenuItem>
                      <MenuItem value="DEBUG">DEBUG</MenuItem>
                      <MenuItem value="WARNING">WARNING</MenuItem>
                      <MenuItem value="ERROR">ERROR</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={optimizationParams.keepTempFiles}
                        onChange={(e) => setOptimizationParams(prev => ({
                          ...prev,
                          keepTempFiles: e.target.checked
                        }))}
                      />
                    }
                    label="Сохранять временные файлы"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Логи */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Логи
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<ClearIcon />}
                    onClick={clearLogs}
                  >
                    Очистить логи
                  </Button>
                </Box>
              </Box>
              
              <Paper sx={{ height: 300, overflow: 'auto', p: 2, bgcolor: '#f5f5f5' }}>
                {logs.length === 0 ? (
                  <Typography color="text.secondary" textAlign="center">
                    Логи будут отображаться здесь
                  </Typography>
                ) : (
                  logs.map((log, index) => (
                    <Box key={index} sx={{ mb: 1, fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      <span style={{ color: '#666' }}>[{log.timestamp}]</span>
                      <span style={{ 
                        color: log.level === 'ERROR' ? '#d32f2f' : 
                               log.level === 'WARNING' ? '#ed6c02' : 
                               log.level === 'DEBUG' ? '#1976d2' : '#2e7d32',
                        fontWeight: 'bold',
                        marginLeft: 8
                      }}>
                        {log.level}
                      </span>
                      <span style={{ marginLeft: 8 }}>{log.message}</span>
                    </Box>
                  ))
                )}
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Действия */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={loading ? <CircularProgress size={20} /> : <PlayIcon />}
                    onClick={handleRunCutting}
                    disabled={!canRun || loading}
                    size="large"
                  >
                    {loading ? 'Выполняется раскрой...' : 'Запустить раскрой'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    startIcon={<ClearIcon />}
                    onClick={clearAll}
                    disabled={loading}
                  >
                    Очистить
                  </Button>
                </Box>
                
                <Typography variant="body2" color="text.secondary">
                  {status}
                </Typography>
              </Box>
              
              {loading && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress variant="determinate" value={progress} />
                  <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                    Прогресс: {progress}%
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Результаты */}
        {optimizationResult && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Результаты оптимизации
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {optimizationResult.efficiency}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Эффективность раскроя
                      </Typography>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {optimizationResult.sheets_used || optimizationResult.total_used_sheets}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Листов использовано
                      </Typography>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="warning.main">
                        {optimizationResult.waste || (100 - optimizationResult.efficiency)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Отходы
                      </Typography>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="info.main">
                        {optimizationResult.dxf_files?.length || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        DXF файлов создано
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
                
                {optimizationResult.dxf_files && optimizationResult.dxf_files.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Созданные DXF файлы:
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Имя файла</TableCell>
                            <TableCell>Размер</TableCell>
                            <TableCell>Действия</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {optimizationResult.dxf_files.map((file, index) => (
                            <TableRow key={index}>
                              <TableCell>{file.split('/').pop()}</TableCell>
                              <TableCell>-</TableCell>
                              <TableCell>
                                <Button
                                  variant="outlined"
                                  size="small"
                                  startIcon={<DownloadIcon />}
                                >
                                  Скачать
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

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

export default CuttingOptimization; 