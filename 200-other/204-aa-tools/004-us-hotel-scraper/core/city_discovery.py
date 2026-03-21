"""
City discovery module for finding Agoda place IDs.

Provides known Agoda City IDs for US Metropolitan Statistical Areas.
The Agoda API requires IDs in format "AGODA_CITY|XXXX" - these cannot be
discovered programmatically from the places API.
"""

import logging
from typing import List, Optional, Tuple

from .database import get_database

logger = logging.getLogger(__name__)


# Known Agoda City IDs for major US cities
# Format: "AGODA_CITY|{numeric_id}"
# These IDs are extracted from the aadvantagehotels.com website
AGODA_CITY_IDS = {
    # Major metros with verified IDs
    ("New York", "NY"): "318",
    ("Los Angeles", "CA"): "12772",
    ("Chicago", "IL"): "7889",
    ("Dallas", "TX"): "8683",
    ("Houston", "TX"): "1178",
    ("Washington", "DC"): "2320",
    ("Philadelphia", "PA"): "2082",
    ("Miami", "FL"): "13668",
    ("Atlanta", "GA"): "12226",
    ("Boston", "MA"): "9254",
    ("Phoenix", "AZ"): "773",
    ("San Francisco", "CA"): "13801",
    ("Seattle", "WA"): "4579",
    ("Minneapolis", "MN"): "8934",
    ("San Diego", "CA"): "1159",
    ("Tampa", "FL"): "14792",
    ("Denver", "CO"): "3649",
    ("St. Louis", "MO"): "5117",
    ("Baltimore", "MD"): "5107",
    ("Orlando", "FL"): "16937",
    ("Charlotte", "NC"): "2339",
    ("San Antonio", "TX"): "15313",
    ("Portland", "OR"): "1143",
    ("Sacramento", "CA"): "8952",
    ("Pittsburgh", "PA"): "4040",
    ("Las Vegas", "NV"): "17072",
    ("Austin", "TX"): "4542",
    ("Cincinnati", "OH"): "4614",
    ("Kansas City", "MO"): "4838",
    ("Columbus", "OH"): "7621",
    ("Indianapolis", "IN"): "5270",
    ("Cleveland", "OH"): "1141",
    ("San Jose", "CA"): "8951",
    ("Nashville", "TN"): "2687",
    ("Milwaukee", "WI"): "6052",
    ("Jacksonville", "FL"): "7813",
    ("Oklahoma City", "OK"): "2685",
    ("Raleigh", "NC"): "11206",
    ("Memphis", "TN"): "3003",
    ("Richmond", "VA"): "3207",
    ("New Orleans", "LA"): "4589",
    ("Louisville", "KY"): "3133",
    ("Salt Lake City", "UT"): "12269",
    ("Hartford", "CT"): "8259",
    ("Buffalo", "NY"): "4283",
    ("Birmingham", "AL"): "13287",
    ("Honolulu", "HI"): "4952",
    ("Tucson", "AZ"): "7787",
    ("Tulsa", "OK"): "5266",
    ("Albuquerque", "NM"): "14437",
    ("Charleston", "SC"): "9050",
    ("Boise", "ID"): "10695",
    ("Savannah", "GA"): "5097",
    ("Fort Lauderdale", "FL"): "2396",
    ("Palm Beach", "FL"): "16947",
    ("Scottsdale", "AZ"): "16295",
    ("Santa Monica", "CA"): "227",
    ("Beverly Hills", "CA"): "2398",
    ("Key West", "FL"): "13665",
    ("Aspen", "CO"): "6714",
    ("Napa", "CA"): "10740",
    ("Maui", "HI"): "9296",
    # Newly discovered via browser automation (Jan 2026)
    # Batch 1 - Major metros
    ("Riverside", "CA"): "21764",
    ("Detroit", "MI"): "3322",
    ("Virginia Beach", "VA"): "8163",
    ("Providence", "RI"): "11639",
    ("Rochester", "NY"): "17127",
    ("Grand Rapids", "MI"): "17080",
    ("Fresno", "CA"): "13602",
    ("Worcester", "MA"): "19522",
    ("Omaha", "NE"): "13630",
    ("Knoxville", "TN"): "11658",
    ("El Paso", "TX"): "7692",
    ("Baton Rouge", "LA"): "4359",
    ("Colorado Springs", "CO"): "10680",
    ("Madison", "WI"): "17136",
    ("Wichita", "KS"): "12289",
    ("Syracuse", "NY"): "5831",
    # Batch 2 - Mid-size metros
    ("Toledo", "OH"): "17123",
    ("Dayton", "OH"): "1394",
    ("Spokane", "WA"): "13796",
    ("Chattanooga", "TN"): "14566",
    ("Scranton", "PA"): "14274",
    ("Modesto", "CA"): "8418",
    ("Augusta", "GA"): "17253",
    ("Durham", "NC"): "2394",
    ("Harrisburg", "PA"): "6031",
    ("Bridgeport", "CT"): "22599",
    ("Greenville", "SC"): "11356",
    ("Bakersfield", "CA"): "14094",
    ("Albany", "NY"): "17096",
    ("New Haven", "CT"): "3984",
    ("McAllen", "TX"): "5397",
    ("Oxnard", "CA"): "10157",
    # Batch 3 - Smaller metros
    ("Allentown", "PA"): "1868",
    ("Columbia", "SC"): "2299",
    ("Sarasota", "FL"): "804",
    ("Greensboro", "NC"): "4689",
    ("Stockton", "CA"): "13336",
    ("Fort Myers", "FL"): "6861",
    ("Little Rock", "AR"): "407",
    ("Lakeland", "FL"): "7485",
    ("Akron", "OH"): "17138",
    ("Des Moines", "IA"): "20802",
    ("Springfield", "MA"): "570",
    ("Provo", "UT"): "1537",
    ("Winston-Salem", "NC"): "19842",
    ("Ogden", "UT"): "10860",
    ("Daytona Beach", "FL"): "3965",
    ("Melbourne", "FL"): "11456",
}

