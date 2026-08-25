import cv2
from vision.hand_tracker import LiveHandTracker


def run_vision_test():
    print("🚀 Initializing Live ONNX Vision Test Environment...")
    tracker = LiveHandTracker()
    tracker.start()

    window_name = "AI Fruit Ninja - ONNX Vision Test"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    print("✅ Tracker active. Move index finger in view. Press 'ESC' to exit.")

    while True:
        state, frame = tracker.get_blade_state()
        h, w, _ = frame.shape

        # Map normalized coordinates to frame pixels
        px = int(state.x * w)
        py = int(state.y * h)
        prev_px = int(state.prev_x * w)
        prev_py = int(state.prev_y * h)

        if state.visible:
            # Draw blade trail line
            cv2.line(frame, (prev_px, prev_py), (px, py), (0, 255, 255), 4)
            # Draw tip point
            cv2.circle(frame, (px, py), 8, (0, 0, 255), -1)
            status_text = f"Tracking Active | Speed: {state.velocity:.1f} px/s"
            status_color = (0, 255, 0)
        else:
            status_text = "Searching for hand..."
            status_color = (0, 0, 255)

        # Telemetry HUD
        cv2.putText(
            frame,
            status_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2,
        )
        cv2.putText(
            frame,
            f"Pos: ({state.x:.3f}, {state.y:.3f})",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )

        cv2.imshow(window_name, frame)

        if cv2.waitKey(16) & 0xFF == 27:  # ESC key
            break

    tracker.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_vision_test()