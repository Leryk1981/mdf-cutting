import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  Description as DxfIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCuttingMaps } from '../store/slices/cuttingMapsSlice';

const CuttingMaps = () => {
  const dispatch = useDispatch();
  const { cuttingMaps: maps, loading, error } = useSelector((state) => state.cuttingMaps);
  const [selectedMap, setSelectedMap] = useState(null);
  const [pdfDialogOpen, setPdfDialogOpen] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    console.log('CuttingMaps: useEffect вызван, загружаем данные...');
    console.log('CuttingMaps: dispatch =', dispatch);
    dispatch(fetchCuttingMaps());
  }, [dispatch]);

  // Добавляем отладочную информацию
  console.log('CuttingMaps: render', { 
    maps: maps, 
    mapsLength: maps ? maps.length : 'undefined',
    loading, 
    error,
    dispatch: !!dispatch
  });
  
  if (loading) {
    console.log('CuttingMaps: показываем загрузку');
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    console.log('CuttingMaps: показываем ошибку:', error);
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  console.log('CuttingMaps: показываем основной контент');
  const paginatedMaps = (maps || []).slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  // Дополнительная диагностика
  if (maps && maps.length > 0) {
    console.log('CuttingMaps: первая карта:', JSON.stringify(maps[0], null, 2));
    console.log('CuttingMaps: paginatedMaps:', JSON.stringify(paginatedMaps, null, 2));
    console.log('CuttingMaps: maps.length:', maps.length);
    console.log('CuttingMaps: page:', page, 'rowsPerPage:', rowsPerPage);
  } else {
    console.log('CuttingMaps: maps пустой или undefined');
  }

  const handleViewPdf = (map) => {
    console.log('Открываем просмотр PDF для карты:', map.name);
    setSelectedMap(map);
    setPdfDialogOpen(true);
  };

  const handleDownloadPdf = async (map) => {
    try {
      console.log('Скачиваем PDF для карты:', map.name);
      
      // Альтернативный способ - открываем в новой вкладке
      const url = `/api/cutting-maps/${map.id}/pdf`;
      const link = document.createElement('a');
      link.href = url;
      link.download = `cutting_map_${map.name}_${map.thickness}.pdf`;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log('PDF скачивание инициировано');
    } catch (error) {
      console.error('Ошибка скачивания PDF:', error);
    }
  };

  const handleDownloadDxf = async (map) => {
    try {
      const response = await fetch(`/api/cutting-maps/${map.id}/dxf`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${map.name}.dxf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Ошибка скачивания DXF:', error);
    }
  };

  const handleClosePdfDialog = () => {
    setPdfDialogOpen(false);
    setSelectedMap(null);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Карты раскроя ({maps ? maps.length : 0})
      </Typography>
      
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (maps || []).length === 0 ? (
        <Alert severity="info">
          Карты раскроя не найдены. Создайте новую карту раскроя для начала работы.
        </Alert>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Название</TableCell>
                  <TableCell>Материал</TableCell>
                  <TableCell>Толщина</TableCell>
                  <TableCell>Размеры</TableCell>
                  <TableCell>Эффективность</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedMaps.map((map) => (
                  <TableRow key={map.id}>
                    <TableCell>{map.id}</TableCell>
                    <TableCell>{map.name}</TableCell>
                    <TableCell>{map.material}</TableCell>
                    <TableCell>{map.thickness}</TableCell>
                    <TableCell>{map.dimensions}</TableCell>
                    <TableCell>{map.efficiency}%</TableCell>
                    <TableCell>
                      <Chip 
                        label={map.status} 
                        color={map.status === 'completed' ? 'success' : 'warning'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton onClick={() => handleViewPdf(map)} title="Просмотр PDF">
                        <PdfIcon />
                      </IconButton>
                      <IconButton onClick={() => handleDownloadPdf(map)} title="Скачать PDF">
                        <DownloadIcon />
                      </IconButton>
                      <IconButton onClick={() => handleDownloadDxf(map)} title="Скачать DXF">
                        <DxfIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={(maps || []).length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </>
      )}

      {/* Диалог просмотра PDF */}
      <Dialog 
        open={pdfDialogOpen} 
        onClose={handleClosePdfDialog}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Карта раскроя: {selectedMap?.name}
            </Typography>
            <IconButton onClick={handleClosePdfDialog}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedMap && (
            <Box height="600px">
              <iframe
                src={`/api/cutting-maps/${selectedMap.id}/pdf`}
                width="100%"
                height="100%"
                style={{ border: 'none' }}
                title="PDF Viewer"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => selectedMap && handleDownloadPdf(selectedMap)}
            startIcon={<DownloadIcon />}
            variant="contained"
            color="primary"
          >
            Скачать для печати
          </Button>
          <Button onClick={handleClosePdfDialog}>
            Закрыть
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CuttingMaps; 