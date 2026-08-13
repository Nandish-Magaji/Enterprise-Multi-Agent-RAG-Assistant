"use client";

import { Loader2, CheckCircle2 } from "lucide-react";

type Stage = {
    label: string;
    completed: boolean;
    active: boolean;
};

interface Props {
    stages: Stage[];
}

export default function GenerationStatus({
    stages,
}: Props) {

    return (
        <div className="rounded-xl border bg-white p-5 shadow-sm">

            <div className="mb-4">

                <p className="font-semibold text-gray-900">
                    One moment...
                </p>

                <p className="text-sm text-gray-500">
                    Generating your article.
                </p>

            </div>

            <div className="space-y-3">

                {stages.map((stage) => (

                    <div
                        key={stage.label}
                        className="flex items-center gap-3"
                    >

                        {stage.completed ? (

                            <CheckCircle2
                                className="h-5 w-5 text-green-600"
                            />

                        ) : stage.active ? (

                            <Loader2
                                className="h-5 w-5 animate-spin text-blue-600"
                            />

                        ) : (

                            <div
                                className="h-5 w-5 rounded-full border"
                            />

                        )}

                        <span
                            className={
                                stage.completed
                                    ? "text-gray-900"
                                    : stage.active
                                    ? "font-medium"
                                    : "text-gray-400"
                            }
                        >
                            {stage.label}
                        </span>

                    </div>

                ))}

            </div>

        </div>
    );

}