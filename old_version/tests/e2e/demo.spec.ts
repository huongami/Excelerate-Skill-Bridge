import { test, expect } from "@playwright/test";

test("human-centred demo flow", async ({ page }) => {
  await page.goto("/profile");
  await page.getByRole("button", { name: "Parse profile" }).click();
  await expect(page.getByText("Operations Team Lead")).toBeVisible();
  await page.getByRole("button", { name: /Confirm and translate/ }).click();
  await expect(page).toHaveURL(/\/skills/);
  await expect(page.getByText("No overall candidate score")).toBeVisible();
  await page.getByRole("link", { name: /Match one job description/ }).click();
  await page.getByRole("button", { name: "Parse & map JD skills" }).click();
  await expect(page.getByText(/skills · 100%/)).toBeVisible();
  await page.getByRole("button", { name: /Create per-skill candidate match/ }).click();
  await expect(page.getByText("No overall candidate score")).toBeVisible();
  await page.getByRole("button", { name: "Needs more info" }).click();
  await expect(page.getByText(/needs more info/i)).toBeVisible();
});

test("HR can parse a JD before a candidate exists", async ({ page }) => {
  await page.goto("/review");
  await expect(page.getByRole("heading", { name: "1. Job description input" })).toBeVisible();
  await expect(page.getByText("JD analysis is available now.")).toBeVisible();
  await page.getByRole("button", { name: "Parse & map JD skills" }).click();
  await expect(page.getByText(/skills · 100%/)).toBeVisible();
  await expect(page.getByRole("button", { name: /Create per-skill candidate match/ })).toBeDisabled();
});
