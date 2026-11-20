DarGlobal + Wasalt Chatbot
Agent har step ke baad is file ko tick karke batayega.
Ek bhi box unticked hai toh "kaam ho gaya" mat bolna.
VERIFY — Step 1: Scraping
 data/darglobal_projects.json hai? Count: ____
 data/wasalt_listings.json hai? Count: ____
 Dono file khaali nahi hai?
 Har record me source_url + scraped_at hai?
 robots.txt check kiya? Kya Disallow tha? ____
 1 sec delay lagaya tha?
USER SE PUCHHO: "Data sahi lag raha hai? Aage badhu?"
VERIFY — Step 2: Cleaning
 Duplicate hataye?
 Empty name wale hataye?
 Price number me convert hua?
 City format ek jaisa hai?
 TESTING.md Test 1 + Test 2 pass?
VERIFY — Step 3: Retriever
 search('Riyadh me villa') -> sahi 5 results?
 search('Mars pe plot') -> galat data nahi diya?
 TESTING.md Test 3 pass?
VERIFY — Step 4: Backend + LLM (Grok FREE API — xAI)
 Model ka naam kya use kiya? ____ (portfolio wala model)
 Base URL: https://api.x.ai/v1 ?
 API Key .env me hai (GROK_API_KEY), code me nahi?
 .gitignore me .env hai?
 Prompt me "Answer ONLY from CONTEXT" likha hai?
 Fallback kaam karta hai? (LLM band karke test kiya?)
 Grok API me kitni calls hui? ____ (2-3 se zyada nahi honi chahiye test me)
 TESTING.md Test 4 + Test 5 pass?
VERIFY — Step 5: Frontend
 Chat window khul raha hai?
 Filter buttons kaam kar rahe hai?
 Har jawab ke saath Sources dikh rahe hai?
 Mobile pe bhi sahi dikh raha hai?
VERIFY — Step 6: Docker
 Dockerfile hai?
 docker-compose up --build bina error chala?
 localhost:8000 pe /chat chala?
 TESTING.md Test 6 pass?
VERIFY — Step 7: Deploy (Agent email nahi bhejega — RULES §9)
 Render URL: ____
 Live URL phone se khola?
 Render Env Variable me GROK_API_KEY dala? (GitHub me nahi)
 GitHub repo public/private? ____ — API key toh nahi push hui?
 TESTING.md Test 7 pass?
FINAL CHECK — HR kya test karega?
HR ye 3 question puchhega, inka jawab live URL pe check kar:

"DarGlobal ke Dubai projects dikhao" -> sahi jawab + source?
"Wasalt pe Riyadh me rent pe apartment" -> sahi jawab + source?
"Jo data me nahi hai" -> bot ne jhooth toh nahi bola?
Agar teeno sahi hai, tabhi DONE bolo.