import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, Tuple, List
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from config.settings import NOMINATIM_USER_AGENT

logger = logging.getLogger(__name__)

class GeolocationService:
    def __init__(self):
        self.nominatim = Nominatim(user_agent=NOMINATIM_USER_AGENT)
        self.session = None
        self.cache = {}  # Simple in-memory cache
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests for Nominatim
        
        # Bangladesh location patterns
        self.bangladesh_patterns = [
            # Major cities
            r'\b(ঢাকা|dhaka|dhaka city)\b',
            r'\b(চট্টগ্রাম|chittagong|chattogram)\b',
            r'\b(সিলেট|sylhet)\b',
            r'\b(রাজশাহী|rajshahi)\b',
            r'\b(খুলনা|khulna)\b',
            r'\b(বরিশাল|barisal|barishal)\b',
            r'\b(রংপুর|rangpur)\b',
            r'\b(ময়মনসিংহ|mymensingh)\b',
            r'\b(কুমিল্লা|comilla|cumilla)\b',
            r'\b(নারায়ণগঞ্জ|narayanganj)\b',
            r'\b(গাজীপুর|gazipur)\b',
            r'\b(টাঙ্গাইল|tangail)\b',
            r'\b(জামালপুর|jamalpur)\b',
            r'\b(নেত্রকোনা|netrokona)\b',
            r'\b(শেরপুর|sherpur)\b',
            r'\b(কিশোরগঞ্জ|kishoreganj)\b',
            r'\b(মানিকগঞ্জ|manikganj)\b',
            r'\b(মুন্শিগঞ্জ|munshiganj)\b',
            r'\b(নরসিংদী|narsingdi)\b',
            r'\b(ফরিদপুর|faridpur)\b',
            r'\b(গোপালগঞ্জ|gopalganj)\b',
            r'\b(মাদারীপুর|madaripur)\b',
            r'\b(রাজবাড়ী|rajbari)\b',
            r'\b(শরীয়তপুর|shariatpur)\b',
            r'\b(নোয়াখালী|noakhali)\b',
            r'\b(ফেনী|feni)\b',
            r'\b(লক্ষ্মীপুর|lakshmipur)\b',
            r'\b(চাঁদপুর|chandpur)\b',
            r'\b(ব্রাহ্মণবাড়িয়া|brahmanbaria)\b',
            r'\b(হবিগঞ্জ|habiganj)\b',
            r'\b(মৌলভীবাজার|moulvibazar)\b',
            r'\b(সুনামগঞ্জ|sunamganj)\b',
            r'\b(নাটোর|natore)\b',
            r'\b(নওগাঁ|naogaon)\b',
            r'\b(চাঁপাইনবাবগঞ্জ|chapainawabganj)\b',
            r'\b(পাবনা|pabna)\b',
            r'\b(সিরাজগঞ্জ|sirajganj)\b',
            r'\b(বগুড়া|bogura|bogra)\b',
            r'\b(জয়পুরহাট|joypurhat)\b',
            r'\b(কুষ্টিয়া|kushtia)\b',
            r'\b(মেহেরপুর|meherpur)\b',
            r'\b(চুয়াডাঙ্গা|chuadanga)\b',
            r'\b(ঝিনাইদহ|jhenaidah)\b',
            r'\b(মাগুরা|magura)\b',
            r'\b(নড়াইল|narail)\b',
            r'\b(সাতক্ষীরা|satkhira)\b',
            r'\b(বাগেরহাট|bagerhat)\b',
            r'\b(ঝালকাঠি|jhalokati)\b',
            r'\b(পটুয়াখালী|patuakhali)\b',
            r'\b(পিরোজপুর|pirojpur)\b',
            r'\b(ভোলা|bhola)\b',
            r'\b(বরগুনা|barguna)\b',
            r'\b(দিনাজপুর|dinajpur)\b',
            r'\b(ঠাকুরগাঁও|thakurgaon)\b',
            r'\b(পঞ্চগড়|panchagarh)\b',
            r'\b(নীলফামারী|nilphamari)\b',
            r'\b(লালমনিরহাট|lalmonirhat)\b',
            r'\b(কুড়িগ্রাম|kurigram)\b',
            r'\b(গাইবান্ধা|gaibandha)\b',
            r'\b(কক্সবাজার|cox\'s bazar|coxsbazar)\b',
            r'\b(রাঙ্গামাটি|rangamati)\b',
            r'\b(বান্দরবান|bandarban)\b',
            r'\b(খাগড়াছড়ি|khagrachhari)\b',
            
            # Areas/localities
            r'\b(উত্তরা|uttara)\b',
            r'\b(গুলশান|gulshan)\b',
            r'\b(ধানমন্ডি|dhanmondi)\b',
            r'\b(বনানী|banani)\b',
            r'\b(মিরপুর|mirpur)\b',
            r'\b(মোহাম্মদপুর|mohammadpur)\b',
            r'\b(রমনা|ramna)\b',
            r'\b(তেজগাঁও|tejgaon)\b',
            r'\b(পল্টন|paltan)\b',
            r'\b(মতিঝিল|motijheel)\b',
            r'\b(ওয়ারী|wari)\b',
            r'\b(পুরান ঢাকা|old dhaka)\b',
            r'\b(নিউ মার্কেট|new market)\b',
            r'\b(শাহবাগ|shahbag)\b',
            r'\b(কারওয়ান বাজার|karwan bazar)\b',
            r'\b(ফার্মগেট|farmgate)\b',
            r'\b(কল্যাণপুর|kalyanpur)\b',
            r'\b(শ্যামলী|shyamoli)\b',
            r'\b(আগারগাঁও|agargaon)\b',
            r'\b(বাড্ডা|badda)\b',
            r'\b(রামপুরা|rampura)\b',
            r'\b(খিলগাঁও|khilgaon)\b',
            r'\b(মালিবাগ|malibagh)\b',
            r'\b(মগবাজার|mogbazar)\b',
            r'\b(সিদ্ধেশ্বরী|siddheshwari)\b',
            r'\b(সেগুনবাগিচা|segunbagicha)\b',
            r'\b(হাতিরঝিল|hatirjheel)\b',
            r'\b(বসুন্ধরা|bashundhara)\b',
            r'\b(বারিধারা|baridhara)\b',
            r'\b(নিকেতন|niketon)\b',
            r'\b(বনশ্রী|banasree)\b',
            r'\b(মেরুল|merul)\b',
            r'\b(যাত্রাবাড়ী|jatrabari)\b',
            r'\b(কদমতলী|kadamtali)\b',
            r'\b(গেন্ডারিয়া|gendaria)\b',
            r'\b(নাজিরাবাজার|nazirabazar)\b',
            r'\b(শান্তিনগর|shantinagar)\b',
            r'\b(কমলাপুর|kamalapur)\b',
            r'\b(সবুজবাগ|sabujbagh)\b',
            r'\b(ডেমরা|demra)\b',
            r'\b(কেরানীগঞ্জ|keraniganj)\b',
            r'\b(সাভার|savar)\b',
            r'\b(আশুলিয়া|ashulia)\b',
            r'\b(টঙ্গী|tongi)\b',
            r'\b(কালিয়াকৈর|kaliakair)\b',
            r'\b(কাপাসিয়া|kapasia)\b',
            r'\b(শ্রীপুর|sreepur)\b',
            r'\b(ভালুকা|bhaluka)\b',
            r'\b(ত্রিশাল|trishal)\b',
            r'\b(ফুলবাড়িয়া|fulbaria)\b',
            r'\b(গফরগাঁও|gafargaon)\b',
            r'\b(ঈশ্বরগঞ্জ|ishwarganj)\b',
            r'\b(নান্দাইল|nandail)\b',
            r'\b(তারাকান্দা|tarakanda)\b',
            r'\b(হালুয়াঘাট|haluaghat)\b',
            r'\b(দেওয়ানগঞ্জ|dewanganj)\b',
            r'\b(বকশীগঞ্জ|bakshiganj)\b',
            r'\b(ইসলামপুর|islampur)\b',
            r'\b(মাদারগঞ্জ|madarganj)\b',
            r'\b(মেলান্দহ|melandaha)\b',
            r'\b(সরিষাবাড়ী|sarishabari)\b',
            r'\b(নকলা|nakla)\b',
            r'\b(ঝিনাইগাতী|jhinaigati)\b',
            r'\b(শ্রীবর্দী|sreebordi)\b',
            r'\b(নালিতাবাড়ী|nalitabari)\b',
            r'\b(মুক্তাগাছা|muktagachha)\b',
            r'\b(ফুলপুর|fulpur)\b',
            r'\b(ধোবাউড়া|dhobaura)\b',
            r'\b(কলমাকান্দা|kolmakanda)\b',
            r'\b(পূর্বধলা|purbadhala)\b',
            r'\b(খালিয়াজুরী|khaliajuri)\b',
            r'\b(মদন|madan)\b',
            r'\b(কেন্দুয়া|kendua)\b',
            r'\b(আটপাড়া|atpara)\b',
            r'\b(বারহাট্টা|barhatta)\b',
            r'\b(দুর্গাপুর|durgapur)\b',
            r'\b(কালমাকান্দা|kalmakanda)\b',
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.bangladesh_patterns]
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def extract_locations_from_text(self, text: str) -> List[str]:
        """Extract potential location names from text using regex patterns"""
        if not text:
            return []
        
        locations = []
        text_lower = text.lower()
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if match not in locations:
                    locations.append(match)
        
        return locations
    
    async def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude for a location using Nominatim"""
        if not location:
            return None
        
        # Check cache first
        cache_key = location.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Rate limiting for Nominatim
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        try:
            # Add Bangladesh context to improve accuracy
            query = f"{location}, Bangladesh"
            
            # Use asyncio to run the synchronous geocoding in a thread
            loop = asyncio.get_event_loop()
            location_data = await loop.run_in_executor(
                None, 
                lambda: self.nominatim.geocode(query, timeout=10)
            )
            
            self.last_request_time = time.time()
            
            if location_data:
                lat_lng = (location_data.latitude, location_data.longitude)
                self.cache[cache_key] = lat_lng
                logger.info(f"Geocoded '{location}' to {lat_lng}")
                return lat_lng
            else:
                logger.warning(f"Could not geocode location: {location}")
                self.cache[cache_key] = None
                return None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding service error for '{location}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error geocoding '{location}': {str(e)}")
            return None
    
    async def geocode_with_pelias(self, location: str) -> Optional[Tuple[float, float]]:
        """Alternative geocoding using Pelias API (if available)"""
        if not location or not self.session:
            return None
        
        try:
            # Pelias geocoding endpoint (using public instance)
            url = "https://api.geocode.earth/v1/search"
            params = {
                'text': f"{location}, Bangladesh",
                'boundary.country': 'BD',
                'size': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    features = data.get('features', [])
                    
                    if features:
                        coordinates = features[0]['geometry']['coordinates']
                        # Pelias returns [lng, lat], we need [lat, lng]
                        lat_lng = (coordinates[1], coordinates[0])
                        logger.info(f"Pelias geocoded '{location}' to {lat_lng}")
                        return lat_lng
                else:
                    logger.warning(f"Pelias API returned status {response.status} for '{location}'")
                    
        except Exception as e:
            logger.error(f"Error using Pelias API for '{location}': {str(e)}")
        
        return None
    
    async def get_location_for_news(self, news_item: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """Extract and geocode location from news item"""
        # Combine title and description for location extraction
        text_to_search = ""
        if news_item.get('title'):
            text_to_search += news_item['title'] + " "
        if news_item.get('description'):
            text_to_search += news_item['description']
        
        # Extract potential locations
        locations = self.extract_locations_from_text(text_to_search)
        
        if not locations:
            # Default to Dhaka if no specific location found
            return await self.geocode_location("Dhaka")
        
        # Try to geocode the first location found
        for location in locations:
            lat_lng = await self.geocode_location(location)
            if lat_lng:
                return lat_lng
        
        # If no locations could be geocoded, default to Dhaka
        return await self.geocode_location("Dhaka")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cached_locations': list(self.cache.keys())
        }

