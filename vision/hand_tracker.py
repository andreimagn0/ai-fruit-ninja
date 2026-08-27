import sys
import time
import cv2
import numpy as np
import mediapipe as mp

from shared.blade_state import BladeState


class LiveHandTracker:

    def __init__(
        self,
        camera_id: int = 0,
        alpha: float = 0.5,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ):
        self.camera_id = camera_id
        self.alpha = alpha

        # Legacy mp.solutions API runs purely on CPU memory buffers
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.cap = None
        self.prev_x = 0.5
        self.prev_y = 0.5
        self.was_visible = False
        self.prev_timestamp = time.perf_counter()

    def start(self):
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
                    f"Could not open webcam capture on camera_id={self.camera_id}"
                )

    def get_blade_state(self) -> tuple[BladeState, np.ndarray]:
        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        if self.cap is None or not self.cap.isOpened():
            self.was_visible = False
            state = BladeState.create(
                self.prev_x, self.prev_y, self.prev_x, self.prev_y, False, self.prev_timestamp, False
            )
            return state, dummy_frame

        success, frame = self.cap.read()
        if not success:
            self.was_visible = False
            state = BladeState.create(
                self.prev_x, self.prev_y, self.prev_x, self.prev_y, False, self.prev_timestamp, False
            )
            return state, dummy_frame

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert to RGB for MediaPipe inference
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            # Landmark 8 = Index Fingertip
            index_tip = hand_landmarks.landmark[8]

            raw_x = float(index_tip.x)
            raw_y = float(index_tip.y)

            is_reacquired = not self.was_visible

            if is_reacquired:
                curr_x = raw_x
                curr_y = raw_y
            else:
                curr_x = self.alpha * raw_x + (1 - self.alpha) * self.prev_x
                curr_y = self.alpha * raw_y + (1 - self.alpha) * self.prev_y

            # Render fingertip overlay
            px, py = int(curr_x * w), int(curr_y * h)
            cv2.circle(frame, (px, py), 10, (0, 255, 0), -1)

            state = BladeState.create(
                x=curr_x,
                y=curr_y,
                prev_x=self.prev_x,
                prev_y=self.prev_y,
                visible=True,
                prev_timestamp=self.prev_timestamp,
                is_reacquired=is_reacquired,
            )

            self.prev_x = curr_x
            self.prev_y = curr_y
            self.was_visible = True
            self.prev_timestamp = state.timestamp
            return state, frame

        # Tracking Lost
        state = BladeState.create(
            x=self.prev_x,
            y=self.prev_y,
            prev_x=self.prev_x,
            prev_y=self.prev_y,
            visible=False,
            prev_timestamp=self.prev_timestamp,
            is_reacquired=False,
        )
        self.was_visible = False
        self.prev_timestamp = state.timestamp
        return state, frame

    def stop(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.hands.close()