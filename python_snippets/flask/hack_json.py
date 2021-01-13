"""Extend supported types of flask jsonify

supported types:
- date (datetime is a subclass of date) -> ISO format string
- timedelta -> seconds with float representation
- (Optional) MongoDB ID (bson.ObjectId) -> string id
- (Optional) Numpy types (ndarray, floating, integer and etc.)
"""
import warnings
from datetime import datetime, timedelta, date

from flask.json import JSONEncoder


def hack_flask_json_encoder(app):
    json_encoder = app.json_encoder or JSONEncoder
    type_formatters = [
        {
            'type': date,
            'format': lambda x: x.isoformat()
        }, {
            'type': timedelta,
            'format': lambda x: x.total_seconds()
        }
    ]

    try:
        from bson import ObjectId
    except ImportError:
        warnings.warn('Please install pymongo')
    else:
        type_formatters.append({
            'type': ObjectId,
            'format': lambda x: str(x)
        })

    try:
        import numpy as np
    except ImportError:
        warnings.warn('Please install numpy')
    else:
        # see: https://stackoverflow.com/questions/9452775/converting-numpy-dtypes-to-native-python-types
        # NOTE: `numpy.asscalar(x)` is deprecated since numpy 1.16, use a.item() instead!
        type_formatters.extend([
            {
                'type': np.ndarray,
                'format': lambda x: x.tolist()
            }, {
                'type': np.generic,
                'format': lambda x: x.item()
            }
        ])

    class HackedJSONEncoder(json_encoder):

        def default(self, o):
            for f_ in type_formatters:
                if isinstance(o, f_['type']):
                    return f_['format'](o)
            return json_encoder.default(self, o)

    app.json_encoder = HackedJSONEncoder


def init_app(app):
    # flask_mongoengine provided object id and datetime json encoder
    hack_flask_json_encoder(app)
