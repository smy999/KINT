from requests.compat import urlparse, urljoin
from requests.exceptions import HTTPError
import time
import sqlite3
from requests import Session
from bs4 import BeautifulSoup
import re
import datetime
import pandas as pd

def download(url, params={}, headers={}, method='GET', limit=3):
    try:
        session = Session()
        resp = session.request(method, url,
                               params=params if method.upper() == 'GET' else '',
                               data=params if method.upper() == 'POST' else '',
                               headers=headers)
        resp.raise_for_status()
    except HTTPError as e:
        if limit > 0 and e.response.status_code >= 500:
            print(limit)
            time.sleep(60)  # Server Error이기 때문에 delay를 두고 실행하기 위해서 사용한다.
            # 보통은 5분에 한 번꼴로 random하게 되도록 설정한다.
            download(url, params, headers, method, limit - 1)
        else:
            print('[{}] '.format(e.response.status_code) + url)
            print(e.response.reason)
            print(e.response.headers)

    return resp

class PCrawler:
    def __init__(self):
        self.conn = sqlite3.connect('Politic.db')
        self.cur = self.conn.cursor()

    def resetdb(self):
        self.cur.executescript('''
            DROP TABLE IF EXISTS head;
            CREATE TABLE head(
                pk INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                head TEXT NOT NULL,
                wdate TEXT NOT NULL,
                cdate TEXT NOT NULL,
                ref INTEGER NOT NULL,
                page INTEGER NOT NULL
            );

            DROP TABLE IF EXISTS history;
            CREATE TABLE history(
                pk INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                seen TEXT NOT NULL,
                ref INTEGER NOT NULL
            )
        ''')

    def bobae_date_update(self):
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=200').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=200').fetchall()]
        cdate = pd.DataFrame(cdate)[0]
        wdate = pd.DataFrame(wdate)[0]
        # 당일 수집된 데이터에 대한 날짜 수정
        try:
            today = \
            pd.DataFrame(['{}'.format(cdate[_][:10]) for _ in range(0, len(wdate)) if re.search(r':', wdate[_])])[0]
            wdate_index = pd.DataFrame([_ for _ in range(0, len(wdate)) if re.search(r':', wdate[_])])[0]
            count = 1
        except:
            print('오늘 수집된 데이터가 없습니다.')
            count = 2
            # 다른 날짜 수정
            temp = list()
            this_year = pd.DataFrame(
                ['{}{}'.format(cdate[_][:5], wdate[_]) for _ in range(0, len(wdate)) if re.search(r'/', wdate[_])])[0]
            this_year = pd.DataFrame([re.sub(r'/', '-', _) for _ in this_year])[0]
            wdate_index = pd.DataFrame([_ for _ in range(0, len(wdate)) if re.search(r'/', wdate[_])])[0]
        else:
            # 다른 날짜 수정
            temp = list()
            this_year = pd.DataFrame(
                ['{}{}'.format(cdate[_][:5], wdate[_]) for _ in range(0, len(wdate)) if re.search(r'/', wdate[_])])[0]
            this_year = pd.DataFrame([re.sub(r'/', '-', _) for _ in this_year])[0]
            wdate_index.append(pd.DataFrame([_ for _ in range(0, len(wdate)) if re.search(r'/', wdate[_])])[0])
        # 연도 변환
        try:
            diff_years = pd.DataFrame(this_year[[_ for _ in range(0, len(this_year)) if this_year[_][5:7] == '12'][0]:])[0]
            this_year = pd.DataFrame(this_year[:[_ for _ in range(0, len(this_year)) if this_year[_][5:7] == '12'][0]])[0]

            date = 2019
            # 2020년 -> 2019년 변환
            for _ in range(0, len(diff_years)):
                diff_years[_] = re.sub(r'{}'.format(str(2020)), str(2019), diff_years[_])
            # 해가 넘어가는 index를 temp에 저장
            for _ in range(0, len(diff_years) - 1):
                if diff_years[_][5:7] < diff_years[_ + 1][5:7]:
                    temp.append(_ + 1)
            # index에 맞게 해가 넘어갈 때마다, year 수정
            for _ in range(0, len(temp)):
                date -= 1
                if _ < len(temp) - 1:
                    for i in range(temp[_], temp[_ + 1]):
                        diff_years[i] = re.sub(r'{}'.format(str(2019)), str(date), diff_years[i])
                else:
                    for i in range(temp[_], len(diff_years)):
                        diff_years[i] = re.sub(r'{}'.format(str(2019)), str(date), diff_years[i])
            # 각 데이터 merge
            today.append(this_year)
            today.append(diff_years)
            for _ in range(0, len(today)):
                self.cur.execute('UPDATE head SET wdate="%s" WHERE pk="%s"' % (today[_], _ + 1))
                self.conn.commit()
        except:
            print('바꿀 연도가 없습니다.')
            if count == 1:
                today.append(this_year)
                for _ in range(0, len(today)):
                    self.cur.execute('UPDATE head SET wdate="%s" WHERE wdate="%s"' % (today[_], wdate[wdate_index[_]]))
                    self.conn.commit()
            else:
                for _ in range(0, len(this_year)):
                    self.cur.execute('UPDATE head SET wdate="%s" WHERE wdate="%s"' % (this_year[_], wdate[wdate_index[_]]))
                    self.conn.commit()
        finally:
            print('update 완료')

    # 보배드림 정치게시판
    def bobae(self, recent=True):
        if recent:
            url = 'https://www.bobaedream.co.kr/list?code=politic&s_cate=&maker_no=&model_no=&or_gu=10&or_se=desc&s_selday=&pagescale=30&info3=&noticeShow=&s_select=&s_key=&level_no=&vdate=&type=list&page=1'

            urls = list()
            seen = list()
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=200 ORDER BY wdate DESC').fetchone()[0]

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    seen.append(seed)

                    resp = download(seed)
                    dom = BeautifulSoup(resp.content, 'lxml')

                    for _ in [_['href'] for _ in dom.select('.pageNumber03 a')
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/\w+(?:[?./=&_]+\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('tr td.pl14 > a.bsubject')]
                    date = [_.text.strip() for _ in dom.select('td.pl14 + td.author02 + td.date')]
                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if re.search(r'/', date[_]):
                                if date[_] > seen_date[5:]:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,200)',
                                                     [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                      re.search(r'page=(\d+)', urlparse(seed)[4]).group(1)])
                                    self.conn.commit()
                                else:
                                    break
                            else:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,200)',
                                                 [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                  re.search(r'page=(\d+)', urlparse(seed)[4]).group(1)])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)
        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=200 ORDER BY pk').fetchall()]
            url = seen[
                -1] if seen else 'https://www.bobaedream.co.kr/list?code=politic&s_cate=&maker_no=&model_no=&or_gu=10&or_se=desc&s_selday=&pagescale=30&info3=&noticeShow=&s_select=&s_key=&level_no=&vdate=&type=list&page=1'

            urls = list()

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 200)', [seed])
                        self.conn.commit()

                    resp = download(seed)
                    dom = BeautifulSoup(resp.content, 'lxml')

                    for _ in [_['href'] for _ in dom.select('.pageNumber03 a')
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/\w+(?:[?./=&_]+\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('tr td.pl14 > a.bsubject')]
                    date = [_.text.strip() for _ in dom.select('td.pl14 + td.author02 + td.date')]
                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,200)',
                                        [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                         re.search(r'page=(\d+)', urlparse(seed)[4]).group(1)])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def ilbe_date_update(self):
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=201').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=201').fetchall()]
        cdate = pd.DataFrame(cdate)[0]
        wdate = pd.DataFrame(wdate)[0]
        try:
            # 당일 수집된 데이터 날짜 수정
            today = \
                pd.DataFrame(['{}'.format(cdate[_][:10]) for _ in range(0, len(wdate)) if re.search(r':', wdate[_])])[0]
            wdate_index = pd.DataFrame([_ for _ in range(0, len(wdate)) if re.search(r':', wdate[_])])[0]
            # 데이터 update
            for _ in range(0, len(today)):
                self.cur.execute('UPDATE head SET wdate="%s" WHERE wdate="%s"' % (today[_], wdate[wdate_index[_]]))
                self.conn.commit()
        except:
            print('오늘 수집된 데이터가 없습니다.')
        finally:
            print('update 완료')

    # 일베-정치/시사
    def ilbe(self, recent=True):
        if recent:
            url = 'https://www.ilbe.com/list/politics'
            params = {
                'page': '',
                'listStyle': 'list',
            }

            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=201 ORDER BY wdate DESC').fetchone()[0]
            seen = list()
            page = list()
            page.append(1)

            count = page[0]

            while page:
                try:
                    params['page'] = page.pop(0)
                    count += 1
                    seen.append(params['page'])
                    self.cur.execute('INSERT INTO history(seen, ref) VALUES(?,201)', [params['page']])
                    self.conn.commit()

                    resp = download(url, params=params, method='GET')
                    dom = BeautifulSoup(resp.text, 'lxml')

                    if '{}'.format(count) in [_.text.strip() for _ in dom.select('.paginate > a') if
                                              _.has_attr('class') == False]:
                        page.append(count)
                    if count % 10 == 1:
                        page.append(count)

                    head = [_.text.strip() for _ in dom.select('.title .subject') if _.has_attr('style') == False]
                    date = [_.text.strip() for _ in dom.select('li > .date')][5:]

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if re.search(r'/', date[_]):
                                if date[_] > seen_date:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,201)',
                                                     [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                      params['page']])
                                    self.conn.commit()
                                else:
                                    break
                            else:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,201)',
                                                 [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                  params['page']])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)
        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=201').fetchall()]
            url = 'https://www.ilbe.com/list/politics'
            params = {
                'page': '',
                'listStyle': 'list',
            }

            page = list()
            page.append(int(seen[-1][0])) if seen else page.append(1)


            count = page[0]

            while page:
                try:
                    params['page'] = page.pop(0)
                    count += 1
                    seen.append(params['page'])
                    self.cur.execute('INSERT INTO history(seen, ref) VALUES(?,201)', [params['page']])
                    self.conn.commit()

                    resp = download(url, params=params, method='GET')
                    dom = BeautifulSoup(resp.text, 'lxml')

                    if '{}'.format(count) in [_.text.strip() for _ in dom.select('.paginate > a') if
                                              _.has_attr('class') == False]:
                        page.append(count)
                    if count % 10 == 1:
                        page.append(count)

                    head = [_.text.strip() for _ in dom.select('.title .subject') if _.has_attr('style') == False]
                    date = [_.text.strip() for _ in dom.select('li > .date')][5:]

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,201)',
                                        [head[_], date[_], str(datetime.datetime.now()).split('.')[0], params['page']])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)