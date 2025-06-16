import { streamChat, fetchMessages } from "@/lib/api";
import { ChatMessage, Prompt } from "@/types/chat";
import { useEffect, useState, useCallback } from "react";
import { apiMessageToChatMessage } from "@/lib/utils";
import { useSession } from "next-auth/react";

export const useChat = (conversationId: string | null) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const {data: session} = useSession();

  useEffect(() => {
    if (session) {
      if (conversationId) {
        fetchMessages(session.APIToken.accessToken, conversationId).then((fetchedMessages) => {
          setMessages(fetchedMessages.map(apiMessageToChatMessage));
        });
      }
    }
  }, [conversationId, session]);

  const submitPrompt = useCallback((prompt: Prompt) => {
    if (session) {
      (async () => {
        if (prompt.content === "" || !conversationId) {
          return;
        }

        setMessages(prevMessages => [...prevMessages, {role: "user", content: prompt.content}]);
        
        const stream = streamChat(session.APIToken.accessToken, prompt);
        let chunkNum = 0;
        for await (const chunk of stream) {
          if (chunkNum === 0) {
            setMessages(prevMessages => [...prevMessages, {role: "assistant", content: chunk}]);
          }
          else {
            setMessages(prevMessages => {
              const updatedMessages = [...prevMessages];
              updatedMessages[updatedMessages.length - 1] = {role: "assistant", content: chunk};
              return updatedMessages;
            });
          }
          chunkNum++;
        }
      })();
    }
  }, [session, conversationId]);

  return { messages, submitPrompt };
}; 