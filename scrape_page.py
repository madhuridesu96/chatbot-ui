import requests
from bs4 import BeautifulSoup

url = "https://www.healthcare.gov/glossary/deductible/"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

main_content = soup.find("main")

if main_content:
    page_text = main_content.get_text(separator="\n", strip=True)
else:
    page_text = soup.get_text(separator="\n", strip=True)

print(page_text)