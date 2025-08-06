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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { 
  fetchMaterials, 
  createMaterial, 
  updateMaterial, 
  deleteMaterial,
  uploadMaterialsFile 
} from '../store/slices/materialsSlice';

const MaterialsManagement = () => {
  const dispatch = useDispatch();
  const { materials, loading, error } = useSelector((state) => state.materials);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [materialForm, setMaterialForm] = useState({
    name: '',
    category: '',
    width: '',
    height: '',
    thickness: '',
    price: '',
    quantity: '',
    description: '',
  });

  useEffect(() => {
    dispatch(fetchMaterials());
  }, [dispatch]);

  const handleAddMaterial = () => {
    setEditingMaterial(null);
    setMaterialForm({
      name: '',
      category: '',
      width: '',
      height: '',
      thickness: '',
      price: '',
      quantity: '',
      description: '',
    });
    setDialogOpen(true);
  };

  const handleEditMaterial = (material) => {
    setEditingMaterial(material);
    setMaterialForm({
      name: material.name,
      category: material.category,
      width: material.width.toString(),
      height: material.height.toString(),
      thickness: material.thickness.toString(),
      price: material.price.toString(),
      quantity: material.quantity.toString(),
      description: material.description || '',
    });
    setDialogOpen(true);
  };

  const handleDeleteMaterial = (id) => {
    if (window.confirm('Вы уверены, что хотите удалить этот материал?')) {
      dispatch(deleteMaterial(id));
    }
  };

  const handleSaveMaterial = () => {
    const materialData = {
      ...materialForm,
      width: parseFloat(materialForm.width),
      height: parseFloat(materialForm.height),
      thickness: parseFloat(materialForm.thickness),
      price: parseFloat(materialForm.price),
      quantity: parseInt(materialForm.quantity),
    };

    if (editingMaterial) {
      dispatch(updateMaterial({ id: editingMaterial.id, data: materialData }));
    } else {
      dispatch(createMaterial(materialData));
    }
    setDialogOpen(false);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      dispatch(uploadMaterialsFile(file));
    }
  };

  const filteredMaterials = materials.filter(material => {
    const matchesSearch = material.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         material.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !filterCategory || material.category === filterCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = [...new Set(materials.map(m => m.category))];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Управление материалами
      </Typography>

      {/* Панель инструментов */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Поиск материалов..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Категория</InputLabel>
                <Select
                  value={filterCategory}
                  label="Категория"
                  onChange={(e) => setFilterCategory(e.target.value)}
                >
                  <MenuItem value="">Все категории</MenuItem>
                  {categories.map(category => (
                    <MenuItem key={category} value={category}>{category}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={5}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleAddMaterial}
                >
                  Добавить материал
                </Button>
                
                <input
                  accept=".csv,.xlsx"
                  style={{ display: 'none' }}
                  id="materials-file-upload"
                  type="file"
                  onChange={handleFileUpload}
                />
                <label htmlFor="materials-file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadIcon />}
                  >
                    Импорт
                  </Button>
                </label>

                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                >
                  Экспорт
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Таблица материалов */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Название</TableCell>
                  <TableCell>Категория</TableCell>
                  <TableCell>Размеры (мм)</TableCell>
                  <TableCell>Толщина (мм)</TableCell>
                  <TableCell>Цена (₽)</TableCell>
                  <TableCell>Количество</TableCell>
                  <TableCell>Статус</TableCell>
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
                ) : filteredMaterials.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      Материалы не найдены
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredMaterials.map((material) => (
                    <TableRow key={material.id}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {material.name}
                          </Typography>
                          {material.description && (
                            <Typography variant="caption" color="text.secondary">
                              {material.description}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={material.category} size="small" />
                      </TableCell>
                      <TableCell>
                        {material.width} × {material.height}
                      </TableCell>
                      <TableCell>{material.thickness}</TableCell>
                      <TableCell>{material.price.toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip 
                          label={material.quantity}
                          color={material.quantity > 10 ? 'success' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={material.quantity > 0 ? 'В наличии' : 'Нет в наличии'}
                          color={material.quantity > 0 ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="Редактировать">
                            <IconButton
                              size="small"
                              onClick={() => handleEditMaterial(material)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Удалить">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteMaterial(material.id)}
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
          {editingMaterial ? 'Редактировать материал' : 'Добавить материал'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Название"
                value={materialForm.name}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, name: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Категория"
                value={materialForm.category}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, category: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Ширина (мм)"
                type="number"
                value={materialForm.width}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, width: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Высота (мм)"
                type="number"
                value={materialForm.height}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, height: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Толщина (мм)"
                type="number"
                value={materialForm.thickness}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, thickness: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Цена (₽)"
                type="number"
                value={materialForm.price}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, price: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Количество"
                type="number"
                value={materialForm.quantity}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, quantity: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Описание"
                multiline
                rows={3}
                value={materialForm.description}
                onChange={(e) => setMaterialForm(prev => ({ ...prev, description: e.target.value }))}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleSaveMaterial} variant="contained">
            {editingMaterial ? 'Сохранить' : 'Добавить'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Ошибки */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default MaterialsManagement; 