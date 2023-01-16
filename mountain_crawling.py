import os, requests, time, base64, pymysql

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

################## 수정 및 적용 부분!
# file = "C:/projects/crawling/search_data.txt"
# m_list = []

# if os.path.isfile(file):
#     f = open(file,'r')
#     lines = f.readlines()
#     for i in lines:
#         m_list[i]
#     f.close()

# else:
#     m_list.append('None')

# print(m_list)

mountainName = input('산 이름 입력: ')

global driver
driver = webdriver.Chrome("C:/projects/chromedriver.exe")

def crawl_info(mountainName) :
    res = requests.get(f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query={mountainName}")
    soup = BeautifulSoup(res.text,"html.parser")
    time.sleep(1)
    info = []
    exist_mountain = soup.select_one(".PkgBl > .LDgIH")        # 네이버 주소값 (html 경로가 바뀔때가 있음. info index 오류나면 확인해보기)
    info_mountain = soup.select(".xHaT3 > .zPfVt")        # 네이버 산 설명글
    if exist_mountain == None:  # 산이 아닌걸 검색시 메세지 창이 뜸
        pass
    else:
        if len(info_mountain) == 0:  # 산의 설명글 정보가 없을시
            info.append("등록된 산 정보가 없습니다.")
            # 설명글 추가 버튼 만들면 좋을 거 같음
        elif len(info_mountain) == 1:
            info.append(info_mountain[0].text)
        else:
            info.append(info_mountain[-1].text) # 설명글은 항상 마지막에 있기 때문에 index에 -1
    return info

def crawl_location(mountainName) :
    # 카카오맵에서 주소 크롤링
    driver.get("https://map.kakao.com/")

    search = driver.find_element(By.CSS_SELECTOR, ".box_searchbar > .query")
    search.send_keys(mountainName, Keys.ENTER) # 산 이름 + 엔터키
    time.sleep(1)

    addr = driver.find_element(By.CSS_SELECTOR, ".addr")
    address = addr.text


    # 위도, 경도 찾는 사이트
    driver.get("https://address.dawul.co.kr/")

    # 주소값 입력
    search = driver.find_element(By.CSS_SELECTOR, "div > #input_juso")
    search.send_keys(address)
    time.sleep(1)

    # 검색버튼 클릭
    btnSearch = driver.find_element(By.CSS_SELECTOR, "#btnSch")
    btnSearch.click()
    time.sleep(1)

    # 위도, 경도 부분만 추출
    bring_location = driver.find_element(By.CSS_SELECTOR, "tr > #insert_data_5").text
    splitComma = bring_location.split(',')
    latlng = [splitComma[0].split(':')[1], splitComma[1].split(':')[1]]
    latlng.reverse()

    print('='*50)
    print('[주소] :', address, '\n[위도, 경도] :', latlng)
    print('='*50)
    return address, latlng

def crawl_img(mountainName) :
    driver.get(f"https://www.google.com/search?q={mountainName}")

    # 웹페이지 이동 ('이미지')
    br_me = driver.find_elements(By.CSS_SELECTOR,".hdtb-mitem > a")

    for i in br_me:

        if i.text == "이미지":
            i.click()
            break

    try:
        os.mkdir('C:/projects/project_M/static/images/'+str(mountainName))
    except:
        pass

    before_height = 0
    img_name = 0
    while True:
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source,"html.parser")
        br_img = soup.select('.islrc > .isv-r > .wXeWr > div > img')

        for i in br_img:
        # 구글에서 새로운 형식 도입시 에러가 발생 할 수 있으므로 try:except으로 처리
            try:
                img_path = i.get('src')
                
                if type(img_path) != str:
                    img_path = i.get('data-src')

                # 이미지 이름 지정 및 정규표현식
                img_name += 1 
                img_type = img_path.split(":")[0]

            except:
                pass

            # 구글에서 새로운 형식 도입시 에러가 발생 할 수 있으므로 else문 추가
            if img_type == "data": # data형식은 base64로 처리
                print(1) # 확인용
                # 같은 파일 생성시 오류 발생 해결을 위해 try:except문 사용
                try:
                    x = img_path.split(",")[1]
                    f = open(f"C:/projects/project_M/static/images/{mountainName}/pic_{img_name}.jpeg","wb")
                    img = base64.b64decode(f"{x}")
                    f.write(img)
                    f.close()

                    temp_split = f.name.split("/")
                    img_url = temp_split[4]+"/"+temp_split[5]+"/"+temp_split[6]
                    # print(img_url) # img_url 확인용
                    sql = f"insert into mydb.main_mountain_img values('{img_url}', '{mountainName}');"
                    cur.execute(sql)

                except:
                    pass

            elif img_type == "https": # https형식은 requests로 처리
                print(2) # 확인용
                # 같은 파일 생성시 오류 발생 해결을 위해 try:except문 사용
                try:
                    res = requests.get(img_path)
                    f = open(f"C:/projects/project_M/static/images/{mountainName}/pic_{img_name}.jpeg","wb")
                    f.write(res.content)
                    f.close()

                    temp_split = f.name.split("/")
                    img_url = temp_split[4]+"/"+temp_split[5]+"/"+temp_split[6]
                    # print(img_url) # img_url 확인용
                    sql = f"insert into mydb.main_mountain_img values('{img_url}', '{mountainName}');"
                    cur.execute(sql)

                except:
                    pass

            else:
                continue

        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        driver.execute_script(f"window.scrollTo(0,{new_height});")
        
        # 멈춰!
        if before_height == new_height:
            break
        before_height = new_height

    time.sleep(0.5)

# print(crawl_info(mountainName))
# print(crawl_location(mountainName))

info = crawl_info(mountainName)
address, latlng = crawl_location(mountainName)


con = pymysql.connect(host='murloc-mysql.clexteph0vvi.ap-northeast-2.rds.amazonaws.com',
                        user='admin', password='murloc1552!', db='mydb', charset='utf8')
cur = con.cursor()

sql = f"insert into mydb.main_mountain values ('{mountainName}', '{address}', '{latlng[0]}', '{latlng[1]}', '{info[0]}');"
cur.execute(sql)
# con.commit()

crawl_img(mountainName)

# rows = cur.fetchall()
# print(rows)

con.commit()
con.close()