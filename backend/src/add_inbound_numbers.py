import os
import asyncio
from dotenv import load_dotenv
from livekit import api
import uuid

load_dotenv(".env.local")

async def main():
    lk = api.LiveKitAPI(
        os.environ['LIVEKIT_URL'],
        os.environ['LIVEKIT_API_KEY'],
        os.environ['LIVEKIT_API_SECRET']
    )
    t = await lk.sip.create_inbound_trunk(
        api.CreateSIPInboundTrunkRequest(
            trunk=api.SIPInboundTrunkInfo(
                name='rakshika-inbound-any',
                numbers=['+17372212163', '17372212163', 'sip:+17372212163']
            )
        )
    )
    print(f"Trunk created: {t.sip_trunk_id}")
    
    room_name = f"rakshika-room-{uuid.uuid4().hex[:6]}"
    
    r = await lk.sip.create_dispatch_rule(
        api.CreateSIPDispatchRuleRequest(
            name='route-to-rakshika-any',
            trunk_ids=[t.sip_trunk_id],
            rule=api.SIPDispatchRule(
                dispatch_rule_direct=api.SIPDispatchRuleDirect(room_name=room_name)
            )
        )
    )
    print(f"Dispatch rule created: {r.sip_dispatch_rule_id} -> {room_name}")
    
    await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())
