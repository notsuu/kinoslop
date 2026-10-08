/*
    basic proxy for the Telegram API. deploy this to a Cloudflare worker
    and configure environment variables:
    - PROXY_AUTH_BYPASS: "1" to disable authentication, anything else to keep it on
    - PROXY_AUTH_KEY: a secret key to authenticate the script
    - TELEGRAM_SERVER: actual API server, usually "https://api.telegram.org"
*/

function proxyError(description, status = 500) {
  return Response.json({ok: false, proxy_error: true, description}, {status});
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return proxyError("Method not allowed", 405);

    const key = request.headers.get("X-Proxy-Auth");
    if (env.PROXY_AUTH_BYPASS !== "1" && key !== env.PROXY_AUTH_KEY)
      return proxyError("Invalid auth key", 407);

    const url = new URL(request.url);
    const body = await request.text();
    if (url.pathname === "/") return proxyError("API method required", 400);

    try {
      return await globalThis.fetch(env.TELEGRAM_SERVER + url.pathname, {
        body,
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=utf-8"
        }
      });
    } catch (e) {
      console.error(e);
      return proxyError("API request failed", 502);
    }
  }
};