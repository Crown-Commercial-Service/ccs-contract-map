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

| Standard                                  | Status          | Implementation Details                                                                                                                                                                          |
|:------------------------------------------|:----------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Use UTF-8 for encoding**                | **Implemented** | The FastAPI framework and Azure hosting environment serve all text and JSON using the UTF-8 standard.                                                                                           |
| **Use uniform interface**                 | **Implemented** | All requests go to the `map` route, no other route is used.                                                                                                                                     |
| **Client and Server must be independent** | **Implemented** | JSON data are returned instead of formatted web pages, it is independent of any front end.                                                                                                      |
| **Use statelessness**                     | **Implemented** | No data is saved to be used in later functionality, every request is independant.                                                                                                               |
| **Use caching**                           | **N/A**         | **Subticket Required:** FastAPI post method is used to get AI model to label contract, however using GET method to get caching will be used for caching identical contract descriptions to reduce AI processing costs. |
| **Layered system capability**             | **Implemented** | allows firewalls and gateway between the client and server.                                                                                                                                     |
| **Use JSON for response formats**         | **Implemented** | The `responses` key in the specification defines `application/json` as the standard interchange format.                                                                                         |
| **Consistent names for resources**        | **Implemented** | Internal naming conventions (e.g., `operationId: run_contract_mapper_map_post`) are consistent and descriptive.                                                                                 |
| **Use standard HTTP responses**           | **Implemented** | The API uses `200` for successful processing and `422` for validation errors.                                                                                                                   |
| **Validate all inputs**                   | **Implemented** | The `requestBody` utilizes the `ContractDescription` schema to enforce that a `description` string is present before processing.                                                                |

## 3. Secure Your API

| Standard | Status | Implementation Details |
| :--- | :--- | :--- |
| **Use TLS 1.2 or above** | **Implemented** | Handled via Azure App Service configuration to ensure all traffic is encrypted over HTTPS. |
| **OAuth 2.0 Authorization** | **Not yet implemented** | **Subticket Required:** The current API does not yet define a security scheme for identity management. |
| **Restrict HTTP Verbs** | **Implemented** | The `/map` resource only accepts `POST` requests. Other methods (GET, DELETE, etc.) are disabled. |
| **CORS Headers** | **Placeholder** | Configuration of `CORSMiddleware` in FastAPI to be audited against GOV.UK security standards. |

## 4. Operate Your API

| Standard | Status | Implementation Details |
| :--- | :--- | :--- |
| **Version your API** | **Not yet implemented** | **Subticket Required:** Current pathing does not include versioning (e.g., `/v1/map`). |
| **API Test Service (Sandbox)** | **Not yet implemented** | **Subticket Required:** A dedicated staging environment for external developer testing is not yet available. |

---

## Required Subtickets

The following items have been identified for development to achieve full compliance with the GOV.UK API Catalogue requirements:

1. **[FEATURE] Implement OAuth 2.0 / JWT Authentication**
   * *Requirement:* Move away from anonymous endpoints to meet "Secure by Design" standards for sensitive contract data.
2. **[FEATURE] API Versioning (URI Versioning)**
   * *Requirement:* Refactor endpoint from `/map` to `/v1/map` to ensure backward compatibility for future updates.
3. **[TASK] Rate Limiting and Throttling Configuration**
   * *Requirement:* Implement policies to prevent resource exhaustion and ensure high availability across government services.
4. **[TASK] API Management Integration**
   * *Requirement:* Ensure the API is discoverable by registering it with the internal and cross-government UK API Catalogues.