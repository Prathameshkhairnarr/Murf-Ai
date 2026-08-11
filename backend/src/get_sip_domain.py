import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv('.env.local')

async def get_domain():
    lk = api.LiveKitAPI(
        url=os.environ['LIVEKIT_URL'],
        api_key=os.environ['LIVEKIT_API_KEY'],
        api_secret=os.environ['LIVEKIT_API_SECRET']
    )
    # The domain is likely stored in the LiveKit Cloud Project or SIP URI.
    # We can try to guess it from the LIVEKIT_URL, e.g., wss://new-project-xyz.livekit.cloud
    # -> new-project-xyz.sip.livekit.cloud
    print("Fetching SIP Dispatch Rules...")
    rules = await lk.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
    
    for rule in rules.items:
        print(f"Rule Name: {rule.name}")
        print(f"Rule ID: {rule.sip_dispatch_rule_id}")
        print(f"Trunks: {rule.trunk_ids}")
        print("-" * 20)
    
    await lk.aclose()

if __name__ == "__main__":
    asyncio.run(get_domain())
