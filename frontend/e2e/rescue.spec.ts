import { test, expect } from "@playwright/test";

test("source, recover, approve and cancel a real inventory reservation", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "A little less last-minute." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Start a rescue" }).click();
  await page.getByLabel("Request name").fill("Browser recovery test");
  await page.getByRole("button", { name: "Find my rescue plan" }).click();
  await expect(
    page.getByRole("heading", { name: "Your rescue options" }),
  ).toBeVisible();
  const reference = await page.locator(".quote-meta>span").first().innerText();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Supplier network", exact: true })
    .click();
  const campus = page
    .locator(".supplier-card")
    .filter({ hasText: "Campus Paper Co." });
  await campus.getByRole("button", { name: "Pause new orders" }).click();
  await expect(campus.getByText("Paused", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Rescue requests", exact: true })
    .click();
  await page
    .getByRole("button", { name: `Review ${reference}`, exact: true })
    .click();
  await page.getByRole("button", { name: "Confirm selected plan" }).click();
  await expect(page.getByText(/changed availability/)).toBeVisible();
  await page.getByRole("button", { name: "Confirm selected plan" }).click();
  await expect(
    page.getByRole("heading", { name: "Your backup plan is in place." }),
  ).toBeVisible();
  const order = await page.locator(".receipt-number strong").innerText();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Orders & receipts", exact: true })
    .click();
  const orderCard = page.locator(".order-card").filter({ hasText: order });
  await orderCard
    .getByRole("button", { name: "Cancel & release inventory" })
    .click();
  await page.getByRole("button", { name: "Cancel order", exact: true }).click();
  await expect(orderCard.getByText("Cancelled", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Supplier network", exact: true })
    .click();
  await campus.getByRole("button", { name: "Resume new orders" }).click();
});

test("mobile navigation and request form fit the viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "A little less last-minute." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Start a rescue" }).click();
  await expect(page.getByLabel("Maximum budget (₹)")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(
    page.getByRole("heading", { name: "A little less last-minute." }),
  ).toBeVisible();
});
