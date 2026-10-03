"""Worker entrypoint. Run with `python -m api.worker`."""

from arq.run_worker import run_worker

from api.jobs import WorkerSettings


if __name__ == "__main__":
    run_worker(WorkerSettings)