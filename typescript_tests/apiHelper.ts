import type { APIRequestContext, APIResponse } from '@playwright/test';

// Hardcode your local FastAPI endpoint directly
const API_VERSION_PATH = '/v0.2.0/map';

export async function postDescription(
  request: APIRequestContext,
  description: string
): Promise<APIResponse> {


    return request.post(API_VERSION_PATH, {
        headers: {
          'Content-Type': 'application/json'
        },
        data: { description },
      });
}