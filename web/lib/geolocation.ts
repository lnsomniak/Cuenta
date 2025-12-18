export interface Coordinates {
    latitude: number;
    longitude: number;
}

export interface NearbyStore {
    id: string;
    name: string;
    chain: string;
    distance: number; // in AMEERICAN NUMERALS RAHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
    address?: string;
}

// Get user's current position
export function getCurrentPosition(): Promise<Coordinates> {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Geolocation not supported"));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                });
            },
            (error) => {
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        reject(new Error("Location permission denied"))
                        break;
                    case error.POSITION_UNAVAILABLE:
                        reject(new Error("Location unavailable"));
                        break;
                    case error.TIMEOUT:
                        reject(new Error("Location request timed out"));
                        break;
                    default:
                        reject(new Error("Unknown location error"));
                }
            },
            {
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 300000, // Cache for 5 minutes, not too strict
            }
        );
    });
}

// Calculate distance between two points (Haversine formula, thank you basic trig)
export function calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number {
    const R = 3959; // Earth's radius in miles orr 6,371km on average. I'm using the equatorial radius of 3,963 miles for more accuracy in Houston area
    const dLat = toRad(lat2 - lat1); 
    const dLon = toRad(lon2 - lon1);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) *
            Math.cos(toRad(lat2)) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2); // used geogebra to verify calculations, but this is a very standard formula so most of what I did testing was just for fun and interest
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function toRad(deg: number): number {
    return deg * (Math.PI / 180);
}

