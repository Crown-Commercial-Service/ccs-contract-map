import { test, expect } from '@playwright/test';
import dotenv from 'dotenv';

// Load the .env file
dotenv.config();

// Functional test
test("checking if model produces expected output @accuracy", async({request})=>{

    const url = process.env.APIM_URL;
    const key = process.env.APIM_SUBSCRIPTION_KEY;
     const example_description: Record<string, string> = {
         "Scalable file and block storage solution." : "Cloud and Hosting",
         "University of Birmingham WebCenter Upgrade on OCI SOW Rev5, as per SSA process.": "Cloud and Hosting",
         "UKRI STFC Estates appointed a supplier to provide Chilbolton Antenna Cabin Improvements.": "Construction",
         "This Statement of Requirement (SoR) defines the requirement to procure, deliver, and install a temporary structural solution in the vicinity of Car Park as part of the Submarine Maintenance Recovery Plan (SMRP). The temporary structure shall consist of eight (8) ISO containers integrated with a canopy system to provide a covered and secure working environment.":"Construction",
        "The term of this contract shall be 1 year: call - off under the HealthTrust Europe LLP Enterprise Level ICT Digital Technology Solutions 2023 F W, ref 2023 S 000-007857": "Digital and Technology Services",
        "The NHS National Services Scotland (NSS) Technology Services team has appointed a supplier to maximise the potential functionality of the WMS Dispatcher system.": "Digital and Technology Services",
        "Destruction shredding of ICT hardware" : "Hardware",
      "Replacement CCTV servers": "Hardware"
         };
     //loop over example_description and apply requests
     const results: string[] = [];
     const expectedValues = Object.values(example_description);

    for (const dict_key of Object.keys(example_description)) {
            console.log(`Testing: ${dict_key}`);

            const response = await request.post(url, {
                headers: {
                    'Ocp-Apim-Subscription-Key': key,
                    'Content-Type': 'application/json'
                },
                data: { description: dict_key }
            });

            const body = await response.json();
            console.log("body",body);
            // Storing the specific AI_label string in our results list
            results.push(body.AI_label);
        }
    console.log("Expected:", expectedValues);
    console.log("Actual:  ", results);


    // Using JSON.stringify for a strict order-based comparison
    expect(JSON.stringify(results), "The AI labels should match the expected categories in order and be correct")
        .toBe(JSON.stringify(expectedValues));

    });