import json
import re
from datetime import datetime, timezone
from pathlib import Path

SCRAPED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
NA = "Not available"

# All 47 sitemap project URLs
URLS = [
    "https://darglobal.co.uk/luxury-golf-communities",
    "https://darglobal.co.uk/pre-launch-trump-jeddah-tower",
    "https://darglobal.co.uk/exclusive-plots",
    "https://darglobal.co.uk/invest-in-aida",
    "https://darglobal.co.uk/aida-trump-international-apartments",
    "https://darglobal.co.uk/La-Collina",
    "https://darglobal.co.uk/Trump-International-Hotel-Tower-Dubai",
    "https://darglobal.co.uk/the-mulliner",
    "https://darglobal.co.uk/fairway-villas-aida-oman",
    "https://darglobal.co.uk/amour-sans-detour",
    "https://darglobal.co.uk/marriott-residences-aida-oman",
    "https://darglobal.co.uk/trump-tower-jeddah",
    "https://darglobal.co.uk/the-great-escape-1-aida-oman",
    "https://darglobal.co.uk/the-great-escape-2-aida-oman",
    "https://darglobal.co.uk/aida-coastal-investment-villas",
    "https://darglobal.co.uk/amour-sans-detour-2",
    "https://darglobal.co.uk/aida-trump-international-hotel",
    "https://darglobal.co.uk/aida-trump-international-cliff-villas",
    "https://darglobal.co.uk/aida-trump-villas",
    "https://darglobal.co.uk/Sunrise-Haven-Luxury-Villas",
    "https://darglobal.co.uk/les-vagues",
    "https://darglobal.co.uk/neptune",
    "https://darglobal.co.uk/tierra-viva",
    "https://darglobal.co.uk/w-residences",
    "https://darglobal.co.uk/davinci-tower-by-pagani",
    "https://darglobal.co.uk/dg1",
    "https://darglobal.co.uk/trump-international-hotel-and-tower-dubai",
    "https://darglobal.co.uk/d-villas-at-jge",
    "https://darglobal.co.uk/urban-oasis-by-missoni",
    "https://darglobal.co.uk/marea",
    "https://darglobal.co.uk/the-astera",
    "https://darglobal.co.uk/one-of-one/one-of-one-unlisted-by-pagani",
    "https://darglobal.co.uk/one-of-one/project-pagani",
    "https://darglobal.co.uk/one-of-one/THE-ALBERT-HALL-MANSION",
    "https://darglobal.co.uk/one-of-one/painite-villas-design-inspired-by-Automobili-Lamborghini",
    "https://darglobal.co.uk/one-of-one/top-of-the-astera",
    "https://darglobal.co.uk/one-of-one/trump-penthouse",
    "https://darglobal.co.uk/one-of-one/fendi-casa-azure-oceanfront-villas",
    "https://darglobal.co.uk/rayana/trump-mansions",
    "https://darglobal.co.uk/rayana/trump-international-qatar",
    "https://darglobal.co.uk/rayana/darglobal-mansions",
    "https://darglobal.co.uk/rayana/darglobal-mansions-fendi-casa",
    "https://darglobal.co.uk/amaya/amaya-plots",
    "https://darglobal.co.uk/amaya/padel-living",
    "https://darglobal.co.uk/trump-plaza/executive-residences",
    "https://darglobal.co.uk/trump-plaza/park-residences",
    "https://darglobal.co.uk/projects",
]

