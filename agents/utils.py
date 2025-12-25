import datetime

def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_news_cutoff_date() -> str:
    """Returns the date 3 months ago for filtering stale news."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=90)
    return cutoff.strftime("%Y-%m-%d")