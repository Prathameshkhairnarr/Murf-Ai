import { useEffect, useState } from "react";
import { useRoomContext, useDataChannel } from "@livekit/components-react";
import { RoomEvent, RemoteParticipant, LocalParticipant } from "livekit-client";

export type AgentTheme = {
  id: string;
  name: string;
  color: "red" | "green" | "blue" | string;
};

const DEFAULT_THEME: AgentTheme = { id: "rakshika_main", name: "Rakshika", color: "red" };

export function useActiveAgentTheme(): AgentTheme {
  const room = useRoomContext();
  const [theme, setTheme] = useState<AgentTheme>(DEFAULT_THEME);

  useEffect(() => {
    if (!room) return;

    const applyFromAttributes = (attrs: Record<string, string>) => {
      console.log("[HANDOFF] applyFromAttributes called with:", attrs);
      if (!attrs.active_agent_id) return;
      const next = {
        id: attrs.active_agent_id,
        name: attrs.active_agent_name ?? DEFAULT_THEME.name,
        color: attrs.active_agent_theme ?? DEFAULT_THEME.color,
      };
      console.log("[HANDOFF] applying new theme to state:", next);
      setTheme(next);
    };

    // Catch the case where attributes were already set before this component mounted
    room.remoteParticipants.forEach((p) => applyFromAttributes(p.attributes));
    applyFromAttributes(room.localParticipant.attributes);

    const handleChange = (
      changed: Record<string, string>,
      participant: RemoteParticipant | LocalParticipant
    ) => {
      console.log("[HANDOFF] attributes changed event fired:", changed, participant.attributes);
      applyFromAttributes(participant.attributes);
    };

    room.on(RoomEvent.ParticipantAttributesChanged, handleChange);
    return () => {
      room.off(RoomEvent.ParticipantAttributesChanged, handleChange);
    };
  }, [room]);

  // Fallback: Listen to data channel messages
  useDataChannel('', (msg) => {
    try {
      const data = JSON.parse(new TextDecoder().decode(msg.payload));
      console.log("[HANDOFF] data channel message received:", data);
      if (data.type === 'agent_ready') {
        setTheme({
          id: data.active_agent_id ?? data.specialist,
          name: data.active_agent_name ?? data.specialist_name,
          color: data.active_agent_theme ?? (data.specialist === 'shelter' ? 'green' : 'red'),
        });
      }
    } catch {
      // ignore
    }
  });

  return theme;
}
