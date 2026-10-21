"""Shared face-match helper (OpenCV YuNet + SFace). Same person: cosine > 0.363.
Models are downloaded once into ./models next to this file."""
import os, urllib.request, cv2
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
URL = {
    'yunet.onnx': 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
    'sface.onnx': 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx',
}
os.makedirs(D, exist_ok=True)
for n, u in URL.items():
    p = os.path.join(D, n)
    if not os.path.exists(p) or os.path.getsize(p) < 100000:  # guard against Git LFS pointer files
        urllib.request.urlretrieve(u, p)
_det = cv2.FaceDetectorYN.create(os.path.join(D, 'yunet.onnx'), '', (320, 320), 0.7)
_rec = cv2.FaceRecognizerSF.create(os.path.join(D, 'sface.onnx'), '')
THRESH = 0.363


def emb(img, max_side=1600):
    """img: path or BGR array. Returns embedding of the largest face, or None."""
    im = cv2.imread(img) if isinstance(img, str) else img
    k = max_side / max(im.shape[:2])
    if k < 1:  # large images must be downscaled or detection fails
        im = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    h, w = im.shape[:2]
    _det.setInputSize((w, h))
    _, r = _det.detect(im)
    if r is None:
        return None
    r = max(r, key=lambda x: x[2] * x[3])
    return _rec.feature(_rec.alignCrop(im, r)).copy()


def sim(a, b):
    if a is None or b is None:
        return None
    return round(float(_rec.match(a, b, cv2.FaceRecognizerSF_FR_COSINE)), 2)
