def paginated(items, page, limit, total):
    total_pages = (total + limit - 1) // limit if limit else 0
    return {
        "data": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }