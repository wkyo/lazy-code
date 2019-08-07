# -*- encoding: utf-8 -*-


from collections import namedtuple
import csv
import io
import re
import warnings


def no_double_quote_surround(s):
    if s.startswith('"') and s.endswith('"'):
        return s[1: -1]
    return s


def _textgrid2dict_by_name(text):
    data = {'items': []}
    BASE_UNIT, ITEM_UNIT, INTV_UNIT = 0, 1, 2
    current_unit = BASE_UNIT

    multi_line_text = []

    for n, line in enumerate(io.StringIO(text)):
        # process multi-line text
        if multi_line_text:
            multi_line_text.append(line)
            if line.replace('""', '').rstrip().endswith('"'):
                interval = data['items'][-1][-1]
                interval['text'] = no_double_quote_surround(
                    '\n'.join(multi_line_text).strip()
                )
                multi_line_text = []
            continue

        # process unit tag
        if re.match(r'\s*item\s*\[\s*\d+\s*\]', line):
            current_unit = ITEM_UNIT
            data['items'].append([])
        elif re.match(r'\s*intervals\s*\[\s*\d+\s*\]', line):
            current_unit = INTV_UNIT
            data['items'][-1].append({})
        else:
            if current_unit == BASE_UNIT:
                kv = line.split('=', 1)
                if len(kv) != 2:
                    continue
                k, v = kv[0].strip(), kv[1].strip()
                if k == 'xmin':
                    data['xmin'] = float(v)
                elif k == 'xmax':
                    data['xmax'] = float(v)
                elif k == 'size':
                    data['size'] = int(v)
            elif current_unit == INTV_UNIT:
                interval = data['items'][-1][-1]
                kv = line.split('=', 1)
                if len(kv) != 2:
                    continue
                k, v = kv[0].strip(), kv[1].lstrip()
                if k == 'xmin':
                    interval['xmin'] = float(v)
                elif k == 'xmax':
                    interval['xmax'] = float(v)
                elif k == 'text':
                    text = v.replace('""', '').strip()
                    if text.startswith('"') and not text[1: ].endswith('"'):
                        # meet multi-line text
                        multi_line_text.append(v)
                    else:
                        interval['text'] = no_double_quote_surround(v.replace('""', '"').strip())
                else:
                    warnings.warn('unkown sentence at line {}:\n{}'.format(n, line))
    return data


TextGridInterval = namedtuple('TextGridInterval', ['xmin', 'xmax', 'text'])


class TextGridReader:

    def __init__(self, text):
        self.raw_data = _textgrid2dict_by_name(text)
        self._dialog = []

        items = self.raw_data.get('items')
        if items:
            self.raw_data['items'] = [[TextGridInterval(intv.get('xmin'), intv.get('xmax'), intv.get('text')) for intv in item] for item in items]

    def __getitem__(self, key):
        if key > self.size:
            raise ValueError('there are only {} item(s)'.format(self.size))
        return self.items[key]

    @property
    def size(self):
        return self.raw_data.get('size')

    @property
    def xmin(self):
        return self.raw_data.get('xmin')

    @property
    def xmax(self):
        return self.raw_data.get('xmax')

    @property
    def items(self):
        return self.raw_data.get('items')

    @property
    def dialog(self):
        if not self._dialog:
            self._dialog = []
            for speaker, item in enumerate(self.items, 0):
                for interval in item:
                    if interval.text:
                        self._dialog.append({
                            'speaker': speaker,
                            'begin': interval.xmin,
                            'end': interval.xmax,
                            'text': interval.text,
                        })
            self._dialog = sorted(self._dialog, key=lambda x: x['begin'])
        return self._dialog


##############################################################
###### FOLLOWING METHODS ARE DEPRECATED, DON'T USE THEM ######

