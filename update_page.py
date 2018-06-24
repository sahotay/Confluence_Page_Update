import csv
import json
import os
import requests
import sys
import ConfigParser
from requests.auth import HTTPBasicAuth

config = ConfigParser.ConfigParser()
dir_name = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(dir_name, "credentials")
config.read(file_name)
username = config.get("confluence", "username")
password = config.get("confluence", "password")


def take_csv_data(file_path):
    """
    The function takes data from csv file.
    :param file_path: Path to csv file.
    :return: List with data.
    """
    csv_data = []
    try:
        with open(file_path, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            csv_data = list(csv_reader)
    except Exception as ex:
        show_error(ex)
    return csv_data


def create_confluence_data(csv_data):
    """
    The function creates data for Confluence page consisting of a chart with repositories names and their number,
    table with Registry, Repository, Tag, Id, Distro, Hostname, Number columns,
    information about access
    and attachments macro.
    :param csv_data: List with data.
    :return: Confluence data.
    """
    confluence_table_dict = {}
    for row in csv_data[1:]:
        key = "".join(row[0:6])
        if key not in confluence_table_dict:
            value = list(row[0:6])
            value.append(1)
            confluence_table_dict[key] = value
        else:
            confluence_table_dict[key][6] += 1

    confluence_table = "<table><tr>"
    for header in csv_data[0][0:6]:
        confluence_table += "<th><![CDATA[" + str(header).replace("]]>", "]]]]><![CDATA[>") + "]]></th>"
    confluence_table += "<th>Number</th>"
    confluence_table += "</tr>"

    confluence_table_values = sorted(confluence_table_dict.values(), key=lambda _value: _value[6], reverse=True)

    for row in confluence_table_values:
        confluence_table += "<tr>"
        for value in row:
            confluence_table += "<td><![CDATA[" + str(value).replace("]]>", "]]]]><![CDATA[>") + "]]></td>"
        confluence_table += "</tr>"
    confluence_table += "</table>"

    confluence_chart_table = "<table><tr><th>Repository</th>"
    for row in confluence_table_values:
        confluence_chart_table += "<th><![CDATA[" + str(row[1]).replace("]]>", "]]]]><![CDATA[>") + "]]></th>"
    confluence_chart_table += "</tr><tr><td>Number</td>"
    for row in confluence_table_values:
        confluence_chart_table += "<td><![CDATA[" + str(row[6]).replace("]]>", "]]]]><![CDATA[>") + "]]></td>"
    confluence_chart_table += "</tr></table>"

    confluence_chart = "<ac:structured-macro ac:name=\"chart\">" \
                       "<ac:parameter ac:name=\"width\">1400</ac:parameter>" \
                       "<ac:parameter ac:name=\"height\">1000</ac:parameter>" \
                       "<ac:rich-text-body>" + confluence_chart_table \
                       + "</ac:rich-text-body></ac:structured-macro>"

    confluence_info = "<br/><ac:structured-macro ac:name=\"info\"><ac:rich-text-body><p>" \
                      "Note that this page is locked down to a select set of viewers for security purposes. " \
                      "If you'd like to request access for someone else please contact " \
                      "<ac:link><ri:user ri:userkey=\"8aa8ca8f54b544f50154c4bee7ac0033\"/></ac:link> " \
                      "or <ac:link><ri:user ri:userkey=\"8aa8ca8f5568fda50155987f1fe50029\"/></ac:link>" \
                      "</p></ac:rich-text-body></ac:structured-macro><br/>"

    confluence_attachment = "<b>Below are detailed list of CVEs for each layers in Skyline images " \
                            "(based on \"dev-latest\" tag)</b><br/>" \
                            "<ac:structured-macro ac:name=\"attachments\">" \
                            "<ac:parameter ac:name=\"upload\">false</ac:parameter>" \
                            "</ac:structured-macro>"

    confluence_data = confluence_chart + confluence_table + confluence_info + confluence_attachment
    return confluence_data


def take_content(page_id):
    """
    The function takes information about current content.
    :param page_id: Id of Confluence page.
    :return: Content title, type and version number.
    """
    url = "https://confluence.comm.com/test/content/" + str(page_id)
    headers = {"X-Atlassian-Token": "no-check"}
    response = requests.get(url, auth=HTTPBasicAuth(username, password), headers=headers)
    if response.status_code != 200:
        show_error(response.text)

    response_data = response.json()
    content_title = response_data["title"]
    content_type = response_data["type"]
    content_version_number = response_data["version"]["number"]

    return content_title, content_type, content_version_number


def send_attachment(file_path, page_id, attachment_id):
    """
    The function updates attachment.
    :param file_path: Path to csv file.
    :param page_id: Id of Confluence page.
    :param attachment_id: Id of attachment in Confluence.
    """
    files = {"file": (os.path.basename(file_path), open(file_path, 'r'))}
    url = "https://confluence.comm.com/rest/api/latest/content/" + page_id \
          + "/child/attachment/" + attachment_id + "/data"
    headers = {"X-Atlassian-Token": "no-check"}
    response = requests.post(url, auth=HTTPBasicAuth(username, password), files=files, headers=headers)
    if response.status_code != 200:
        show_error(response.text)


def send_content(page_id, content_title, content_type, content_version_number, confluence_data):
    """
    The function updates Confluence page.
    :param page_id: Id of Confluence page.
    :param content_title: Title of Confluence content.
    :param content_type: Type of Confluence content.
    :param content_version_number: Version number of Confluence content.
    :param confluence_data: Confluence updated data.
    """
    url = "https://confluence.comm.com/rest/api/latest/content/" + str(page_id)
    payload = {
        "version": {
            "number": content_version_number + 1},
        "title": content_title,
        "type": content_type,
        "body":
            {"storage":
                {"value": confluence_data,
                    "representation": "storage"}}}

    headers = {"content-type": "application/json", "X-Atlassian-Token": "no-check"}
    response = requests.put(url, auth=HTTPBasicAuth(username, password), data=json.dumps(payload), headers=headers)
    if response.status_code != 200:
        show_error(response.text)


def show_error(message):
    """
    The function stops executing program and shows an error message.
    :param message: Error message.
    """
    sys.exit("Error occured. Details below.\n" + str(message))


def main():
    """
    The main function calling other functions.
    """
    if len(sys.argv) != 4:
        show_error("Missing command-line argument.\nCorrect calling this script is:\n"
                   "python SCRIPT_NAME PATH_TO_CSV_FILE CONFLUENCE_PAGE_ID ATTACHMENT_ID")
    file_path = sys.argv[1]
    page_id = sys.argv[2]
    attachment_id = sys.argv[3]
    csv_data = take_csv_data(file_path)
    confluence_data = create_confluence_data(csv_data)
    content_title, content_type, content_version_number = take_content(page_id)
    send_attachment(file_path, page_id, attachment_id)
    send_content(page_id, content_title, content_type, content_version_number, confluence_data)
    print "Page and attachment updated successfully"


if __name__ == '__main__':
    main()