import cv2
import numpy as np
from logger_config import logger

def display_frames(results, lock):
    logger.info("🖥️ Display thread started.")
    
    while True:
        composite = None
        display_info = {}
        frames = {}

        with lock:
            # Collect wire counts and frames first
            for name in [ "LCG","PWLC"]:
                stream_data = results.get(name, {})
                frame = stream_data.get("frame")
                wire_count = stream_data.get("wire_count", "N/A")
                display_info[name] = wire_count
                frames[name] = frame

        # Calculate total after collecting both counts
        total_wire = sum(wc for wc in display_info.values() if isinstance(wc, int))

        # Now draw frames
        for name in ["LCG","PWLC"]:  # PWLC on left, LCG on right
            frame = frames.get(name)
            wire_count = display_info.get(name, "N/A")

            if frame is not None:
                resized = cv2.resize(frame, (640, 360))
                cv2.putText(resized, f"{name} Count: {wire_count}", (10, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                if name == "LCG":
                    # ✅ Correct total count now appears below LCG only
                    cv2.putText(resized, f"Total Wire: {total_wire}", (10, 75),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            else:
                resized = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(resized, f"{name} Stream Missing", (60, 180),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

            if composite is None:
                composite = resized
            else:
                composite = np.hstack((composite, resized))

        if composite is not None:
            cv2.imshow("Wire Count: PWLC | LCG", composite)

        

        if cv2.waitKey(1) & 0xFF == ord("q"):
            logger.info("🛑 Display loop stopped by user.")
            break

    cv2.destroyAllWindows()
