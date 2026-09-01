import sys
import time
import threading
import cv2
import numpy as np
import mediapipe as mp

from shared.blade_state import BladeState


class LiveHandTracker:

    def __init__(
        self,
        camera_id: int = 0,
        base_alpha: float = 0.4,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self.camera_id = camera_id
        self.base_alpha = base_alpha

        # MediaPipe Hands (Lite model complexity for high FPS)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.cap = None
        self.prev_x = 0.5
        self.prev_y = 0.5
        self.was_visible = False
        self.prev_timestamp = time.perf_counter()

        # Threading state
        self._running = False
        self._lock = threading.Lock()
        self._latest_state = BladeState.create(
            0.5, 0.5, 0.5, 0.5, False, time.perf_counter(), False
        )
        self._latest_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def start(self):
        """Starts background capture and MediaPipe inference thread."""
        if sys.platform.startswith("win"):
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        elif sys.platform.startswith("darwin"):
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_AVFOUNDATION)
        else:
            self.cap = cv2.VideoCapture(self.camera_id)

        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Could not open webcam on camera_id={self.camera_id}"
                )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 60)

        # Launch background thread
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self):
        """Worker thread running MediaPipe asynchronously."""
        while self._running:
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.005)
                continue

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Downscale frame for fast neural network inference
            small_frame = cv2.resize(
                frame, (320, 240), interpolation=cv2.INTER_NEAREST
            )
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            results = self.hands.process(rgb_frame)

            with self._lock:
                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    index_tip = hand_landmarks.landmark[8]  # Landmark 8 = Index tip

                    raw_x = float(index_tip.x)
                    raw_y = float(index_tip.y)
                    is_reacquired = not self.was_visible

                    if is_reacquired:
                        curr_x, curr_y = raw_x, raw_y
                    else:
                        raw_dist = np.hypot(raw_x - self.prev_x, raw_y - self.prev_y)
                        adaptive_alpha = min(1.0, self.base_alpha + raw_dist * 4.0)
                        curr_x = adaptive_alpha * raw_x + (1 - adaptive_alpha) * self.prev_x
                        curr_y = adaptive_alpha * raw_y + (1 - adaptive_alpha) * self.prev_y

                    px, py = int(curr_x * w), int(curr_y * h)
                    cv2.circle(frame, (px, py), 8, (0, 255, 0), -1)

                    self._latest_state = BladeState.create(
                        x=curr_x,
                        y=curr_y,
                        prev_x=self.prev_x,
                        prev_y=self.prev_y,
                        visible=True,
                        prev_timestamp=self.prev_timestamp,
                        is_reacquired=is_reacquired,
                    )
                    self.prev_x, self.prev_y = curr_x, curr_y
                    self.was_visible = True
                    self.prev_timestamp = self._latest_state.timestamp
                else:
                    self._latest_state = BladeState.create(
                        self.prev_x,
                        self.prev_y,
                        self.prev_x,
                        self.prev_y,
                        False,
                        self.prev_timestamp,
                        False,
                    )
                    self.was_visible = False
                    self.prev_timestamp = self._latest_state.timestamp

                self._latest_frame = frame

    def get_blade_state(self) -> tuple[BladeState, np.ndarray]:
        """Instant non-blocking state fetch for the Pygame loop."""
        with self._lock:
            return self._latest_state, self._latest_frame.copy()

def stop(self):
    self._running = False

    thread = getattr(self, "_thread", None)
    if thread and thread.is_alive():
        thread.join(timeout=1.0)

    # Avoid closing resources while the worker may still be using them.
    if thread and thread.is_alive():
        return

    if self.cap and self.cap.isOpened():
        self.cap.release()
    self.hands.close()