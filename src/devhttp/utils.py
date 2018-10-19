import os


def find(root):
    for filename in os.listdir(root):
        path = os.path.join(root, filename)
        if os.path.isfile(path):
            yield filename
        elif os.path.isdir(path):
            for sub_path in find(path):
                yield os.path.join(filename, sub_path)


def normalize_url(url):
    return url.replace("\\", '/').strip('/')
