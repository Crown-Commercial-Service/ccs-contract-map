import { test, expect } from "@playwright/test";
import { postDescription } from "./apiHelper";

// Non-Functional test
test("parallel test @load", async ({ request }) => {
  const total_requests = 100;
  console.log(`Sending ${total_requests} to APIM`);

  const tasks = Array.from({ length: total_requests }).map(async (_, i) => {
    return postDescription(request, `Test load ${i}`);
  });
  // fire all requests all at the same time
  const responses = await Promise.all(tasks);

  // collect status code
  const statuses = responses.map((res) => res.status());

  // Count the results
  const successCount = statuses.filter((s) => s === 200).length;

  console.log("------------------------------------");
  console.log(`✅ Success (200): ${successCount}`);


  expect(successCount, "total parallel request").toBe(total_requests);
});
