---
# **Prerequisites**
1. Python with required libraries installed.
2. Confluence page with an attachment which should be updated.  
3. .csv file.
4. The id of Confluence page.
5. The id of the attachment.

## Required libraries
* csv
* json
* os
* requests
* sys
* ConfigParser
* requests.auth

---
# **How to run script**
```
python SCRIPT_NAME PATH_TO_CSV_FILE CONFLUENCE_PAGE_ID ATTACHMENT_ID  
```

Example command:
```
python update_page.py test.csv 53000038 att50990900
```