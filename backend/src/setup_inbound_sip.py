import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv('.env.local')

async def main():
    lk = api.LiveKitAPI(
        url=os.environ['LIVEKIT_URL'],
        api_key=os.environ['LIVEKIT_API_KEY'],
        api_secret=os.environ['LIVEKIT_API_SECRET']
    )
    
    print("Creating LiveKit Inbound SIP Trunk...")
    trunk = await lk.sip.create_sip_inbound_trunk(
        api.CreateSIPInboundTrunkRequest(
            trunk=api.SIPInboundTrunkInfo(
                name="linphone-inbound",
                numbers=["+17372212163"] # Twilio number used as wildcard
            )
        )
    )
    print(f"Trunk Created: {trunk.sip_trunk_id}")

    print("\nCreating SIP Dispatch Rule...")
    dispatch_rule = await lk.sip.create_sip_dispatch_rule(
        api.CreateSIPDispatchRuleRequest(
            name="route-to-rakshika",
            rule=api.SIPDispatchRule(
                dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                    room_prefix="rakshika-room-"
                )
            ),
            trunk_ids=[trunk.sip_trunk_id]
        )
    )
    print(f"Dispatch Rule Created: {dispatch_rule.sip_dispatch_rule_id}")
    await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())
