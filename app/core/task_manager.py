"""
Gerenciador de tarefas assíncronas para processamento de longa duração.
"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Status das tarefas."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo:
    """Informações de uma tarefa."""
    
    def __init__(self, task_id: str, task_type: str):
        self.task_id = task_id
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.message = "Tarefa iniciada"
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def update(self, status: TaskStatus = None, progress: int = None, 
               message: str = None, result: Any = None, error: str = None):
        """Atualiza informações da tarefa."""
        if status:
            self.status = status
        if progress is not None:
            self.progress = progress
        if message:
            self.message = message
        if result is not None:
            self.result = result
        if error:
            self.error = error
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TaskManager:
    """Gerenciador de tarefas assíncronas."""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.cleanup_interval = 3600  # 1 hora
    
    def create_task(self, task_type: str) -> str:
        """Cria uma nova tarefa."""
        task_id = str(uuid.uuid4())
        task_info = TaskInfo(task_id, task_type)
        self.tasks[task_id] = task_info
        logger.info(f"Tarefa criada: {task_id} ({task_type})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Obtém informações de uma tarefa."""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs):
        """Atualiza uma tarefa."""
        if task_id in self.tasks:
            self.tasks[task_id].update(**kwargs)
            logger.debug(f"Tarefa atualizada: {task_id}")
    
    def complete_task(self, task_id: str, result: Any):
        """Marca tarefa como concluída."""
        self.update_task(
            task_id, 
            status=TaskStatus.COMPLETED, 
            progress=100, 
            message="Tarefa concluída com sucesso",
            result=result
        )
        logger.info(f"Tarefa concluída: {task_id}")
    
    def fail_task(self, task_id: str, error: str):
        """Marca tarefa como falhada."""
        self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="Tarefa falhou",
            error=error
        )
        logger.error(f"Tarefa falhada: {task_id} - {error}")
    
    def cleanup_old_tasks(self):
        """Remove tarefas antigas."""
        now = datetime.now(timezone.utc)
        to_remove = []
        
        for task_id, task_info in self.tasks.items():
            age = (now - task_info.updated_at).total_seconds()
            if age > self.cleanup_interval:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            logger.info(f"Tarefa removida por idade: {task_id}")
    
    async def run_task(self, task_id: str, coro):
        """Executa uma corrotina como tarefa."""
        try:
            self.update_task(task_id, status=TaskStatus.PROCESSING, message="Processando...")
            result = await coro
            self.complete_task(task_id, result)
            return result
        except Exception as e:
            self.fail_task(task_id, str(e))
            raise


# Instância global
task_manager = TaskManager()
