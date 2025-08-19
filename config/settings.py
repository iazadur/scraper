import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "bangladesh_news")
RAW_COLLECTION = os.getenv("RAW_COLLECTION", "raw_news")
UNIQUE_COLLECTION = os.getenv("UNIQUE_COLLECTION", "unique_news")

# Geolocation settings
NOMINATIM_USER_AGENT = os.getenv("NOMINATIM_USER_AGENT", "bangladesh_news_scraper")
PELIAS_API_URL = os.getenv("PELIAS_API_URL", "https://api.geocode.earth/v1")

# Scraping settings
SCRAPING_DELAY = int(os.getenv("SCRAPING_DELAY", "1"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Redis settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# News sources configuration
NEWS_SOURCES = {
    "prothom_alo": {
        "name": "Prothom Alo",
        "base_url": "https://www.prothomalo.com",
        "rss_feeds": [
            "https://www.prothomalo.com/feed/",
            "https://www.prothomalo.com/bangladesh/feed/",
            "https://www.prothomalo.com/world/feed/",
            "https://www.prothomalo.com/sports/feed/",
            "https://www.prothomalo.com/entertainment/feed/"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".story-element-text p, .article-content p",
            "image": ".story-element-image img, .article-image img",
            "date": ".story-element-publish-date, .publish-date"
        }
    },
    "daily_star": {
        "name": "The Daily Star",
        "base_url": "https://www.thedailystar.net",
        "rss_feeds": [
            "https://www.thedailystar.net/rss.xml",
            "https://www.thedailystar.net/bangladesh/rss.xml",
            "https://www.thedailystar.net/world/rss.xml",
            "https://www.thedailystar.net/sports/rss.xml"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .story-content p",
            "image": ".article-image img, .story-image img",
            "date": ".publish-date, .article-date"
        }
    },
    "bdnews24": {
        "name": "bdnews24.com",
        "base_url": "https://bdnews24.com",
        "rss_feeds": [
            "https://bdnews24.com/rss.xml",
            "https://bdnews24.com/bangladesh/rss.xml",
            "https://bdnews24.com/world/rss.xml",
            "https://bdnews24.com/sports/rss.xml"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .news-content p",
            "image": ".article-image img, .news-image img",
            "date": ".publish-date, .news-date"
        }
    },
    "jugantor": {
        "name": "Jugantor",
        "base_url": "https://www.jugantor.com",
        "rss_feeds": [
            "https://www.jugantor.com/feed/",
            "https://www.jugantor.com/national/feed/",
            "https://www.jugantor.com/international/feed/",
            "https://www.jugantor.com/sports/feed/"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .news-content p",
            "image": ".article-image img, .news-image img",
            "date": ".publish-date, .news-date"
        }
    },
    "kaler_kantho": {
        "name": "Kaler Kantho",
        "base_url": "https://www.kalerkantho.com",
        "rss_feeds": [
            "https://www.kalerkantho.com/rss.xml",
            "https://www.kalerkantho.com/home/rss.xml",
            "https://www.kalerkantho.com/world/rss.xml",
            "https://www.kalerkantho.com/sports/rss.xml"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .news-content p",
            "image": ".article-image img, .news-image img",
            "date": ".publish-date, .news-date"
        }
    },
    "bangladesh_pratidin": {
        "name": "Bangladesh Pratidin",
        "base_url": "https://www.bd-pratidin.com",
        "rss_feeds": [
            "https://www.bd-pratidin.com/feed/",
            "https://www.bd-pratidin.com/national/feed/",
            "https://www.bd-pratidin.com/international/feed/",
            "https://www.bd-pratidin.com/sports/feed/"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .news-content p",
            "image": ".article-image img, .news-image img",
            "date": ".publish-date, .news-date"
        }
    },
    "dhaka_tribune": {
        "name": "Dhaka Tribune",
        "base_url": "https://www.dhakatribune.com",
        "rss_feeds": [
            "https://www.dhakatribune.com/feed",
            "https://www.dhakatribune.com/bangladesh/feed",
            "https://www.dhakatribune.com/world/feed",
            "https://www.dhakatribune.com/sports/feed"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .story-content p",
            "image": ".article-image img, .story-image img",
            "date": ".publish-date, .article-date"
        }
    },
    "daily_nayadiganta": {
        "name": "Daily Nayadiganta",
        "base_url": "https://www.dailynayadiganta.com",
        "rss_feeds": [
            "https://www.dailynayadiganta.com/rss.xml",
            "https://www.dailynayadiganta.com/national/rss.xml",
            "https://www.dailynayadiganta.com/international/rss.xml",
            "https://www.dailynayadiganta.com/sports/rss.xml"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .news-content p",
            "image": ".article-image img, .news-image img",
            "date": ".publish-date, .news-date"
        }
    },
    "daily_observer": {
        "name": "The Daily Observer",
        "base_url": "https://www.observerbd.com",
        "rss_feeds": [
            "https://www.observerbd.com/feed/",
            "https://www.observerbd.com/national/feed/",
            "https://www.observerbd.com/international/feed/",
            "https://www.observerbd.com/sports/feed/"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .news-content p",
            "image": ".article-image img, .news-image img",
            "date": ".publish-date, .news-date"
        }
    },
    "bss": {
        "name": "BSS",
        "base_url": "https://www.bssnews.net",
        "rss_feeds": [
            "https://www.bssnews.net/feed/",
            "https://www.bssnews.net/national/feed/",
            "https://www.bssnews.net/international/feed/",
            "https://www.bssnews.net/sports/feed/"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .news-content p",
            "image": ".article-image img, .news-image img",
            "date": ".publish-date, .news-date"
        }
    },
    "business_standard": {
        "name": "The Business Standard",
        "base_url": "https://www.tbsnews.net",
        "rss_feeds": [
            "https://www.tbsnews.net/feed",
            "https://www.tbsnews.net/bangladesh/feed",
            "https://www.tbsnews.net/world/feed",
            "https://www.tbsnews.net/economy/feed"
        ],
        "selectors": {
            "title": "h1.title, h1.headline",
            "description": ".article-content p, .story-content p",
            "image": ".article-image img, .story-image img",
            "date": ".publish-date, .article-date"
        }
    }
}

