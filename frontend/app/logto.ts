import type { LogtoNextConfig } from "@logto/next";

function required(name: string): string {
  return process.env[name] || "";
}

export const logtoConfig: LogtoNextConfig = {
  appId: required("LOGTO_APP_ID"),
  appSecret: required("LOGTO_APP_SECRET"),
  endpoint: required("LOGTO_ENDPOINT"),
  baseUrl: required("LOGTO_BASE_URL"),
  cookieSecret: required("LOGTO_COOKIE_SECRET"),
  cookieSecure: process.env.NODE_ENV === "production",
  resources: [required("LOGTO_API_RESOURCE")],
};
