import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Dict, Any

class TaskQueue:
    def __init__(self, queue_dir: str = "./data/tasks"):
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()

    def enqueue(self, task_type: str, payload: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "status": "pending",
            "created_at": time.time(),
        }
        
        task_file = self.queue_dir / f"{task_id}.json"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, ensure_ascii=False)
        
        return task_id

    def dequeue(self) -> Dict[str, Any] | None:
        with self.lock:
            task_files = sorted(self.queue_dir.glob("*.json"), key=lambda x: x.stat().st_mtime)
            
            for task_file in task_files:
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        task_data = json.load(f)
                    
                    if task_data.get("status") == "pending":
                        task_data["status"] = "processing"
                        with open(task_file, "w", encoding="utf-8") as f:
                            json.dump(task_data, f, ensure_ascii=False)
                        
                        return task_data
                except Exception:
                    try:
                        task_file.unlink()
                    except:
                        pass
            
            return None

    def complete(self, task_id: str, result: Dict[str, Any] | None = None):
        task_file = self.queue_dir / f"{task_id}.json"
        if task_file.exists():
            try:
                with open(task_file, "r", encoding="utf-8") as f:
                    task_data = json.load(f)
                
                task_data["status"] = "completed"
                task_data["completed_at"] = time.time()
                if result:
                    task_data["result"] = result
                
                with open(task_file, "w", encoding="utf-8") as f:
                    json.dump(task_data, f, ensure_ascii=False)
            except Exception:
                pass

    def fail(self, task_id: str, error: str):
        task_file = self.queue_dir / f"{task_id}.json"
        if task_file.exists():
            try:
                with open(task_file, "r", encoding="utf-8") as f:
                    task_data = json.load(f)
                
                task_data["status"] = "failed"
                task_data["error"] = error
                task_data["completed_at"] = time.time()
                
                with open(task_file, "w", encoding="utf-8") as f:
                    json.dump(task_data, f, ensure_ascii=False)
            except Exception:
                pass

    def get_status(self, task_id: str) -> str:
        task_file = self.queue_dir / f"{task_id}.json"
        if task_file.exists():
            try:
                with open(task_file, "r", encoding="utf-8") as f:
                    task_data = json.load(f)
                return task_data.get("status", "unknown")
            except Exception:
                return "unknown"
        return "not_found"

    def start_worker(self, handlers: Dict[str, Callable[[Dict[str, Any]], Any]]):
        if self.running:
            return
        
        self.running = True
        
        def worker():
            while self.running:
                task = self.dequeue()
                if task:
                    try:
                        handler = handlers.get(task["task_type"])
                        if handler:
                            result = handler(task["payload"])
                            self.complete(task["task_id"], result)
                        else:
                            self.fail(task["task_id"], f"No handler for {task['task_type']}")
                    except Exception as e:
                        self.fail(task["task_id"], str(e))
                else:
                    time.sleep(1)
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def stop_worker(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)

    def cleanup(self, max_age_seconds: int = 86400):
        now = time.time()
        for task_file in self.queue_dir.glob("*.json"):
            try:
                if task_file.stat().st_mtime < now - max_age_seconds:
                    task_file.unlink()
            except Exception:
                pass

task_queue = TaskQueue()
