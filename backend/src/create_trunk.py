import os
import asyncio
from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

async def main():
    lk = api.LiveKitAPI(
        os.environ['LIVEKIT_URL'],
        os.environ['LIVEKIT_API_KEY'],
        os.environ['LIVEKIT_API_SECRET']
    )
    trunk = await lk.sip.create_outbound_trunk(
        api.CreateSIPOutboundTrunkRequest(
            trunk=api.SIPOutboundTrunkInfo(
                name="LinPhone Trunk Clean",
                address="sip.linphone.org",
                numbers=["+14155552671"],
                transport=api.SIP_TRANSPORT_UDP,
            )
        )
    )
    print(f"TRUNK_ID={trunk.sip_trunk_id}")
    await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())
