'''Author: Mausam Rajbanshi (AI Developer)'''
import os

def fast_scandir(dirname):
    '''scans directories and their subdirectories in provided directory'''
    subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders


def latest_version(path):
    '''Determines the stored version'''
    with open(path, 'r') as vc_file:
        contents = vc_file.readlines()
    last_version = int(
        [line.strip() for line in contents][-1][1:]
    )
    return last_version
