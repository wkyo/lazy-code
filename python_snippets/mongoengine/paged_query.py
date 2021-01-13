import math


def page_query_with_skip(query, skip=0, limit=100, max_count=None, lazy_count=False):
    """Query data with skip, limit and count by `QuerySet`

    Args:
        query(mongoengine.queryset.QuerySet): A valid `QuerySet` object.
        skip(int): Skip N items.
        limit(int): Maximum number of items returned.
        max_count(int): Maximum statistical value of the counter.
            If `max_count` is None, it will count all on the `QuerySet`.
        lazy_count(bool): Don't report correct value of total when queried items is empty, use estimates, instead.

    Returns:
        A dict with keys: total, skip, limit, items
    """
    if max_count:
        total = query.skip(skip).limit(
            max_count).count(with_limit_and_skip=True)
        if lazy_count or total > 0:
            total += skip
        else:
            total = query.count()
    else:
        total = query.count()
    items = query.skip(skip).limit(limit)
    return {
        'total': total,
        'skip': skip,
        'limit': limit,
        'items': items
    }


def page_query(query, page=1, per_page=100, max_count_pages=5):
    page, per_page = max(page, 1), max(per_page, 1)
    skip = (page - 1) * per_page
    limit = per_page
    max_count = max_count_pages * per_page if max_count_pages else None

    result = page_query_with_skip(query, skip, limit, max_count)

    total = result['total']
    items = result['items']
    pages = math.ceil(total / per_page)

    return {
        'page': page,
        'page_prev': page - 1 if page > 1 else None,
        'page_next': page + 1 if pages > page else None,
        'pages': pages,
        'per_page': per_page,
        'items': items
    }
