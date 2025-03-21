from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

root = Path('emuru_data')

data = defaultdict(list)

for img_path in tqdm(root.rglob('*.png')):
    _, dataset, method, author, img_name = img_path.parts
    # rename every image to have a unique name composed by dataset + img_name
    if img_name.startswith(dataset):
        continue
    new_img_name = f'{dataset}_{img_name}'
    img_path.rename(img_path.with_name(new_img_name))

for img_path in tqdm(root.rglob('*.png')):
    _, dataset, method, author, img_name = img_path.parts
    key = img_name[:-4]
    data[method].append(img_path)

for method, images in data.items():
    with open(root / f'{method}_imgs_list.csv', 'w') as f:
        for img_path in images:
            f.write(str(img_path.relative_to(Path())) + '\n')
    print(f'{method} images: {len(images)}')