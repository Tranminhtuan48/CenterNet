CenterNet (Objects as Points) using PyTorch

Dataset: `kaggle datasets download -d nadinpethiyagoda/vehicle-dataset-for-yolo`
or https://www.kaggle.com/datasets/nadinpethiyagoda/vehicle-dataset-for-yolo/data

Run `pip install -r requirements.txt`

For virtual env 
1. python -m venv Centernet
2. source Centernet/bin/activate

### Train

* Run `bash main.sh $ --train` for training, `$` is number of GPUs

### Train

* Run `python main.py --test` for testing

### Dataset structure 

    ├── vehicle
        ├── images
            ├── train
                ├── 1111.jpg
                ├── 2222.jpg
            ├── val
                ├── 1111.jpg
                ├── 2222.jpg
        ├── labels
            ├── train
                ├── 1111.txt
                ├── 2222.txt
            ├── val
                ├── 1111.txt
                ├── 2222.txt