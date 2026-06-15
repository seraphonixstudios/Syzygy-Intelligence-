import { describe, it, expect } from "vitest";

describe("config", () => {
  it("API_URL defaults to localhost:8000", async () => {
    const { API_URL } = await import("./config");
    expect(API_URL).toBe("http://localhost:8000");
  });

  it("WS_URL defaults to ws://localhost:8000/ws", async () => {
    const { WS_URL } = await import("./config");
    expect(WS_URL).toBe("ws://localhost:8000/ws");
  });
});
