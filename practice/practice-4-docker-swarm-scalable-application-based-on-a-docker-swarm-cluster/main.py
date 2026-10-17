"""API постановки CSV-заданий в общую очередь RQ."""
import os
import socket
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from redis import Redis
from redis.exceptions import LockError, RedisError
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job
from rq.registry import StartedJobRegistry

connection = Redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
                            socket_connect_timeout=2, socket_timeout=2)
queue = Queue('csv', connection=connection)
ACTIVE = 'practice4:active'
app = FastAPI(title='CSV TOP-N')


@app.exception_handler(RedisError)
async def storage_error(request, error):
    return JSONResponse(status_code=503, content={'detail': 'Очередь временно недоступна.'})


@app.get('/', response_class=FileResponse)
def index():
    return FileResponse(Path(__file__).with_name('index.html'))


@app.get('/instance')
def instance():
    return {'instance': socket.gethostname()}


@app.get('/health')
def health():
    connection.ping()
    return {'status': 'ok'}


@app.post('/jobs', status_code=202)
def submit(file: UploadFile = File(...), column: str = Form(..., min_length=1, max_length=500),
           n: int = Form(..., ge=1, le=100)):
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, 'Размер CSV превышает 5 МиБ.')
    if not data:
        raise HTTPException(422, 'Файл пуст.')
    if not column.strip():
        raise HTTPException(422, 'Укажите столбец.')
    try:
        with connection.lock('practice4:submission', timeout=15, blocking_timeout=3):
            StartedJobRegistry('csv', connection=connection).cleanup()
            for job_id in connection.smembers(ACTIVE):
                try:
                    status = Job.fetch(job_id.decode(), connection=connection).get_status()
                except NoSuchJobError:
                    status = None
                if status not in ('queued', 'started', 'deferred', 'scheduled'):
                    connection.srem(ACTIVE, job_id)
            if connection.scard(ACTIVE) >= 10:
                raise HTTPException(429, 'Очередь заполнена: максимум 10 активных заданий.')
            job_id = uuid4().hex
            with connection.pipeline() as pipeline:
                queue.enqueue_call('tasks.top_n', args=(data, column, n), job_id=job_id,
                                   timeout=120, result_ttl=3600, failure_ttl=3600,
                                   description='CSV TOP-N ' + job_id, pipeline=pipeline)
                pipeline.sadd(ACTIVE, job_id)
                pipeline.execute()
    except LockError:
        raise HTTPException(503, 'Очередь занята, повторите запрос.') from None
    return {'job_id': job_id}


@app.get('/jobs/{job_id}')
def result(job_id: str):
    try:
        UUID(job_id)
    except ValueError:
        raise HTTPException(404, 'Задание не найдено.') from None
    StartedJobRegistry('csv', connection=connection).cleanup()
    try:
        job = Job.fetch(job_id, connection=connection)
    except NoSuchJobError:
        raise HTTPException(404, 'Задание не найдено или срок хранения истек.') from None
    status = job.get_status()
    if status == 'finished':
        value = job.return_value()
        if not isinstance(value, dict):
            return {'job_id': job_id, 'status': 'failed', 'error': 'Задание завершилось без результата.'}
        if 'error' in value:
            return {'job_id': job_id, 'status': 'failed', 'error': value['error']}
        return {'job_id': job_id, 'status': 'finished', 'result': value}
    if status in ('failed', 'stopped', 'canceled'):
        return {'job_id': job_id, 'status': 'failed', 'error': 'Обработка прервана или не выполнена.'}
    return {'job_id': job_id, 'status': 'started' if status == 'started' else 'queued'}
