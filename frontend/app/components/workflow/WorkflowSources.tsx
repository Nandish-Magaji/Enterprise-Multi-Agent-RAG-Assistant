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
                            {source.url || source.citation.startsWith("http") ? (
                                <a
                                    href={source.url || source.citation}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="break-all text-blue-700 underline underline-offset-2 hover:text-blue-900 dark:text-blue-300 dark:hover:text-blue-200"
                                >
                                    {source.citation}
                                </a>
                            ) : (
                                source.citation
                            )}
                        </div>

                    </div>

                ))}

            </div>

        </div>

    );

}