# Top 100 US Metropolitan Statistical Areas by population
# Source: US Census Bureau estimates
US_MSAS = [
    # Rank, MSA Name, Principal City, State, Population (est)
    (1, "New York-Newark-Jersey City", "New York", "NY", 19768458),
    (2, "Los Angeles-Long Beach-Anaheim", "Los Angeles", "CA", 12872808),
    (3, "Chicago-Naperville-Elgin", "Chicago", "IL", 9426216),
    (4, "Dallas-Fort Worth-Arlington", "Dallas", "TX", 7694730),
    (5, "Houston-The Woodlands-Sugar Land", "Houston", "TX", 7206841),
    (6, "Washington-Arlington-Alexandria", "Washington", "DC", 6356434),
    (7, "Philadelphia-Camden-Wilmington", "Philadelphia", "PA", 6246160),
    (8, "Miami-Fort Lauderdale-Pompano Beach", "Miami", "FL", 6183199),
    (9, "Atlanta-Sandy Springs-Alpharetta", "Atlanta", "GA", 6144050),
    (10, "Boston-Cambridge-Newton", "Boston", "MA", 4899932),
    (11, "Phoenix-Mesa-Chandler", "Phoenix", "AZ", 4946145),
    (12, "San Francisco-Oakland-Berkeley", "San Francisco", "CA", 4566961),
    (13, "Riverside-San Bernardino-Ontario", "Riverside", "CA", 4650631),
    (14, "Detroit-Warren-Dearborn", "Detroit", "MI", 4342304),
    (15, "Seattle-Tacoma-Bellevue", "Seattle", "WA", 4018762),
    (16, "Minneapolis-St. Paul-Bloomington", "Minneapolis", "MN", 3690512),
    (17, "San Diego-Chula Vista-Carlsbad", "San Diego", "CA", 3269973),
    (18, "Tampa-St. Petersburg-Clearwater", "Tampa", "FL", 3219514),
    (19, "Denver-Aurora-Lakewood", "Denver", "CO", 2963821),
    (20, "St. Louis", "St. Louis", "MO", 2806349),
    (21, "Baltimore-Columbia-Towson", "Baltimore", "MD", 2797407),
    (22, "Orlando-Kissimmee-Sanford", "Orlando", "FL", 2673376),
    (23, "Charlotte-Concord-Gastonia", "Charlotte", "NC", 2660329),
    (24, "San Antonio-New Braunfels", "San Antonio", "TX", 2558143),
    (25, "Portland-Vancouver-Hillsboro", "Portland", "OR", 2509288),
    (26, "Sacramento-Roseville-Folsom", "Sacramento", "CA", 2397382),
    (27, "Pittsburgh", "Pittsburgh", "PA", 2354842),
    (28, "Las Vegas-Henderson-Paradise", "Las Vegas", "NV", 2265461),
    (29, "Austin-Round Rock-Georgetown", "Austin", "TX", 2283371),
    (30, "Cincinnati", "Cincinnati", "OH", 2256884),
    (31, "Kansas City", "Kansas City", "MO", 2192035),
    (32, "Columbus", "Columbus", "OH", 2138926),
    (33, "Indianapolis-Carmel-Anderson", "Indianapolis", "IN", 2111040),
    (34, "Cleveland-Elyria", "Cleveland", "OH", 2048449),
    (35, "San Jose-Sunnyvale-Santa Clara", "San Jose", "CA", 1945084),
    (36, "Nashville-Davidson-Murfreesboro", "Nashville", "TN", 1989519),
    (37, "Virginia Beach-Norfolk-Newport News", "Virginia Beach", "VA", 1787169),
    (38, "Providence-Warwick", "Providence", "RI", 1624578),
    (39, "Milwaukee-Waukesha", "Milwaukee", "WI", 1568113),
    (40, "Jacksonville", "Jacksonville", "FL", 1605848),
    (41, "Oklahoma City", "Oklahoma City", "OK", 1441647),
    (42, "Raleigh-Cary", "Raleigh", "NC", 1413982),
    (43, "Memphis", "Memphis", "TN", 1337779),
    (44, "Richmond", "Richmond", "VA", 1314434),
    (45, "New Orleans-Metairie", "New Orleans", "LA", 1271845),
    (46, "Louisville-Jefferson County", "Louisville", "KY", 1285439),
    (47, "Salt Lake City", "Salt Lake City", "UT", 1232696),
    (48, "Hartford-East Hartford-Middletown", "Hartford", "CT", 1204877),
    (49, "Buffalo-Cheektowaga", "Buffalo", "NY", 1127983),
    (50, "Birmingham-Hoover", "Birmingham", "AL", 1115289),
    # Continue with more cities...
    (51, "Rochester", "Rochester", "NY", 1090135),
    (52, "Grand Rapids-Kentwood", "Grand Rapids", "MI", 1087592),
    (53, "Tucson", "Tucson", "AZ", 1043433),
    (54, "Urban Honolulu", "Honolulu", "HI", 1000890),
    (55, "Tulsa", "Tulsa", "OK", 1015331),
    (56, "Fresno", "Fresno", "CA", 1002046),
    (57, "Worcester", "Worcester", "MA", 947066),
    (58, "Bridgeport-Stamford-Norwalk", "Bridgeport", "CT", 943332),
    (59, "Omaha-Council Bluffs", "Omaha", "NE", 967604),
    (60, "Albuquerque", "Albuquerque", "NM", 917774),
    (61, "Greenville-Anderson-Greer", "Greenville", "SC", 920477),
    (62, "Bakersfield", "Bakersfield", "CA", 900202),
    (63, "Albany-Schenectady-Troy", "Albany", "NY", 880766),
    (64, "New Haven-Milford", "New Haven", "CT", 864835),
    (65, "McAllen-Edinburg-Mission", "McAllen", "TX", 870781),
    (66, "Knoxville", "Knoxville", "TN", 869046),
    (67, "El Paso", "El Paso", "TX", 868859),
    (68, "Oxnard-Thousand Oaks-Ventura", "Oxnard", "CA", 843843),
    (69, "Baton Rouge", "Baton Rouge", "LA", 856779),
    (70, "Allentown-Bethlehem-Easton", "Allentown", "PA", 844052),
    (71, "Columbia", "Columbia", "SC", 838433),
    (72, "North Port-Sarasota-Bradenton", "Sarasota", "FL", 836995),
    (73, "Dayton-Kettering", "Dayton", "OH", 805998),
    (74, "Charleston-North Charleston", "Charleston", "SC", 802122),
    (75, "Greensboro-High Point", "Greensboro", "NC", 779343),
    (76, "Stockton", "Stockton", "CA", 779233),
    (77, "Cape Coral-Fort Myers", "Fort Myers", "FL", 770577),
    (78, "Colorado Springs", "Colorado Springs", "CO", 755105),
    (79, "Boise City", "Boise", "ID", 764718),
    (80, "Little Rock-North Little Rock-Conway", "Little Rock", "AR", 748031),
    (81, "Lakeland-Winter Haven", "Lakeland", "FL", 724777),
    (82, "Akron", "Akron", "OH", 702219),
    (83, "Des Moines-West Des Moines", "Des Moines", "IA", 699292),
    (84, "Springfield", "Springfield", "MA", 698537),
    (85, "Provo-Orem", "Provo", "UT", 659399),
    (86, "Winston-Salem", "Winston-Salem", "NC", 676008),
    (87, "Ogden-Clearfield", "Ogden", "UT", 694863),
    (88, "Madison", "Madison", "WI", 680796),
    (89, "Deltona-Daytona Beach-Ormond Beach", "Daytona Beach", "FL", 658961),
    (90, "Palm Bay-Melbourne-Titusville", "Melbourne", "FL", 601942),
    (91, "Syracuse", "Syracuse", "NY", 650502),
    (92, "Wichita", "Wichita", "KS", 647610),
    (93, "Toledo", "Toledo", "OH", 642706),
    (94, "Augusta-Richmond County", "Augusta", "GA", 611000),
    (95, "Durham-Chapel Hill", "Durham", "NC", 587093),
    (96, "Harrisburg-Carlisle", "Harrisburg", "PA", 583390),
    (97, "Spokane-Spokane Valley", "Spokane", "WA", 573493),
    (98, "Chattanooga", "Chattanooga", "TN", 561055),
    (99, "Scranton-Wilkes-Barre", "Scranton", "PA", 553885),
    (100, "Modesto", "Modesto", "CA", 546235),
]


