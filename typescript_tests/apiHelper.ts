import type { APIRequestContext, APIResponse } from '@playwright/test';
import dotenv from 'dotenv';
dotenv.config();


const APIM_URL = process.env.APIM_URL;
const APIM_SUBSCRIPTION_KEY = process.env.APIM_SUBSCRIPTION_KEY;

if (!APIM_URL || !APIM_SUBSCRIPTION_KEY) {
  console.error('Error: APIM_URL and APIM_SUBSCRIPTION_KEY must be set in the environment variables.');
  process.exit(1);
}

export async function postDescription(
  request: APIRequestContext,
  description: string
): Promise<APIResponse> {
  return request.post(`${APIM_URL}`, {
     headers: {
      'Ocp-Apim-Subscription-Key': `${APIM_SUBSCRIPTION_KEY}`,
      'Content-Type': 'application/json'
    },
    data: { description },
  });
}

