import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Rating,
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
  Grid,
} from '@mui/material'
import { useDispatch } from 'react-redux'
import { submitFeedback } from '../../store/slices/aiSlice.js'

const FeedbackDialog = ({ open, onClose }) => {
  const dispatch = useDispatch()
  const [feedback, setFeedback] = useState({
    satisfactionRating: 3,
    acceptedCorrections: '',
    rejectedCorrections: '',
    comments: '',
    includeInTraining: true,
  })

  const handleSubmit = () => {
    const feedbackData = {
      ...feedback,
      acceptedCorrections: feedback.acceptedCorrections
        .split(',')
        .map(id => id.trim())
        .filter(id => id),
      rejectedCorrections: feedback.rejectedCorrections
        .split(',')
        .map(id => id.trim())
        .filter(id => id),
    }

    dispatch(submitFeedback(feedbackData))
    onClose()
    
    // Reset form
    setFeedback({
      satisfactionRating: 3,
      acceptedCorrections: '',
      rejectedCorrections: '',
      comments: '',
      includeInTraining: true,
    })
  }

  const handleClose = () => {
    onClose()
    // Reset form
    setFeedback({
      satisfactionRating: 3,
      acceptedCorrections: '',
      rejectedCorrections: '',
      comments: '',
      includeInTraining: true,
    })
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h6">
          💬 Обратная связь о работе AI
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Ваш отзыв поможет улучшить работу системы
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        <Grid container spacing={3}>
          {/* Rating */}
          <Grid item xs={12}>
            <Typography component="legend" gutterBottom>
              Оцените работу AI
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Rating
                value={feedback.satisfactionRating}
                onChange={(event, newValue) => {
                  setFeedback(prev => ({ ...prev, satisfactionRating: newValue }))
                }}
                size="large"
              />
              <Typography variant="body2" color="text.secondary">
                {feedback.satisfactionRating}/5 звезд
              </Typography>
            </Box>
          </Grid>

          {/* Accepted Corrections */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Принятые предложения (ID через запятую)"
              value={feedback.acceptedCorrections}
              onChange={(e) => setFeedback(prev => ({ 
                ...prev, 
                acceptedCorrections: e.target.value 
              }))}
              placeholder="S1, S3, S5"
              helperText="Введите ID предложений, которые вы приняли"
            />
          </Grid>

          {/* Rejected Corrections */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Отклоненные предложения (ID через запятую)"
              value={feedback.rejectedCorrections}
              onChange={(e) => setFeedback(prev => ({ 
                ...prev, 
                rejectedCorrections: e.target.value 
              }))}
              placeholder="S2, S4"
              helperText="Введите ID предложений, которые вы отклонили"
            />
          </Grid>

          {/* Comments */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Дополнительные комментарии"
              value={feedback.comments}
              onChange={(e) => setFeedback(prev => ({ 
                ...prev, 
                comments: e.target.value 
              }))}
              placeholder="Расскажите о своем опыте работы с AI..."
              helperText="Ваши комментарии помогут улучшить систему"
            />
          </Grid>

          {/* Training Checkbox */}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={feedback.includeInTraining}
                  onChange={(e) => setFeedback(prev => ({ 
                    ...prev, 
                    includeInTraining: e.target.checked 
                  }))}
                  color="primary"
                />
              }
              label="Использовать этот отзыв для улучшения AI"
            />
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} color="inherit">
          Отмена
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          color="primary"
          disabled={feedback.satisfactionRating === 0}
        >
          Отправить
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default FeedbackDialog 