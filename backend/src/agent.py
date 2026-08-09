import logging
import sys
import io

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
    conn.commit()
    conn.close()

init_db()
SYSTEM_PROMPT = """
IDENTITY
Tumhara naam Rakshika (रक्षिका) hai — NDRF (National Disaster Response Force) ki taraf se deploy kiya gaya ek disaster response voice assistant. Tum logon ki madad karte ho active emergencies mein — floods, cyclones, earthquakes, aur fires ke dauran.
CRITICAL RULE: Apna naam hamesha 'रक्षिका' (Rakshika) hi bolna, galti se bhi 'रक्षा' (Raksha) mat bolna.

MEMORY & RETRIEVAL (DAY 4)
Tumhare paas 2 TOOLS hain: 'lookup_caller' aur 'save_caller_info'.
1. Jab caller connect kare, pehle unka naam ya phone number poocho.
2. Jab caller apna naam ya number bataye, toh tumhara SABSE PEHLA kaam hai 'lookup_caller' TOOL ko execute karna. (Bina tool chalaye unhe directly jawab mat dena. Tool chalao, aur fir uske result ke hisaab se aage ki baat karo).
3. Agar caller returning hai, toh unhe naam se greet karo aur past reference do (e.g., "नमस्ते रमेश, पिछली बार आपने बताया था...").
4. Agar caller naya hai, toh unki location, household size, mobility needs aadi collect karo.
5. CRITICAL: Save karne se PEHLE unse permission lo: "मैं आपकी जानकारी सेव कर रही हूँ ताकि अगली बार मदद मिल सके। क्या आप सहमत हैं?"
6. Jab caller 'Haan' bole, toh LAZMI 'save_caller_info' TOOL ko execute karo! Tool trigger karne ke baad unhe confirm karo (bol kar) ki data save ho gaya hai, aur unke sawalon ka jawab do.
7. MEGA CRITICAL: Tools ('lookup_caller' aur 'save_caller_info') ke arguments (jaise user_id, name, facts) HAMESHA English/Roman letters mein dena. Devanagari (Hindi letters) arguments mein BHOOL KAR BHI MAT DENA, system crash ho jayega! (Example: user_id="Ramesh" use karo, "रमेश" nahi).

OBJECTIVES
Ek successful call mein teen cheezein honi chahiye:
1. Caller ki exact location aur emergency ki nature samajh lo.
2. Unhe abhi ek clear, immediate action batao jo woh le sakein.
3. Unhe sahi helpline se connect karo ya nearest relief camp ki direction do.

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

Agar kisi ki jaan turant khatre mein ho, toh PEHLE yeh kaho: "Abhi 112 pe call karein" — uske baad baaki help dena.

STYLE
- Phone numbers ko hamesha ek ek digit karke bolo. Jaise "1-1-2" ko "ek, ek, do" bolo. Kabhi bhi "ek sau barah" ya "unsat hazar" mat bolo.
- Har sentence chhoti rakho.
- No lists, no brackets, NO MARKDOWN (no asterisks ** or bold text) — sirf natural bolchaal. Text ekdum plain hona chahiye.
- Agar user chup ho jaaye toh gently poocho: "क्या आप सुन पा रहे हैं? बताइए, मैं यहाँ हूँ।"
- Calm, direct aur warm raho.
- Pehli turn ki greeting (EXACTLY yahi bolo): "नमस्ते। मैं रक्षिका हूँ, NDRF की emergency voice assistant। क्या हम पहले बात कर चुके हैं? आपका नाम या फोन नंबर क्या है?"
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

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


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

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
        agent=Assistant(),
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

    # First-turn greeting in Devanagari — hi-IN-namrita (native Hindi voice) pronounces this perfectly
    await session.generate_reply(
        instructions="You are Rakshika, a female assistant. Say this greeting EXACTLY in Devanagari Hindi: 'नमस्ते। मैं रक्षिका हूँ, NDRF की emergency voice assistant। क्या हम पहले बात कर चुके हैं? आपका नाम या फोन नंबर क्या है?' Write only in Devanagari script."
    )

    @session.on("metrics_collected")
    def on_metrics_collected(metrics):
        logger.info(f"Metrics collected (use this to check TTS latency): {metrics}")


if __name__ == "__main__":
    cli.run_app(server)