def get_agoda_place_id(city_name: str, state: str) -> Optional[str]:
    """
    Get the Agoda place ID for a city from the known mapping.

    Args:
        city_name: City name
        state: State abbreviation

    Returns:
        Agoda place ID in format "AGODA_CITY|XXXX" or None
    """
    key = (city_name, state)
    agoda_id = AGODA_CITY_IDS.get(key)
    if agoda_id:
        return f"AGODA_CITY|{agoda_id}"
    return None


def register_city(
    city_name: str,
    state: str,
    msa_name: str,
    population: int,
) -> Tuple[str, Optional[str]]:
    """
    Register a city in the database with its Agoda place ID.

    Args:
        city_name: City name
        state: State abbreviation
        msa_name: MSA name
        population: Population estimate

    Returns:
        Tuple of (msa_name, place_id or None)
    """
    db = get_database()

    # Check if already registered
    existing = db.get_city_by_name(city_name, state)
    if existing and existing.get('agoda_place_id'):
        logger.debug(f"Already have place ID for {city_name}, {state}")
        return msa_name, existing['agoda_place_id']

    # Look up place ID from known mapping
    place_id = get_agoda_place_id(city_name, state)

    if place_id:
        db.upsert_city(
            msa_name=msa_name,
            city_name=city_name,
            state=state,
            agoda_place_id=place_id,
            population=population,
        )
        logger.info(f"Registered: {city_name}, {state} -> {place_id}")
    else:
        db.upsert_city(
            msa_name=msa_name,
            city_name=city_name,
            state=state,
            population=population,
        )
        logger.warning(f"No Agoda ID for {city_name}, {state} (not in known mapping)")

    return msa_name, place_id


def discover_all_cities(
    limit: Optional[int] = None,
) -> dict:
    """
    Register all MSAs with their Agoda place IDs.

    Uses the hardcoded AGODA_CITY_IDS mapping since the places API
    returns Google Place IDs which don't work with the search API.

    Args:
        limit: Optional limit on number of cities to process

    Returns:
        Dict with discovery statistics
    """
    cities_to_discover = US_MSAS[:limit] if limit else US_MSAS

    logger.info(f"Registering {len(cities_to_discover)} cities...")

    results = {
        'total': len(cities_to_discover),
        'discovered': 0,
        'missing': 0,
    }

    for rank, msa_name, city_name, state, population in cities_to_discover:
        msa, place_id = register_city(city_name, state, msa_name, population)
        if place_id:
            results['discovered'] += 1
        else:
            results['missing'] += 1

    logger.info(
        f"Registration complete: {results['discovered']} with Agoda IDs, "
        f"{results['missing']} without (not in known mapping)"
    )

    return results


def get_all_msa_data() -> List[Tuple]:
    """Get the full MSA data list."""
    return US_MSAS


def get_top_msas(limit: int = 50) -> List[Tuple]:
    """Get top MSAs by population."""
    return US_MSAS[:limit]
