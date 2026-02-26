"""
Batch processing patterns with connection pooling for background workers.

Designed for the 700-file processing workload while staying within the
Toolforge connection budget.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable, TypeVar

from sqlalchemy import text

from .engine_factory import get_background_engine, get_connection

logger = logging.getLogger(__name__)
T = TypeVar("T")
R = TypeVar("R")


class BatchProcessor:
    """
    Process large batches of items with controlled concurrency.

    max_workers should not exceed the background engine's pool_size (4).
    Each worker borrows exactly one connection at a time, so:
      peak connections = max_workers x pods = 4 x 2 = 8
    """

    def __init__(self, max_workers: int = 4, batch_size: int = 50):
        # Warn if caller requests more workers than pool slots available
        if max_workers > 4:
            logger.warning(
                "event=batch_worker_count_warning "
                "max_workers=%s bg_pool_size=4 — "
                "excess workers will queue on the pool and slow throughput",
                max_workers,
            )
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.engine = get_background_engine()

    def process_items(
        self,
        items: Iterable[T],
        processor: Callable[[T, Any], R],
        error_handler: Callable[[T, Exception], None] | None = None,
    ) -> list[R]:
        """
        Process items concurrently using a thread pool backed by the connection pool.

        Each worker borrows one connection, processes one item, then returns the
        connection to the pool before picking up the next item.

        Args:
            items:         Items to process.
            processor:     Function(item, db_conn) -> result called per item.
            error_handler: Optional callback(item, exc) on per-item failures.

        Returns:
            List of successful results (failed items are excluded).
        """
        items_list = list(items)
        results, errors = [], []

        logger.info(
            "event=batch_start items=%s workers=%s batch_size=%s",
            len(items_list),
            self.max_workers,
            self.batch_size,
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_item = {
                executor.submit(self._process_single, item, processor): item
                for item in items_list
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    logger.error("event=batch_item_error item=%s error=%s", item, exc)
                    errors.append((item, exc))
                    if error_handler:
                        error_handler(item, exc)

        logger.info(
            "event=batch_complete total=%s success=%s errors=%s",
            len(items_list),
            len(results),
            len(errors),
        )
        return results

    def _process_single(self, item: T, processor: Callable[[T, Any], R]) -> R:
        """Borrow one connection from the pool, process the item, return connection."""
        with get_connection(self.engine) as conn:
            return processor(item, conn)

    def bulk_insert(
        self,
        table: str,
        records: list[dict],
        on_duplicate: str | None = None,
    ) -> int:
        """
        Insert records in batches of self.batch_size.

        Args:
            table:        Target table name.
            records:      List of row dicts; all must share the same keys.
            on_duplicate: Optional ON DUPLICATE KEY UPDATE clause.

        Returns:
            Total rows affected.
        """
        if not records:
            return 0

        total = 0
        columns = list(records[0].keys())

        # Build INSERT template once, outside the batch loop
        placeholders = ", ".join(f":{col}" for col in columns)
        columns_str = ", ".join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        if on_duplicate:
            sql += f" {on_duplicate}"

        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            with get_connection(self.engine) as conn:
                result = conn.execute(text(sql), batch)
                total += result.rowcount

            logger.debug(
                "event=bulk_insert_batch batch=%s/%s rows=%s",
                i // self.batch_size + 1,
                -(-len(records) // self.batch_size),  # ceiling division
                result.rowcount,
            )

        return total

    def chunked_query(
        self,
        sql: str,
        params: dict | None = None,
        chunk_size: int = 1000,
    ):
        """
        Yield query results in chunks to limit memory usage.

        Each chunk borrows and immediately returns one connection, keeping the
        pool free between chunks for other workers.

        Usage:
            for chunk in processor.chunked_query("SELECT * FROM tasks"):
                process(chunk)
        """
        offset = 0
        while True:
            chunk_sql = f"{sql} LIMIT {chunk_size} OFFSET {offset}"
            with get_connection(self.engine, readonly=True) as conn:
                result = conn.execute(text(chunk_sql), params or {})
                rows = [dict(row._mapping) for row in result]

            if not rows:
                break

            yield rows
            offset += chunk_size

            # Stop early if the last page was partial (no more rows remain)
            if len(rows) < chunk_size:
                break


def process_files_with_pool(
    files: list[str],
    process_func: Callable[[str], Any],
    max_workers: int = 4,
) -> dict:
    """
    High-level function for processing file batches.

    Example usage for the 700-file workload:
        results = process_files_with_pool(
            files=file_list,
            process_func=process_single_file,
            max_workers=4,
        )
    """
    processor = BatchProcessor(max_workers=max_workers)

    def wrapper(file_path: str, conn) -> dict:
        # Pass connection to processor if needed for DB operations
        return {"file": file_path, "result": process_func(file_path)}

    results = processor.process_items(files, wrapper)

    return {
        "total": len(files),
        "successful": len([r for r in results if r["result"] is not None]),
        "results": results,
    }
