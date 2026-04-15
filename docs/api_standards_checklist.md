# API Standards Checklist: Contract Mapper

This document assesses the Contract Mapper API against the [GOV.UK API technical and data standards](https://www.gov.uk/guidance/api-technical-and-data-standards).

---

## 1. Design Your API

| Standard                          | Status | Implementation Details                                                                                                                                                                                                    |
|:----------------------------------| :--- |:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Gather user needs**           | **Implemented** | Users need a tool that can map contracts to GCA mapping for data analysis and data visibilty.                                                                                                                             |
| **Use the REST API style**        | **Implemented** | The API utilises the REST architectural style due to using FastAPI, employing standard HTTP methods (`POST`) and resource-based URL paths (`/map`).                                                                       |
| **Design your API first**         | **Implemented** | An OpenAPI 3.1.0 specification was generated as the primary output of the design process to label contracts.                                                                                                              |
| **Use the OpenAPI Specification** | **Implemented** | The service provides a machine-readable `openapi.json` file, this is found [here](https://crowncommercialservice.atlassian.net/wiki/spaces/CAT1/pages/5379915786/OpenApi+Json+Design), allowing for automated documentation via Swagger UI, this is found [here](https://azt-contract-mapping-8645.azurewebsites.net/docs). |
| **Follow ISO 8601 for dates**     | **N/A** | Current data models do not handle date/time fields. Any future date fields must follow YYYY-MM-DD format.                                                                                                                 |

## 2. Build Your API

| Standard                                  | Status                           | Implementation Details                                                                                                                                                                          |
|:------------------------------------------|:---------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Use UTF-8 for encoding**                | **Implemented**                  | The FastAPI framework and Azure hosting environment serve all text and JSON using the UTF-8 standard.                                                                                           |
| **Use uniform interface**                 | **Implemented**                  | All requests go to the `map` route, no other route is used.                                                                                                                                     |
| **Client and Server must be independent** | **Implemented**                  | JSON data are returned instead of formatted web pages, it is independent of any front end.                                                                                                      |
| **Use statelessness**                     | **Implemented**                  | No data is saved to be used in later functionality, every request is independant.                                                                                                               |
| **Use caching**                           | **Not yet implemented**          | **Subticket Required:** FastAPI post method is used to get AI model to label contract, however using GET method to get caching will be used for caching identical contract descriptions to reduce AI processing costs. |
| **Layered system capability**             | **Implemented**                  | allows firewalls and gateway between the client and server.                                                                                                                                     |
| **Use JSON for response formats**         | **Implemented**                  | The `responses` key in the specification defines `application/json` as the standard interchange format.                                                                                         |
| **Consistent names for resources**        | **Implemented**                  | Internal naming conventions (e.g., `operationId: run_contract_mapper_map_post`) are consistent and descriptive.                                                                                 |
| **Use standard HTTP responses**           | **Implemented**                  | The API uses `200` for successful processing and `422` for validation errors.                                                                                                                   |
| **Validate all inputs**                   | **Implemented**                  | The `requestBody` utilizes the `ContractDescription` schema to enforce that a `description` string is present before processing.                                                                |

## 3. Secure Your API

| Standard                          | Status                  | Implementation Details                                                                                                                          |
|:----------------------------------|:------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------|
| **Use TLS 1.2 or above**          | **Implemented**         | Handled via Azure App Service configuration to ensure all traffic is encrypted over HTTPS.                                                      |
| **OAuth 2.0 Authorization**       | **Not yet implemented** | **Subticket Required:** The current API does not yet define a security scheme for identity management.                                          |
| **Restrict HTTP Verbs**           | **Implemented**         | The `/map` resource only accepts `POST` requests. Other methods (GET, DELETE, etc.) are disabled.                                               |
| **CORS Headers**                  | **Not yet implemented** | **Subticket Required:**   will be handled via APIM in the policy.xml but will need to investigate what websites will connect to the API(if any) |
| **Data and Application security** | **Implemented**         | Virtual network and white listing is used to make sure only authorised users can use API                                                        |
| **Auditing**                      | **Implemented**         | Azure already shows API usage.                                                                                                                  |

## 4. Operate Your API

| Standard | Status | Implementation Details                                                                                                            |
| :--- | :--- |:----------------------------------------------------------------------------------------------------------------------------------|
| **Version your API** | **Not yet implemented** | **Subticket Required:** Current pathing does not include versioning (e.g., `/v1/map`).                                            |
| **API Test Service (Sandbox)** | **Not yet implemented** | **Subticket Required:** A dedicated staging environment for external developer testing is not yet available. Can be using postman |

---

## Required Subtickets

1. **[TASK] Configure APIM Security Policy (OAuth 2.0 / JWT)**
   * *Requirement:* Implement a `validate-jwt` policy in the APIM `policy.xml` to move away from anonymous access and meet GOV.UK security mandates.
2. **[TASK] Standardize Internal Error Responses (HTTP 500)**
   * *Requirement:* Refactor the Python `try/except` block to raise a FastAPI `HTTPException` with a `500` status code. Returning an error message with a `200` status is non-compliant.
3. **[FEATURE] API URI Versioning (v1)**
   * *Requirement:* Update the endpoint path to `/v1/map` to ensure backward compatibility and follow government URI standards.
4. **[TASK] Implement APIM CORS Policy**
   * *Requirement:* Configure the APIM gateway to whitelist specific government domains, ensuring secure browser-based integration.
5. **[TASK] Develop Postman Testing Suite**
   * *Requirement:* Create a Postman Collection and Environment file that includes tests for success (200), validation errors (422), and authentication failure (401). This will serve as the primary "Test Service" for developers.
6. **[FEATURE] Caching Strategy for AI Inference**
   * *Requirement:* Implement a caching layer to store results for identical contract descriptions, reducing redundant AI processing and Azure compute costs.
7. **[TASK] Register with API Catalogue**
   * *Requirement:* Ensure the Contract Mapper metadata is added to the relevant internal and cross-government API catalogues for discoverability.rement:* Implement a caching layer to store results for identical contract descriptions, reducing redundant AI processing and Azure compute costs.