from livekit.agents import Agent, RunContext, function_tool
import aiohttp
import logging

logger = logging.getLogger("shelter_agent")

import csv
import os

async def lookup_shelters_for_location(location: str):
    """Helper to find nearby shelters/relief camps using local CSV database with strict matching."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "data", "shelters.csv")
        loc_lower = location.lower().strip()
        results = []
        
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    city = row.get("City", "").lower()
                    district = row.get("District", "").lower()
                    if city and district and (city in loc_lower or loc_lower in city or district in loc_lower or loc_lower in district):
                        results.append(row)
        
        if not results:
            return None
            
        shelters_str = ""
        for idx, s in enumerate(results[:3], 1):
            shelters_str += (
                f"{idx}. {s.get('Shelter Name')} "
                f"(Capacity: {s.get('Total Capacity')}, Available Beds: {s.get('Available Beds')})\n"
                f"Contact: {s.get('Contact Person')} at {s.get('Contact Phone')}\n"
            )
            
        return (
            f"Exact shelter data found for {location}:\n"
            f"{shelters_str}\n"
            f"Instructions: Do NOT read this as a list. Speak naturally in plain Hindi Devanagari. "
            f"DO NOT use asterisks, hyphens, or numbers like 1., 2.. "
            f"Just mention the first shelter in a normal sentence, e.g., 'नासिक में सबसे नज़दीक [Name] है, वहां [Beds] बेड खाली हैं और आप [Contact] से बात कर सकते हैं।'"
        )
    except Exception as e:
        logger.error(f"Shelter data error: {e}")
        return None

class ShelterSpecialistAgent(Agent):
    """
    Focused specialist: shelter / relief camp information only.
    Male Specialist Agent (Aarav) with hi-IN-karan voice.
    Does NOT handle weather, hospital search, or rescue escalation —
    if the caller asks about those, hand back to the main agent.
    """

    def __init__(self, chat_ctx=None, room=None):
        super().__init__(
            instructions="""
आप Aarav हैं — NDRF / Disaster Response Team के Shelter & Relief Camp Specialist (Male Agent)। आपका काम सिर्फ इतना है:

1. Caller को उनके location के सबसे नज़दीकी relief camp / shelter की सटीक जानकारी देना। 
2. आपको हमेशा कैंप की EXACT capacity और उपलब्ध बेड्स (Available Beds) की जानकारी देनी है। 
3. बोलने का तरीका बिल्कुल प्राकृतिक (Natural) होना चाहिए, जैसे आप किसी से फोन पर बात कर रहे हों। कभी भी बुलेट पॉइंट्स (1, 2, 3), स्टार्स (**), या डैश (-) का इस्तेमाल न करें। सारा डेटा साधारण वाक्यों में बोलें।
4. अगर 3 शेल्टर मिलते हैं, तो एक साथ सब मत बताएं। सिर्फ सबसे पहला शेल्टर बताएं, और पूछें कि क्या उन्हें और विकल्प चाहिए।
5. अगर आपके डेटाबेस में उस लोकेशन की जानकारी नहीं है, तो साफ़ कहें: "क्षमा करें, मेरे पास इस इलाके के शेल्टर का डेटा मौजूद नहीं है।"
6. कभी भी rescue ETA, "सब ठीक हो जाएगा", या all-clear जैसे वादे न करें।
7. आधार नंबर या कोई financial detail कभी न मांगें।
8. अगर caller weather update, hospital, या rescue escalation मांगे — तो उन्हें बताएं कि आप उन्हें वापस मुख्य अधिकारी रक्षिका जी से जोड़ रहे हैं, और transfer_to_main tool का उपयोग करें। (CRITICAL: टूल का नाम बोलकर या लिखकर मत बताएं)।