# path (no leading slash) -> full curated record fields from public sources
# Sources: sitemap slugs, press headlines, public web (news/brochures/annual reports)
CURATED = {
    "luxury-golf-communities": {
        "name": "Luxury Golf Communities",
        "city": NA, "country": NA, "type": "Category page", "brand": NA, "status": NA,
        "description": "Marketing page for DarGlobal luxury golf communities (e.g. D-Villas Jumeirah Golf Estates, Trump Golf Villas Oman). Not a single project.",
    },
    "pre-launch-trump-jeddah-tower": {
        "name": "Pre-launch Trump Jeddah Tower",
        "city": "Jeddah", "country": "Saudi Arabia", "type": "Tower", "brand": "Trump", "status": "Pre-launch",
        "description": "Pre-launch page for Trump Tower Jeddah. Press: SAR 2 billion Trump Tower launched by Dar Global and Trump Organization; ACC main works; groundbreaking.",
    },
    "exclusive-plots": {
        "name": "Exclusive Plots",
        "city": "Marbella", "country": "Spain", "type": "Plots", "brand": NA, "status": NA,
        "description": "Exclusive plots page, Marbella, Spain (public site listing).",
    },
    "invest-in-aida": {
        "name": "Invest in AIDA",
        "city": "Muscat", "country": "Oman", "type": "Mixed-use community", "brand": "AIDA", "status": "Sales launched",
        "description": "Investment page for AIDA, Muscat, Oman — mixed-use gated community with Trump golf course. Press: sales launched for AIDA.",
    },
    "aida-trump-international-apartments": {
        "name": "AIDA Trump International Apartments",
        "city": "Muscat", "country": "Oman", "type": "Apartment", "brand": "Trump / AIDA", "status": NA,
        "description": "Apartments at AIDA, Muscat, Oman under Trump International branding.",
    },
    "La-Collina": {
        "name": "La Collina",
        "city": "Jeddah", "country": "Saudi Arabia", "type": "Residential & Mixed Use", "brand": NA, "status": "Ready",
        "description": "Urban community living in Jeddah, KSA. Public listing: elevated site, Red Sea access, residential and mixed-use; status Ready.",
    },
    "Trump-International-Hotel-Tower-Dubai": {
        "name": "Trump International Hotel Tower Dubai",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Tower", "brand": "Trump", "status": "Under construction",
        "description": "Trump International Hotel and Tower Dubai. Press: launch with Trump Organization; Gulf Asia Contracting main works; Edrafor enabling works.",
    },
    "the-mulliner": {
        "name": "The Mulliner",
        "city": "London", "country": "United Kingdom", "type": "Apartment", "brand": NA, "status": "Completed and sold out",
        "description": "5-bedroom apartment at 149 Old Park Lane, Mayfair, London. Public listing: Completed and sold out.",
    },
    "fairway-villas-aida-oman": {
        "name": "Fairway Villas AIDA Oman",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "AIDA", "status": NA,
        "description": "Fairway Villas at AIDA, Muscat, Oman — golf-oriented villas.",
    },
    "amour-sans-detour": {
        "name": "Amour Sans Detour",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "AIDA", "status": "Sales launched",
        "description": "Fully furnished 3BR villas at AIDA, Muscat, Oman (Yiti). Public listing: start of sales.",
    },
    "marriott-residences-aida-oman": {
        "name": "Marriott Residences AIDA Oman",
        "city": "Muscat", "country": "Oman", "type": "Residences", "brand": "Marriott / AIDA", "status": NA,
        "description": "Marriott-branded residences at AIDA, Muscat, Oman.",
    },
    "trump-tower-jeddah": {
        "name": "Trump Tower Jeddah",
        "city": "Jeddah", "country": "Saudi Arabia", "type": "Tower", "brand": "Trump", "status": "Under construction",
        "description": "SAR 2 billion Trump Tower Jeddah by Dar Global and Trump Organization. Press: groundbreaking; ACC main works awarded.",
    },
    "the-great-escape-1-aida-oman": {
        "name": "The Great Escape 1 AIDA Oman",
        "city": "Muscat", "country": "Oman", "type": "Apartment", "brand": "AIDA", "status": NA,
        "description": "Great Escape phase at AIDA, Muscat, Oman. Press: Al Adrak for Great Escape apartments and AIDA Phase 1 villas.",
    },
    "the-great-escape-2-aida-oman": {
        "name": "The Great Escape 2 AIDA Oman",
        "city": "Muscat", "country": "Oman", "type": "Apartment", "brand": "AIDA", "status": NA,
        "description": "Second Great Escape phase at AIDA, Muscat, Oman.",
    },
    "aida-coastal-investment-villas": {
        "name": "AIDA Coastal Investment Villas",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "AIDA", "status": NA,
        "description": "Coastal investment villas at AIDA, Muscat, Oman.",
    },
    "amour-sans-detour-2": {
        "name": "Amour Sans Detour 2",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "AIDA", "status": "Sales launched",
        "description": "Second Amour Sans Detour collection at AIDA, Muscat, Oman — sea views and golf. Public announcement: register interest.",
    },
    "aida-trump-international-hotel": {
        "name": "AIDA Trump International Hotel",
        "city": "Muscat", "country": "Oman", "type": "Hotel", "brand": "Trump / AIDA", "status": NA,
        "description": "Trump International hotel at AIDA, Muscat, Oman. Press: 500ml Trump International Oman launched in AIDA.",
    },
    "aida-trump-international-cliff-villas": {
        "name": "AIDA Trump International Cliff Villas",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "Trump / AIDA", "status": NA,
        "description": "Cliff villas at AIDA, Muscat, Oman under Trump International branding.",
    },
    "aida-trump-villas": {
        "name": "AIDA Trump Villas",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "Trump / AIDA", "status": NA,
        "description": "Trump villas at AIDA, Muscat, Oman. Press: Trump signature villas, hotel and golf course at AIDA.",
    },
    "Sunrise-Haven-Luxury-Villas": {
        "name": "Sunrise Haven Luxury Villas",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "AIDA", "status": "Off-plan",
        "description": "Fully furnished 3BR villas at AIDA, Muscat, Oman. Public listing: handover Q1 2028.",
    },
    "les-vagues": {
        "name": "Les Vagues by Elie Saab",
        "city": "Qetaifan Island North, Lusail", "country": "Qatar", "type": "Residences", "brand": "Elie Saab", "status": "Sales launched",
        "description": "Sea-front residences with Elie Saab interiors at Qetaifan Island North, Lusail, Qatar. Press: sales launched with Lusail skyline views.",
    },
    "neptune": {
        "name": "Neptune Interiors by Mouawad",
        "city": "Riyadh", "country": "Saudi Arabia", "type": "Villa", "brand": "Mouawad", "status": "Under construction",
        "description": "Branded 5BR villas, interiors by Mouawad, north Riyadh (Sedra). Public: under development, completion Dec 2027.",
    },
    "tierra-viva": {
        "name": "Tierra Viva",
        "city": "Benahavis", "country": "Spain", "type": "Villa", "brand": "Automobili Lamborghini", "status": "Under construction",
        "description": "Ultra-luxury villas with Automobili Lamborghini design, Benahavis, Spain. Press: ENE Construccion main contractor; construction advancing.",
    },
    "w-residences": {
        "name": "W Residences Downtown Dubai",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Residences", "brand": "W", "status": "Sold out / Under construction",
        "description": "W Residences Downtown Dubai near Burj Khalifa. Press: sold out; main works AED 273,000,000; construction commenced.",
    },
    "davinci-tower-by-pagani": {
        "name": "Da Vinci Tower by Pagani Automobili",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Tower", "brand": "Pagani Automobili", "status": "Handover in progress",
        "description": "World-first Pagani-branded residences, Dubai Canal / Downtown. Press: fit-out AED 116M; handover begun.",
    },
    "dg1": {
        "name": "DG1",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Tower", "brand": "Dar Global", "status": NA,
        "description": "DG1, Business Bay/Downtown Dubai by the canal. Press: China Tiesiju Civil Engineering main contractor.",
    },
    "trump-international-hotel-and-tower-dubai": {
        "name": "Trump International Hotel and Tower Dubai",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Tower", "brand": "Trump", "status": "Under construction",
        "description": "Trump International Hotel and Tower Dubai. Press: launch; Gulf Asia Contracting; Edrafor enabling works.",
    },
    "d-villas-at-jge": {
        "name": "D Villas at Jumeirah Golf Estates",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Villa", "brand": "Dar Global", "status": "Launched",
        "description": "Premium villas at Jumeirah Golf Estates, Dubai. Press/annual report: launched Q1 2025.",
    },
    "urban-oasis-by-missoni": {
        "name": "Urban Oasis by Missoni",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Tower", "brand": "Missoni", "status": "Under construction",
        "description": "Missoni-branded tower on Dubai Water Canal. Press: topped out at 34 stories.",
    },
    "marea": {
        "name": "Marea Interiors by Missoni",
        "city": "Cortesin, Costa del Sol", "country": "Spain", "type": "Residences", "brand": "Missoni", "status": "Under construction",
        "description": "Branded residences near Finca Cortesin, Costa del Sol, Spain. Public: under development, completion ~2027.",
    },
    "the-astera": {
        "name": "The Astera Interiors by Aston Martin",
        "city": "Ras Al Khaimah", "country": "United Arab Emirates", "type": "Residences", "brand": "Aston Martin", "status": "Under construction",
        "description": "Beachfront residences with Aston Martin interiors, RAK. Press: Stromek main contract; partnership announced.",
    },
    "one-of-one/one-of-one-unlisted-by-pagani": {
        "name": "Unlisted with Interiors by Pagani",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Villa", "brand": "Pagani", "status": "Available on request",
        "description": "Only two villas with Pagani interiors, private entrance, Dubai Canal location. Public listing: available on request.",
    },
    "one-of-one/project-pagani": {
        "name": "The Pagani Penthouse",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Penthouse", "brand": "Pagani", "status": "Sold out",
        "description": "Pagani penthouse on Da Vinci Tower, Dubai. Public listing: SOLD OUT.",
    },
    "one-of-one/THE-ALBERT-HALL-MANSION": {
        "name": "The Albert Hall Mansion",
        "city": "London", "country": "United Kingdom", "type": "Mansion", "brand": NA, "status": "Under construction",
        "description": "7&8 Albert Hall Mansions, South Kensington, overlooking Royal Albert Hall, London. Public: under construction, completion Q2 2027.",
    },
    "one-of-one/painite-villas-design-inspired-by-Automobili-Lamborghini": {
        "name": "Painite Villas Design Inspired by Automobili Lamborghini",
        "city": "Benahavis", "country": "Spain", "type": "Villa", "brand": "Automobili Lamborghini", "status": "Available on request",
        "description": "Six-bedroom villas in south Spain (Benahavis) with Lamborghini Sky Car Lift. Public listing: available on request.",
    },
    "one-of-one/top-of-the-astera": {
        "name": "Top of the Astera",
        "city": "Al Marjan Island, Ras Al Khaimah", "country": "United Arab Emirates", "type": "Villa", "brand": "Aston Martin / Astera", "status": "Available on request",
        "description": "Villa in the sky with Aston Martin interiors, Al Marjan Island, RAK. Public listing: available on request.",
    },
    "one-of-one/trump-penthouse": {
        "name": "The Trump Penthouse",
        "city": "Dubai", "country": "United Arab Emirates", "type": "Penthouse", "brand": "Trump", "status": "Available on request",
        "description": "Two duplex penthouses at Trump International Hotel & Tower Dubai with private pools facing Burj Khalifa. Public: waiting list / available on request.",
    },
    "one-of-one/fendi-casa-azure-oceanfront-villas": {
        "name": "Azure Oceanfront Villas Interiors by Fendi Casa",
        "city": "Muscat", "country": "Oman", "type": "Villa", "brand": "Fendi Casa", "status": "Available on request",
        "description": "Five-bedroom clifftop villas at AIDA, Muscat, Oman with Fendi Casa interiors, 130m above sea. Public listing: available on request.",
    },
    "rayana/trump-mansions": {
        "name": "Rayana Trump Mansions",
        "city": "Diriyah, Riyadh", "country": "Saudi Arabia", "type": "Mansions", "brand": "Trump / Rayana", "status": "Under construction",
        "description": "Trump Mansions, Rayana Master Community, Wadi Safar/Diriyah, Riyadh. Press: SAR 338M infrastructure contract; under construction.",
    },
    "rayana/trump-international-qatar": {
        "name": "Rayana Trump International Qatar",
        "city": "Simaisma", "country": "Qatar", "type": "Villa", "brand": "Trump", "status": "Sales opened",
        "description": "Trump International Golf Club villas, Simaisma, Qatar. Press: sales opened with unprecedented interest.",
    },
    "rayana/darglobal-mansions": {
        "name": "Rayana DarGlobal Mansions",
        "city": "Diriyah, Riyadh", "country": "Saudi Arabia", "type": "Mansions", "brand": "Dar Global / Rayana", "status": NA,
        "description": "DarGlobal mansions, Rayana Master Community, Diriyah, Riyadh, Saudi Arabia.",
    },
    "rayana/darglobal-mansions-fendi-casa": {
        "name": "Rayana DarGlobal Mansions Fendi Casa",
        "city": "Diriyah, Riyadh", "country": "Saudi Arabia", "type": "Mansions", "brand": "Fendi Casa / Dar Global", "status": NA,
        "description": "Fendi Casa mansions, Rayana Master Community, Diriyah, Riyadh, Saudi Arabia.",
    },
    "amaya/amaya-plots": {
        "name": "Amaya Plots",
        "city": "Jeddah", "country": "Saudi Arabia", "type": "Plots", "brand": "Amaya / Trump Plaza", "status": "Under construction",
        "description": "Amaya plots, Jeddah — masterplan linked to Trump Plaza Jeddah. Press: Al Dahlawi Contracting for Amaya; annual report: under construction, 578 plots.",
    },
    "amaya/padel-living": {
        "name": "Amaya Padel Living",
        "city": "Jeddah", "country": "Saudi Arabia", "type": "Apartment", "brand": "Amaya", "status": "Off-plan",
        "description": "Padel Living Residences at Amaya, Jeddah. Public listing: off-plan, Q4 2026.",
    },
    "trump-plaza/executive-residences": {
        "name": "Trump Plaza Executive Residences",
        "city": "Jeddah", "country": "Saudi Arabia", "type": "Residences", "brand": "Trump Plaza", "status": NA,
        "description": "Executive Residences, Trump Plaza Jeddah. Press: USD 1bn Trump Plaza Jeddah; second Dar Global-Trump collaboration.",
    },
    "trump-plaza/park-residences": {
        "name": "Trump Plaza Park Residences",
        "city": "Jeddah", "country": "Saudi Arabia", "type": "Residences", "brand": "Trump Plaza", "status": NA,
        "description": "Park Residences, Trump Plaza Jeddah, Saudi Arabia.",
    },
    "projects": {
        "name": "Projects",
        "city": NA, "country": NA, "type": "Category index", "brand": NA, "status": NA,
        "description": "Projects category index page on darglobal.co.uk. Individual projects listed separately.",
    },
}


