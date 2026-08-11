"""
Day 6 — Outbound SIP Call via LiveKit
Rakshika calls you directly on LinPhone (no Twilio needed).

Steps:
1. Make sure your agent.py is running: uv run python src/agent.py dev
2. Run this script:  uv run python src/outbound_sip_call.py
3. Answer the call on LinPhone app!

Usage:
    uv run python src/outbound_sip_call.py
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbound_sip")

LIVEKIT_URL        = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY    = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]

TARGET_SIP  = "sip:pratham197600@sip.linphone.org"
import uuid
ROOM_NAME   = f"rakshika-sip-{uuid.uuid4().hex[:6]}"
AGENT_NAME  = "rakshika-agent"


async def main():
    logger.info("Rakshika SIP Outbound — Starting...")
    logger.info(f"  Calling: {TARGET_SIP}")

    lk = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    # Step 1: Create LiveKit room
    await lk.room.create_room(api.CreateRoomRequest(name=ROOM_NAME))
    logger.info(f"[OK] Room created: {ROOM_NAME}")

    # Step 2: Dispatch Rakshika agent into the room
    dispatch = await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            room=ROOM_NAME,
            agent_name=AGENT_NAME,
            metadata="outbound_alert",
        )
    )
    logger.info(f"[OK] Agent dispatched: {dispatch.id}")

    # Step 3: Hardcoded Trunk ID to prevent creating too many trunks and getting spam-blocked
    TRUNK_ID = "ST_FxXn7XxdpNdC"
    logger.info(f"[OK] Using existing SIP Trunk: {TRUNK_ID}")

    # Wait for agent to enter the room before ringing the phone
    logger.info("  [DELAY] Waiting 3 seconds for Rakshika to join the room...")
    await asyncio.sleep(3)

    # Step 4: Place the SIP call — Rakshika calls your LinPhone
    participant = await lk.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=ROOM_NAME,
            sip_trunk_id=TRUNK_ID,
            sip_call_to="pratham197600",   # username only, not full SIP URI
            participant_identity="phone-user",
            participant_name="Rakshika",
        )
    )
    logger.info(f"[OK] SIP call placed! Participant: {participant.participant_identity}")
    logger.info("  [PHONE] LinPhone should ring now — answer it!")

    await lk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
