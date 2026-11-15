import { test, expect } from "@playwright/test";

test("selecting and moving devices preserves a calculated route; deletion clears endpoints", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toContainText("PC-A → R1 → PC-B");
  const node = page.locator(".react-flow__node").filter({ hasText: "PC-A" });
  await node.click();
  await expect(page.locator(".route-result")).toBeVisible();
  const box = await node.boundingBox();
  await page.mouse.move(box!.x + 40, box!.y + 30);
  await page.mouse.down();
  await page.mouse.move(box!.x + 65, box!.y + 60, { steps: 5 });
  await page.mouse.up();
  await expect(page.locator(".route-result")).toBeVisible();
  await page.getByRole("button", { name: "Delete device" }).click();
  await expect(page.getByLabel("Source device")).toHaveValue("");
  await expect(
    page.getByRole("button", { name: "Calculate shortest path" }),
  ).toBeDisabled();
});

test("fractional and zero link costs can be entered, invalid drafts restore prior value", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .locator(".react-flow__edge")
    .first()
    .locator(".react-flow__edge-textwrapper")
    .click();
  const input = page.getByLabel("Link cost");
  await input.fill("");
  await input.pressSequentially("0.25");
  await input.press("Tab");
  await expect(input).toHaveValue("0.25");
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toContainText("1.25");
  await input.fill("-2");
  await input.press("Tab");
  await expect(input).toHaveValue("0.25");
  await input.fill("0");
  await input.press("Tab");
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toContainText("Total cost 1");
});

test("malformed saved topology is rejected without breaking the canvas", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  for (const value of [
    null,
    { nodes: [null], edges: [] },
    { nodes: [], edges: [null] },
    { nodes: [], edges: [], source: {} },
  ]) {
    await page.evaluate(
      (v) => localStorage.setItem("netsim-topology", JSON.stringify(v)),
      value,
    );
    await page.getByRole("button", { name: "Load", exact: true }).click();
  }
  expect(errors).toEqual([]);
  // A well-formed empty topology is allowed, and disables route controls.
  await expect(
    page.getByRole("button", { name: "Send packet" }),
  ).toBeDisabled();
});

test("slow subnet responses cannot overwrite newer input", async ({ page }) => {
  await page.goto("/");
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/subnet", async (route) => {
    await gate;
    await route.fulfill({
      json: { network: "192.168.1.0", broadcast: "192.168.1.63" },
    });
  });
  await page
    .getByRole("button", { name: "Subnet calculator", exact: true })
    .click();
  await page.getByRole("button", { name: "Calculate subnet" }).click();
  await page.getByLabel("IPv4 address / prefix").fill("10.0.0.1/24");
  release();
  await expect(page.locator(".subnet-results")).not.toContainText(
    "192.168.1.63",
  );
  await expect(
    page.getByRole("button", { name: "Calculate subnet" }),
  ).toBeEnabled();
});

test("failed route request clears old route and shows an actionable error", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toBeVisible();
  await page.route("**/api/route", (route) =>
    route.fulfill({ status: 503, body: "Service unavailable" }),
  );
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toHaveCount(0);
  await expect(page.locator(".log-lines")).toContainText(
    "Check that it is running on port 8000",
  );
});

test("same-device transmission records creation and delivery", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Destination device").selectOption("PC-A");
  await page.getByRole("button", { name: "Send packet" }).click();
  await expect(page.locator(".log-lines")).toContainText(
    "Packet created at PC-A",
  );
  await expect(page.locator(".log-lines")).toContainText(
    "Packet delivered to PC-A",
  );
  await expect(page.locator(".route-result")).toContainText("Total cost 0");
});

test("device ports create bidirectional links and prevent duplicate links", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .locator(".react-flow__edge")
    .first()
    .locator(".react-flow__edge-textwrapper")
    .click();
  await page.getByRole("button", { name: "Delete link" }).click();
  await expect(page.locator(".react-flow__edge")).toHaveCount(3);
  const start = page.locator('[data-id="PC-A"] .react-flow__handle-right');
  const end = page.locator('[data-id="R1"] .react-flow__handle-left');
  const link = async () => {
    const a = await start.boundingBox(),
      b = await end.boundingBox();
    await page.mouse.move(a!.x + a!.width / 2, a!.y + a!.height / 2);
    await page.mouse.down();
    await page.mouse.move(b!.x + b!.width / 2, b!.y + b!.height / 2, {
      steps: 10,
    });
    await page.mouse.up();
  };
  await link();
  await expect(page.locator(".react-flow__edge")).toHaveCount(4);
  await link();
  await expect(page.locator(".react-flow__edge")).toHaveCount(4);
  await page.getByLabel("Source device").selectOption("PC-B");
  await page.getByLabel("Destination device").selectOption("PC-A");
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toContainText("PC-B → R1 → PC-A");
});
