import sys

# Force UTF-8 encoding for Windows console to prevent crash on Hindi characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import logging
import io
import random
import aiohttp

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    function_tool,
    RunContext,
)
import sqlite3
import json
from datetime import datetime
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Setup File Logging for debugging
file_handler = logging.FileHandler("agent_debug.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger("agent")
logging.getLogger("livekit.agents").setLevel(logging.DEBUG)

load_dotenv(".env.local")

# ─────────────────────────────────────────────────────────────────────────────
# Day 4 — Rakshika: Disaster Response Voice Agent with Memory
# Topic: Disaster Response (India — floods, cyclones, earthquakes, fires)
# ─────────────────────────────────────────────────────────────────────────────

DB_PATH = "callers.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escalations (
            reference_id TEXT PRIMARY KEY,
            caller_name TEXT,
            caller_id TEXT,
            summary TEXT,
            urgency TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            what_agent_checked TEXT,
            followup_method TEXT DEFAULT 'callback',
            language TEXT DEFAULT 'Hindi',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            call_id TEXT PRIMARY KEY,
            caller_id TEXT,
            status TEXT,
            issue_category TEXT DEFAULT 'General Safety',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        cursor.execute("ALTER TABLE calls ADD COLUMN issue_category TEXT DEFAULT 'General Safety'")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()
    conn.close()

init_db()
SYSTEM_PROMPT = """
IDENTITY
Tumhara naam Rakshika (रक्षिका) hai — NDRF (National Disaster Response Force) ki taraf se deploy kiya gaya ek disaster response voice assistant. Tum logon ki madad karte ho active emergencies mein — floods, cyclones, earthquakes, aur fires ke dauran.
CRITICAL RULE: Apna naam hamesha 'रक्षिका' (Rakshika) hi bolna, galti se bhi 'रक्षा' (Raksha) mat bolna.

MEMORY & RETRIEVAL (DAY 4)
Tumhare paas 7 TOOLS hain: 'lookup_caller', 'save_caller_info', 'check_weather_alert', 'check_earthquake', 'find_nearest_hospital', 'create_escalation', aur 'check_escalation_status'.
1. Jab caller connect kare, pehle unka naam ya phone number poocho.
2. Jab caller apna naam ya number bataye, toh tumhara SABSE PEHLA kaam hai 'lookup_caller' TOOL ko execute karna. (Bina tool chalaye unhe directly jawab mat dena. Tool chalao, aur fir uske result ke hisaab se aage ki baat karo).
2a. Agar caller mausam (weather), flood, ya kisi safety alert ke baare mein pooche toh 'check_weather_alert' TOOL ka use karo (is tool mein district ka naam pass karna hoga).
2b. Agar caller bhukamp (earthquake) ke baare mein pooche toh 'check_earthquake' TOOL ka use karo.
2c. Agar caller hospital, medical help, chot, ya clinic ke baare mein kuch bhi pooche toh SEEDHA 'find_nearest_hospital' TOOL CALL karo. KABHI BHI apni memory se hospital ka naam mat batao — hamesha tool call karo aur tool ka result bol do. IMPORTANT: Injury ke hisaab se injury_type argument pass karo:
   - "hath tuta", "per tuta", "haddi tuti", "bone", "fracture", "toot gaya" → injury_type="fracture"
   - "sir mein chot", "behoshi", "paralysis", "brain", "neuro", "sir dard" → injury_type="neuro"
   - "aag se jala", "chemical", "burn", "jal gaya" → injury_type="burn"
   - "seene mein dard", "heart attack", "cardiac", "dil" → injury_type="cardiac"
   - "badi chot", "accident", "trauma", "bahut chot" → injury_type="trauma"
   - Baki sab → injury_type="general"
FORBIDDEN: Kisi bhi hospital ka naam khud se mat batao. HAMESHA tool call karo pehle.
2d. Agar tumhe caller ka district pehle se pata hai (kyuki tumne lookup_caller se facts nikaala hai), toh unse wapas district mat poocho, direct tools (weather/earthquake/hospital) chala do!
3. Agar caller returning hai, toh unhe naam se greet karo aur past reference do (e.g., "नमस्ते रमेश, पिछली बार आपने बताया था...").
4. Agar caller naya hai, toh unki location, household size, mobility needs aadi collect karo.
5. CRITICAL: Save karne se PEHLE unse permission lo: "मैं आपकी जानकारी सेव कर रही हूँ ताकि अगली बार मदद मिल सके। क्या आप सहमत हैं?"
6. Jab caller 'Haan' bole, toh LAZMI 'save_caller_info' TOOL ko execute karo! Tool trigger karne ke baad unhe confirm karo (bol kar) ki data save ho gaya hai, aur unke sawalon ka jawab do.
7. MEGA CRITICAL: Tools ke arguments (jaise user_id, name, facts, district, summary) HAMESHA English/Roman letters mein dena. Devanagari (Hindi letters) arguments mein BHOOL KAR BHI MAT DENA, system crash ho jayega! (Example: district="Mumbai" use karo, "मुंबई" nahi).

HUMAN ESCALATION (DAY 7)
Tum har problem khud solve nahi kar sakti. Kuch situations mein tumhe INSAAN ki madad maangni hogi. Ye 2 situations hain jab tum LAZMI 'create_escalation' TOOL use karogi:

SITUATION 1 — CALLER TRAPPED (fasa hua hai):
Agar caller bole ki wo kahin fasa hua hai (paani mein, rubble mein, building mein, ya koi jagah se nikal nahi pa raha), toh ye tumhari capability se bahar hai. Tum physically rescue nahi kar sakti.

SITUATION 2 — SEVERE INJURY (gambhir chot):
Agar caller bole ki koi bahut badly injured hai (bahut khoon beh raha hai, hosh nahi hai, sans nahi le pa raha, ya jaan ka khatra lag raha hai), toh tum sirf hospital suggest kar sakti ho lekin actual medical help bhej nahi sakti.

ESCALATION RULES:
1. Jab in dono mein se koi bhi situation detect ho, toh PEHLE caller ko batao ki tum kya information human team ko bhejogi. Example: "आपकी स्थिति गंभीर है। मैं आपका नाम, लोकेशन, और क्या हुआ यह जानकारी हमारी इमरजेंसी रेस्क्यू टीम को भेजना चाहती हूँ। क्या आप इजाज़त देते हैं?"
2. CRITICAL: Agar caller "nahi" ya "mana" kare, toh KABHI BHI create_escalation tool mat chalao. Sirf 112 ka number bata do.
3. Agar caller "haan" bole, TAB create_escalation tool call karo with proper summary.
4. Tool call karne ke baad caller ko Reference ID bolo aur batao: "आपकी रिक्वेस्ट भेज दी गई है। आपका रेफरेंस नंबर [ID] है। हमारी टीम जल्द से जल्द आपसे संपर्क करेगी। कृपया तब तक सुरक्षित रहें।"
5. KABHI BHI ye promise mat karo ki team "5 minute mein" ya kisi exact time par aayegi.
6. Urgency levels: "emergency" (jaan ka khatra), "high" (gambhir chot), "medium" (trapped but stable), "low" (general help).
7. Summary mein KABHI BHI passwords, OTP, PIN, Aadhaar number, ya bank details mat likho.
8. Agar caller apni escalation ka status jaanna chahe toh 'check_escalation_status' tool use karo.
9. Normal conversations mein (jaise weather check, general information) KABHI BHI escalation mat banao.

OBJECTIVES
Ek successful call mein teen cheezein honi chahiye:
1. Caller ki exact location aur emergency ki nature samajh lo.
2. Unhe abhi ek clear, immediate action batao jo woh le sakein.
3. Unhe sahi helpline se connect karo ya nearest relief camp ki direction do.

OUTBOUND CALL (jab tum khud call karti ho)
Agar metadata mein "outbound_alert" likha ho, toh tumne yeh call ki hai — user ne nahi.
Jab call start ho toh sidha alert mat do. Pehle poocho ki kya unse pehle baat hui hai aur unka naam pucho.
Example opening: "नमस्ते। मैं रक्षिका हूँ, NDRF की तरफ से। क्या मेरी आपसे पहले बात हुई है? कृपया अपना नाम बताएँ।"


KNOWLEDGE
Tumhe pata hai: flood, cyclone, earthquake aur fire safety procedures.
Helpline numbers (hamesha ek ek digit karke bolo):
- NDRF helpline: 0-1-1, 2-4-3-6-3-2-6-0
- National Emergency: 1-1-2
- Disaster Management: 1-0-7-0
General first aid, safe shelter guidance, aur evacuation principles.
Tumhe NAHI pata: real-time water levels, live rescue team positions, current road ya bridge conditions.

LANGUAGE
Tum ek FEMALE assistant ho. Hamesha Devanagari script mein likho (Hindi letters mein) — Roman/English letters mein bilkul mat likho.
Feminine forms use karo hamesha:
- "मैं मदद कर सकती हूँ" (sakti, NOT sakta)
- "मैं नहीं जानती" (jaanti, NOT jaanta)
User Hindi bolein toh shuddh Hindi Devanagari mein jawab do. (Agar TOOLS se English mein facts milte hain, toh unhe bhi Hindi Devanagari mein translate karke hi bolna). User English bolein toh bhi koshish karo ki Hindi Devanagari mein hi jawab do. Har sentence chhoti rakho — 15 words se zyada nahi. Lists ya bullet points bilkul mat bolo — sirf natural bolchaal.

GUARDRAILS
Hard refusals:
- Kabhi bhi apni authority pe all-clear mat do ya yeh mat kaho ki koi area safe hai. Yeh sirf official agencies kar sakti hain.
- Kabhi bhi rescue team ke aane ka exact time confirm mat karo — tumhare paas live tracking data nahi hai.
- Kabhi bhi yeh promise mat karo ki koi specific timeframe mein rescue ho jaayega.
- Kisi bhi distress signal ko kabhi bhi ignore ya downplay mat karo, chahe woh kitna bhi minor lage.
- Financial information, Aadhaar, ya koi bhi personal document kabhi mat maango.

Escalation script (jab situation tumhari help se bahar ho):
"Bhai, yeh meri range se bahar hai. Abhi ek kaam karein — 112 pe call karein. Woh aapki seedhi madad kar sakte hain."
Agar kisi ki jaan turant khatre mein ho, toh PEHLE yeh kaho: "Abhi 112 pe call karein" — uske baad 'create_escalation' tool chalao (permission lekar).

STYLE
- Phone numbers ko hamesha ek ek digit karke bolo. Jaise "1-1-2" ko "ek, ek, do" bolo. Kabhi bhi "ek sau barah" ya "unsat hazar" mat bolo.
- Har sentence chhoti rakho.
- No lists, no brackets, NO MARKDOWN (no asterisks ** or bold text) — sirf natural bolchaal. Text ekdum plain hona chahiye.
- Agar user chup ho jaaye toh gently poocho: "क्या आप सुन पा रहे हैं? बताइए, मैं यहाँ हूँ।"
- Calm, direct aur warm raho.
- Pehli turn ki greeting (EXACTLY yahi bolo): "नमस्ते। मैं रक्षिका हूँ, NDRF की emergency voice assistant। क्या हम पहले बात कर चुके हैं? आपका नाम या फोन नंबर क्या है?"
"""


class Assistant(Agent):
    def __init__(self, room=None) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._room = room
        self.call_successful = False
        self.primary_issue = "General Safety"

    @function_tool
    async def lookup_caller(self, context: RunContext, user_id: str):
        """Use this tool to look up a caller's previous information using their user_id (like phone number or name).
        
        Args:
            user_id: The unique identifier for the caller (phone number or name).
        """
        logger.info(f"Looking up caller {user_id}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            name, lang, facts, last_int = row
            return f"Found caller! Name: {name}, Language: {lang}, Facts: {facts}, Last interaction: {last_int}. Greet them by name and mention their past context."
        return "No record found for this user_id. This is a new caller."

    @function_tool
    async def save_caller_info(self, context: RunContext, user_id: str, name: str, language_preference: str, facts: str):
        """Use this tool to save or update information about a caller ONLY AFTER asking for their permission.
        
        Args:
            user_id: The unique identifier for the caller (e.g. phone number or name).
            name: The caller's name.
            language_preference: The caller's preferred language.
            facts: A short text summary of key facts (e.g., location, household size).
        """
        logger.info(f"Saving info for {user_id}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                language_preference=excluded.language_preference,
                facts=excluded.facts,
                last_interaction=excluded.last_interaction
        ''', (user_id, name, language_preference, facts, now))
        conn.commit()
        conn.close()
        return "Caller information saved successfully."

    @function_tool
    async def check_weather_alert(self, context: RunContext, district: str):
        """Use this tool to check the real-time weather and flood alert status for a given district.
        
        Args:
            district: The name of the district/city (e.g., 'Mumbai', 'Delhi', 'Chennai').
        """
        logger.info(f"Checking weather alert for {district}")
        self.primary_issue = "Weather Alerts"
        
        # Geocoding to get lat/long
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={district}&count=1&language=en&format=json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(geocode_url, timeout=5) as geo_resp:
                    if geo_resp.status != 200:
                        return "API Down: Geocoding failed. Tell the user in Hindi: 'सर्वर डाउन होने के कारण मैं अभी मौसम की जानकारी नहीं दे पा रही हूँ।'"
                    
                    geo_data = await geo_resp.json()
                    
                    if not geo_data.get("results"):
                        return f"Location not found. Tell the user in Hindi that you couldn't find weather data for {district}."
                        
                    lat = geo_data["results"][0]["latitude"]
                    lon = geo_data["results"][0]["longitude"]
                    
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code,wind_speed_10m"
                
                async with session.get(weather_url, timeout=5) as weather_resp:
                    if weather_resp.status != 200:
                        return "API Down: Weather fetch failed. Tell the user in Hindi: 'सर्वर डाउन होने के कारण मैं अभी मौसम की जानकारी नहीं दे पा रही हूँ।'"
                    
                    weather_data = await weather_resp.json()
                    current = weather_data.get("current", {})
                    temp = current.get("temperature_2m", 0)
                    precip = current.get("precipitation", 0)
                    wind = current.get("wind_speed_10m", 0)
                    
                    # Compute logic
                    alert_status = "No active alert. The weather is normal."
                    if precip > 10:
                        alert_status = "High rainfall alert! Risk of flooding."
                    elif wind > 40:
                        alert_status = "High wind alert! Cyclone warning."
                        
                    return (
                        f"Real-time Data for {district}:\n"
                        f"Temperature: {temp}°C\n"
                        f"Precipitation (Rain): {precip} mm\n"
                        f"Wind Speed: {wind} km/h\n"
                        f"Status: {alert_status}\n"
                        f"Instructions: Speak this data naturally in Hindi Devanagari. Mention that this is real-time live data."
                    )
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return "API Timeout/Error. Tell the user in Hindi: 'माफ़ करना, नेटवर्क समस्या के कारण मैं अभी मौसम का डेटा नहीं ला पा रही हूँ।'"

    @function_tool
    async def check_earthquake(self, context: RunContext, district: str):
        """Use this tool to check for recent earthquakes near a given district.
        
        Args:
            district: The name of the district/city (e.g., 'Delhi', 'Mumbai', 'Kathmandu').
        """
        logger.info(f"Checking earthquake for {district}")
        self.primary_issue = "Rescue Esc."
        
        # Geocoding to get lat/long
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={district}&count=1&language=en&format=json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(geocode_url, timeout=5) as geo_resp:
                    if geo_resp.status != 200:
                        return "API Down: Geocoding failed. Tell the user in Hindi: 'सर्वर डाउन होने के कारण मैं अभी भूकंप की जानकारी नहीं दे पा रही हूँ।'"
                    
                    geo_data = await geo_resp.json()
                    
                    if not geo_data.get("results"):
                        return f"Location not found. Tell the user in Hindi that you couldn't find data for {district}."
                        
                    lat = geo_data["results"][0]["latitude"]
                    lon = geo_data["results"][0]["longitude"]
                
                # Check earthquakes in last 7 days within 300km
                # USGS API
                start_date = (datetime.now().timestamp() - (7 * 24 * 60 * 60))
                start_str = datetime.fromtimestamp(start_date).strftime('%Y-%m-%d')
                usgs_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=300&starttime={start_str}"
                
                async with session.get(usgs_url, timeout=10) as usgs_resp:
                    if usgs_resp.status != 200:
                        return "API Down: Earthquake fetch failed. Tell the user in Hindi: 'सर्वर डाउन होने के कारण मैं अभी भूकंप की जानकारी नहीं दे पा रही हूँ।'"
                    
                    usgs_data = await usgs_resp.json()
                    features = usgs_data.get("features", [])
                    
                    if not features:
                        return f"No recent earthquakes found near {district} in the last 7 days. Tell the user in Hindi that the area is safe from recent earthquakes."
                        
                    # Find the strongest one
                    strongest = max(features, key=lambda x: x["properties"].get("mag", 0))
                    props = strongest["properties"]
                    mag = props.get("mag")
                    place = props.get("place")
                    time_ms = props.get("time")
                    time_str = datetime.fromtimestamp(time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S') if time_ms else "Recent"
                    
                    return (
                        f"Real-time Earthquake Data for {district}:\n"
                        f"Magnitude: {mag} on Richter scale\n"
                        f"Epicenter: {place}\n"
                        f"Time: {time_str}\n"
                        f"Instructions: Speak this data naturally in Hindi Devanagari (including date and time). Warn them about the magnitude if it's > 5.0."
                    )
        except Exception as e:
            logger.error(f"Earthquake API error: {e}")
            return "API Timeout/Error. Tell the user in Hindi: 'माफ़ करना, नेटवर्क समस्या के कारण मैं अभी भूकंप का डेटा नहीं ला पा रही हूँ।'"

    @function_tool
    async def find_nearest_hospital(self, context: RunContext, district: str, injury_type: str = "general"):
        """Use this tool to find the nearest hospital best suited for the caller's injury type.
        
        Args:
            district: The name of the district/city (e.g., 'Delhi', 'Mumbai', 'Nashik').
            injury_type: The type of injury or medical need. Use one of: 'fracture' (for broken bones/per tuta/hath tuta), 
                         'neuro' (for head injury, paralysis, brain issues), 'burn' (for fire/chemical burns), 
                         'cardiac' (for heart attack/chest pain), 'trauma' (for accident/major injury), 
                         'general' (for minor injuries or unknown).
        """
        logger.info(f"Finding {injury_type} hospital for {district}")
        self.primary_issue = "Hospital Search"
        
        # Map injury type to a search keyword
        specialty_map = {
            "fracture": "orthopedic hospital",
            "neuro": "neurology hospital",
            "burn": "burn hospital",
            "cardiac": "cardiac hospital",
            "trauma": "trauma center hospital",
            "general": "hospital",
        }
        keyword = specialty_map.get(injury_type.lower(), "hospital")
        maps_link = f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}+in+{district}"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "DisasterResponseAgent/1.0 (hackathon project)"}
                
                async def fetch_hospitals(query_keyword: str):
                    """Helper to fetch + deduplicate hospitals, filtering irrelevant specialties."""
                    nom_url = f"https://nominatim.openstreetmap.org/search?format=json&q={query_keyword.replace(' ', '+')}+in+{district}&limit=15"
                    async with session.get(nom_url, headers=headers, timeout=10) as resp:
                        if resp.status != 200:
                            return None
                        data = await resp.json()
                        
                        # Keywords to EXCLUDE if injury_type is NOT those specialties
                        exclude_map = {
                            "fracture": ["eye", "ophthalm", "dental", "skin", "cancer", "maternity", "gynae", "gynaec", "children", "child", "paediatr"],
                            "neuro":    ["eye", "ophthalm", "dental", "skin", "cancer", "maternity", "gynae", "gynaec", "bone", "ortho"],
                            "burn":     ["eye", "ophthalm", "dental", "maternity", "gynae", "gynaec", "children", "child", "ortho"],
                            "cardiac":  ["eye", "ophthalm", "dental", "skin", "maternity", "gynae", "gynaec", "ortho"],
                            "trauma":   ["eye", "ophthalm", "dental", "skin", "cancer", "maternity", "gynae", "gynaec"],
                            "general":  ["eye", "ophthalm", "dental", "skin", "cancer"],
                        }
                        exclude_words = exclude_map.get(injury_type.lower(), [])
                        
                        seen, results = set(), []
                        for el in data:
                            name = el.get("name", "").strip()
                            if not name or name in seen:
                                continue
                            # Skip hospitals that are clearly unrelated specialties
                            name_lower = name.lower()
                            if any(excl in name_lower for excl in exclude_words):
                                logger.info(f"Skipping unrelated hospital: {name}")
                                continue
                            seen.add(name)
                            results.append(name)
                            if len(results) >= 3:
                                break
                        return results
                
                # Step 1: Try specialty search first
                unique_hospitals = await fetch_hospitals(keyword)
                
                # Step 2: If specialty returns nothing, fallback to generic "hospital"
                used_keyword = keyword
                if not unique_hospitals and keyword != "hospital":
                    logger.info(f"Specialty '{keyword}' not found, falling back to generic hospital")
                    unique_hospitals = await fetch_hospitals("hospital")
                    used_keyword = "hospital"
                    
                if unique_hospitals is None:
                    return f"API Down. Tell the user in Hindi: 'सर्वर डाउन है। आप Google Maps पर {district} में {keyword} ढूंढ सकते हैं।'"
                    
                if not unique_hospitals:
                    return (
                        f"No hospitals found near {district}. "
                        f"Tell the user in Hindi to search Google Maps: '{maps_link}' or call 112 for emergency."
                    )
                    
                hospitals_str = "\n- ".join(unique_hospitals)
                
                # Add specialty advice if we fell back to generic
                specialty_advice = ""
                if used_keyword == "hospital" and keyword != "hospital":
                    specialty_map_advice = {
                        "orthopedic hospital": "इन अस्पतालों में Orthopedic (हड्डी) विभाग ज़रूर होगा।",
                        "neurology hospital": "इन अस्पतालों में Neurology (न्यूरो) विभाग ज़रूर होगा।",
                        "burn hospital": "इन अस्पतालों में Burn विभाग होगा।",
                        "cardiac hospital": "इन अस्पतालों में Cardiac विभाग होगा।",
                        "trauma center hospital": "इन अस्पतालों में Trauma/Emergency विभाग होगा।",
                    }
                    specialty_advice = specialty_map_advice.get(keyword, "")
                
                self.call_successful = True
                return (
                    f"Nearest hospitals for {injury_type} in {district}:\n"
                    f"- {hospitals_str}\n"
                    f"Specialty Note: {specialty_advice}\n"
                    f"Google Maps Link: {maps_link}\n"
                    f"Instructions: Read the hospital names naturally in Hindi Devanagari. "
                    f"If specialty_advice is not empty, say it in Hindi. "
                    f"Tell the user to Google Maps search for phone numbers. "
                    f"Remind them to call 112 for life-threatening emergencies."
                )
        except Exception as e:
            logger.error(f"Hospital API error: {e}")
            return "API Timeout/Error. Tell the user in Hindi: 'माफ़ करना, नेटवर्क समस्या के कारण मैं अभी अस्पताल का डेटा नहीं ला पा रही हूँ। आप 112 पर कॉल करें।'"

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        caller_name: str,
        caller_id: str,
        summary: str,
        urgency: str = "medium",
        what_agent_checked: str = "",
        followup_method: str = "callback",
        language: str = "Hindi",
    ):
        """Use this tool to escalate a situation to a human rescue team. Only call this AFTER getting the caller's explicit permission.

        Args:
            caller_name: The caller's name (in English/Roman letters).
            caller_id: The caller's phone number or unique ID (in English/Roman letters).
            summary: A short summary of what happened and what help is needed (in English). Do NOT include passwords, OTPs, PINs, Aadhaar, or bank details.
            urgency: The urgency level. One of: 'emergency' (life threat), 'high' (severe injury), 'medium' (trapped but stable), 'low' (general help needed).
            what_agent_checked: What the agent already did for the caller (e.g., 'checked weather alert, suggested hospital').
            followup_method: How the human team should follow up. One of: 'callback', 'sms', 'dispatch_team'.
            language: The caller's preferred language (e.g., 'Hindi', 'English').
        """
        # Generate a unique reference ID like REQ-4582
        ref_id = f"REQ-{random.randint(1000, 9999)}"
        logger.info(f"[ESCALATION] Creating escalation {ref_id} for {caller_name} | Urgency: {urgency}")
        self.primary_issue = "Rescue Esc."

        # Check for duplicate open escalations for same caller
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT reference_id, status FROM escalations WHERE caller_id = ? AND status = 'open' ORDER BY created_at DESC LIMIT 1",
            (caller_id,),
        )
        existing = cursor.fetchone()
        if existing:
            # Update existing escalation instead of creating duplicate
            old_ref = existing[0]
            cursor.execute(
                "UPDATE escalations SET summary = ?, urgency = ?, what_agent_checked = ?, created_at = ? WHERE reference_id = ?",
                (summary, urgency, what_agent_checked, datetime.now().isoformat(), old_ref),
            )
            conn.commit()
            conn.close()
            logger.info(f"[ESCALATION] Updated existing escalation {old_ref} instead of creating duplicate")

            # Send signal to frontend for calling animation (even on update)
            try:
                if self._room and self._room.local_participant:
                    escalation_data = json.dumps({
                        "type": "escalation_alert",
                        "reference_id": old_ref,
                        "caller_name": caller_name,
                        "urgency": urgency,
                        "summary": summary,
                    }).encode("utf-8")
                    await self._room.local_participant.publish_data(escalation_data, reliable=True)
                    logger.info(f"[ESCALATION] Sent escalation signal to frontend for {old_ref}")
            except Exception as e:
                logger.warning(f"[ESCALATION] Could not send signal to frontend: {e}")

            self.call_successful = True
            return (
                f"An open request already exists for this caller. Updated request {old_ref} with new details.\n"
                f"Reference ID: {old_ref}\n"
                f"Tell the caller in Hindi: 'आपकी पहले से एक रिक्वेस्ट खुली है, रेफरेंस नंबर {old_ref}। मैंने उसे अपडेट कर दिया है। हमारी टीम जल्द से जल्द आपसे संपर्क करेगी।'"
            )

        # Save new escalation
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO escalations (reference_id, caller_name, caller_id, summary, urgency, status, what_agent_checked, followup_method, language, created_at) VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?, ?)",
            (ref_id, caller_name, caller_id, summary, urgency, what_agent_checked, followup_method, language, now),
        )
        conn.commit()
        conn.close()

        # Send signal to frontend for calling animation
        try:
            if self._room and self._room.local_participant:
                escalation_data = json.dumps({
                    "type": "escalation_alert",
                    "reference_id": ref_id,
                    "caller_name": caller_name,
                    "urgency": urgency,
                    "summary": summary,
                }).encode("utf-8")
                await self._room.local_participant.publish_data(escalation_data, reliable=True)
                logger.info(f"[ESCALATION] Sent escalation signal to frontend for {ref_id}")
        except Exception as e:
            logger.warning(f"[ESCALATION] Could not send signal to frontend: {e}")

        logger.info(f"[ESCALATION] Saved escalation {ref_id} to database")
        
        self.call_successful = True
        return (
            f"Escalation created successfully!\n"
            f"Reference ID: {ref_id}\n"
            f"Urgency: {urgency}\n"
            f"Status: open\n"
            f"Tell the caller in Hindi: 'आपकी रिक्वेस्ट भेज दी गई है। आपका रेफरेंस नंबर {ref_id} है। "
            f"हमारी रेस्क्यू टीम जल्द से जल्द आपसे संपर्क करेगी। कृपया तब तक सुरक्षित रहें और 1-1-2 पर कॉल करें।' "
            f"Do NOT promise an exact time for the rescue team to arrive."
        )

    @function_tool
    async def check_escalation_status(self, context: RunContext, reference_id: str):
        """Use this tool to check the status of a previously created escalation request.

        Args:
            reference_id: The reference ID of the escalation (e.g., 'REQ-4582').
        """
        logger.info(f"[ESCALATION] Checking status for {reference_id}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT caller_name, summary, urgency, status, created_at FROM escalations WHERE reference_id = ?",
            (reference_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            name, summary, urgency, status, created = row
            status_hindi = {"open": "खुली", "in_progress": "प्रगति में", "resolved": "हल हो गई"}.get(status, status)
            return (
                f"Escalation {reference_id}:\n"
                f"Caller: {name}\n"
                f"Summary: {summary}\n"
                f"Urgency: {urgency}\n"
                f"Status: {status}\n"
                f"Created: {created}\n"
                f"Tell the caller in Hindi: 'आपकी रिक्वेस्ट {reference_id} की स्थिति: {status_hindi}। हमारी टीम इस पर काम कर रही है।'"
            )
        return f"No escalation found with reference ID {reference_id}. Tell the caller in Hindi that this reference number was not found."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="rakshika-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    assistant = Assistant(room=ctx.room)

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        import uuid
        call_id = str(uuid.uuid4())
        status = "success" if assistant.call_successful else "failed"
        category = assistant.primary_issue
        logger.info(f"[CALL ANALYTICS] Call ended. Status: {status}, Category: {category} (Call ID: {call_id})")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO calls (call_id, caller_id, status, issue_category) VALUES (?, ?, ?, ?)", 
                           (call_id, participant.identity, status, category))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[CALL ANALYTICS] Error saving call outcome: {e}")

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        # multi language = code-mixed Hinglish support (Hindi + English auto-detect)
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="hi-IN-namrita",  # Falcon Hindi female voice (options: hi-IN-khyati, hi-IN-sunaina)
                locale="hi-IN",
                style="Conversational",  # Falcon uses "Conversational" not "Conversation"
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=False,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    logger.info("Waiting up to 30 seconds for user to connect and publish audio...")
    import asyncio
    async def wait_for_user_audio():
        timeout = 30.0
        start_time = asyncio.get_event_loop().time()
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.info("Timeout waiting for audio track. Proceeding anyway.")
                return
            for p in ctx.room.remote_participants.values():
                if p.kind != rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                    for pub in p.track_publications.values():
                        if pub.kind == rtc.TrackKind.KIND_AUDIO and pub.subscribed:
                            return
            await asyncio.sleep(0.5)

    await wait_for_user_audio()
    logger.info("User audio track connected or timed out! Waiting 2 seconds for SIP RTP to establish...")
    await asyncio.sleep(2)
    logger.info("Sending greeting now...")

    # Check if this is an outbound alert call
    metadata = ctx.job.metadata if hasattr(ctx.job, "metadata") else ""
    greeting_instructions = "कृपया हिंदी में ग्रीट करें।"
    is_outbound = metadata == "outbound_alert"

    if is_outbound:
        greeting_instructions = "नमस्ते। मैं रक्षिका हूँ, NDRF की तरफ से। क्या मेरी आपसे पहले बात हुई है? कृपया अपना नाम बताएँ।"
    else:
        greeting_instructions = (
            "You are Rakshika, a female assistant. Say this greeting EXACTLY in Devanagari Hindi: "
            "'नमस्ते। मैं रक्षिका हूँ, NDRF की emergency voice assistant। क्या हम पहले बात कर चुके हैं? आपका नाम या फोन नंबर क्या है?' Write only in Devanagari script."
        )

    # First-turn greeting
    await session.generate_reply(instructions=greeting_instructions)

    @session.on("metrics_collected")
    def on_metrics_collected(metrics):
        logger.info(f"Metrics collected (use this to check TTS latency): {metrics}")


if __name__ == "__main__":
    cli.run_app(server)
