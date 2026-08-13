import { CheckCircle, AlertTriangle } from "lucide-react";
import { VerificationReport } from "@/types/workflow";

interface Props {
    verification: VerificationReport;
}

export default function StatusBadge({
    verification,
}: Props) {

    const passed = verification.verdict === "PASS";

    return (
        <span
            className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium ${
                passed
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-amber-50 text-amber-800"
            }`}
        >
            {passed
                ? <CheckCircle size={14} />
                : <AlertTriangle size={14} />
            }

            {passed ? "Verified" : "Needs Review"}
        </span>
    );
}
