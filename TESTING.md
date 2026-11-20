TESTING.md — DarGlobal + Wasalt Chatbot
Har step ke baad ye test chalana hai. Bina test pass kiye aage mat badhna.
LLM wale test sabse last me, sirf 2-3 baar.
Test 0: Setup Test (LLM call = 0)
 python --version -> 3.11 aana chahiye
 pip install -r requirements.txt -> error nahi aana chahiye
 playwright install chromium -> ho gaya?
 .env file hai? GROK_API_KEY usme hai?
 .gitignore me .env likha hai?
Test 1: DarGlobal Scraper Test (LLM call = 0)
Command:
python scraper/darglobal_scraper.py
Pass hoga jab:

 Pehle 3 links pe naam / city / description aaya
 data/darglobal_projects.json bana
 Count 40-60 ke beech hai
 Har record me source_url hai
 Duplicate URL nahi hai
Test 2: Wasalt Scraper Test (LLM call = 0)
Command:
python scraper/wasalt_scraper.py
Pass hoga jab:

 wasalt_debug.html bana aur size > 10KB hai
 Property links mile (kam se kam 20)
 data/wasalt_listings.json bana
 Count 100-200 ke beech hai
 Price number me hai, string "SAR ..." me nahi
Test 3: Retriever Test (LLM call = 0) — SABSE IMPORTANT
Command:
python -c "from app.retriever import search; print(search('Riyadh me villa'))"
Pass hoga jab:

 Top 5 results aaye
 Sab me city = Riyadh hai
 Khaali list nahi aayi
 Galat question pe: search('Mars pe plot') -> khaali / "not found" aaye, galat data na aaye
Test 4: Backend Test (LLM call = 0, pehle fallback mode)
Command:
uvicorn app.main:app --reload
Browser: http://localhost:8000/health
Pass hoga jab:

 /health -> {"status": "ok"} aaye
 /projects?city=Riyadh -> list aaye
 /chat bina LLM ke fallback jawab de (retrieved chunks)
Test 5: LLM Test (LLM call = SIRF 2-3 BAAR) — Grok free limit yahan kharch hogi
Command: Frontend se ya curl se 2 question puchho

"Trump Tower Jeddah kya hai?"
"Riyadh me 3 bedroom apartment dikhao"
Pass hoga jab:
 Jawab scraped data se hai, bahar ki baat nahi boli
 Sources me sahi URL hai
 Data me nahi hai toh "Not available in scraped data" bola, jhooth nahi bola
 Server logs me sirf 2-3 LLM calls dikhe, 20 nahi
Test 6: Docker Test (LLM call = 0)
Command:
docker-compose up --build
Pass hoga jab:

 Container bina error ke chala
 http://localhost:8000 khula
 /chat wahan bhi chala
Test 7: Deploy Test (LLM call = 1)
 Render URL khul raha hai (phone se bhi check karo)
 Render logs me error nahi hai
 1 baar live URL pe /chat test karo
 URL ko email me bhejne se pehle dobara khol ke dekho