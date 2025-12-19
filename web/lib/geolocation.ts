export interface Coordinates {
    latitude: number;
    longitude: number;
}

export interface StoreLocation {
    id: string;
    name: string;
    chain: string;
    address: string;
    lat: number;
    lon: number;
}

export interface NearbyStore extends StoreLocation {
    distance: number;
}

export const HOUSTON_STORES: StoreLocation[] = [
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
    { id: "aldi-louetta-road",name: "Aldi - Louetta Road", chain: "Aldi", lat: 30.0020036, lon: -95.5599323, address: "9870 Louetta Road, Houston, TX 77070"},
    
    { id: "target-1", name: "Target Westchase", chain: "Target", address: "10801 Westheimer Road, Houston, TX 77042", lat: 29.73503860163631, lon: -95.56780919335166 },
    { id: "target-2", name: "Target Northwest Fwy", chain: "Target", address: "13250 Northwest Freeway, Houston, TX 77040,", lat: 29.84921911307792, lon: -95.50270633625009 },
    { id: "target-3", name: "Target Katy", chain: "Target", address: "19955 Katy Fwy, Houston, TX 77094", lat: 29.7821551, lon: -95.7160541 },
    { id: "target-4", name: "Target Galleria", chain: "Target", address: "4323 San Felipe Street, Houston, TX 77027", lat: 29.7446495, lon: -95.4531133 },
    { id: "target-5", name: "Target CopperField", chain: "Target", address: "6955 North Highway 6, Houston, TX 77084", lat: 29.877406, lon: -95.6474813 },
    { id: "target-6", name: "Target Tomball Pkwy", chain: "Target", address: "21515 Tomball Parkway, Houston, TX 77070", lat: 29.9994221, lon: -95.5842856 },
    { id: "target-7", name: "Target South Main", chain: "Target", address: "8500 Main St, Houston, TX 77025", lat: 29.6926322, lon: -95.4192764 },
    { id: "target-8", name: "Target Memorial", chain: "Target", address: "984 Gessner Rd, Houston, TX 77024", lat: 29.78300920697949, lon: -95.54190085801496 },
    { id: "target-9", name: "Target Meyerland Plaza", chain: "Target", address: "Meyerland Plaza, Target, 300, Houston, TX 77096", lat: 29.6871888, lon: -95.4621266 },
    { id: "target-10", name: "Target Willowbrook", chain: "Target", address: "6801 Cypress Creek Parkway, Houston, TX 77069", lat: 29.967738737552597, lon: -95.53054208713093 },
    { id: "target-11", name: "Target Central", chain: "Target", address: "2580 Shearn Street, Houston, TX 77007", lat: 29.7741659, lon: -95.3854351 },
    { id: "target-12", name: "Target Westheimer", chain: "Target", address: "8605 Westheimer Road, Houston, TX 77063", lat: 29.7345928, lon: -95.5177455 },
    { id: "target-13", name: "Target Steeplechase", chain: "Target", address: "12701 North Eldridge Parkway, Houston, TX 77082", lat: 29.919249039012165, lon: -95.60497702609074 },
    { id: "target-14", name: "Target Houston Eldridge Pkwy", chain: "Target", address: "2700 Eldridge Parkway, Houston, TX 77082", lat: 29.7325745, lon: -95.6273463 },
    { id: "target-15", name: "Target Houston South", chain: "Target", address: "8503 South Sam Houston Parkway East, Houston, TX 77075", lat: 29.6026242, lon: -95.264021 },
    { id: "target-16", name: "Target Montrose", chain: "Target", address: "2075 Westheimer Road, Houston, TX 77098,", lat: 29.7412274, lon: -95.4094771 },
    { id: "target-17", name: "Target Humble", chain: "Target", address: "20777 Eastex Freeway, Humble, TX 77338", lat: 30.0192483, lon: -95.2687528 },
    { id: "target-18", name: "Target Atascocita", chain: "Target", address: "6931 Kingwood Glen Drive, Humble, TX 77346", lat: 30.000910702762337, lon: -95.1725171534204 },
    { id: "target-19", name: "Target Houston North Central", chain: "Target", address: "19511 North Freeway, Spring, TX 77388", lat: 30.0501898, lon: -95.4348629 },
    { id: "target-20", name: "Target Spring Grand Parkway North", chain: "Target", address: "6635 North Grand Parkway West, Spring, TX 77389", lat: 30.0868916, lon: -95.5205025 },
    { id: "target-21", name: "Target Katy Cinco Ranch", chain: "Target", address: "Commercial Center Boulevard, Cinco Ranch, TX 25826,", lat: 29.73575665821079, lon: -95.77578752505156 },
    { id: "target-22", name: "Target Katy Elyson", chain: "Target", address: "22165 Freeman Road, Katy, TX 77493", lat: 29.872731865816558, lon: -95.75947887682412 },
    { id: "target-23", name: "Target Sugar Land", chain: "Target", address: "Southwest Freeway Frontage Road, Sugar Land, TX 77479", lat: 29.59620141334226, lon: -95.62732859940195 }
];

/**
 *  Get the user's current position using browsers geolocation API
 */
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

/**
 * Calculates the dstance between two points using the haversine formula, thank you basic trig and geogebra
 * returns distanffce in american units
 */
export function calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number {
    const R = 3959;

    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = 
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) *
            Math.cos(toRad(lat2)) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function toRad(deg: number): number {
    return deg * (Math.PI / 180);
}

/*Find nearest store toooo the user's loc optionally filtered by chain seen in frontend
*/
export function findNearestStores(
    userLat: number,
    userLon: number,
    limit: number = 5,
    chainFilter?: string
): NearbyStore [] {
    let stores = HOUSTON_STORES;

    if (chainFilter) {
        stores = stores.filter(
            (store) => store.chain.toLowerCase() === chainFilter.toLowerCase());
    }

    const withDistances: NearbyStore[] = stores.map((store) => ({
        ...store,
        distance: calculateDistance(userLat, userLon, store.lat, store.lon),
    }));
    
    // Sort by distance and take the top
    return withDistances
        .sort((a, b) => a.distance - b.distance)
        .slice(0, limit);
    }

/*
This gets the zip using reverse geocoding thanks to this api called nominatim. I need to credit them as well. 
Should just be a fallback, but I like to be thorough
*/
export async function getZipFromCoordinates(
    lat: number,
    lon: number
): Promise<string | null> {
    try {
        const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`,
    {
        headers: {
            "User-Agent": "Cuenta-App/1.0",
        },
    }
);
    
    if (!response.ok) return null;
    
    const data = await response.json();
    return data.address?.postcode || null;
} catch {
    return null;
    }
}

export function getAvailableChains(): string[] {
    const chains = new Set(HOUSTON_STORES.map((store) => store.chain));
    return Array.from(chains).sort();
}

export function getStoreCountByChain(): Record<string, number> {
    const counts: Record<string, number> = {};
    HOUSTON_STORES.forEach((store) => {
        counts[store.chain] = (counts[store.chain] || 0) + 1;
    });
    return counts;
}