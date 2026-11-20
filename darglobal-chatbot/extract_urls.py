import json
import re
from pathlib import Path

sitemap = Path(__file__).resolve().parent.parent / "sitemap_tmp.xml"
text = sitemap.read_text(encoding="utf-8")
urls = re.findall(r"<loc>(.*?)</loc>", text)

skip_substrings = ("/blog", "/press", "/insights", "/projects/", "/partners")
static_paths = {
    "",
    "/",
    "/about",
    "/aida-360",
    "/aston-martin-media",
    "/become-a-broker",
    "/become-an-agent",
    "/careers",
    "/commercial",
    "/development-management",
    "/dg-circle",
    "/exclusive-membership",
    "/faq",
    "/get-in-touch",
    "/hospitality",
    "/insignia",
    "/internship-application",
    "/internships",
    "/investor",
    "/landing-page",
    "/bookYourUnit",
    "/campaigns",
    "/win-a-trip-to-dubai",
    "/blog",
    "/insights",
    "/landingpage/newStaticLandingPageHtml",
    "/live-all-in",
    "/new-home-page",
    "/partners",
    "/pay-online",
    "/pay-online/status",
    "/press",
    "/privacy-policy",
    "/sohar-islamic",
    "/success",
    "/terms-conditions",
    "/terms-of-uses",
    "/thank-you",
    "/tokenization",
    "/why-invest",
    "/DarGlobal-exclusive-Off-Plan-Investment-Catalogue",
    "/DarGlobal-Insignia-Card",
    "/Invest-crypto",
    "/broker-contest-terms-conditions",
    "/one-of-one",
    "/landing-page/aida",
}

seen = set()
projects = []
for u in urls:
    path = u.replace("https://darglobal.co.uk", "").rstrip("/")
    if any(s in u for s in skip_substrings):
        continue
    if path in static_paths:
        continue
    if u in seen:
        continue
    seen.add(u)
    projects.append(u)

out = Path(__file__).resolve().parent / "project_urls.json"
out.write_text(json.dumps(projects, indent=2), encoding="utf-8")
print("PROJECT URLS:", len(projects))
for p in projects:
    print(p)
