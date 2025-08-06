"""
Система обучения ML-моделей.

Этот модуль содержит:
- Тренеры для моделей предсказания
- Обучение с подкреплением
- Логирование экспериментов
"""

import torch
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from tqdm import tqdm
import logging
from pathlib import Path
import json
from datetime import datetime

try:
    import mlflow
    import mlflow.pytorch
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logging.warning("MLflow не установлен. Логирование экспериментов будет ограничено.")

logger = logging.getLogger(__name__)


class CorrectionModelTrainer:
    """Тренер для моделей предсказания корректировок"""
    
    def __init__(self, model, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.device = torch.device(config.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
        self.model.to(self.device)
        
        # Оптимизатор
        self.optimizer = optim.Adam(
            self.model.parameters(), 
            lr=config.get("learning_rate", 0.001),
            weight_decay=config.get("weight_decay", 1e-5)
        )
        
        # Планировщик learning rate
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, 
            mode='min', 
            factor=0.5, 
            patience=5, 
            verbose=True
        )
        
        # Функции потерь
        self.params_criterion = nn.MSELoss()
        self.confidence_criterion = nn.BCELoss()
        self.type_criterion = nn.CrossEntropyLoss()
        
        # MLflow для экспериментов
        if MLFLOW_AVAILABLE:
            mlflow.set_experiment("mdf_cutting_ai")
        
        self.best_val_loss = float('inf')
        self.training_history = []
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int):
        """Основной цикл обучения"""
        if MLFLOW_AVAILABLE:
            with mlflow.start_run():
                mlflow.log_params(self.config)
                return self._train_with_mlflow(train_loader, val_loader, epochs)
        else:
            return self._train_without_mlflow(train_loader, val_loader, epochs)
    
    def _train_with_mlflow(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int):
        """Обучение с логированием в MLflow"""
        for epoch in range(epochs):
            # Обучение
            train_loss = self._train_epoch(train_loader)
            
            # Валидация
            val_loss, val_metrics = self._validate_epoch(val_loader)
            
            # Обновление LR
            self.scheduler.step(val_loss)
            
            # Логирование
            mlflow.log_metrics({
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_confidence_acc": val_metrics.get("confidence_acc", 0),
                "val_params_mae": val_metrics.get("params_mae", 0),
                "lr": self.optimizer.param_groups[0]['lr']
            }, step=epoch)
            
            print(f"Epoch {epoch+1}/{epochs} - Train: {train_loss:.4f}, Val: {val_loss:.4f}")
            
            # Сохранение лучшей модели
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self._save_checkpoint(epoch, val_loss)
                mlflow.pytorch.log_model(self.model, "best_model")
        
        return self.best_val_loss
    
    def _train_without_mlflow(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int):
        """Обучение без MLflow"""
        for epoch in range(epochs):
            # Обучение
            train_loss = self._train_epoch(train_loader)
            
            # Валидация
            val_loss, val_metrics = self._validate_epoch(val_loader)
            
            # Обновление LR
            self.scheduler.step(val_loss)
            
            # Логирование
            epoch_info = {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_metrics": val_metrics,
                "lr": self.optimizer.param_groups[0]['lr']
            }
            self.training_history.append(epoch_info)
            
            print(f"Epoch {epoch+1}/{epochs} - Train: {train_loss:.4f}, Val: {val_loss:.4f}")
            
            # Сохранение лучшей модели
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self._save_checkpoint(epoch, val_loss)
        
        return self.best_val_loss
    
    def _train_epoch(self, train_loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        
        for batch in tqdm(train_loader, desc="Training"):
            self.optimizer.zero_grad()
            
            # Подготовка данных
            features = {k: v.to(self.device) for k, v in batch["features"].items()}
            targets = {k: v.to(self.device) for k, v in batch["targets"].items()}
            
            # Forward pass
            outputs = self.model(features)
            
            # Расчет потерь
            params_loss = self.params_criterion(
                outputs["correction_params"], 
                targets["correction_params"]
            )
            
            confidence_loss = self.confidence_criterion(
                outputs["improvement_score"], 
                targets["confidence"]
            )
            
            type_loss = self.type_criterion(
                outputs["correction_type"], 
                targets["correction_type"]
            )
            
            # Взвешенная общая потеря
            loss = (
                0.5 * params_loss +
                0.3 * confidence_loss +
                0.2 * type_loss
            )
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(train_loader)
    
    def _validate_epoch(self, val_loader: DataLoader) -> Tuple[float, Dict[str, float]]:
        self.model.eval()
        total_loss = 0.0
        all_confidences = []
        all_targets = []
        all_params_errors = []
        
        with torch.no_grad():
            for batch in val_loader:
                features = {k: v.to(self.device) for k, v in batch["features"].items()}
                targets = {k: v.to(self.device) for k, v in batch["targets"].items()}
                
                outputs = self.model(features)
                
                # Потери
                params_loss = self.params_criterion(
                    outputs["correction_params"], 
                    targets["correction_params"]
                )
                
                confidence_loss = self.confidence_criterion(
                    outputs["improvement_score"], 
                    targets["confidence"]
                )
                
                type_loss = self.type_criterion(
                    outputs["correction_type"], 
                    targets["correction_type"]
                )
                
                loss = (
                    0.5 * params_loss +
                    0.3 * confidence_loss +
                    0.2 * type_loss
                )
                
                total_loss += loss.item()
                
                # Метрики
                all_confidences.extend(outputs["improvement_score"].cpu().numpy())
                all_targets.extend(targets["confidence"].cpu().numpy())
                
                params_error = F.l1_loss(
                    outputs["correction_params"], 
                    targets["correction_params"]
                )
                all_params_errors.append(params_error.item())
        
        # Расчет метрик
        confidence_acc = np.mean(
            np.round(all_confidences) == all_targets
        ) if all_confidences else 0.0
        avg_params_mae = np.mean(all_params_errors) if all_params_errors else 0.0
        
        avg_loss = total_loss / len(val_loader)
        metrics = {
            "confidence_acc": confidence_acc,
            "params_mae": avg_params_mae
        }
        
        return avg_loss, metrics
    
    def _save_checkpoint(self, epoch: int, val_loss: float):
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'config': self.config,
            'training_history': self.training_history
        }
        
        checkpoint_dir = Path("models/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch}.pth"
        torch.save(checkpoint, checkpoint_path)
        
        logger.info(f"Checkpoint сохранен: {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """Загрузка чекпоинта"""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        logger.info(f"Checkpoint загружен: {checkpoint_path}")
        return checkpoint


class ReinforcementTrainer:
    """Тренер для RL-модели"""
    
    def __init__(self, model, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.device = torch.device(config.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
        self.model.to(self.device)
        
        # Оптимизатор
        self.optimizer = optim.Adam(self.model.parameters(), lr=config.get("lr", 0.001))
        
        # Параметры RL
        self.gamma = config.get("gamma", 0.99)  # дисконтирование
        self.eps_start = config.get("eps_start", 0.9)
        self.eps_end = config.get("eps_end", 0.05)
        self.eps_decay = config.get("eps_decay", 200)
        self.steps_done = 0
        
        # Память опыта (Replay Buffer)
        self.memory = []
        self.capacity = config.get("memory_capacity", 10000)
        
        # Логирование
        self.training_history = []
    
    def remember(self, state, action, reward, next_state, done):
        """Сохранение опыта в память"""
        self.memory.append((state, action, reward, next_state, done))
        if len(self.memory) > self.capacity:
            self.memory.pop(0)
    
    def select_action(self, state, training=True):
        """Выбор действия с epsilon-greedy стратегией"""
        sample = np.random.random()
        eps_threshold = self.eps_end + (self.eps_start - self.eps_end) * \
                        np.exp(-1. * self.steps_done / self.eps_decay)
        self.steps_done += 1
        
        if training and sample > eps_threshold:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                _, action_probs = self.model(state_tensor)
                return torch.argmax(action_probs).item()
        else:
            return np.random.randint(0, self.model.actor[-1].out_features)
    
    def train_step(self, batch_size=32):
        """Шаг обучения на мини-пакете из памяти"""
        if len(self.memory) < batch_size:
            return 0.0
        
        # Сэмплирование опыта
        indices = np.random.choice(len(self.memory), batch_size, replace=False)
        batch = [self.memory[i] for i in indices]
        
        states = torch.FloatTensor([b[0] for b in batch]).to(self.device)
        actions = torch.LongTensor([b[1] for b in batch]).to(self.device)
        rewards = torch.FloatTensor([b[2] for b in batch]).to(self.device)
        next_states = torch.FloatTensor([b[3] for b in batch]).to(self.device)
        dones = torch.BoolTensor([b[4] for b in batch]).to(self.device)
        
        # Оценка текущих Q-значений
        current_state_values, current_action_probs = self.model(states)
        current_q_values = current_state_values.gather(1, actions.unsqueeze(1))
        
        # Оценка следующих Q-значений
        with torch.no_grad():
            next_state_values, _ = self.model(next_states)
            next_q_values = next_state_values.max(1)[0]
            expected_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # Потери
        loss = F.smooth_l1_loss(current_q_values.squeeze(), expected_q_values)
        
        # Обучение
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        return loss.item()
    
    def train_episode(self, env, max_steps=1000):
        """Обучение на одном эпизоде"""
        state = env.reset()
        total_reward = 0
        episode_losses = []
        
        for step in range(max_steps):
            # Выбор действия
            action = self.select_action(state, training=True)
            
            # Выполнение действия
            next_state, reward, done, _ = env.step(action)
            
            # Сохранение опыта
            self.remember(state, action, reward, next_state, done)
            
            # Обучение
            if len(self.memory) > 32:
                loss = self.train_step(batch_size=32)
                episode_losses.append(loss)
            
            total_reward += reward
            state = next_state
            
            if done:
                break
        
        avg_loss = np.mean(episode_losses) if episode_losses else 0.0
        
        episode_info = {
            "total_reward": total_reward,
            "steps": step + 1,
            "avg_loss": avg_loss,
            "epsilon": self.eps_end + (self.eps_start - self.eps_end) * \
                      np.exp(-1. * self.steps_done / self.eps_decay)
        }
        
        self.training_history.append(episode_info)
        
        return episode_info
    
    def save_model(self, path: str):
        """Сохранение модели"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'training_history': self.training_history,
            'steps_done': self.steps_done
        }, path)
        
        logger.info(f"RL модель сохранена: {path}")
    
    def load_model(self, path: str):
        """Загрузка модели"""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_history = checkpoint.get('training_history', [])
        self.steps_done = checkpoint.get('steps_done', 0)
        
        logger.info(f"RL модель загружена: {path}")