def _textgrid2dict(text):
    """convert textgrid to a python dict object accordding to indent"""
    data = {}
    dict_stack = [data]
    indent_size = 0
    # stage data when process multi-line text
    staging_dict = None
    staging_key = None
    staging_text = []

    for n, line in enumerate(io.StringIO(text)):
        # process multi-line text
        if staging_dict:
            text = line.replace('""', '')
            if text.rstrip().endswith('"'):
                staging_text.append(line.rstrip())
                staging_dict[staging_key] = '\n'.join(staging_text)
                staging_dict = None
                staging_key = None
                staging_text = []
            else:
                staging_text.append(line.replace('""', '"'))
            continue

        _indent_size = 0
        for c in line:
            if c != ' ':
                break
            _indent_size += 1
        # set default indent size
        if indent_size == 0 and _indent_size > indent_size:
            indent_size = _indent_size
        elif indent_size > 0 and _indent_size % indent_size != 0:
            raise ValueError('unexpected indent at line {}:\n{}'.format(n, line))
        # set current indent level
        indent_level = _indent_size // indent_size if indent_size > 0 else 0
        if indent_level + 1 > len(dict_stack):
            raise ValueError('unexpected indent at line {}:\n{}'.format(n, line))
        else:  # delete redundant stack-top
            del dict_stack[indent_level + 1: ]
        # parse line to key-value pair
        line = line.strip()
        if not line:
            continue
        k, v = None, None
        if line[-1] == ':':
            k, v = line[: -1].strip(), {}
            dict_stack.append(v)
        else:
            try:
                k, v = line.split('=', 1)
                k, v = k.strip(), v.strip()
            except:
                continue
        # process multi-line text
        if isinstance(v, str) and v.startswith('"'):
            # in `praat`, a single `"` will be writed as `""`
            text = v[1:].replace('""', '')
            if not text.endswith('"'):
                staging_dict = dict_stack[indent_level]
                staging_key = k
                staging_text.append(v)
        dict_stack[indent_level][k] = v
    return _dict_filter(data, _textgrid_data_handler)


def _dict_filter(d, handler, max_depth=0):
    """filter the items of given dict, this method will alter `d`
    Args:
        d: dict-like object
        handler: a callback function which return NEW key-value pair
            accepted, otherwise,  None
        max_depth: maximum depth

    Returns:
        filtered dict
    """
    seq = [(0, d)]
    while seq:
        depth, target = seq.pop()
        depth += 1
        for k, v in list(target.items()):
            kv = handler(k, v)
            if kv:
                _k, v = kv
                if k != _k:
                    del target[k]
                target[_k] = v
                if isinstance(v, dict) and (max_depth == 0 or depth < max_depth):
                    seq.append((depth, v))
            else:
                del target[k]
    return d

def _int_from_str(s):
    result = re.search('(?P<digit>\\d+)', s)
    return result if result is None else int(result.groupdict()['digit'])


def _textgrid_data_handler_item(item_data):
    interval_n_pattern = re.compile('intervals\\s*\\[\\d+\\]')
    interval_list = []
    for k, v in item_data.items():
        if re.fullmatch(interval_n_pattern, k):
            interval = TextGridInterval(float(v['xmin']), float(v['xmax']), v['text'].strip('\'"'))
            interval_list.append((_int_from_str(k), interval))
    return [v for _, v in sorted(interval_list, key=lambda x: x[0])]


def _textgrid_data_handler(key, value):
    item_list_pattern = re.compile('item\\s*\\[\\s*\\]')
    inline_colon_pattern = re.compile('\\s*:\\s*')
    item_n_pattern = re.compile('item\\s*\\[\\d+\\]')
    if re.fullmatch(item_list_pattern, key):
        key = 'items'
        item_list = []
        for k, v in list(value.items()):
            if re.fullmatch(item_n_pattern, k):
                item_list.append((_int_from_str(k), _textgrid_data_handler_item(v)))
        value = [v for _, v in sorted(item_list, key=lambda x: x[0])]
    elif ':' in key:
        key = re.sub(inline_colon_pattern, '-', key)
    elif key in {'xmin', 'xmax'}:
        value = float(value)
    elif key == 'size':
        value = int(value)
    return key, value


