"""Database store for fix_nested tasks."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
import json

from .db_class import Database

logger = logging.getLogger("svg_translate")


class FixNestedTaskStore:
    """Database store for managing fix_nested tasks."""

    def __init__(self, db: Database) -> None:
        """Initialize the fix_nested task store.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self._init_schema()

    def _init_schema(self) -> None:
        """Create the fix_nested_tasks table if it doesn't exist."""
        ddl = """
            CREATE TABLE IF NOT EXISTS fix_nested_tasks (
                id VARCHAR(128) PRIMARY KEY,
                username TEXT NULL,
                filename TEXT NOT NULL,
                status VARCHAR(64) NOT NULL,
                nested_tags_before INT NULL,
                nested_tags_after INT NULL,
                nested_tags_fixed INT NULL,
                download_result JSON NULL,
                upload_result JSON NULL,
                error_message TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_fix_nested_status (status),
                INDEX idx_fix_nested_username (username(255)),
                INDEX idx_fix_nested_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        self.db.execute_query_safe(ddl)

    def create_task(
        self,
        task_id: str,
        filename: str,
        username: Optional[str] = None,
    ) -> bool:
        """Create a new fix_nested task record.
        
        Args:
            task_id: Unique task identifier
            filename: Name of the SVG file
            username: Username of the user who created the task
            
        Returns:
            True if task was created successfully
        """
        query = """
            INSERT INTO fix_nested_tasks (id, username, filename, status)
            VALUES (%s, %s, %s, %s)
        """
        try:
            self.db.execute_query_safe(query, (task_id, username, filename, "pending"))
            logger.info(f"Created fix_nested task {task_id} for file {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to create fix_nested task {task_id}: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Retrieve a task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task data as dictionary, or None if not found
        """
        query = """
            SELECT * FROM fix_nested_tasks WHERE id = %s
        """
        results = self.db.fetch_query_safe(query, (task_id,))
        if results:
            task = dict(results[0])
            # Parse JSON fields
            if task.get("download_result"):
                try:
                    task["download_result"] = json.loads(task["download_result"])
                except (json.JSONDecodeError, TypeError):
                    pass
            if task.get("upload_result"):
                try:
                    task["upload_result"] = json.loads(task["upload_result"])
                except (json.JSONDecodeError, TypeError):
                    pass
            return task
        return None

    def update_status(self, task_id: str, status: str) -> bool:
        """Update task status.
        
        Args:
            task_id: Task identifier
            status: New status (pending/running/completed/failed/cancelled)
            
        Returns:
            True if update was successful
        """
        query = """
            UPDATE fix_nested_tasks SET status = %s WHERE id = %s
        """
        try:
            self.db.execute_query_safe(query, (status, task_id))
            logger.debug(f"Updated fix_nested task {task_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update status for task {task_id}: {e}")
            return False

    def update_nested_counts(
        self,
        task_id: str,
        before: Optional[int] = None,
        after: Optional[int] = None,
        fixed: Optional[int] = None,
    ) -> bool:
        """Update nested tag counts.
        
        Args:
            task_id: Task identifier
            before: Count before fix
            after: Count after fix
            fixed: Count of tags fixed
            
        Returns:
            True if update was successful
        """
        updates = []
        params = []
        
        if before is not None:
            updates.append("nested_tags_before = %s")
            params.append(before)
        if after is not None:
            updates.append("nested_tags_after = %s")
            params.append(after)
        if fixed is not None:
            updates.append("nested_tags_fixed = %s")
            params.append(fixed)
        
        if not updates:
            return True
        
        params.append(task_id)
        query = f"UPDATE fix_nested_tasks SET {', '.join(updates)} WHERE id = %s"
        
        try:
            self.db.execute_query_safe(query, tuple(params))
            return True
        except Exception as e:
            logger.error(f"Failed to update nested counts for task {task_id}: {e}")
            return False

    def update_download_result(self, task_id: str, result: Dict) -> bool:
        """Update download result.
        
        Args:
            task_id: Task identifier
            result: Download result data
            
        Returns:
            True if update was successful
        """
        query = """
            UPDATE fix_nested_tasks SET download_result = %s WHERE id = %s
        """
        try:
            self.db.execute_query_safe(query, (json.dumps(result), task_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update download result for task {task_id}: {e}")
            return False

    def update_upload_result(self, task_id: str, result: Dict) -> bool:
        """Update upload result.
        
        Args:
            task_id: Task identifier
            result: Upload result data
            
        Returns:
            True if update was successful
        """
        query = """
            UPDATE fix_nested_tasks SET upload_result = %s WHERE id = %s
        """
        try:
            self.db.execute_query_safe(query, (json.dumps(result), task_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update upload result for task {task_id}: {e}")
            return False

    def update_error(self, task_id: str, error_message: str) -> bool:
        """Update error message.
        
        Args:
            task_id: Task identifier
            error_message: Error message
            
        Returns:
            True if update was successful
        """
        query = """
            UPDATE fix_nested_tasks SET error_message = %s, status = 'failed' WHERE id = %s
        """
        try:
            self.db.execute_query_safe(query, (error_message, task_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update error for task {task_id}: {e}")
            return False

    def list_tasks(
        self,
        status: Optional[str] = None,
        username: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """List tasks with optional filters.
        
        Args:
            status: Filter by status
            username: Filter by username
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of task dictionaries
        """
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        if username:
            conditions.append("username = %s")
            params.append(username)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT * FROM fix_nested_tasks
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        try:
            results = self.db.fetch_query_safe(query, tuple(params))
            tasks = []
            for row in results:
                task = dict(row)
                # Parse JSON fields
                if task.get("download_result"):
                    try:
                        task["download_result"] = json.loads(task["download_result"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if task.get("upload_result"):
                    try:
                        task["upload_result"] = json.loads(task["upload_result"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                tasks.append(task)
            return tasks
        except Exception as e:
            logger.error(f"Failed to list fix_nested tasks: {e}")
            return []

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if deletion was successful
        """
        query = """
            DELETE FROM fix_nested_tasks WHERE id = %s
        """
        try:
            self.db.execute_query_safe(query, (task_id,))
            logger.info(f"Deleted fix_nested task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
