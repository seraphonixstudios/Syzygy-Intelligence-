import { describe, it, expect, vi, beforeEach } from "vitest";
import { logger } from "./logger";

describe("logger", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("subscribes listeners and calls them on log", () => {
    const fn = vi.fn();
    const unsub = logger.subscribe(fn);
    logger.info("test message");
    expect(fn).toHaveBeenCalled();
    const entry = fn.mock.calls[0][0];
    expect(entry.message).toBe("test message");
    expect(entry.level).toBe("info");
    unsub();
  });

  it("unsubscribe removes listener", () => {
    const fn = vi.fn();
    const unsub = logger.subscribe(fn);
    unsub();
    logger.info("after unsub");
    expect(fn).not.toHaveBeenCalled();
  });

  it("calls console.debug for debug", () => {
    const spy = vi.spyOn(console, "debug").mockImplementation(() => {});
    logger.debug("debug msg");
    expect(spy).toHaveBeenCalled();
  });

  it("calls console.error for error", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    logger.error("error msg");
    expect(spy).toHaveBeenCalled();
  });

  it("includes source in log prefix", () => {
    const spy = vi.spyOn(console, "info").mockImplementation(() => {});
    logger.info("msg", undefined, "TestSource");
    expect(spy.mock.calls[0][0]).toContain("TestSource");
  });
});
