import requests
import urllib
from http import HTTPStatus
import headless_pdfkit
import base64
import redis

from config.config import Config

from flask import Flask, make_response

app = Flask(__name__)
cfg = Config.instance()

class RedisManager:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        r = redis.Redis(self.host, self.port)
        self.r = r

    def retrive(self, name):
        if self.r == None:
            return None
        
        val = self.r.get(name)
        return val
    
    def insert_if_not_exists(self, key, val):
        if not self.r.exists(key):
            self.r.set(key, val)


class Statistics:
    def __init__(self, hindex, citations, relevance_score):
        self.hindex = hindex
        self.citations = citations
        self.relevance_score = relevance_score

class Article:
   def __init__(self, name, year, url):
       self.title = name
       self.year = year
       self.url = url

class Institution:
    def __init__(self, name, years, country):
        self.name = name
        self.years = years
        self.country = country

    def get_intervals(self):
        years_sorted = sorted(self.years)
        years_intervals = []

        if len(years_sorted) == 0:
            return []
        
        start_year = years_sorted[0]
        current_year = years_sorted[0]
        for i in range(1, len(years_sorted)):
            if years_sorted[i] == current_year + 1:
                current_year += 1
                continue

            years_intervals.append([start_year, current_year])
            start_year = years_sorted[i]
            current_year = years_sorted[i]

        years_intervals.append([start_year, current_year])
        return years_intervals
    
    def get_intervals_format(self):
        years_intervals = self.get_intervals()
        return ", ".join(map(lambda x: f"{x[0]} - {x[1]}" if x[0] != x[1] else f"{x[0]}", years_intervals))

