import requests
from pathlib import Path
import argparse
from collections import defaultdict
from tqdm import tqdm
import time
import random

def get_id_from_path(path):
    return path.stem

parser = argparse.ArgumentParser(description='Upload an image to the server')
parser.add_argument('csv_paths', type=Path, nargs='+', help='Paths to the CSV files to upload')
parser.add_argument('--url', type=str, default='https://www.vpippi.com/user_study/upload_question')
# parser.add_argument('--url', type=str, default='http://127.0.0.1:8000/user_study/upload_question')
parser.add_argument('--img_root', type=Path, default=Path())
args = parser.parse_args()

images = defaultdict(dict)
for csv_path in args.csv_paths:
    name = csv_path.stem.replace('_imgs_list', '')
    for img_path in tqdm(csv_path.read_text().splitlines()):
        img_id = get_id_from_path(Path(img_path))
        if img_id in images:
            assert name not in images[img_id], f"Image {img_id} already has a {name} image"
        images[img_id][name] = args.img_root / img_path
        assert images[img_id][name].exists(), f"Image {images[img_id][name]} does not exist"

keys = list(images.keys())
keys = [key for key in keys if key.startswith('karaoke_handw')]
good_keys = random.sample(keys, 2)
images = {key: images[key] for key in good_keys}

for img_id, img_paths in tqdm(images.items()):
    files = {name: (str(img_id), open(img_path, 'rb')) for name, img_path in img_paths.items()}
    response = requests.post(args.url, files=files)
    for file in files.values():
        file[1].close()
    # time.sleep(1)
    assert response.status_code == 200, f"Failed to upload image {img_id}. Status code: {response.status_code}"