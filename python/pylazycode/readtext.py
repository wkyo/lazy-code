# -*- encoding: utf-8 -*-

import warnings

try:
    import chardet
except ImportError:
    warnings.warn('package chardet not found')


DEFAULT_ENCODINGS = (
    'utf-8',
    'utf-16',
    'utf-32',
    'gb2312',
    'gbk',
    'gb18030'
)


def readtext(filepath, encodings=None):
    """Read text from file with unkonwn encoding. By default, this method will
    use `chardet` to detect file encoding. If failed, None will be returned.

    Note: this method is dangerous, it will load the whole data of file.

    Args:
        filepath: File path.
        encodings: Predefined sequence of encodings to decode file. If `chardet`
            not found and encodings is not provided, DEFAULT_ENCODINGS will be
            used.
    """
    text = None
    with open(filepath, 'rb') as fp:
        data = fp.read()
        if encodings is None:
            if 'chardet' in locals():
                encodings = [chardet.detect(data).get('encoding')]
            else:
                encodings = DEFAULT_ENCODINGS
        for e in encodings:
            try:
                text = data.decode(e)
            except:
                pass
            else:
                break
    return text