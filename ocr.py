# -*- coding: utf-8 -*-

import numpy as np
from trade_data import trained_data

DEBUG = 0


def recognize(pic):
    # filter to binary np array, 0 means white, 1 means black
    pic = pic.convert('L')
    pix = np.array(pic)
    pix /= 128
    pix = 1 - pix

    # do recognize
    s = ''
    for area in _selectImageArea(pix): s += _recognize(pix, area)
    return eval(s)


def _selectImageArea(pix):
    h, w = pix.shape
    image_lines = [i for i in xrange(w) if any([pix[j][i] for j in xrange(h)])]

    i = 0
    image_area = []
    while i < len(image_lines):
        j = i + 1
        while j < len(image_lines) and image_lines[j] == image_lines[j - 1] + 1: j += 1
        image_area += [image_lines[i], image_lines[j - 1]]
        i = j
    image_area = zip(image_area[::2], image_area[1::2])
    return image_area


def _match(pix):
    arr = pix.ravel()
    key = ''.join(map(str, arr.tolist()))
    for k, v in trained_data:
        sim = sum([1 for i in xrange(len(v)) if v[i] == key[i]])
        if sim > 620: return k
    return '?'


def _recognize(pix, area):
    a, b = area
    w = b - a + 1
    d = {7: '1', 9: '-', 16: _recognize_16(pix, area), 17: _recognize_17(pix, area)}
    return d[w]


def _recognize_16(pix, area):
    if area[1] - area[0] + 1 == 16:
        return _match(pix[:, area[0]:area[1] + 1])


def _recognize_17(pix, area):
    if area[1] - area[0] + 1 == 17:
        a, b = area
        if pix[6][a + 8]:
            return '4'
        else:
            return '+'
