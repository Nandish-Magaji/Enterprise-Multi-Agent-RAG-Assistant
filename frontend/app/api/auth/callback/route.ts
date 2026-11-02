import { handleSignIn } from "@logto/next/server-actions";
import { redirect } from "next/navigation";
import { logtoConfig } from "@/app/logto";

function isNextRedirect(error: unknown): boolean {
  return Boolean(
    error &&
      typeof error === "object" &&
      "digest" in error &&
      typeof error.digest === "string" &&
      error.digest.startsWith("NEXT_REDIRECT"),
  );
}

export async function GET(request: Request) {
  try {
    await handleSignIn(logtoConfig, new URL(request.url));
  } catch (error) {
    // Logto completes a successful callback by throwing Next.js's internal
    // redirect sentinel. It must pass through or the app starts login again.
    if (isNextRedirect(error)) {
      throw error;
    }

    // A direct, stale, or duplicated callback must restart authentication,
    // not surface Logto's sign_in_session.not_found as a server error.
    console.warn("Logto callback could not be completed; restarting sign-in.", error);
    redirect("/api/auth/sign-in?reason=session-expired");
  }
  redirect("/");
}
