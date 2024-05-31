import json, requests,uuid,re,os,sys
from urllib.parse import urljoin
from rprint import *

class Uploader:
    def __init__(self) -> None:
        self.url = ""
        self.username = ""
        self.password = ""
        self.albumID = "0"
        self.headers = {
            'Sec-Ch-Ua': '"-Not.A/Brand";v="8", "Chromium";v="102"',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Ch-Ua-Mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.cookie = ""
        self.read_config()
        self.session = requests.session()


    def read_config(self):
        config = ""
        with open("./config.json", "r",encoding="utf-8") as f:
            config = json.load(f)
        self.url = config["url"]
        self.username = config["username"]
        self.password = config["password"]
        if( config["albumID"] != None ):
            self.albumID = config["albumID"]


    def login(self) -> bool:
        r = self.session.get(self.url)
        data = {    "function" : "Session::login",
                    "user"     : self.username,
                    "password" : self.password}
        r = self.session.post(urljoin(self.url,"/php/index.php"), data=data, headers = self.headers)
        if (r.status_code == 200 and r.text == "true"):
            self.cookie = r.cookies
            return True
        else:
            return False

    def upload(self, filepath: str) -> bool:

        file_content = b""
        try:
            with open(filepath,"rb") as f:
                file_content = f.read()
        except:
            error("file not exist")
            return False
        filename = os.path.basename(filepath).encode()
        boundary = "----WebKitFormBoundary"+str(uuid.uuid1()).replace("-","")
        body = (
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="function"\r\n\r\n'
            'Photo::add\r\n'
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="albumID"\r\n\r\n'
            f'{self.albumID}\r\n'                         #default ID
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="0"; filename="{filename.decode("ISO-8859-1")}"\r\n'
            'Content-Type: image/jpeg\r\n\r\n'
            f'{file_content.decode("ISO-8859-1")}\r\n'
            f'--{boundary}--\r\n'
            )
        # body = body.encode('utf-8')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            'Content-Type': f'multipart/form-data; boundary={boundary}',
        }
        # response = requests.post(url, headers=headers, data=body)
        r = self.session.post(urljoin(self.url,"/php/index.php"), data=body, headers = headers)
        if(r.status_code == 200):
            return r.text
        if(r.status_code == 413):
            info("picture size too large")
        else:
            return False
        
    def get_pic(self, picID:str) -> str:
        data = {    "function" : "Photo::get",
            "photoID"     : picID,
            "albumID" : self.albumID}
        json_info = self.session.post(urljoin(self.url,"/php/index.php"), data=data, headers = self.headers).json()
        # info(json_info)
        if(type(json_info)==str):
            error(json_info)
            return None
        if("url" in json_info.keys()):
            return urljoin(self.url,json_info["url"])
        else:
            return None

def main(mdfile_path:str):
    uploader = Uploader()
    file_content = ""
    with open(mdfile_path,"r",encoding="utf-8") as f:
        file_content = f.read()
    pattern = "!\[.*?\]\((.*?)\)"
    matches = re.findall(pattern, file_content)
    if not uploader.login():
        error("can't login")

    for match in matches:
        try:
            if(match[:4] == "http"):
                info("onelined pic","JUMP",match)
                continue
            picid = uploader.upload(match)
            if(picid):
                pic_url = uploader.get_pic(picid)
                if(pic_url != None):
                    file_content = file_content.replace(match, pic_url)
                    success("file",match,"uploaded")
            else:
                error(match,"upload Failed")
        except Exception as e:
            error(e)
            continue
            
    with open(mdfile_path,"w",encoding="utf-8") as f:
        f.write(file_content)
    

if __name__ == "__main__":
    main(sys.argv[1])