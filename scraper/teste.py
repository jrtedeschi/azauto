import csv
from selectolax.parser import HTMLParser

# Read the HTML file
with open(
    "/home/jrtedeschi/projetos/tenex/azauto/scraper/data.html", "r", encoding="utf-8"
) as file:
    html = file.read()

# Parse the HTML
parser = HTMLParser(html)

# Find all table rows
rows = parser.css('div[role="row"]')

# Create a CSV file for writing
with open("table_data.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    # Write the header row
    writer.writerow(
        [
            "File Name",
            "File Type",
            "Privacy",
            "Modified Date",
            "Modified By",
            "File Size",
        ]
    )

    # Iterate over the rows and extract the data
    for row in rows:
        file_name = (
            row.css_first('button[data-automationid="FieldRenderer-name"]')
            .text()
            .strip()
        )
        file_type = row.css_first("img").attributes["alt"]
        privacy = (
            row.css_first("div.fieldRendererHeroCommandContainer_9ab02edc")
            .text()
            .strip()
        )
        modified_date = (
            row.css_first('div[data-automationid="FieldRenderer-date"]').text().strip()
        )
        modified_by = row.css_first("div.fieldText_875b1af5").text().strip()
        file_size = row.css_first("span.signalFieldValue_b9e74371").text().strip()

        # Write the row to the CSV file
        writer.writerow(
            [file_name, file_type, privacy, modified_date, modified_by, file_size]
        )

print("Table data has been extracted and saved to 'table_data.csv'.")
