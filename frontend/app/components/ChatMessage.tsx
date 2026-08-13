"use client";

import CopyButton from "./CopyButton";
import DocumentRenderer from "./markdown/DocumentRenderer";

interface Props {
  role: "user" | "assistant";
  content: string;
}

export default function ChatMessage({
  role,
  content,
}: Props) {

  const isUser = role === "user";

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`
          max-w-4xl
          rounded-xl
          p-4
          my-2
          whitespace-pre-wrap
          ${
            isUser
              ? "bg-blue-600 text-white"
              : "bg-white text-gray-900 border border-gray-200 shadow-sm"
          }
        `}
      >
        <DocumentRenderer content={content} />  

        {!isUser && (
          <CopyButton text={content} />
        )}
      </div>
    </div>
  );
}