---
title: "Building Rakshika: A Multi-Agent Disaster Response Voice AI in 10 Days"
tags: [VoiceAI, MurfAI, LiveKit, Python, AI]
cover_image: [YOUR_COVER_IMAGE_LINK_HERE] # Replace with a nice banner image link
---

Over the past 10 days, I participated in the **10 Days of Voice Agents — VoiceForBharat Edition** challenge. The goal? Build a fully functional, highly capable voice agent using **LiveKit** and the ultra-fast **Murf Falcon** TTS API.

For my track, I chose **Disaster Response**. During natural disasters like floods, cyclones, or earthquakes, emergency helplines are often overwhelmed. People in distress need immediate, calm, and accurate information in their native language. 

To solve this, I built **Rakshika**, a Hindi-speaking emergency triage voice assistant.

Here’s the story of how Rakshika evolved from a simple text prompt into a complex, multi-agent ecosystem.

---

## 🦸‍♀️ Meet Rakshika & Aarav

Rakshika isn't just a basic FAQ bot. She is a highly constrained, empathetic triage agent who can handle high-stress emergency calls. 

But as the system grew, I realized one agent shouldn't do everything. So, I introduced **Aarav**, a Shelter Information Specialist. 

* **Rakshika (Primary Agent):** Handles general safety, weather/flood alerts, earthquake tracking, hospital routing, and human escalations.
* **Aarav (Specialist Agent):** Takes over specifically when a caller needs precise details about relief camps, total capacity, and available beds.

![Rakshika and Aarav UI Demo]([ADD_YOUR_UI_SCREENSHOT_LINK_HERE]) 
*<center>Caption: The clean UI showing Rakshika taking a call.</center>*

---

## ✨ The Most Important Features

### 1. 🗣️ Ultra-Fast, Natural Voice (Murf Falcon)
Using **Murf Falcon**, Rakshika speaks in a natural female Indian voice (`hi-IN-namrita`), while Aarav uses a distinct male voice (`hi-IN-karan`). The latency is incredibly low, making the conversation feel like a real phone call.

### 2. 🤝 Seamless Multi-Agent Handoffs
When a user asks Rakshika, *"Where can I find a relief camp in Nashik?"*, she seamlessly hands the call over to Aarav. 
* **Under the hood:** LiveKit handles the agent switching. The frontend dynamically updates its UI theme (Red for Rakshika, Green for Aarav) based on data channel signals. 
* **Two-way routing:** If the user asks Aarav about weather, he hands the call back to Rakshika!

![Handoff Process UI]([ADD_AGENT_HANDOFF_SCREENSHOT_LINK_HERE])
*<center>Caption: The UI dynamically changing to Green when Aarav takes over the call.</center>*

### 3. ⚡ Real-Time API Integrations
Rakshika uses function calling to fetch live data:
* **Open-Meteo API** for live flood and weather alerts.
* **USGS API** for real-time earthquake tracking within a 300km radius.
* **Google Maps/Nominatim** to route callers to specific hospitals based on injury type (e.g., Burn vs. Neuro).

### 4. 🚨 Human Escalation
If a caller is physically trapped or severely injured, Rakshika asks for permission and triggers a `create_escalation` tool. She generates a unique Reference ID (e.g., REQ-1234), saves the context to a local SQLite database, and alerts the frontend UI for human intervention.

![Human Escalation Alert]([ADD_ESCALATION_ALERT_SCREENSHOT_LINK_HERE])
*<center>Caption: The Red Escalation card showing the generated Request ID for the rescue team.</center>*

### 5. 🧠 Memory & Context
Using a local SQLite database, Rakshika looks up the caller's phone number when they connect. If they've called before, she greets them by name and remembers their past context.

---

## 🛠️ How the System Works (Architecture)

The pipeline is entirely orchestrated by **LiveKit Agents**:
1. **STT (Speech-to-Text):** Deepgram Nova-3 (handles code-mixed Hindi/English perfectly).
2. **VAD (Voice Activity Detection):** Silero VAD detects when the user starts and stops speaking.
3. **LLM:** Google Gemini 1.5 Flash processes the text, executes tools, and manages context.
4. **TTS (Text-to-Speech):** Murf Falcon converts the LLM's Hindi text back into hyper-realistic audio.

