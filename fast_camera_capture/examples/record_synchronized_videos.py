import asyncio
import logging
import os
from pathlib import Path

import cv2

from fast_camera_capture.detection.detect_cameras import detect_cameras
from fast_camera_capture.examples.framerate_diagnostics import (
    calculate_camera_diagnostic_results, create_timestamp_diagnostic_plots,
)
from fast_camera_capture.opencv.group.camera_group import CameraGroup
from fast_camera_capture.opencv.video_recorder.save_synchronized_videos import save_synchronized_videos
from fast_camera_capture.opencv.video_recorder.video_recorder import VideoRecorder

logger = logging.getLogger(__name__)


async def record_synchronized_videos(camera_ids_list: list, save_path: str | Path):
    camera_group = CameraGroup(camera_ids_list)
    shared_zero_time = time.perf_counter_ns()
    camera_group.start()
    should_continue = True

    video_recorder_dictionary = {}
    for camera_id in camera_ids_list:
        video_recorder_dictionary[camera_id] = VideoRecorder()

    while should_continue:
        latest_frame_payloads = camera_group.latest_frames()
        for cam_id, frame_payload in latest_frame_payloads.items():
            if frame_payload is not None:
                video_recorder_dictionary[cam_id].append_frame_payload_to_list(
                    frame_payload
                )
                cv2.imshow(f"Camera {cam_id} - Press ESC to quit", frame_payload.image)

        frame_count_dictionary = {}
        for cam_id, video_recorder in video_recorder_dictionary.items():
            frame_count_dictionary[cam_id] = video_recorder.number_of_frames
        print(f"{frame_count_dictionary}")

        if cv2.waitKey(1) == 27:
            logger.info(f"ESC key pressed - shutting down")
            cv2.destroyAllWindows()
            should_continue = False

    camera_group.close()

    raw_frame_list_dictionary = {}
    for camera_id, video_recorder in video_recorder_dictionary.items():
        raw_frame_list_dictionary[camera_id] = video_recorder._frame_payload_list.copy()

    # save videos
    synchronized_frame_list_dictionary = save_synchronized_videos(
        dictionary_of_video_recorders=video_recorder_dictionary,
        folder_to_save_videos=save_path)

    # get timestamp diagnostics
    timestamps_dictionary = {}
    for cam_id, video_recorder in video_recorder_dictionary.items():
        timestamps_dictionary[cam_id] = video_recorder.timestamps
    timestamp_diagnostic_data_class = calculate_camera_diagnostic_results(
        timestamps_dictionary
    )

    print(timestamp_diagnostic_data_class.__dict__)

    diagnostic_plot_file_path = Path(save_path) / "timestamp_diagnostic_plots.png"
    create_timestamp_diagnostic_plots(
        raw_frame_list_dictionary=raw_frame_list_dictionary,
        synchronized_frame_list_dictionary=synchronized_frame_list_dictionary,
        path_to_save_plots_png=diagnostic_plot_file_path
    )

    os.startfile(diagnostic_plot_file_path, 'open')
if __name__ == "__main__":
    import time

    found_camera_response = detect_cameras()
    camera_ids_list_in = found_camera_response.cameras_found_list

    save_path_in = (
            Path.home()
            / "fast-camera-capture-recordings"
            / time.strftime("%m-%d-%Y_%H_%M_%S")
    )
    save_path_in.mkdir(parents=True, exist_ok=True)
    asyncio.run(
        record_synchronized_videos(
            camera_ids_list=camera_ids_list_in, save_path=save_path_in
        )
    )

    print("done!")