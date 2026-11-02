import { signIn } from "@logto/next/server-actions";
import { logtoConfig } from "@/app/logto";

export async function GET() {
  await signIn(logtoConfig, {
    redirectUri: `${logtoConfig.baseUrl}/api/auth/callback`,
    postRedirectUri: logtoConfig.baseUrl,
  });
}
