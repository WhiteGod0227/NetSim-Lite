import { test, expect } from "@playwright/test";
test("routing, delivery, failures, persistence and subnetting", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByText("Backend connected")).toBeVisible();
  await page.getByRole("button", { name: "Send packet" }).click();
  await expect(page.locator(".route-result")).toContainText("PC-A → R1 → PC-B");
  await expect(page.locator(".log-lines")).toContainText(
    "Packet delivered to PC-B",
  );
  await expect(page.getByRole("button", { name: "Send packet" })).toBeEnabled();
  // Click a link label to inspect and disable the primary route.
  await page
    .locator(".react-flow__edge")
    .first()
    .locator(".react-flow__edge-textwrapper")
    .click();
  await page.getByLabel("Link enabled").uncheck();
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toContainText("PC-A → R2 → PC-B");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page.getByRole("button", { name: "Reset to demo" }).click();
  await page.getByRole("button", { name: "Load", exact: true }).click();
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toContainText("PC-A → R2 → PC-B");
  await page
    .locator(".react-flow__edge")
    .nth(2)
    .locator(".react-flow__edge-textwrapper")
    .click();
  await page.getByLabel("Link enabled").uncheck();
  await page.getByRole("button", { name: "Calculate shortest path" }).click();
  await expect(page.locator(".route-result")).toContainText(
    "Destination unreachable",
  );
  await page
    .getByRole("button", { name: "Subnet calculator", exact: true })
    .click();
  await page.getByRole("button", { name: "Calculate subnet" }).click();
  await expect(page.locator(".subnet-results")).toContainText("192.168.1.63");
  await expect(page.locator(".subnet-results")).toContainText(
    "255.255.255.192",
  );
  await page.getByLabel("IPv4 address / prefix").fill("invalid");
  await page.getByRole("button", { name: "Calculate subnet" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  expect(errors).toEqual([]);
});
test("device creation, editing and deletion", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Switch Connect devices" }).click();
  await page.getByLabel("Device name").fill("Lab switch");
  await expect(
    page.locator(".device").filter({ hasText: "Lab switch" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Delete device" }).click();
  await expect(
    page.locator(".device").filter({ hasText: "Lab switch" }),
  ).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});
