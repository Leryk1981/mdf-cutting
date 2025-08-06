import React from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Box,
} from '@mui/material'
import {
  CheckCircle,
  Cancel,
  Info,
  Visibility,
} from '@mui/icons-material'

const SuggestionsTable = ({ suggestions }) => {
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success'
    if (confidence >= 0.6) return 'warning'
    return 'error'
  }

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'Высокая'
    if (confidence >= 0.6) return 'Средняя'
    return 'Низкая'
  }

  const handleApply = (suggestion) => {
    // TODO: Implement apply suggestion
    console.log('Apply suggestion:', suggestion)
  }

  const handleReject = (suggestion) => {
    // TODO: Implement reject suggestion
    console.log('Reject suggestion:', suggestion)
  }

  const handleViewDetails = (suggestion) => {
    // TODO: Implement view details
    console.log('View details:', suggestion)
  }

  return (
    <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
      <Table stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>Тип корректировки</TableCell>
            <TableCell>Уверенность</TableCell>
            <TableCell>Потенциал улучшения</TableCell>
            <TableCell>Действия</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {suggestions.map((suggestion, index) => (
            <TableRow key={index} hover>
              <TableCell>{suggestion.piece_id || `S${index + 1}`}</TableCell>
              <TableCell>
                <Chip
                  label={suggestion.correction_type || 'Неизвестно'}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={`${Math.round(suggestion.confidence * 100)}%`}
                    size="small"
                    color={getConfidenceColor(suggestion.confidence)}
                  />
                  <Typography variant="caption" color="text.secondary">
                    ({getConfidenceLabel(suggestion.confidence)})
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {suggestion.expected_improvement ? 
                    `${(suggestion.expected_improvement * 100).toFixed(1)}%` : 
                    'N/A'
                  }
                </Typography>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="Применить">
                    <IconButton
                      size="small"
                      color="success"
                      onClick={() => handleApply(suggestion)}
                    >
                      <CheckCircle />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Отклонить">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleReject(suggestion)}
                    >
                      <Cancel />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Подробнее">
                    <IconButton
                      size="small"
                      color="info"
                      onClick={() => handleViewDetails(suggestion)}
                    >
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default SuggestionsTable 