class EnsembleTrainer:
    """Тренер для ансамбля моделей"""
    
    def __init__(self, ensemble_model, config: Dict[str, Any]):
        self.ensemble_model = ensemble_model
        self.config = config
        self.device = torch.device(config.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
        self.ensemble_model.to(self.device)
        
        # Оптимизаторы для каждой модели
        self.optimizers = [
            optim.Adam(model.parameters(), lr=config.get("learning_rate", 0.001))
            for model in self.ensemble_model.models
        ]
        
        # Оптимизатор для мета-обучателя
        self.meta_optimizer = optim.Adam(
            self.ensemble_model.meta_learner.parameters(),
            lr=config.get("meta_learning_rate", 0.0001)
        )
        
        # Функции потерь
        self.params_criterion = nn.MSELoss()
        self.confidence_criterion = nn.BCELoss()
        self.type_criterion = nn.CrossEntropyLoss()
        
        self.training_history = []
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int):
        """Обучение ансамбля"""
        for epoch in range(epochs):
            # Обучение отдельных моделей
            individual_losses = self._train_individual_models(train_loader)
            
            # Обучение мета-обучателя
            meta_loss = self._train_meta_learner(train_loader)
            
            # Валидация
            val_loss, val_metrics = self._validate_ensemble(val_loader)
            
            # Логирование
            epoch_info = {
                "epoch": epoch + 1,
                "individual_losses": individual_losses,
                "meta_loss": meta_loss,
                "val_loss": val_loss,
                "val_metrics": val_metrics
            }
            self.training_history.append(epoch_info)
            
            print(f"Epoch {epoch+1}/{epochs} - Val: {val_loss:.4f}")
        
        return val_loss
    
    def _train_individual_models(self, train_loader: DataLoader) -> List[float]:
        """Обучение отдельных моделей ансамбля"""
        losses = []
        
        for i, (model, optimizer) in enumerate(zip(self.ensemble_model.models, self.optimizers)):
            model.train()
            total_loss = 0.0
            
            for batch in train_loader:
                optimizer.zero_grad()
                
                features = {k: v.to(self.device) for k, v in batch["features"].items()}
                targets = {k: v.to(self.device) for k, v in batch["targets"].items()}
                
                outputs = model(features)
                
                # Потери
                params_loss = self.params_criterion(
                    outputs["correction_params"], 
                    targets["correction_params"]
                )
                
                confidence_loss = self.confidence_criterion(
                    outputs["improvement_score"], 
                    targets["confidence"]
                )
                
                type_loss = self.type_criterion(
                    outputs["correction_type"], 
                    targets["correction_type"]
                )
                
                loss = 0.5 * params_loss + 0.3 * confidence_loss + 0.2 * type_loss
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            losses.append(total_loss / len(train_loader))
        
        return losses
    
    def _train_meta_learner(self, train_loader: DataLoader) -> float:
        """Обучение мета-обучателя"""
        self.ensemble_model.meta_learner.train()
        total_loss = 0.0
        
        for batch in train_loader:
            self.meta_optimizer.zero_grad()
            
            features = {k: v.to(self.device) for k, v in batch["features"].items()}
            targets = {k: v.to(self.device) for k, v in batch["targets"].items()}
            
            outputs = self.ensemble_model(features)
            
            # Потери для мета-обучателя
            params_loss = self.params_criterion(
                outputs["correction_params"], 
                targets["correction_params"]
            )
            
            confidence_loss = self.confidence_criterion(
                outputs["improvement_score"], 
                targets["confidence"]
            )
            
            type_loss = self.type_criterion(
                outputs["correction_type"], 
                targets["correction_type"]
            )
            
            loss = 0.5 * params_loss + 0.3 * confidence_loss + 0.2 * type_loss
            
            loss.backward()
            self.meta_optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(train_loader)
    
    def _validate_ensemble(self, val_loader: DataLoader) -> Tuple[float, Dict[str, float]]:
        """Валидация ансамбля"""
        self.ensemble_model.eval()
        total_loss = 0.0
        all_confidences = []
        all_targets = []
        
        with torch.no_grad():
            for batch in val_loader:
                features = {k: v.to(self.device) for k, v in batch["features"].items()}
                targets = {k: v.to(self.device) for k, v in batch["targets"].items()}
                
                outputs = self.ensemble_model(features)
                
                # Потери
                params_loss = self.params_criterion(
                    outputs["correction_params"], 
                    targets["correction_params"]
                )
                
                confidence_loss = self.confidence_criterion(
                    outputs["improvement_score"], 
                    targets["confidence"]
                )
                
                type_loss = self.type_criterion(
                    outputs["correction_type"], 
                    targets["correction_type"]
                )
                
                loss = 0.5 * params_loss + 0.3 * confidence_loss + 0.2 * type_loss
                total_loss += loss.item()
                
                # Метрики
                all_confidences.extend(outputs["improvement_score"].cpu().numpy())
                all_targets.extend(targets["confidence"].cpu().numpy())
        
        avg_loss = total_loss / len(val_loader)
        confidence_acc = np.mean(np.round(all_confidences) == all_targets) if all_confidences else 0.0
        
        metrics = {
            "confidence_acc": confidence_acc,
            "ensemble_weights": outputs["ensemble_weights"].cpu().numpy().tolist()
        }
        
        return avg_loss, metrics
    
    def save_ensemble(self, path: str):
        """Сохранение ансамбля"""
        torch.save({
            'ensemble_state_dict': self.ensemble_model.state_dict(),
            'config': self.config,
            'training_history': self.training_history
        }, path)
        
        logger.info(f"Ансамбль сохранен: {path}")
    
    def load_ensemble(self, path: str):
        """Загрузка ансамбля"""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.ensemble_model.load_state_dict(checkpoint['ensemble_state_dict'])
        self.training_history = checkpoint.get('training_history', [])
        
        logger.info(f"Ансамбль загружен: {path}")


