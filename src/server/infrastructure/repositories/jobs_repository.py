from apscheduler.jobstores.base import BaseJobStore, ConflictingIdError, JobLookupError
from apscheduler.util import datetime_to_utc_timestamp, utc_timestamp_to_datetime
import pickle
import sqlite3
from datetime import datetime, timezone
from apscheduler.job import Job


class SQLiteJobsRepository(BaseJobStore):
    def __init__(self, db_path="db/apscheduler_jobs.sqlite", pickle_protocol=pickle.HIGHEST_PROTOCOL):
        super().__init__()
        self.db_path = db_path
        self.pickle_protocol = pickle_protocol
        self._create_table()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def _create_table(self):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    next_run_time REAL,
                    job_state BLOB
                )
            """)
            conn.commit()

    def lookup_job(self, job_id):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT job_state FROM jobs WHERE id = ?", (job_id,))
            row = c.fetchone()
            if row:
                return self._reconstitute_job(row[0])
            return None

    def get_due_jobs(self, now):
        timestamp = datetime_to_utc_timestamp(now)
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT job_state FROM jobs WHERE next_run_time IS NOT NULL AND next_run_time <= ?", (timestamp,))
            rows = c.fetchall()
            return self._reconstitute_jobs((None, row[0]) for row in rows)

    def get_next_run_time(self):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT next_run_time FROM jobs WHERE next_run_time IS NOT NULL ORDER BY next_run_time ASC LIMIT 1")
            row = c.fetchone()
            if row and row[0] is not None:
                return utc_timestamp_to_datetime(row[0])
            return None

    def get_all_jobs(self):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT job_state FROM jobs")
            rows = c.fetchall()
            jobs = self._reconstitute_jobs((None, row[0]) for row in rows)
            paused_sort_key = datetime(9999, 12, 31, tzinfo=timezone.utc)
            return sorted(jobs, key=lambda job: job.next_run_time or paused_sort_key)

    def add_job(self, job):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM jobs WHERE id = ?", (job.id,))
            if c.fetchone():
                raise ConflictingIdError(job.id)
            job_state = pickle.dumps(job.__getstate__(), self.pickle_protocol)
            next_run_time = datetime_to_utc_timestamp(job.next_run_time) if job.next_run_time else None
            c.execute(
                "INSERT INTO jobs (id, next_run_time, job_state) VALUES (?, ?, ?)",
                (job.id, next_run_time, job_state)
            )
            conn.commit()

    def update_job(self, job):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM jobs WHERE id = ?", (job.id,))
            if not c.fetchone():
                raise JobLookupError(job.id)
            job_state = pickle.dumps(job.__getstate__(), self.pickle_protocol)
            next_run_time = datetime_to_utc_timestamp(job.next_run_time) if job.next_run_time else None
            c.execute(
                "UPDATE jobs SET next_run_time = ?, job_state = ? WHERE id = ?",
                (next_run_time, job_state, job.id)
            )
            conn.commit()

    def remove_job(self, job_id):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            if c.rowcount == 0:
                raise JobLookupError(job_id)
            conn.commit()

    def remove_all_jobs(self):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM jobs")
            conn.commit()

    def _reconstitute_job(self, job_state):
        job_state = pickle.loads(job_state)
        job = Job(scheduler=self._scheduler, id=job_state["id"], **job_state["kwargs"])
        job.__setstate__(job_state)
        return job

    def _reconstitute_jobs(self, job_states):
        jobs = []
        for _, job_state in job_states:
            try:
                jobs.append(self._reconstitute_job(job_state))
            except Exception:
                self._logger.exception("Failed to restore job from state")
        return jobs
