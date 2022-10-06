import multiprocessing
from multiprocessing import Process
from typing import Dict, List

from fast_camera_capture import CamArgs, Camera


class CamGroupProcess:
    def __init__(self, cam_ids: List[str]):
        self._cam_ids = cam_ids
        self._process: Process = None
        self._payload = None
        self._queues = self._create_queues()

    def start_capture(self):
        self._process = Process(target=CamGroupProcess._begin, args=(self._cam_ids, self._queues))
        self._process.start()

    def _create_queues(self):
        d = {}
        for cam_id in self._cam_ids:
            d.update({
                cam_id: multiprocessing.Queue()
            })
        return d

    @staticmethod
    def _create_cams(cam_ids: List[str]):
        return [Camera(CamArgs(cam_id=cam)) for cam in cam_ids]

    @staticmethod
    def _begin(cam_ids: List[str], queues: Dict[str, multiprocessing.Queue]):
        cameras = CamGroupProcess._create_cams(cam_ids)
        for cam in cameras:
            cam.connect()
        while True:
            for cam in cameras:
                if cam.new_frame_ready:
                    queue = queues[cam.cam_id]
                    print(f"Sending frame for {cam.cam_id}")
                    queue.put_nowait(cam.latest_frame)

    def get_all(self):
        result = []
        for cam_id in self._cam_ids:
            queue = self._queues[cam_id]
            if not queue.empty():
                result.append(queue.get_nowait())

        return result


if __name__ == "__main__":
    p = CamGroupProcess(["0", "2"])
    p.start_capture()
    while True:
        frames = p.get_all()
        print(frames)