महत्वपूर्ण निर्देश:
- आप एक MALE (पुरुष) एजेंट हैं जिनका नाम आरव (Aarav) है।
- हमेशा पुल्लिंग (masculine) क्रिया रूपों का प्रयोग करें (जैसे: 'बता रहा हूँ', 'मदद करूँगा', 'सकता हूँ' — कभी भी 'रही हूँ' या 'सकती हूँ' न बोलें)।
- छोटे, स्पष्ट, शांत वाक्यों में बोलें — यह एक आपातकालीन कॉल है।
- कोई Markdown (**, -, 1.) इस्तेमाल न करें। केवल plain text।
""",
            chat_ctx=chat_ctx,
        )
        self._room = room
        self.primary_issue = "Shelter"
        self.call_successful = False

    async def on_enter(self) -> None:
        logger.info("[SHELTER AGENT] on_enter called - switching to male voice (hi-IN-karan) and setting shelter attributes")
        
        # 1. Update LiveKit room attributes FIRST to trigger Green ring on frontend
        if hasattr(self, "_room") and self._room and hasattr(self._room, "local_participant"):
            logger.info(f"[HANDOFF] About to call set_attributes on local_participant {self._room.local_participant.sid}")
            await self._room.local_participant.set_attributes({
                "active_agent_id": "shelter_specialist",
                "active_agent_name": "Aarav (Shelter Specialist)",
                "active_agent_theme": "green"
            })
            
            import json
            data = json.dumps({
                "type": "agent_ready",
                "active_agent_id": "shelter_specialist",
                "active_agent_name": "Aarav (Shelter Specialist)",
                "active_agent_theme": "green"
            }).encode("utf-8")
            await self._room.local_participant.publish_data(data, reliable=True)
            logger.info("[HANDOFF] Successfully called set_attributes and publish_data")
            
        # 2. Switch TTS voice to Male (hi-IN-karan) for Aarav
        if hasattr(self.session, "tts") and hasattr(self.session.tts, "update_options"):
            self.session.tts.update_options(voice="hi-IN-karan")

        # 3. STRICT RULE: Wait 0.5 seconds so user visibly sees the ring turn Green BEFORE Aarav speaks
        # (We already waited 4.5s in the main agent before switching)
        import asyncio
        await asyncio.sleep(0.5)
            
        # 4. ONLY AFTER color changes, Aarav speaks in male voice
        await self.session.generate_reply(
            instructions=(
                "आप आरव हैं (Male Shelter Specialist)। "
                "Devanagari Hindi में शांत, विनम्र और आश्वस्त करने वाले अंदाज़ में बोलिए: "
                "'नमस्ते, मैं आरव हूँ — आश्रय स्थल (Shelter) विशेषज्ञ। बताइए आप अभी किस इलाके या शहर में हैं?' "
                "हमेशा पुल्लिंग (masculine) में बोलें।"
            )
        )

    @function_tool()
    async def find_nearest_shelter(self, context: RunContext, location: str):
        """Look up the nearest relief camp/shelter for the caller's stated location.
        IMPORTANT: Always translate the location name to English (e.g., if user says 'नासिक', pass 'Nashik' or 'Nasik').
        Do NOT pass Devanagari script.
        Call this as soon as the caller tells you their area or landmark."""
        logger.info(f"Finding shelter in {location}")
        self.call_successful = True
        
        # Quick hack to fix common spelling issue
        if location.lower() == "nasik":
            location = "nashik"
            
        shelters = await lookup_shelters_for_location(location)
        if not shelters:
            return (
                "इस इलाके के लिए अभी कोई पुष्ट शरण स्थल जानकारी उपलब्ध नहीं है। "
                "कृपया नज़दीकी सरकारी भवन, स्कूल, या सामुदायिक भवन में सम्पर्क करें।"
            )
        return shelters

    @function_tool()
    async def transfer_to_main(self, context: RunContext):
        """Use this when the caller needs weather info, hospital search, or rescue
        escalation — anything outside shelter information."""
        from agent import Assistant

        try:
            import asyncio
            import json

            try:
                if self._room and self._room.local_participant:
                    data = json.dumps({
                        "type": "agent_transfer",
                        "to": "main"
                    }).encode("utf-8")
                    self._room.local_participant.publish_data(data, reliable=True)
                    logger.info("[TRANSFER] Sent agent_transfer signal to frontend (main)")
            except Exception as e:
                logger.warning(f"[TRANSFER] Could not send transfer signal to frontend: {e}")

            # Wait for Aarav to finish speaking his natural response
            await asyncio.sleep(4.5)
            
            new_ctx = self.chat_ctx.copy(exclude_instructions=True) if hasattr(self, "chat_ctx") and self.chat_ctx else None
            if not new_ctx and hasattr(self.session, "chat_ctx") and self.session.chat_ctx:
                new_ctx = self.session.chat_ctx.copy(exclude_instructions=True)
                
            return (
                Assistant(room=self._room, chat_ctx=new_ctx),
                "Transferring back to main agent Rakshika",
            )
        except Exception as e:
            logger.error(f"[ERROR IN SHELTER TRANSFER TO MAIN] {e}")
            return f"Error transferring: {e}"
