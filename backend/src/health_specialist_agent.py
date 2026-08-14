from livekit.agents import Agent, RunContext, function_tool
import logging

logger = logging.getLogger("health_agent")

class HealthSpecialistAgent(Agent):
    """
    Focused specialist: general health/medical guidance during a disaster
    (injuries, medicine access, symptoms triage-level advice only).
    NEVER diagnoses, prescribes doses, or replaces a doctor — always pushes
    toward the nearest hospital/medical camp for anything serious.
    """

    def __init__(self, chat_ctx=None, room=None):
        super().__init__(
            instructions="""
आप Rakshika AI की Health Specialist हैं। आपको caller की जानकारी मुख्य सहायक से पहले ही
मिल चुकी है — दोबारा नाम या समस्या मत पूछिए, सीधे मदद शुरू कीजिए।

नियम:
1. कभी भी medical diagnosis या दवा की dose न बताएं। सिर्फ सामान्य first-aid जैसी सलाह
   और यह बताएं कि नज़दीकी अस्पताल/मेडिकल कैंप कब जाना ज़रूरी है।
2. गंभीर लक्षण (सांस लेने में दिक्कत, तेज़ खून बहना, बेहोशी) सुनते ही तुरंत नज़दीकी
   अस्पताल जाने की सलाह दें और ज़रूरत पड़े तो मुख्य सहायक को वापस बुलाएं ताकि rescue
   escalation हो सके।
3. कभी भी "आप ठीक हो जाएंगे" जैसा भरोसा या rescue ETA न दें।
4. आधार या financial जानकारी कभी न मांगें।
""",
            chat_ctx=chat_ctx,
        )
        self._room = room
        self.primary_issue = "Health"
        self.call_successful = False

    async def on_enter(self) -> None:
        if hasattr(self, "_room") and self._room and hasattr(self._room, "local_participant"):
            await self._room.local_participant.set_attributes({
                "active_agent_id": "health_specialist",
                "active_agent_name": "Health Specialist",
                "active_agent_theme": "blue"
            })
            
            import json
            data = json.dumps({
                "type": "agent_ready",
                "active_agent_id": "health_specialist",
                "active_agent_name": "Health Specialist",
                "active_agent_theme": "blue"
            }).encode("utf-8")
            await self._room.local_participant.publish_data(data, reliable=True)

        # Since we use SQLite lookup in main agent, the caller name might not be neatly in userdata.name
        # But we can just use a general greeting.
        await self.session.generate_reply(
            instructions=(
                "बिल्कुल इसी भावना के साथ शुरुआत कीजिए: 'नमस्ते। मुझे आपकी जानकारी "
                "Rakshika से मिल गई है। मैं आपकी क्या मदद कर सकती हूं?' — फिर caller की "
                "health समस्या सुनिए। दोबारा नाम/समस्या मत पूछिए, जो chat context में "
                "पहले से मौजूद है उसे इस्तेमाल कीजिए।"
            )
        )

    @function_tool()
    async def escalate_to_rescue(self, context: RunContext):
        """Use this if symptoms sound serious and the caller needs physical rescue,
        not just guidance. Hands back to the main agent to run rescue escalation."""
        from agent import Assistant

        self.call_successful = True
        try:
            await self.session.generate_reply(
                instructions="बताइए कि आप उन्हें rescue escalation के लिए मुख्य सहायक से जोड़ रही हैं।"
            )
            
            new_ctx = self.chat_ctx.copy(exclude_instructions=True) if hasattr(self, "chat_ctx") and self.chat_ctx else None
            if not new_ctx and hasattr(self.session, "chat_ctx") and self.session.chat_ctx:
                new_ctx = self.session.chat_ctx.copy(exclude_instructions=True)
                
            return (
                Assistant(room=self._room, chat_ctx=new_ctx),
                "Transferring back to main agent for rescue escalation",
            )
        except Exception as e:
            logger.error(f"[ERROR IN ESCALATE TO RESCUE] {e}")
            return f"Error transferring: {e}"
