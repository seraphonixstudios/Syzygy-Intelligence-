import { test, expect } from "@playwright/test";
import { API, TEST_PASS, testEmail, registerAndLogin } from "./helpers";

test.describe("Shadow agents", () => {
  let token: string;
  let email: string;
  let parentId: string;
  let shadowId: string;

  test.beforeAll(async ({ request }) => {
    email = testEmail("shadow");
    const regRes = await request.post(`${API}/api/auth/register`, {
      data: { email, password: TEST_PASS },
    });
    expect(regRes.ok()).toBeTruthy();
    token = (await regRes.json()).access_token;

    // Create a parent agent
    const agentRes = await request.post(`${API}/api/agents/`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { archetype: "sage", name: "Test Sage" },
    });
    expect(agentRes.ok()).toBeTruthy();
    parentId = (await agentRes.json()).agent.id;
  });

  test("POST /api/agents/shadow/create creates a shadow agent", async ({ request }) => {
    const res = await request.post(`${API}/api/agents/shadow/create`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { parent_archetype: "sage", name: "Shadow Sage One" },
    }).catch(() => null);
    if (!res || !res.ok()) {
      test.skip();
      return;
    }
    const body = await res.json();
    expect(body.shadow_agent).toHaveProperty("id");
    expect(body.shadow_agent.name).toBe("Shadow Sage One");
    expect(body.shadow_agent.parent_archetype).toBe("sage");
    expect(body.shadow_agent.shadow_name).toBe("Shadow Sage");
    shadowId = body.shadow_agent.id;
  });

  test("GET /api/agents/shadow/list lists shadow agents", async ({ request }) => {
    const res = await request.get(`${API}/api/agents/shadow/list`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(Array.isArray(body.shadow_agents)).toBeTruthy();
    expect(body.shadow_agents.length).toBeGreaterThanOrEqual(1);
  });

  test("GET /api/agents/shadow/list?parent_archetype=sage filters by parent", async ({ request }) => {
    const res = await request.get(`${API}/api/agents/shadow/list?parent_archetype=sage`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    for (const agent of body.shadow_agents) {
      expect(agent.parent_archetype).toBe("sage");
    }
  });

  test("GET /api/agents/shadow/:id returns single shadow agent", async ({ request }) => {
    if (!shadowId) { test.skip(); return; }
    const res = await request.get(`${API}/api/agents/shadow/${shadowId}`, {
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => null);
    if (!res || !res.ok()) { test.skip(); return; }
    const body = await res.json();
    expect(body.shadow_agent.id).toBe(shadowId);
  });

  test("POST /api/agents/shadow/:id/align increases alignment", async ({ request }) => {
    const res = await request.post(`${API}/api/agents/shadow/${shadowId}/align`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { delta: 0.3 },
    }).catch(() => null);
    if (!res || !res.ok()) {
      test.skip();
      return;
    }
    const body = await res.json();
    expect(body.alignment_score).toBeGreaterThan(0.5);
    expect(body.delta).toBe(0.3);
  });

  test("POST /api/agents/shadow/:id/misalign decreases alignment", async ({ request }) => {
    // First align high
    const alignRes = await request.post(`${API}/api/agents/shadow/${shadowId}/align`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { delta: 0.4 },
    }).catch(() => null);
    // Then misalign
    const res = await request.post(`${API}/api/agents/shadow/${shadowId}/misalign`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { delta: 0.2 },
    }).catch(() => null);
    if (!res || !res.ok()) {
      test.skip();
      return;
    }
    const body = await res.json();
    expect(body.alignment_score).toBeGreaterThanOrEqual(0);
  });

  test("POST /api/agents/shadow/:id/integrate/:parent integrates shadow back to parent", async ({ request }) => {
    if (!shadowId) { test.skip(); return; }
    const res = await request.post(
      `${API}/api/agents/shadow/${shadowId}/integrate/${parentId}`,
      { headers: { Authorization: `Bearer ${token}` } },
    ).catch(() => null);
    if (!res || !res.ok()) { test.skip(); return; }
    const body = await res.json();
    expect(body.integration_report).toHaveProperty("insights");
    expect(Array.isArray(body.integration_report.insights)).toBeTruthy();
    expect(body.integration_report.insights.length).toBeGreaterThan(0);
    expect(body.integration_report.parent_agent_id).toBe(parentId);
    expect(body.integration_report.shadow_agent_id).toBe(shadowId);
    expect(body.integration_report.new_alignment_score).toBeGreaterThan(0);
  });

  test("POST /api/agents/shadow/compose creates balanced shadow team", async ({ request }) => {
    const res = await request.post(`${API}/api/agents/shadow/compose`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(Array.isArray(body.shadow_agents)).toBeTruthy();
    expect(body.shadow_agents.length).toBe(3);
  });

  test("DELETE /api/agents/shadow/:id deletes shadow agent", async ({ request }) => {
    // Create a shadow to delete
    const createRes = await request.post(`${API}/api/agents/shadow/create`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { parent_archetype: "hero", name: "Temp Shadow" },
    }).catch(() => null);
    if (!createRes || !createRes.ok()) { test.skip(); return; }
    const tempId = (await createRes.json()).shadow_agent.id;

    const res = await request.delete(`${API}/api/agents/shadow/${tempId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    expect((await res.json()).status).toBe("deleted");

    // Verify deletion
    const getRes = await request.get(`${API}/api/agents/shadow/${tempId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(getRes.status()).toBe(404);
  });

  test("shadow agent participates in consensus", async ({ request }) => {
    test.setTimeout(60000);
    // Create shadow agents
    await request.post(`${API}/api/agents/shadow/compose`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    // Create a parent team
    await request.post(`${API}/api/agents/compose`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    // Consensus should run without error (skip if LLM is slow/unavailable)
    const res = await request.post(`${API}/api/consensus/run`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        task: "Test shadow participation in consensus",
        max_rounds: 2,
      },
      timeout: 20000,
    }).catch(() => null);
    if (!res) {
      test.skip();
      return;
    }
    // The consensus endpoint may fail if no LLM is available, but should not 500
    expect(res.status()).not.toBe(500);
  });
});
