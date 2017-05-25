import time
from threading import Thread, Event
import logging


class ServiceWorker(object):
    def __init__(self, worker_callback):
        self.thread = Thread(target=worker_callback, args=[self])
        self.thread.daemon = True
        self.pause_event = Event()
        self.stop_event = Event()
        self.resume_event = Event()
        self.activity_paused = Event()
        self.is_busy_event = Event()

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def process_pause_signal(self):
        if self.pause_event.is_set():
            self.activity_paused.set()
            self.resume_event.wait()

    def pause(self):
        self.resume_event.clear()
        self.pause_event.set()
        while True:
            if self.activity_paused.wait(0.1):
                break
            if not self.is_alive():
                break

    def resume(self):
        self.pause_event.clear()
        self.activity_paused.clear()
        self.resume_event.set()

    def is_alive(self):
        return self.thread.isAlive()


class BaseService(object):
    def create_worker(self, worker_action):
        return ServiceWorker(worker_action)

    def iterate_workers(self, objects):
        for obj in objects:
            assert isinstance(obj, (ServiceWorker, list))
            if isinstance(obj, ServiceWorker):
                yield obj
            elif isinstance(obj, list):
                for item in obj:
                    yield item

    def start(self):
        for worker in self.iterate_workers(self.worker_registry):
            worker.start()

    def stop(self):
        for worker in self.iterate_workers(self.worker_registry):
            worker.stop()

    def pause(self):
        for worker in self.iterate_workers(self.worker_registry):
            worker.pause()
        logging.debug('Service %s paused' % self.__class__.__name__)

    def resume(self):
        for worker in self.iterate_workers(self.worker_registry):
            worker.resume()
        logging.debug('Service %s resumed' % self.__class__.__name__)

    def register_workers(self, *args):
        self.worker_registry = args 

    def is_busy(self):
        return any(x.is_busy_event.is_set() for x in
                   self.iterate_workers(self.worker_registry))

    def is_alive(self):
        return any(x.is_alive() for x in
                   self.iterate_workers(self.worker_registry))
