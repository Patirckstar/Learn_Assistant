import base64
import json
import os
import uuid

import cv2
import numpy as np

_face_rec = None


def _get_face_recognition():
    global _face_rec
    if _face_rec is None:
        import face_recognition as _face_rec
    return _face_rec


def decode_base64_image(image_data: str) -> np.ndarray:
    if image_data.startswith('data:image/'):
        image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法解码图片")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def detect_and_encode_face(image: np.ndarray) -> np.ndarray | None:
    fr = _get_face_recognition()
    face_locations = fr.face_locations(image)
    if len(face_locations) == 0:
        return None
    return fr.face_encodings(image, face_locations)[0]


def encode_to_json(encoding: np.ndarray) -> str:
    return json.dumps(encoding.tolist())


def decode_from_json(encoding_json: str) -> np.ndarray:
    return np.array(json.loads(encoding_json))


def compare_faces(known_encoding: np.ndarray, input_encoding: np.ndarray, tolerance: float = 0.6) -> bool:
    fr = _get_face_recognition()
    distances = fr.face_distance([known_encoding], input_encoding)
    return distances[0] < tolerance


def calculate_distance(known_encoding: np.ndarray, input_encoding: np.ndarray) -> float:
    fr = _get_face_recognition()
    return fr.face_distance([known_encoding], input_encoding)[0]


def save_face_image(image: np.ndarray, storage_dir: str) -> str:
    os.makedirs(storage_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(storage_dir, filename)
    cv2.imwrite(filepath, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return filepath


def simple_liveness_detection(image: np.ndarray) -> bool:
    """简单图像质量检测：检查图像是否足够清晰，而非真正的活体检测。
    降低阈值以适应普通笔记本摄像头的画质。"""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
    if edge_density < 0.003:
        return False

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    blur_score = np.var(laplacian)
    if blur_score < 15:
        return False

    return True
