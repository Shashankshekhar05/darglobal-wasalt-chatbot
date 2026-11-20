

RULES.md, TESTING.md, VERIFY.md, STEPS.md padho
Ye folder structure banao:
darglobal-chatbot/
├── app/
├── scraper/
├── data/
├── .env
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
requirements.txt banao:
fastapi
uvicorn
requests
beautifulsoup4
playwright
scikit-learn
python-dotenv
.env banao — isme sirf ye likho, key user se lekar:
GROK_API_KEY=xxxx
.gitignore me ye likho:
.env
__pycache__/
wasalt_debug.html
Step DONE hoga jab:

 Folder structure bana hai
 requirements install ho gaya, error nahi hai
 .env me GROK_API_KEY hai, code me nahi hai
 .gitignore me .env hai
 TESTING.md -> Test 0 pass
Agent user ko bolega: "Step 0 done. Aage badhu?"

STEP 1 — DarGlobal Scraping (Data Lao)
User bolega: Step 1 karo

Agent ko karna hai:

scraper/darglobal_scraper.py banao — requests + BeautifulSoup
Pehle https://darglobal.co.uk/robots.txt + sitemap.xml check karo
Pehle SIRF 3 links pe test karo
Phir full scrape karo, 1 sec delay ke saath — time.sleep(1)
data/darglobal_projects.json me save karo
Har record me ye chahiye:

name, city, country, type, brand, status, description, source_url, scraped_at
Step DONE hoga jab:

 File bani: data/darglobal_projects.json
 Count: 40-60 projects
 Khaali file nahi hai
 Har record me source_url hai
 Duplicate URL nahi hai
 TESTING.md -> Test 1 pass
Agent user ko bolega: "Step 1 done. Total __ projects aaye. Aage badhu?"

STEP 2 — Wasalt Scraping (Data Lao)
User bolega: Step 2 karo

Agent ko karna hai:

scraper/wasalt_scraper.py banao — Playwright (requests se nahi hoga, JS site hai)
Pehle https://wasalt.sa/robots.txt check karo
Pehle page ka HTML wasalt_debug.html me save karke dekho
Network Tab / API wala trick bhi try karo — agar API mil jaye toh usse lo
data/wasalt_listings.json me save karo
Har record me ye chahiye:

title, city, price_sar, bedrooms, type, listing_type (Sale/Rent), source_url, scraped_at
Step DONE hoga jab:

 File bani: data/wasalt_listings.json
 Count: 100-200 listings
 Price number me hai: 1200000 (string "SAR ..." me nahi)
 Har record me source_url hai
 TESTING.md -> Test 2 pass
Agent user ko bolega: "Step 2 done. Total __ listings aaye. Aage badhu?"

STEP 3 — Data Cleaning
User bolega: Step 3 karo

Agent ko karna hai:

scraper/clean.py banao
Dono JSON ko saaf karo:
Duplicate source_url hatao
Empty name wale hatao
Price ko number banao
City ko ek format me karo: riyadh -> Riyadh
Clean hui files wapas same data/ me save karo
Step DONE hoga jab:

 Dono files me duplicate nahi hai
 Price sab number me hai
 City format ek jaisa hai
 VERIFY.md -> Step 2 tick hua
Agent user ko bolega: "Step 3 done. Data clean hai. Aage badhu?"

STEP 4 — Retriever (Bina LLM ke Search)
User bolega: Step 4 karo

Agent ko karna hai:

app/retriever.py banao — TF-IDF + JSON (Qdrant mat lagana)
Function: search(query) -> top 5 results dega
Dono JSON files ko ek saath search karega
Step DONE hoga jab:

 search('Riyadh me villa') -> sahi 5 results, sab Riyadh ke hai
 search('Mars pe plot') -> galat data nahi diya, khaali / not found diya
 TESTING.md -> Test 3 pass
 Is step me LLM call = 0 honi chahiye
Agent user ko bolega: "Step 4 done. Retriever sahi kaam kar raha hai. Aage badhu?"

STEP 5 — Backend + Grok LLM (Chatbot ka Dimaag)
User bolega: Step 5 karo

Agent ko karna hai:

