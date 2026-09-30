import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { adminApi, setAuthSession, clearAuthSession } from "./api";

function respond(body, ok = true) {
  return { ok, json: async () => body };
}

describe("adminApi", () => {
  beforeEach(() => setAuthSession("test-token", "shalini", "admin"));
  afterEach(() => clearAuthSession());

  it("sends a PATCH with the Authorization header and JSON body", async () => {
    globalThis.fetch = vi.fn(() => Promise.resolve(respond({ review_status: "APPROVED" })));
    await adminApi.patch("/api/admin/linkedin/activities/LI-00001", { review_status: "APPROVED", _note: "ok" });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/admin/linkedin/activities/LI-00001",
      expect.objectContaining({
        method: "PATCH",
        headers: expect.objectContaining({ Authorization: "Bearer test-token" }),
      }),
    );
    const options = globalThis.fetch.mock.calls[0][1];
    expect(JSON.parse(options.body)).toEqual({ review_status: "APPROVED", _note: "ok" });
  });

  it("attaches the auth header to GET requests", async () => {
    globalThis.fetch = vi.fn(() => Promise.resolve(respond({ ok: true })));
    await adminApi.get("/api/admin/linkedin/summary");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/admin/linkedin/summary",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer test-token" }),
      }),
    );
  });

  it("surfaces the server error detail on a failed PATCH", async () => {
    globalThis.fetch = vi.fn(() => Promise.resolve(respond({ error: "invalid status" }, false)));
    await expect(adminApi.patch("/api/admin/linkedin/activities/LI-00001", { reportable_status: "NOPE" }))
      .rejects.toThrow("invalid status");
  });
});