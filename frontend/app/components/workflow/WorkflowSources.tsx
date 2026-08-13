"use client";

import { WorkflowSource } from "@/types/workflow";

interface Props {
    sources: WorkflowSource[];
}

export default function WorkflowSources({
    sources,
}: Props) {

    if (!sources.length) return null;

    return (

        <div className="space-y-3">

            <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">

                Proof Sources

            </h3>

            <div className="grid gap-3">

                {sources.map((source) => (

                    <div
                        key={`${source.source_id}-${source.chunk_index}`}
                        className="rounded-xl border border-zinc-200 bg-zinc-50 p-4"
                    >

                        <div className="font-medium">

                            {source.source_title}

                        </div>

                        <div className="mt-2 text-sm text-zinc-600">

                            {source.citation}

                        </div>

                    </div>

                ))}

            </div>

        </div>

    );

}