![Architecture Diagram]([ADD_ARCHITECTURE_DIAGRAM_LINK_HERE])
*<center>Caption: A simple high-level overview of the audio processing pipeline.</center>*

---

## 🚧 The Biggest Challenge: The "Robotic Handoff" Bug

Building a multi-agent system wasn't entirely smooth. On Day 9, I hit a major roadblock: **The Handoff Clashing Bug.**

**The Problem:** 
When Rakshika decided to hand off the call to Aarav, she was supposed to say, *"I am connecting you to our shelter specialist."* 
However, she would either stay completely silent, or say it twice. Furthermore, when Aarav fetched shelter data from a local CSV, he read it out like a robotic markdown list: *"1. Asterisk Asterisk Rajiv Gandhi Camp... Dash Total Capacity..."*

**The Solution:**
1. **Fixing the Handoff Timing:** I realized the LiveKit `transfer` function was abruptly killing the TTS stream before Rakshika could finish speaking. I removed the hardcoded `generate_reply` from the tool itself, allowed the LLM to speak the phrase naturally as part of its conversational output, and simply added an `asyncio.sleep(4.5)` inside the tool execution to give the TTS engine time to finish speaking before swapping the agent context.
2. **Fixing Robotic Speech:** I heavily modified Aarav's System Prompt and the return string of the CSV tool. I strictly forbade the use of markdown (asterisks, bullet points) and instructed the LLM to process the raw CSV data into a single, natural Hindi sentence.

```python
# Code snippet showing how we give time for the TTS to finish before transferring
@function_tool()
async def transfer_to_shelter_specialist(self, context: RunContext):
    # 1. Trigger connecting animation on frontend via data message
    data = json.dumps({"type": "agent_transfer", "to": "shelter"}).encode("utf-8")
    self._room.local_participant.publish_data(data, reliable=True)

    # 2. Wait for Rakshika to finish speaking her natural response 
    await asyncio.sleep(4.5)

    # 3. Transfer the context and agent
    return (
        ShelterSpecialistAgent(chat_ctx=new_ctx, room=self._room),
        "Transferring to shelter specialist Aarav",
    )
```

---

## 🚀 How to Build and Run it Yourself

If you want to build your own Voice AI, here is how you can get started with this repository.

### Prerequisites
* Python 3.10+
* Node.js (for the frontend)
* API Keys for LiveKit, Murf AI, Deepgram, and Google Gemini.

### 1. Clone the Repo
```bash
git clone https://github.com/Prathameshkhairnarr/Murf-Ai.git
cd Murf-Ai
```

### 2. Set Up Environment Variables
Create a `.env.local` file in both the `backend` and `frontend` directories. Never commit this file!
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
MURF_API_KEY=your_murf_key
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_API_KEY=your_gemini_key
```

### 3. Run the Backend (Python)
We use `uv` for fast dependency management.
```bash
cd backend
uv sync
uv run python src/agent.py dev
```

### 4. Run the Frontend (Next.js)
```bash
cd frontend
pnpm install
pnpm dev
```
Open `http://localhost:3000`, connect your microphone, and start talking!

---

## 🔗 Links & Resources
* 🐙 **GitHub Repository:** [Prathameshkhairnarr/Murf-Ai](https://github.com/Prathameshkhairnarr/Murf-Ai)
* 🎙️ **LiveKit Voice AI Quickstart:** [Docs](https://docs.livekit.io/agents/start/voice-ai/)
* 🦅 **Murf Falcon Docs:** [Docs](https://murf.ai/api/docs/text-to-speech-models/falcon-2)

Building Rakshika was an incredible learning experience. Going from a simple text prompt to a fully conversational, multi-agent voice application that handles real-time data and human escalations shows just how powerful modern Voice AI has become. 

A huge shoutout to @Murf AI and LiveKit for hosting the 10 Days of Voice Agents challenge!

#VoiceForBharat #MurfAI #LiveKit #VoiceAI #ArtificialIntelligence #Hackathon #DisasterManagement #BuildInPublic
