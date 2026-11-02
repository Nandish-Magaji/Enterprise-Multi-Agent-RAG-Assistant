interface Props {
  label?: string;
}

export default function GenerationLoader({ label = "Generating..." }: Props) {
  return (
    <div className="flex items-center gap-2 text-sm text-zinc-500" role="status" aria-live="polite">
      <span className="size-2 animate-pulse rounded-full bg-zinc-500" />
      {label}
    </div>
  );
}
