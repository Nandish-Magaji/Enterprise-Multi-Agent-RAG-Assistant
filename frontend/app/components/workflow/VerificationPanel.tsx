"use client";

import DocumentRenderer from "../markdown/DocumentRenderer";
import { VerificationReport } from "@/types/workflow";

interface Props {
    verification: VerificationReport;
}

export default function VerificationPanel({
    verification,
}: Props) {

    if (!verification.reasoning) {

        return null;

    }

    return (

        <details className="rounded-xl border border-zinc-200">

            <summary className="cursor-pointer px-4 py-3 font-medium">

                Verification Details

            </summary>

            <div className="border-t p-4">

                <DocumentRenderer
                    content={verification.reasoning ?? ""}
                />

            </div>

        </details>

    );

}