import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
} from 'recharts';
import {
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';

const Reports = () => {
  const [loading, setLoading] = useState(false);
  const [reportType, setReportType] = useState('efficiency');
  const [dateRange, setDateRange] = useState('month');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Моковые данные для демонстрации
  const efficiencyData = [
    { month: 'Янв', efficiency: 85, projects: 12, waste: 15 },
    { month: 'Фев', efficiency: 88, projects: 15, waste: 12 },
    { month: 'Мар', efficiency: 92, projects: 18, waste: 8 },
    { month: 'Апр', efficiency: 89, projects: 14, waste: 11 },
    { month: 'Май', efficiency: 94, projects: 20, waste: 6 },
    { month: 'Июн', efficiency: 91, projects: 16, waste: 9 },
  ];

  const materialUsageData = [
    { name: 'МДФ 16мм', value: 35, color: '#8884d8' },
    { name: 'МДФ 18мм', value: 25, color: '#82ca9d' },
    { name: 'ЛДСП 16мм', value: 20, color: '#ffc658' },
    { name: 'ЛДСП 18мм', value: 15, color: '#ff7300' },
    { name: 'Другое', value: 5, color: '#8dd1e1' },
  ];

  const projectStats = [
    { category: 'Кухни', completed: 45, inProgress: 8, draft: 3 },
    { category: 'Шкафы', completed: 32, inProgress: 5, draft: 2 },
    { category: 'Стеллажи', completed: 28, inProgress: 4, draft: 1 },
    { category: 'Столы', completed: 15, inProgress: 3, draft: 1 },
    { category: 'Другое', completed: 12, inProgress: 2, draft: 1 },
  ];

  const costAnalysisData = [
    { month: 'Янв', materials: 85000, labor: 45000, total: 130000 },
    { month: 'Фев', materials: 92000, labor: 48000, total: 140000 },
    { month: 'Мар', materials: 105000, labor: 52000, total: 157000 },
    { month: 'Апр', materials: 98000, labor: 50000, total: 148000 },
    { month: 'Май', materials: 115000, labor: 55000, total: 170000 },
    { month: 'Июн', materials: 108000, labor: 53000, total: 161000 },
  ];

  const handleGenerateReport = () => {
    setLoading(true);
    // Имитация загрузки
    setTimeout(() => setLoading(false), 2000);
  };

  const handleDownloadReport = () => {
    // Логика скачивания отчета
    console.log('Downloading report...');
  };

  const renderEfficiencyChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={efficiencyData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="efficiency" fill="#8884d8" name="Эффективность (%)" />
        <Bar dataKey="waste" fill="#ff7300" name="Отходы (%)" />
      </BarChart>
    </ResponsiveContainer>
  );

  const renderMaterialUsageChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={materialUsageData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {materialUsageData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );

  const renderProjectStatsChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={projectStats}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="category" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="completed" fill="#82ca9d" name="Завершено" />
        <Bar dataKey="inProgress" fill="#ffc658" name="В работе" />
        <Bar dataKey="draft" fill="#8884d8" name="Черновики" />
      </BarChart>
    </ResponsiveContainer>
  );

  const renderCostAnalysisChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={costAnalysisData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Area type="monotone" dataKey="materials" stackId="1" stroke="#8884d8" fill="#8884d8" name="Материалы" />
        <Area type="monotone" dataKey="labor" stackId="1" stroke="#82ca9d" fill="#82ca9d" name="Трудозатраты" />
      </AreaChart>
    </ResponsiveContainer>
  );

  const renderReportContent = () => {
    switch (reportType) {
      case 'efficiency':
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Анализ эффективности раскроя
            </Typography>
            {renderEfficiencyChart()}
          </Box>
        );
      case 'materials':
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Использование материалов
            </Typography>
            {renderMaterialUsageChart()}
          </Box>
        );
      case 'projects':
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Статистика проектов
            </Typography>
            {renderProjectStatsChart()}
          </Box>
        );
      case 'costs':
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Анализ затрат
            </Typography>
            {renderCostAnalysisChart()}
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Отчеты и аналитика
      </Typography>

      {/* Панель управления */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Тип отчета</InputLabel>
                <Select
                  value={reportType}
                  label="Тип отчета"
                  onChange={(e) => setReportType(e.target.value)}
                >
                  <MenuItem value="efficiency">Эффективность раскроя</MenuItem>
                  <MenuItem value="materials">Использование материалов</MenuItem>
                  <MenuItem value="projects">Статистика проектов</MenuItem>
                  <MenuItem value="costs">Анализ затрат</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Период</InputLabel>
                <Select
                  value={dateRange}
                  label="Период"
                  onChange={(e) => setDateRange(e.target.value)}
                >
                  <MenuItem value="week">Неделя</MenuItem>
                  <MenuItem value="month">Месяц</MenuItem>
                  <MenuItem value="quarter">Квартал</MenuItem>
                  <MenuItem value="year">Год</MenuItem>
                  <MenuItem value="custom">Произвольный</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {dateRange === 'custom' && (
              <>
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    label="С даты"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    label="По дату"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12} md={3}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <AssessmentIcon />}
                  onClick={handleGenerateReport}
                  disabled={loading}
                >
                  {loading ? 'Генерация...' : 'Сформировать отчет'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadReport}
                >
                  Скачать
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Ключевые показатели */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success.main">
                91%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Средняя эффективность
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary.main">
                156
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Завершенных проектов
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUpIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" color="warning.main">
                8.5%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Средние отходы
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AssessmentIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" color="info.main">
                2.1M ₽
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Общая стоимость
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* График отчета */}
      <Card>
        <CardContent>
          {renderReportContent()}
        </CardContent>
      </Card>

      {/* Детальная таблица */}
      {reportType === 'efficiency' && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Детальная статистика по месяцам
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Месяц</TableCell>
                    <TableCell align="right">Проектов</TableCell>
                    <TableCell align="right">Эффективность (%)</TableCell>
                    <TableCell align="right">Отходы (%)</TableCell>
                    <TableCell align="right">Экономия (₽)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {efficiencyData.map((row) => (
                    <TableRow key={row.month}>
                      <TableCell>{row.month}</TableCell>
                      <TableCell align="right">{row.projects}</TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={`${row.efficiency}%`}
                          color={row.efficiency > 90 ? 'success' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={`${row.waste}%`}
                          color={row.waste < 10 ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        {((100 - row.efficiency) * 1000).toLocaleString()} ₽
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Reports; 