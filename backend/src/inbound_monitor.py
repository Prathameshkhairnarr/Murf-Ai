import os
import asyncio
from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

async def monitor():
    lk = api.LiveKitAPI(
        os.environ['LIVEKIT_URL'],
        os.environ['LIVEKIT_API_KEY'],
        os.environ['LIVEKIT_API_SECRET']
    )
    print("Monitoring for incoming SIP calls...")
    dispatched_rooms = set()
    
    while True:
        try:
            rooms = await lk.room.list_rooms(api.ListRoomsRequest())
            for room in rooms.rooms:
                if room.name.startswith("rakshika-room-") and room.name not in dispatched_rooms:
                    print(f"New incoming call detected! Room: {room.name}")
                    
                    # Wait 2 seconds for SIP participant to fully join
                    await asyncio.sleep(2)
                    
                    # Dispatch agent
                    await lk.agent_dispatch.create_dispatch(
                        api.CreateAgentDispatchRequest(
                            room=room.name,
                            agent_name="rakshika-agent",
                            metadata="inbound_alert"
                        )
                    )
                    print(f"Agent dispatched to {room.name}")
                    dispatched_rooms.add(room.name)
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(monitor())
