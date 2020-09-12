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
                    if text.startswith('"') and not text[1:].endswith('"'):
                        # meet multi-line text
                        multi_line_text.append(v)
                    else:
                        interval['text'] = no_double_quote_surround(
                            v.replace('""', '"').strip())
                else:
                    warnings.warn(
                        'unkown sentence at line {}:\n{}'.format(n, line))
    return data


TextGridInterval = namedtuple('TextGridInterval', ['xmin', 'xmax', 'text'])


class TextGridReader:

    def __init__(self, text):
        self.raw_data = _textgrid2dict_by_name(text)
        self._dialog = []

        items = self.raw_data.get('items')
        if items:
            self.raw_data['items'] = [[TextGridInterval(intv.get('xmin'), intv.get(
                'xmax'), intv.get('text')) for intv in item] for item in items]

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
