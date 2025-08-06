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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Folder as FolderIcon,
  Description as DescriptionIcon,
  CalendarToday as CalendarIcon,
  Person as PersonIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

const Projects = () => {
  const [projects, setProjects] = useState([
    {
      id: 1,
      name: 'Кухонный гарнитур "Модерн"',
      description: 'Полный комплект кухонной мебели в современном стиле',
      status: 'completed',
      createdAt: '2025-08-01',
      updatedAt: '2025-08-05',
      client: 'ООО "МебельСтрой"',
      details: 45,
      materials: 8,
      efficiency: 92,
      totalCost: 125000,
    },
    {
      id: 2,
      name: 'Шкаф-купе "Классик"',
      description: 'Двухдверный шкаф-купе с зеркальными фасадами',
      status: 'in_progress',
      createdAt: '2025-08-03',
      updatedAt: '2025-08-06',
      client: 'ИП Иванов А.С.',
      details: 23,
      materials: 5,
      efficiency: 87,
      totalCost: 45000,
    },
    {
      id: 3,
      name: 'Стеллаж для офиса',
      description: 'Модульный стеллаж для документов и канцелярии',
      status: 'draft',
      createdAt: '2025-08-04',
      updatedAt: '2025-08-04',
      client: 'ООО "БизнесМебель"',
      details: 12,
      materials: 3,
      efficiency: 0,
      totalCost: 18000,
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [projectForm, setProjectForm] = useState({
    name: '',
    description: '',
    client: '',
    status: 'draft',
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'draft': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return 'Завершен';
      case 'in_progress': return 'В работе';
      case 'draft': return 'Черновик';
      default: return 'Неизвестно';
    }
  };

  const handleAddProject = () => {
    setEditingProject(null);
    setProjectForm({
      name: '',
      description: '',
      client: '',
      status: 'draft',
    });
    setDialogOpen(true);
  };

  const handleEditProject = (project) => {
    setEditingProject(project);
    setProjectForm({
      name: project.name,
      description: project.description,
      client: project.client,
      status: project.status,
    });
    setDialogOpen(true);
  };

  const handleDeleteProject = (id) => {
    if (window.confirm('Вы уверены, что хотите удалить этот проект?')) {
      setProjects(prev => prev.filter(p => p.id !== id));
    }
  };

  const handleSaveProject = () => {
    if (editingProject) {
      setProjects(prev => prev.map(p => 
        p.id === editingProject.id 
          ? { ...p, ...projectForm, updatedAt: new Date().toISOString().split('T')[0] }
          : p
      ));
    } else {
      const newProject = {
        id: Date.now(),
        ...projectForm,
        createdAt: new Date().toISOString().split('T')[0],
        updatedAt: new Date().toISOString().split('T')[0],
        details: 0,
        materials: 0,
        efficiency: 0,
        totalCost: 0,
      };
      setProjects(prev => [...prev, newProject]);
    }
    setDialogOpen(false);
  };

  const handleViewProject = (project) => {
    // Логика просмотра проекта
    console.log('Viewing project:', project);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Управление проектами
      </Typography>

      {/* Панель инструментов */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                placeholder="Поиск проектов..."
                InputProps={{
                  startAdornment: <FolderIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleAddProject}
                >
                  Новый проект
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Статистика */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {projects.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Всего проектов
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {projects.filter(p => p.status === 'completed').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Завершенных
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">
                {projects.filter(p => p.status === 'in_progress').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                В работе
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {projects.reduce((sum, p) => sum + p.totalCost, 0).toLocaleString()} ₽
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Общая стоимость
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Таблица проектов */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Проект</TableCell>
                  <TableCell>Клиент</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Детали</TableCell>
                  <TableCell>Эффективность</TableCell>
                  <TableCell>Стоимость</TableCell>
                  <TableCell>Дата обновления</TableCell>
                  <TableCell>Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : projects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      Проекты не найдены
                    </TableCell>
                  </TableRow>
                ) : (
                  projects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {project.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {project.description}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <PersonIcon fontSize="small" />
                          {project.client}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={getStatusLabel(project.status)}
                          color={getStatusColor(project.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <DescriptionIcon fontSize="small" />
                          {project.details}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {project.efficiency > 0 ? (
                          <Chip 
                            label={`${project.efficiency}%`}
                            color={project.efficiency > 90 ? 'success' : 'warning'}
                            size="small"
                          />
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            Не рассчитано
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {project.totalCost.toLocaleString()} ₽
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CalendarIcon fontSize="small" />
                          {project.updatedAt}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="Просмотр">
                            <IconButton
                              size="small"
                              onClick={() => handleViewProject(project)}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Редактировать">
                            <IconButton
                              size="small"
                              onClick={() => handleEditProject(project)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Удалить">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteProject(project.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Диалог добавления/редактирования */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingProject ? 'Редактировать проект' : 'Новый проект'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Название проекта"
                value={projectForm.name}
                onChange={(e) => setProjectForm(prev => ({ ...prev, name: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Описание"
                multiline
                rows={3}
                value={projectForm.description}
                onChange={(e) => setProjectForm(prev => ({ ...prev, description: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Клиент"
                value={projectForm.client}
                onChange={(e) => setProjectForm(prev => ({ ...prev, client: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Статус"
                select
                value={projectForm.status}
                onChange={(e) => setProjectForm(prev => ({ ...prev, status: e.target.value }))}
              >
                <MenuItem value="draft">Черновик</MenuItem>
                <MenuItem value="in_progress">В работе</MenuItem>
                <MenuItem value="completed">Завершен</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleSaveProject} variant="contained">
            {editingProject ? 'Сохранить' : 'Создать'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Projects; 