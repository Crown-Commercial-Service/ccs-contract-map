import type { APIRequestContext, APIResponse } from '@playwright/test';

// Hardcode your local FastAPI endpoint directly
const LOCAL_URL = 'http://localhost:5000/v0.2.0/map';

export async function postDescription(
  request: APIRequestContext,
  description: string
): Promise<APIResponse> {

  console.log(` Sending request to local backend: ${LOCAL_URL}`);

  return request.post(LOCAL_URL, {
    headers: {
      'Content-Type': 'application/json'
    },
    data: { description },
  });
}