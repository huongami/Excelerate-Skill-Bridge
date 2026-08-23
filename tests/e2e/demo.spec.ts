import { test, expect } from "@playwright/test";

test("human-centred demo flow", async ({ page }) => {
  await page.goto("/profile");
  await page.getByRole("button", { name: "Parse profile" }).click();
  await expect(page.getByText("Product Owner")).toBeVisible();
  await page.getByRole("button", { name: /Confirm and translate/ }).click();
  await expect(page).toHaveURL(/\/skills/);
  await expect(page.getByText("No overall candidate score")).toBeVisible();
  await page.getByRole("link", { name: /Match one job description/ }).click();
  await page.getByRole("button", { name: "Create per-skill match" }).click();
  await expect(page.getByText("No overall candidate score")).toBeVisible();
  await page.getByRole("button", { name: "Needs more info" }).click();
  await expect(page.getByText(/needs more info/i)).toBeVisible();
});
