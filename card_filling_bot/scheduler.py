


jobstores = {
    'default': SQLAlchemyJobStore(url=database_uri)
}
executors = {
    'default': ThreadPoolExecutor(scheduler_threads)
}

scheduler = Back