import { redirect } from "next/navigation";

import { getLogtoContext } from "@logto/next/server-actions";
import Workspace from "./Workspace";
import { logtoConfig } from "./logto";

export const dynamic = "force-dynamic";

export default async function Page() {
  const { isAuthenticated } = await getLogtoContext(logtoConfig);
  if (!isAuthenticated) redirect("/api/auth/sign-in");
  return <Workspace />;
}
