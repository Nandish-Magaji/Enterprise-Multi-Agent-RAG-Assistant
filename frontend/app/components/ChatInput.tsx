"use client";

import { useState } from "react";

interface Props {
  onSend: (message: string) => void;
  loading: boolean;
}

export default function ChatInput({
  onSend,
  loading,
}: Props) {
  const [message, setMessage] = useState("");

  const send = () => {
    if (!message.trim()) return;

    onSend(message);
    setMessage("");
  };

  return (
    <div className="border-t bg-white p-4">
      <div
        className="
          max-w-4xl
          mx-auto
          flex
          items-end
          gap-2
          border
          rounded-full
          px-4
          py-2
          shadow-sm
          bg-white
        "
      >
        <textarea
          value={message}
          placeholder="Ask anything..."
          rows={1}
          onChange={(e) => {
            setMessage(e.target.value);

            e.target.style.height = "auto";
            e.target.style.height =
              e.target.scrollHeight + "px";
          }}
          onKeyDown={(e) => {
            if (
              e.key === "Enter" &&
              !e.shiftKey
            ) {
              e.preventDefault();
              send();
            }
          }}
          className="
            flex-1
            resize-none
            outline-none
            border-none
            bg-transparent
            text-sm
            leading-6
            max-h-40
            overflow-y-auto
            py-2
          "
        />

        <button
          onClick={send}
          disabled={loading}
          className="
            h-10
            w-10
            rounded-full
            bg-black
            text-white
            flex
            items-center
            justify-center
            hover:opacity-90
            disabled:opacity-50
            disabled:cursor-not-allowed
          "
        >
          {loading ? (
            <span className="text-xs">
              ...
            </span>
          ) : (
            <span className="text-lg">
              ↑
            </span>
          )}
        </button>
      </div>
    </div>
  );
}