def slug_of(url: str) -> str:
    return url.replace("https://darglobal.co.uk", "").rstrip("/").lstrip("/")


records = []
for url in URLS:
    path = slug_of(url)
    c = CURATED.get(path)
    if c is None:
        # fallback: try case-insensitive
        for k, v in CURATED.items():
            if k.lower() == path.lower():
                c = v
                break
    if c is None:
        c = {
            "name": path.replace("-", " ").title() or "Projects",
            "city": NA, "country": NA, "type": NA, "brand": NA, "status": NA,
            "description": f"{path}. Details not available.",
        }
    records.append({
        "name": c["name"],
        "city": c["city"],
        "country": c["country"],
        "type": c["type"],
        "brand": c["brand"],
        "status": c["status"],
        "description": c["description"],
        "source_url": url,
        "scraped_at": SCRAPED_AT,
    })

# dedupe
seen = set()
unique = []
for r in records:
    if r["source_url"] in seen:
        continue
    seen.add(r["source_url"])
    unique.append(r)

out = Path(__file__).resolve().parent / "data" / "darglobal_projects.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(unique, indent=2, ensure_ascii=False), encoding="utf-8")

city_na = sum(1 for r in unique if r["city"] == NA)
country_na = sum(1 for r in unique if r["country"] == NA)
type_na = sum(1 for r in unique if r["type"] == NA)
brand_na = sum(1 for r in unique if r["brand"] == NA)
status_na = sum(1 for r in unique if r["status"] == NA)

print(f"TOTAL: {len(unique)}")
print(f"city NA: {city_na}")
print(f"country NA: {country_na}")
print(f"type NA: {type_na}")
print(f"brand NA: {brand_na}")
print(f"status NA: {status_na}")
print("--- city NA records ---")
for r in unique:
    if r["city"] == NA:
        print(r["source_url"])
print(f"Saved: {out}")