app/llm.py banao — SIRF Grok FREE API, portfolio wala setup
Base URL: https://api.x.ai/v1 (portfolio wala hi use karo)
Model: portfolio wala hi model (user se puchh ke likho)
Env: GROK_API_KEY — OpenRouter mat likhna
app/main.py banao — FastAPI, 3 API:
GET /health -> {"status": "ok"}
GET /projects?city=Riyadh
POST /chat -> isme ye order hoga:
1. Question aaya
2. Retriever se top 5 chunks nikale
3. Prompt banaya: "Answer ONLY from CONTEXT. If not in context, say 'Not available in scraped data'"
4. Grok ko bheja
5. Jawab + Sources return kiya
6. Agar Grok fail -> fallback: seedha retrieved chunks return karo
Step DONE hoga jab:

 /health chalta hai
 /chat bina LLM ke fallback deta hai
 /chat Grok se SIRF 2 question pe test hua (zyada call mat karo)
 Jawab me Sources (URLs) hai
 Data me nahi hai toh "Not available" bola, jhooth nahi bola
 TESTING.md -> Test 4 + Test 5 pass
Agent user ko bolega: "Step 5 done. Chatbot kaam kar raha hai. Aage badhu?"

STEP 6 — Frontend (Chat UI)
User bolega: Step 6 karo

Agent ko karna hai:

app/static/index.html banao — ek hi file, React mat lagana
Isme hona chahiye:
Chat window (user type kare, bot jawab de)
Filter buttons: City (Riyadh / Jeddah / Dubai), Buy / Rent, Apartment / Villa
Har jawab ke neeche Sources links
Mobile pe bhi sahi dikhe
Step DONE hoga jab:

 Page khul raha hai
 Chat se jawab aa raha hai
 Filter kaam kar raha hai
 Sources dikh rahe hai
Agent user ko bolega: "Step 6 done. UI ready hai. Aage badhu?"

STEP 7 — Docker (Pack Karo)
User bolega: Step 7 karo

Agent ko karna hai:

Dockerfile banao
docker-compose.yml banao
docker-compose up --build chalake test karo
Step DONE hoga jab:

 Container bina error chala
 http://localhost:8000 khula
 Wahan /chat chala
 TESTING.md -> Test 6 pass
Agent user ko bolega: "Step 7 done. Docker me chal gaya. Aage badhu?"

STEP 8 — Deploy (Live URL)
User bolega: Step 8 karo

Agent ko karna hai:

Code GitHub pe push karne ke liye ready karo — API key push nahi honi chahiye, check karo
Render pe deploy karne ke steps user ko batao:
Render -> New Web Service -> GitHub repo select karo
Env Variable me daalo: GROK_API_KEY
Deploy dabao
Live URL ko test karo
Step DONE hoga jab:

 Render URL khul raha hai: ____
 Phone se bhi khul raha hai
 Live URL pe 1 baar /chat test hua
 GitHub me API key nahi gayi
 TESTING.md -> Test 7 pass
Agent user ko bolega: "Step 8 done. Live URL: ____"

STEP 9 — Final Check (DONE bolne se pehle)
User bolega: Step 9 karo / Final check karo

Agent ko karna hai:
Ye 3 question live URL pe khud test karo:

"DarGlobal ke Dubai projects dikhao" -> sahi jawab + source?
"Wasalt pe Riyadh me rent pe apartment" -> sahi jawab + source?
"Jo data me nahi hai" -> bot ne jhooth toh nahi bola?
Step DONE hoga jab:

 Teeno test pass
 VERIFY.md full tick hai
 README.md me Live URL + kaise chalaye likha hai
Agent user ko bolega: "Sab done. Live URL ready hai. Ab tu email khud bhej de."

Agent ko Prompt kaise dena hai — Copy Paste karo
Pehli baar:

RULES.md, TESTING.md, VERIFY.md, STEPS.md padh.
Phir Step 0 karo. Step khatam hone pe mujhe bata, main agla step bolunga.
Uske baad har baar sirf ye likhna hai:

Step 1 karo
Step 2 karo
Step 3 karo
...
Bas. Baar-baar lamba prompt nahi dena hai.

