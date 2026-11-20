RULES.md — DarGlobal + Wasalt AI Chatbot
Agent ko ye file pehle padhni hai. Iske bahar kaam nahi karna.
1. Project Goal
Scrape: DarGlobal (darglobal.co.uk) + Wasalt (wasalt.sa) — sirf PUBLIC data
Chatbot: User ke question ka jawab SIRF scraped data se dega
LLM: SIRF Grok API use karna hai — OpenRouter mat use karna
Deploy: Docker me pack karke Render par live URL dena hai
2. Tech Stack — Isko Change Mat Karna
Language: Python 3.11
Backend: FastAPI
Scraper DarGlobal: requests + BeautifulSoup
Scraper Wasalt: Playwright (JS site hai, requests se nahi hoga)
Retriever: TF-IDF + JSON (Qdrant / Vector DB mat lagana)
LLM: SIRF Grok API (xAI) — FREE, 
Base URL: https://api.x.ai/v1


Frontend: Single index.html (React mat lagana)
Deploy: Docker + Render (Free tier)
3. Grok API Rules — IMPORTANT
Grok ka FREE API use karna hai — wahi key / wahi setup jo user apne portfolio me pichle 6 mahine se use kar raha hai
Paid / credit wala setup mat banana. ₹200 / credit add karne ko mat bolna
Portfolio wala hi Base URL + Model + Key use karna hai, naya paid plan mat banana
Bina wajah LLM call mat karna. Har test me LLM call mat karo
Pehle retriever test karo (LLM ke bina), phir 2-3 baar hi LLM test karo
API Key kabhi code / GitHub me mat daalna. Sirf .env me + Render Env Variable me
.env ko .gitignore me daalna mandatory hai
Env variable ka naam: GROK_API_KEY (OPENROUTER_API_KEY mat likhna)
4. Scraping Rules
Sirf public pages. Login / paywall / private API mat todna
robots.txt check karo. Disallow wala page mat scrape karo
Har request ke beech 1 sec delay — time.sleep(1)
User-Agent me likho: DarGlobal-Assignment-Research
Ek baar me 1000 request mat maro. Pehle 3 links pe test, phir full
Target: DarGlobal 40-60 projects, Wasalt 100-200 listings
5. Data Rules
Dono JSON ka schema SAME hoga
Har record me ye hone chahiye: name/title, city, type, source_url, scraped_at
Duplicate source_url hatao
Empty name wale record hatao
Price ko number banao: "SAR 1,200,000" -> 1200000
City ko capital format me: riyadh -> Riyadh
6. Chatbot Rules — Hallucination Ban
Prompt me hamesha likho: "Answer ONLY from CONTEXT. If not in context, say 'Not available in scraped data'"
Har jawab ke saath Sources (URLs) return karo
Agar Grok fail ho / free limit khatam ho -> fallback: seedha retrieved chunks return karo, bot khaali na bole
User ka personal data (phone/email) kabhi log mat karo, sirf lead form me alag se save karo
7. Code Rules
File structure jo Architecture me di hai, wahi rakho
Har file me chhota-chhota function likho, ek file me sab mat bharo
Har nayi file banane se pehle VERIFY.md check karo
Code English me, comments English me
Koi bhi bada kaam karne se pehle user se puchho, khud se install / deploy mat karo
8. Agentic Coding Rules
Agent ek step me ek kaam karega: Scrape -> Clean -> Retriever -> Backend -> Frontend -> Docker -> Deploy
Step khatam hone pe TESTING.md wala test chalayega, phir VERIFY.md check karega
Agar test fail ho, toh agle step pe mat jao
Har step ke baad user ko batayega: kya hua, kitna data aaya, kya fail hua
9. Is File Me Kya NAHI Hai
Isme email bhejne ka kaam nahi hai. Agent ka kaam sirf project banana hai — scrape, chatbot, Docker, deploy.
Email user khud bhejega.