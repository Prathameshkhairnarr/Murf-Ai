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
    print("Fetching outbound trunks...")
    trunks = await lk.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest())
    print(f"Found {len(trunks.items)} trunks. Deleting...")
    for t in trunks.items:
        await lk.sip.delete_sip_trunk(api.DeleteSIPTrunkRequest(sip_trunk_id=t.sip_trunk_id))
    print("Done!")
    await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())
