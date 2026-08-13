"use client";

import { useEffect, useRef } from "react";
import MessageBubble from "./chat/MessageBubble";
import { Message } from "@/types/chat";

interface Props {
  messages: Message[];
}

export default function ChatWindow({
  messages,
}: Props) {

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  return (
    <div className="flex-1 min-h-0 overflow-y-auto scroll-smooth p-6">

      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
        />
      ))}

      <div ref={bottomRef} />

    </div>
  );
}