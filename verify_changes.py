import ast
import os

def safe_print(text):
    try:
        print(text)
    except:
        pass

print("=" * 60)
print("VERIFYING ALL CODE CHANGES")
print("=" * 60)

# 1. Check Python syntax
print("\n--- Python Syntax Validation ---")
for fname in ['app/retriever.py', 'app/main.py', 'app/llm.py']:
    path = os.path.join('darglobal-chatbot', fname)
    try:
        with open(path, encoding='utf-8') as f:
            ast.parse(f.read())
        safe_print(f"  {fname}: SYNTAX OK")
    except SyntaxError as e:
        safe_print(f"  {fname}: SYNTAX ERROR")

# 2. Check retriever changes
print("\n--- Retriever: Arabic Map & Source Filter ---")
with open('darglobal-chatbot/app/retriever.py', encoding='utf-8') as f:
    c = f.read()
safe_print("  Checking ARABIC_MAP keys in retriever.py...")
arabic_present = ['\u062c\u0642\u0644', '\u062c\u0642', '\u0641\u0644\u0627\u0644\u0629', '\u0644\u0628\u0639', '\u0644\u0627\u0631\u064a\u062c', '\u0627\u0631\u0627\u062f\u0644', '\u0606\u062c\u062f', '\u062f\u0631\u062d\u062f', '\u062a\u0648\u0644\u0631 \u0644\u0642\u0639\u0651']
for key in arabic_present:
    try:
        if key in c:
            safe_print(f"    Key present: YES")
        else:
            safe_print(f"    Key present: NO")
    except:
        pass

# Check _source_filter
if 'has_wasalt and not has_dg' in c and 'has_dg and not has_wasalt' in c:
    safe_print("  _source_filter strict source enforcement: YES")
else:
    safe_print("  _source_filter strict source enforcement: NO/MISSING")

# 3. Check main.py format changes
print("\n--- Main: Answer Format ---")
with open('darglobal-chatbot/app/main.py', encoding='utf-8') as f:
    c = f.read()
safe_print("  Checking for new format markers...")
if 'Here are the top' in c:
    safe_print("    'Here are the top' marker: YES (new format)")
else:
    safe_print("    'Here are the top' marker: NO")

if 'City:' in c and '📍' not in c:
    safe_print("    'City:' marker without emoji: YES (good)")
else:
    safe_print("    'City:' marker without emoji: NO/has emoji")

# Check no emoji markers remain
for emoji_keyword in ['📍', '💰', '🔗', '🛏️']:
    try:
        if emoji_keyword in c:
            safe_print(f"    Emoji '{emoji_keyword}' in main.py: YES (PROBLEM)")
        else:
            safe_print(f"    Emoji '{emoji_keyword}' in main.py: NO (good)")
    except:
        pass

# 4. Check llm.py format
print("\n--- LLM: System Prompt ---")
with open('darglobal-chatbot/app/llm.py', encoding='utf-8') as f:
    c = f.read()
safe_print("  Checking LLM system prompt format...")
if 'City: [City], [Country]' in c:
    safe_print("    New format (City: ...) in llm.py: YES")
else:
    safe_print("    New format (City: ...) in llm.py: NO")

# 5. Check HTML filter removal
print("\n--- Frontend: Filter Removal ---")
with open('darglobal-chatbot/app/static/index.html', encoding='utf-8') as f:
    c = f.read()
safe_print("  Checking frontend for filter elements...")
has_filters = '.filters' in c
has_aside = 'FILTERED LISTINGS' in c or 'browseList' in c
has_chips = 'data-group' in c or 'chip' in c
has_state = 'state = { city' in c

safe_print(f"    '.filters' in HTML: {'YES - PROBLEM' if has_filters else 'NO - GOOD'}")
safe_print(f"    'FILTERED LISTINGS' or 'browseList' in HTML: {'YES - PROBLEM' if has_aside else 'NO - GOOD'}")
safe_print(f"    'data-group' or 'chip' in HTML: {'YES - PROBLEM' if has_chips else 'NO - GOOD'}")
safe_print(f"    'state = {{ city' in HTML (old filter): {'YES - PROBLEM' if has_state else 'NO - GOOD'}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)