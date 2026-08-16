**Task:** Enhance the "Author" field in Wikimedia Commons Wikitext files using Our World in Data metadata.

**Goal:**
Update the `|author=` line in the wikitext of files uploaded from "Our World in Data (OWID)" to include full attribution details (original data provider + OWID processing), rather than just "Our World in Data".

---

### Instructions & Rules

1. **Locate Metadata File:**
   For any OWID chart URL (e.g., `https://ourworldindata.org/grapher/[chart-name]`), fetch its metadata JSON endpoint at `https://ourworldindata.org/grapher/[chart-name].metadata.json`.

2. **Extract Attribution String:**

    - Primary path: Extract the value from `columns.[column_key].citationShort`.
    - Fallback path: Use `chart.citation` if `citationShort` is not present.
    - Example extracted value:
      `"Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World in Data"`

3. **Update Wikitext `|author=` Field:**
   Replace `|author = Our World In Data` with the exact extracted attribution string.

---

### Example

**Target File:** `File:Wheat_yields,_World,_2023_(cropped).svg`
**Source URL:** `https://ourworldindata.org/grapher/wheat-production`
**Metadata Endpoint:** `https://ourworldindata.org/grapher/wheat-production.metadata.json`

#### Full Metadata JSON:

```json
{
    "chart": {
        "title": "Wheat production",
        "subtitle": "Wheat production is measured in tonnes.",
        "citation": "Food and Agriculture Organization of the United Nations (2025)",
        "originalChartUrl": "https://ourworldindata.org/grapher/wheat-production",
        "selection": ["Australia", "United States", "United Kingdom"]
    },
    "columns": {
        "Wheat | 00000015 || Production | 005510 || tonnes": {
            "titleShort": "Wheat production",
            "titleLong": "Wheat production - UN FAO",
            "shortUnit": "t",
            "unit": "tonnes",
            "timespan": "1961-2024",
            "type": "Numeric",
            "owidVariableId": 1199532,
            "shortName": "wheat__00000015__production__005510__tonnes",
            "lastUpdated": "2026-02-25",
            "nextUpdate": "2027-02-25",
            "citationShort": "Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World in Data",
            "citationLong": "Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World in Data. “Wheat production – UN FAO” [dataset]. Food and Agriculture Organization of the United Nations, “Production: Crops and livestock products” [original data].",
            "fullMetadata": "https://api.ourworldindata.org/v1/indicators/1199532.metadata.json"
        }
    },
    "dateDownloaded": "2026-08-16"
}
```

#### Original Wikitext:

```wikitext
=={{int:filedesc}}==
{{Information
|description={{en|1=Wheat yields, World}}
|author = Our World In Data
|date= 2023
|source = https://ourworldindata.org/grapher/wheat-yields?tab=map
|permission = "License: All of Our World in Data is completely open access and all work is licensed under the Creative Commons BY license. You have the permission to use, distribute, and reproduce in any medium, provided the source and authors are credited."
|other versions ={{Extracted from|1=wheat yields, World, 2023.svg}}
}}
{{Map showing old data|year=2023}}

```

#### Updated Wikitext Result:

```wikitext
=={{int:filedesc}}==
{{Information
|description={{en|1=Wheat yields, World}}
|author = Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World in Data
|date= 2023
|source = https://ourworldindata.org/grapher/wheat-yields?tab=map
|permission = "License: All of Our World in Data is completely open access and all work is licensed under the Creative Commons BY license. You have the permission to use, distribute, and reproduce in any medium, provided the source and authors are credited."
|other versions ={{Extracted from|1=wheat yields, World, 2023.svg}}
}}
{{Map showing old data|year=2023}}

```