class PDFGenerator:
    def __init__(self):
        pass

    def get_statistics(self, data):
        return Statistics(data["summary_stats"]["h_index"], data["cited_by_count"], float(data["relevance_score"]))

    def get_institutions_from_author(self, data):
        institutions = []
        for item in data:
                institutions.append(Institution(item["institution"]["display_name"], item["years"], "RO"))
        return institutions
    
    def get_articles_from_author(self, base_url):
        count = 0
        page = 1
        url = base_url

        articles = []
        while True:
            response = requests.get(url)
            if response.status_code != HTTPStatus.OK:
                return
            
            response_json = response.json()

            for item in response_json["results"]:
                if item["type"] == "article":
                    title = item["title"]
                    publication_year = item["publication_year"]
                    if item["doi"]:
                        url = item["doi"]
                    elif item["primary_location"] and item["primary_location"]["landing_page_url"]:
                        url = item["primary_location"]["landing_page_url"]
                    else:
                        url = None

                    articles.append(Article(title, publication_year, url))
            
            count += len(response_json["results"])
            if count == response_json["meta"]["count"]:
                break
            page += 1
        
            url = f"{base_url}&page={page}"
        

        return articles
    
    def search_author(self, author_name):
        author_encoded = urllib.parse.quote(author_name)
        baseUrl = f"https://api.openalex.org/authors?filter=display_name.search:{author_encoded}"
        response = requests.get(baseUrl)
        if response.status_code == HTTPStatus.OK:
            response_json = response.json()
            metadata = response_json["meta"]

            if metadata["count"] < 1:
                return
            
            result = response_json["results"][0]
            author_name = result["display_name"]

            articles = self.get_articles_from_author(result["works_api_url"])

            institutions = self.get_institutions_from_author(result["affiliations"])    

            article_set = []
            article_names = set()
            for article in articles:
                title_formated = ""
                for letter in article.title:
                    if (letter >= 'a' and letter <= 'z') or (letter >= 'A' and letter <= 'Z') or (letter >= '0' and letter <= '9'):
                        title_formated += letter 
                title_formated = title_formated.upper().replace(" ", "")
                if title_formated in article_names:
                    continue
                article_names.add(title_formated)
                article_set.append(article)

            articles = article_set
            articles.sort(key= lambda article : article.year, reverse=True)

            statistics = self.get_statistics(result)

            author_information = {
                'name': author_name,
                'institutions': institutions,
                'articles': articles,
                'statistics': statistics,
            }

            # Generate PDF with author information
            self.generate_author_info_pdf(author_information)

    def generate_author_info_pdf(self, author_info, output_path='author_info.pdf'):
        # HTML template for the PDF
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                .articles-list {{
                    list-style-type: none;
                    paddin)g: 0;
                }}
                .article {{
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <h1>{author_info['name']}</h1>
            <div>
            <h2> Summary Statistics </h2>
            <li> <b> H-Index </b> : {author_info['statistics'].hindex} </li>
            <li> <b> Total Citations </b> : {author_info['statistics'].citations} </li>
            <li> <b> Relevance score </b> : {author_info['statistics'].relevance_score} </li>
            </div>
            <div>
            <h2>Institutions</h2>
                <div>
                    <ul class="articles-list">
                        {"".join(f'<li class="article"> {institution.get_intervals_format()} {institution.name} </li>' for institution in author_info['institutions'])}
                    </ul>
                </div>
                <div>
                <h2>Articles</h2>
                    <ul class="articles-list">
                        {"".join(f'<li class="article">  {article.year} <a href="{article.url}">{article.title}</a></li>' for article in author_info['articles'])}
                    </ul>
                </div>
            </div>

            
        </body>
        </html>
        """

        # Convert HTML to PDF
        res = headless_pdfkit.generate_pdf(html_template)

        # with open(output_path, 'wb') as w:
        #     w.write(res)
        return res

    def generate_pdf(self, author_name):
        author_encoded = urllib.parse.quote(author_name)
        baseUrl = f"https://api.openalex.org/authors?filter=display_name.search:{author_encoded}"
        response = requests.get(baseUrl)
        if response.status_code == HTTPStatus.OK:
            response_json = response.json()
            metadata = response_json["meta"]

            if metadata["count"] < 1:
                return
            
            result = response_json["results"][0]
            author_name = result["display_name"]

            articles = self.get_articles_from_author(result["works_api_url"])

            institutions = self.get_institutions_from_author(result["affiliations"])    

            article_set = []
            article_names = set()
            for article in articles:
                title_formated = ""
                for letter in article.title:
                    if (letter >= 'a' and letter <= 'z') or (letter >= 'A' and letter <= 'Z') or (letter >= '0' and letter <= '9'):
                        title_formated += letter 
                title_formated = title_formated.upper().replace(" ", "")
                if title_formated in article_names:
                    continue
                article_names.add(title_formated)
                article_set.append(article)

            articles = article_set
            articles.sort(key= lambda article : article.year, reverse=True)

            statistics = self.get_statistics(result)

            author_information = {
                'name': author_name,
                'institutions': institutions,
                'articles': articles,
                'statistics': statistics,
            }

            # Generate PDF with author information
            res = self.generate_author_info_pdf(author_information)
            return res


class Writer:
    def __init__(self):
        pass

    def write(filename : str, bytes : bytearray) :
        with open(filename, 'wb') as w:
            w.write(bytes)

class WebscrapperManager:
    def __init__(self):
        self.redis_manager = RedisManager("redis", 6379)
        self.pdf_generator = PDFGenerator()

    def retrieve_request(self, name):
        value = self.redis_manager.retrive(name)
        if value == None:
            bytes = self.pdf_generator.generate_pdf(author_name=name)
            if bytes == None:
                print("Could not generate pdf")
                return
            encoded = base64.b64encode(bytes)

            self.redis_manager.insert_if_not_exists(name, encoded)
        else:
            print("cached")
            bytes = base64.b64decode(value)

        return bytes
           

def initialize_config():
    print(Config.get_base_url())

# def main():
#     initialize_config()

webManager = WebscrapperManager()
@app.route("/report.pdf")
def get_pdf():
    bytes_pdf = webManager.retrieve_request("catalin gosman")
    
    response = make_response(bytes_pdf)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'inline', filename='report.pdf')
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    # main()