class ModelEvaluator:
    """Оценщик качества моделей"""
    
    def __init__(self, model, device: str = "cpu"):
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()
    
    def evaluate(self, test_loader: DataLoader) -> Dict[str, float]:
        """Оценка модели на тестовых данных"""
        total_loss = 0.0
        all_predictions = []
        all_targets = []
        
        with torch.no_grad():
            for batch in test_loader:
                features = {k: v.to(self.device) for k, v in batch["features"].items()}
                targets = {k: v.to(self.device) for k, v in batch["targets"].items()}
                
                outputs = self.model(features)
                
                # Сохраняем предсказания и цели
                all_predictions.append(outputs)
                all_targets.append(targets)
        
        # Вычисляем метрики
        metrics = self._calculate_metrics(all_predictions, all_targets)
        
        return metrics
    
    def _calculate_metrics(self, predictions: List[Dict], targets: List[Dict]) -> Dict[str, float]:
        """Вычисление метрик качества"""
        # Объединяем все предсказания и цели
        all_correction_params = []
        all_correction_types = []
        all_improvement_scores = []
        
        all_target_params = []
        all_target_types = []
        all_target_confidences = []
        
        for pred, target in zip(predictions, targets):
            all_correction_params.append(pred["correction_params"].cpu().numpy())
            all_correction_types.append(pred["correction_type"].cpu().numpy())
            all_improvement_scores.append(pred["improvement_score"].cpu().numpy())
            
            all_target_params.append(target["correction_params"].cpu().numpy())
            all_target_types.append(target["correction_type"].cpu().numpy())
            all_target_confidences.append(target["confidence"].cpu().numpy())
        
        # Преобразуем в numpy массивы
        pred_params = np.concatenate(all_correction_params, axis=0)
        pred_types = np.concatenate(all_correction_types, axis=0)
        pred_scores = np.concatenate(all_improvement_scores, axis=0)
        
        target_params = np.concatenate(all_target_params, axis=0)
        target_types = np.concatenate(all_target_types, axis=0)
        target_confidences = np.concatenate(all_target_confidences, axis=0)
        
        # Вычисляем метрики
        params_mae = np.mean(np.abs(pred_params - target_params))
        params_rmse = np.sqrt(np.mean((pred_params - target_params) ** 2))
        
        type_accuracy = np.mean(np.argmax(pred_types, axis=1) == np.argmax(target_types, axis=1))
        
        confidence_mae = np.mean(np.abs(pred_scores - target_confidences))
        
        # Дополнительные метрики
        params_correlation = np.corrcoef(pred_params.flatten(), target_params.flatten())[0, 1]
        
        return {
            "params_mae": float(params_mae),
            "params_rmse": float(params_rmse),
            "type_accuracy": float(type_accuracy),
            "confidence_mae": float(confidence_mae),
            "params_correlation": float(params_correlation)
        } 