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
    trunks = await lk.sip.list_inbound_trunk(api.ListSIPInboundTrunkRequest())
    print("Inbound Trunks:")
    for t in trunks.items:
        print(t.sip_trunk_id, t.name, t.numbers)
        
    rules = await lk.sip.list_dispatch_rule(api.ListSIPDispatchRuleRequest())
    print("\nDispatch Rules:")
    for r in rules.items:
        print(r.sip_dispatch_rule_id, r.name, r.trunk_ids)

    await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())
