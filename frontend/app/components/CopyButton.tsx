"use client";

interface Props {
  text: string;
}

export default function CopyButton({ text }: Props) {

  const copy = async () => {
    await navigator.clipboard.writeText(text);
  };

  return (
    <button
      onClick={copy}
      className="text-sm text-blue-500 mt-2"
    >
      Copy
    </button>
  );
}