import os
import random

import numpy
import torch
from PIL import Image
from torch.utils import data

from utils import util

FORMATS = 'bmp', 'dng', 'jpeg', 'jpg', 'mpo', 'png', 'tif', 'tiff', 'webp'


class Dataset(data.Dataset):
    def __init__(self, filenames, input_size=640, augment=False):
        self.augment = augment
        self.input_size = input_size

        # Read labels
        cache = self.load_label(filenames)
        labels, shapes = zip(*cache.values())

        self.labels = list(labels)
        self.shapes = numpy.array(shapes, dtype=numpy.float64)

        self.filenames = list(cache.keys())  # update
        self.n = len(shapes)  # number of samples
        self.indices = range(self.n)

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, index):
        index = self.indices[index]
        while True:
            if self.augment:
                # MOSAIC
                image, label = util.load_mosaic(self, index)
                # MixUp augmentation
                if random.random() < 0.2:
                    mix_image1, mix_label1 = image, label
                    mix_image2, mix_label2 = util.load_mosaic(self, random.randint(0, self.n - 1))
                    image, label = util.mix_up(mix_image1, mix_label1, mix_image2, mix_label2)
                # HSV color-space
                util.augment_hsv(image)
            else:
                # Load image
                image, shape, (h, w) = util.load_image(self, index)

                # Letterbox
                image, ratio, pad = util.resize(image, self.input_size)

                label = self.labels[index].copy()
                if len(label):
                    label[:, 1:] = util.wh2xy(label[:, 1:], ratio[0] * w, ratio[1] * h, pad[0], pad[1])

            nl = len(label)  # number of labels
            if not nl:
                index = random.choice(self.indices)
                continue

            # Flip left-right
            if self.augment and random.random() < 0.5:
                image = numpy.fliplr(image)
                if nl:
                    label[:, 1:] = util.xy2wh(label[:, 1:], image.shape[1], image.shape[0])
                    label[:, 1] = 1 - label[:, 1]
                    label[:, 1:] = util.wh2xy(label[:, 1:], image.shape[1], image.shape[0])

            # Convert HWC -> CHW, BGR -> RGB
            sample = image.transpose((2, 0, 1))[::-1]
            sample = numpy.ascontiguousarray(sample)
            sample = torch.from_numpy(sample)

            if self.augment:
                target = torch.from_numpy(label)
                return sample, target
            else:
                target = torch.zeros((nl, 6))
                if nl:
                    target[:, 1:] = torch.from_numpy(label)
                return sample, target

    @staticmethod
    def collate_fn1(batch):
        samples, targets = zip(*batch)
        return torch.stack(samples, 0), targets

    @staticmethod
    def collate_fn2(batch):
        samples, targets = zip(*batch)
        for i, l in enumerate(targets):
            l[:, 0] = i
        return torch.stack(samples, 0), torch.cat(targets, 0)

    @staticmethod
    def load_label(filenames):
        x = {}
        for filename in filenames:
            try:
                # verify images
                image = Image.open(filename)
                image.verify()
                shape = image.size
                assert (shape[0] > 9) & (shape[1] > 9), f'image size {shape} <10 pixels'
                assert image.format.lower() in FORMATS, f'invalid image format {image.format}'

                # verify labels
                a = f'{os.sep}images{os.sep}'
                b = f'{os.sep}labels{os.sep}'
                if os.path.isfile(b.join(filename.rsplit(a, 1)).rsplit('.', 1)[0] + '.txt'):
                    with open(b.join(filename.rsplit(a, 1)).rsplit('.', 1)[0] + '.txt') as f:
                        label = [x.split() for x in f.read().strip().splitlines() if len(x)]
                        label = numpy.array(label, dtype=numpy.float32)
                    nl = len(label)
                    if nl:
                        assert label.shape[1] == 5, 'labels require 5 columns'
                        assert (label >= 0).all(), 'negative label values'
                        assert (label[:, 1:] <= 1).all(), 'non-normalized coordinates'
                        _, i = numpy.unique(label, axis=0, return_index=True)
                        if len(i) < nl:
                            label = label[i]
                    else:
                        label = numpy.zeros((0, 5), dtype=numpy.float32)
                else:
                    label = numpy.zeros((0, 5), dtype=numpy.float32)
                if filename:
                    x[filename] = [label, shape]
            except FileNotFoundError:
                pass
        return x
