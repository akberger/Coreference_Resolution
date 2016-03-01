#!/usr/bin/env python
import os
import glob
import shutil

""" Run this script from the base directory of the project.
Assumes that the distributed conll-2012 data directory is
one level above the base directory.
"""

data_dir = os.path.abspath('../conll-2012/train/english/annotations/')
new_dir = os.path.abspath('../data/train')
train_files = glob.glob(os.path.join(data_dir, '*/*/*/*.v4_auto_conll'))

if not os.path.exists(new_dir):
    os.makedirs(new_dir)

for f in train_files:
    shutil.copyfile(f, os.path.join(new_dir, os.path.basename(f)))

print('Copied {} files from {} to {}'.format(
    len(train_files), data_dir, new_dir))