// Houston area store locations (fallback data)
const HOUSTON_STORES: Array<{
    id: string;
    name: string;
    chain: string;
    lat: number;
    lon: number;
    address: string;
}> = [
    // Kroger
    {
        id: "kroger-heights",
        name: "Kroger - Heights",
        chain: "Kroger",
        lat: 29.789632,
        lon: -95.411206,
        address: "1035 N Shepherd Dr Houston, TX 77008",
    },
    {
        id: "kroger-Memorial-Park",
        name: "Kroger - Memorial Park",
        chain: "Kroger",
        lat: 29.773292,
        lon: -95.389846,
        address: "1440 Studemont St, Houston, TX 77007",
    },
    {
        id: "kroger-river-oaks",
        name: "Kroger - River Oaks",
        chain: "Kroger",
        lat: 29.754087,
        lon: -95.405477,
        address: "1938 W Gray St, Houston, TX 77019",
    },
    {
        id: "kroger-kirby",
        name: "Kroger - Kirby Drive",
        chain: "Kroger",
        lat: 29.695913,
        lon: -95.415509,
        address: "7747 Kirby Drive, Houston, TX 77030",
    },    
    {
        id: "kroger-south-central",
        name: "Kroger - South Central",
        chain: "Kroger",
        lat: 29.7397,
        lon: -95.340458,
        address: "4000 Polk Street, Houston, TX 77023",
    },    
    {
        id: "kroger-southeast-houston",
        name: "Kroger - Southeast Houston",
        chain: "Kroger",
        lat: 29.674862,
        lon: -95.291033,
        address: "6322 Telephone Rd, Houston, TX 77087",
    },    
    {
        id: "kroger-rice-village",
        name: "Kroger - Rice Village",
        chain: "Kroger",
        lat: 29.727178,
        lon: -95.430888,
        address: "5150 Buffalo Speedway, Houston, TX 77005",
    },
        {
        id: "kroger-meyerland",
        name: "Kroger - MeyerLand",
        chain: "Kroger",
        lat: 29.669287,
        lon: -95.463963,
        address: "10306 S Post Oak Rd, Houston, TX 77035",
    },
        {
        id: "kroger-pearland",
        name: "Kroger - Pearland",
        chain: "Kroger",
        lat: 29.583137,
        lon: -95.389792,
        address: "11003 Shadow Creek Pkwy, Pearland, TX 77584",
    },
        {
        id: "kroger-northside",
        name: "Kroger - Northside",
        chain: "Kroger",
        lat: 29.804573,
        lon: -95.400458,
        address: "239 W 20th St, Houston, TX 77008",
    },
            {
        id: "kroger-southbelt-ellington",
        name: "Kroger - SouthBelt / Ellington",
        chain: "Kroger",
        lat: 29.602202,
        lon: -95.213513,
        address: "11701 S Sam Houston Pkwy E, Houston, TX 77089",
    },
            {
        id: "kroger-westside",
        name: "Kroger - Westside",
        chain: "Kroger",
        lat: 29.748231,
        lon: -95.500104,
        address: "1801 S Voss Rd, Houston, TX 77057",
    },
            {
        id: "kroger-brookside-village",
        name: "Kroger - Brookside Village",
        chain: "Kroger",
        lat: 29.560689,
        lon: -95.348942,
        address: "8323 Broadway St, Pearland, TX 77581",
    },
    {
        id: "kroger-sugar-land",
        name: "Kroger - Sugar-land",
        chain: "Kroger",
        lat: 29.551179,
        lon: -95.585335,
        address: "18861 University Blvd, Sugar Land, TX 77479",
    },
        {
        id: "kroger-channelview-cloverleaf",
        name: "Kroger - Channelview / Cloverleaf",
        chain: "Kroger",
        lat: 29.789446,
        lon: -95.200917,
        address: "12620 Woodforest Blvd, Houston, TX 77015",
    },
        {
        id: "kroger-oak-forest-shopping-center",
        name: "Kroger - Oak Forest Shopping Center",
        chain: "Kroger",
        lat: 29.828882,
        lon: -95.432023,
        address: "1352 W 43rd St, Houston, TX 77018",
    },
        {
        id: "kroger-oak-hilshire-village",
        name: "Kroger - Hilshire Village",
        chain: "Kroger",
        lat: 29.796824,
        lon: -95.486444,
        address: "1505 Wirt Rd, Houston, TX 77055",
    },
    // H-E-B Locations
    {
        id: "heb-bunker-hill",
        name: "H-E-B - Bunker Hill",
        chain: "HEB",
        lat: 29.787809,
        lon: -95.532455,
        address: "9710 Katy Fwy, Houston, TX 77024"
    },
    {
        id: "heb-bellaire",
        name: "H-E-B - Bellaire",
        chain: "HEB",
        lat: 29.707367,
        lon: -95.469776,
        address: "5106 Bissonnet St, Bellaire, TX 77401"
    },
    {
        id: "heb-montrose-market",
        name: "H-E-B - Montrose Market",
        chain: "HEB",
        lat: 29.738044,
        lon: -95.402767,
        address: "1701 West Alabama Street, Houston, TX 77098"
    },
    {
        id: "heb-buffalo-speedway",
        name: "H-E-B - Buffalo Speedway",
        chain: "HEB",
        lat: 29.727043,
        lon: -95.427167,
        address: "5225 Buffalo Speedway, Houston, TX 77005"
    },
        {
        id: "heb-buffalo-speedway",
        name: "H-E-B - Buffalo Speedway",
        chain: "HEB",
        lat: 29.76888820422564,
        lon: -95.39669119450645,
        address: "3663 Washington Avenue, Houston, TX 77007"
    },
    {
        id: "heb-pearland-market",
        name: "H-E-B - Pearland Market",
        chain: "HEB",
        lat: 29.558204,
        lon: -95.264978,
        address: "4250 Broadway St, Pearland, TX 77581"
    },
    {
        id: "heb-Beechnut",
        name: "H-E-B - Beechnut",
        chain: "HEB",
        lat: 29.69118,
        lon: -95.559822,
        address: "10100 Beechnut Street, Houston, TX 77072"
    },
    {
        id: "heb-woodlands-market",
        name: "H-E-B - Woodlands Market",
        chain: "HEB",
        lat: 30.163491,
        lon: -95.466775,
        address: "9595 Six Pines Drive, The Woodlands, TX 77380"
    },
    {
        id: "heb-kingswood-market",
        name: "H-E-B - Kingswood Market",
        chain: "HEB",
        lat: 30.05312,
        lon: -95.183584,
        address: "4517 Kingwood Drive, Houston, TX 77345"
    },
    {
        id: "heb-heights",
        name: "H-E-B - The Heights",
        chain: "HEB",
        lat: 29.807331,
        lon: -95.408783,
        address: "2300 North Shepherd Drive, Houston, TX 77008"
    },
    {
        id: "heb-san-felipe",
        name: "H-E-B - San Felipe",
        chain: "HEB",
        lat: 29.74797,
        lon: -95.485142,
        address: "5895 San Felipe Street, Houston, TX 77057"
    },
    {
        id: "heb-kempwood-gressner",
        name: "H-E-B - Kempwood & Gressner",
        chain: "HEB",
        lat: 29.821437,
        lon: -95.547302,
        address: "10251 Kempwood Drive, Houston, TX 77080"
    },
        {
        id: "heb-cleveland",
        name: "H-E-B - Cleveland",
        chain: "HEB",
        lat: 30.335387,
        lon: -95.095268,
        address: "100 Truly Plaza, Cleveland, TX 77327"
    },
            {
        id: "heb-north-frazier-street",
        name: "H-E-B - North Frazier Street",
        chain: "HEB",
        lat: 30.335615,
        lon: -95.465283,
        address: "2108 North Frazier Street, Conroe, TX 77301"
    },
            {
        id: "heb-sawdust-road",
        name: "H-E-B - Sawdust Road",
        chain: "HEB",
        lat: 30.1277449,
        lon: -95.4457448,
        address: "130 Sawdust Road, Spring, TX 77380"
    },
            {
        id: "heb-spring-creek-market",
        name: "H-E-B - Spring Creek Market",
        chain: "HEB",
        lat: 30.1077833,
        lon: -95.3874381,
        address: "3540 Rayford Road, Spring, TX 77386"
    },
            {
        id: "heb-tomball-pkwy",
        name: "H-E-B - Tomball Pkwy",
        chain: "HEB",
        lat: 30.0886326,
        lon: -95.6291742,
        address: "28520 Tomball Parkway, Tomball, TX 77375"
    },
            {
        id: "heb-champion-forest-market",
        name: "H-E-B - Champion Forest Market",
        chain: "HEB",
        lat: 30.0537776,
        lon: -95.5769399,
        address: "20311 Champion Forest Drive, Spring, TX 77379"
    },
            {
        id: "heb-creekside-park",
        name: "H-E-B - Creekside Park",
        chain: "HEB",
        lat: 30.1443287,
        lon: -95.5494852,
        address: "26500 Kuykendahl Road, Tomball, TX 77375"
    },
            {
        id: "heb-spring-market",
        name: "H-E-B - Spring Market",
        chain: "HEB",
        lat: 30.0687022,
        lon: -95.4498978,
        address: "2121 FM 2920, Spring, TX 77388"
    },
            {
        id: "heb-atascocita",
        name: "H-E-B - Atascocita ",
        chain: "HEB",
        lat: 30.000285922473907,
        lon: -95.1643467177677,
        address: "7405 West Lake Houston Parkway, Humble, TX 77346"
    },
            {
        id: "heb-blackhawk",
        name: "H-E-B - Blackhawk",
        chain: "HEB",
        lat: 29.6017771,
        lon: -95.2501689,
        address: "9828 Blackhawk Boulevard, Houston, TX 77075"
    },
            {
        id: "heb-northpark",
        name: "H-E-B - Northpark",
        chain: "HEB",
        lat: 30.0686029,
        lon: -95.2516844,
        address: "19529 Northpark Drive, Pittsville, Houston, TX 77339"
    },
                {
        id: "heb-vintage-park-market",
        name: "H-E-B - Vintage Park Market",
        chain: "HEB",
        lat: 29.9953234,
        lon: -95.57623,
        address: "10919 Louetta Road, Houston, TX 77070"
    },
                {
        id: "heb-louetta-and-stuebner",
        name: "H-E-B - Louetta and Stuebner",
        chain: "HEB",
        lat: 30.0223761,
        lon: -95.5273891,
        address: "7310 Louetta Road, Spring, TX 77379"
    },
                {
        id: "heb-market-at-gosling",
        name: "H-E-B - Market at Gosling",
        chain: "HEB",
        lat: 30.0717641,
        lon: -95.5018275,
        address: "5251 FM 2920, Spring, TX 77388"
    },
                {
        id: "heb-macgregor-market",
        name: "H-E-B - MacGregor Market",
        chain: "HEB",
        lat: 29.7139677,
        lon: -95.3768317,
        address: "6055 South Freeway, Houston, TX 77004"
    },
                {
        id: "heb-gulfgate",
        name: "H-E-B - Gulfgate",
        chain: "HEB",
        lat: 29.6984809,
        lon: -95.294894,
        address: "3111 Woodridge Drive, Houston, TX 77087"
    },
                {
        id: "heb-northpark",
        name: "H-E-B - Northpark",
        chain: "HEB",
        lat: 30.0686029,
        lon: -95.2516844,
        address: "19529 Northpark Drive, Pittsville, Houston, TX 77339"
    },
    // Aldi Locations
    {
        id: "aldi-ost",
        name: "Aldi - Old Spanish Trail",
        chain: "Aldi",
        lat: 29.7013695,
        lon: -95.3633575,
        address: "3618 Old Spanish Trail, Houston, TX 77021"
    },
    {
        id: "aldi-almeda",
        name: "Aldi - Almeda Genoa",
        chain: "Aldi",
        lat: 29.6267715,
        lon: -95.2370634,
        address: "10064 Almeda Genoa Rd, Houston, TX 77075"
    },
    {
        id: "aldi-tomball",
        name: "Aldi - Tomball",
        chain: "Aldi",
        lat: 29.9161341,
        lon: -95.4857796,
        address: "13340 Tomball Parkway, Houston, TX 77086"
    },
    {
        id: "aldi-spring",
        name: "Aldi - Spring",
        chain: "Aldi",
        lat: 29.9936761,
        lon: -95.4858917,
        address: "3715 Cypress Creek Parkway, Houston, TX 77068"
    },
    {
        id: "aldi-spring",
        name: "Aldi - Spring",
        chain: "Aldi",
        lat: 30.061,
        lon: -95.414,
        address: "20647 Kuykendahl Rd, Spring, TX 77379"
    },
    {
        id: "aldi-west-road",
        name: "Aldi - West Road",
        chain: "Aldi",
        lat: 29.9144512,
        lon: -95.4096383,
        address: "161 West Road, Houston, TX 77037"
    },
    {
        id: "aldi-el-camino-real",
        name: "Aldi - El Camino Real",
        chain: "Aldi",
        lat: 29.5563709,
        lon: -95.1206663,
        address: "16701 El Camino Real, Houston, TX 77062"
    },
        {
        id: "aldi-gessner",
        name: "Aldi - Gessner",
        chain: "Aldi",
        lat: 29.8180432,
        lon: -95.5447357,
        address: "2550 Gessner Road, Houston, TX 77080"
    },
        {
        id: "aldi-south-highway-6",
        name: "Aldi - South Highway 6",
        chain: "Aldi",
        lat: 29.7180388,
        lon: -95.6430306,
        address: "3601 South Highway 6, Houston, TX 77082"
    },
        {
        id: "aldi-north-shepherd-drive",
        name: "Aldi - North Shepherd Drive",
        chain: "Aldi",
        lat: 29.8229583,
        lon: -95.4097761,
        address: "3938 North Shepherd Drive, Houston, TX 77018"
    },
        {
        id: "aldi-north-highway-6",
        name: "Aldi - North Highway 6",
        chain: "Aldi",
        lat: 29.8615984,
        lon: -95.6464975,
        address: "5855 North Highway 6, Houston, TX 77084"
    },
            {
        id: "aldi-bissonnet-street",
        name: "Aldi - Bissonnet Street",
        chain: "Aldi",
        lat: 29.689455,
        lon: -95.501558,
        address: "6751 Bissonnet Street, Houston, TX 77074"
    },        {
        id: "aldi-jones-road",
        name: "Aldi - Jones Road",
        chain: "Aldi",
        lat: 29.9078721,
        lon: -95.5857979,
        address: "9251 Jones Road, Houston, TX 77065"
    },        {
        id: "aldi-westheimer-road",
        name: "Aldi - Westheimer Road",
        chain: "Aldi",
        lat: 29.736257,
        lon: -95.5335557,
        address: "9525 Westheimer Road, Houston, TX 77063"
    },
        {
        id: "aldi-louetta-road",
        name: "Aldi - Louetta Road",
        chain: "Aldi",
        lat: 30.0020036,
        lon: -95.5599323,
        address: "9870 Louetta Road, Houston, TX 77070"
    }    
];

// Find nearest stores to user's location
export function findNearestStores(
    userLat: number,
    userLon: number,
    limit: number = 5,
    chainFilter?: string
): NearbyStore[] {
    let stores = HOUSTON_STORES;

    // Filter by chain if specified
    if (chainFilter) {
        stores = stores.filter(
            (s) => s.chain.toLowerCase() === chainFilter.toLowerCase()
        );
    }

    // Calculate distances and sort
    const withDistances = stores.map((store) => ({
        id: store.id,
        name: store.name,
        chain: store.chain,
        address: store.address,
        distance: calculateDistance(userLat, userLon, store.lat, store.lon),
    }));

    withDistances.sort((a, b) => a.distance - b.distance);

    return withDistances.slice(0, limit);
}

// Get ZIP code from coordinates (reverse geocoding)
// Uses free Nominatim API - respect rate limits!
export async function getZipFromCoordinates(
    lat: number,
    lon: number
): Promise<string | null> {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`,
            {
                headers: {
                    "User-Agent": "Cuenta-App/1.0",
                },
            }
        );

        if (!response.ok) return null;

        const data = await response.json();
        return data.address?.postcode || null;
    } catch (e) {
        console.error("Reverse geocoding failed:", e);
        return null;
    }
}