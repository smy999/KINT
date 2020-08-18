# ref
# { 오늘의유머_베스트오브베스트 : 1, 오늘의유머_베스트게시판 : 2, 일베_일간베스트 : 3, 디시인사이드_야구갤러리 : 4, 뽐뿌_자유게시판 : 5, 네이트판_10대게시판 : 6, 네이트판_20대게시판 :7, 네이트판_톡커들의선택 : 8,
# 디시인사이드_인터넷방송갤러리 : 100, 디시인사이드_남자연예인갤러리 : 101, 디시인사이드_여자연예인갤러리 : 102, 인스티즈_이슈 : 103,
# 보배드림_정치 : 200, 일베_정치/시사 : 201 }
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
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=200 ORDER BY wdate ASC').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=200 ORDER BY wdate ASC').fetchall()]
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
            seen_date = seen_date[5:7] + '/' + seen_date[8:]

            urls.append(url)

            count = 0
            varbreak = 0

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
                                if date[_] > seen_date:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,200)',
                                                     [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                      re.search(r'page=(\d+)', urlparse(seed)[4]).group(1)])
                                    self.conn.commit()
                                else:
                                    varbreak = 1
                                    break
                            else:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,200)',
                                                 [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                  re.search(r'page=(\d+)', urlparse(seed)[4]).group(1)])
                                self.conn.commit()
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)
        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=200').fetchall()]
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
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=201 ORDER BY wdate ASC').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=201 ORDER BY wdate ASC').fetchall()]
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
            varbreak = 0

            while page:
                try:
                    params['page'] = page.pop(0)
                    count += 1
                    seen.append(params['page'])

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
                            if re.search(r'-', date[_]):
                                if date[_] > seen_date:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,201)',
                                                     [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                      params['page']])
                                    self.conn.commit()
                                else:
                                    varbreak = 1
                                    break
                            else:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,201)',
                                                 [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                  params['page']])
                                self.conn.commit()
                        if varbreak == 1:
                            break

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
            page.append(int(seen[-1])) if seen else page.append(1)


            count = page[0]

            while page:
                try:
                    params['page'] = page.pop(0)
                    count += 1
                    if params['page'] not in seen:
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

class HCrawler:
    def __init__(self):
        self.conn = sqlite3.connect('Humor.db')
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

    def ou(self,bob=True,recent=True):
        if recent:
            url = 'http://www.todayhumor.co.kr/board/list.php?table=bestofbest&page=1' if bob else 'http://www.todayhumor.co.kr/board/list.php?table=humorbest&page=1'

            urls = list()
            seen = list()
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=1 ORDER BY wdate DESC').fetchone()[0] if bob else self.cur.execute('SELECT wdate FROM head WHERE ref=2 ORDER BY wdate DESC').fetchone()[0]

            urls.append(url)

            count = 0
            varbreak = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    seen.append(seed)

                    resp = download(seed)
                    dom = BeautifulSoup(resp.text, 'lxml')

                    for _ in [_['href'] for _ in dom.select('tbody > tr:nth-of-type(33) a')
                              if _.has_attr('href') and re.match(r'(^l.+)', _['href']).group()]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('td.subject > a')]
                    date = [_.text.strip() for _ in dom.select('tbody > tr > td.date')]
                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if date[_] > seen_date:
                                if bob:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,1)',
                                                     [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                      re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                    self.conn.commit()
                                else:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,2)',
                                                [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                 re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                    self.conn.commit()
                            else:
                                varbreak = 1
                                break
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

        else:
            if bob:
                seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=1').fetchall()]
                url = seen[-1] if seen else 'http://www.todayhumor.co.kr/board/list.php?table=bestofbest&page=1'
            else:
                seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=2').fetchall()]
                url = seen[-1] if seen else 'http://www.todayhumor.co.kr/board/list.php?table=humorbest&page=1'

            urls = list()

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    if seed not in seen:
                        seen.append(seed)
                        if bob:
                            self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 1)', [seed])
                        else:
                            self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 2)', [seed])
                        self.conn.commit()

                    resp = download(seed)
                    dom = BeautifulSoup(resp.text, 'lxml')

                    for _ in [_['href'] for _ in dom.select('tbody > tr:nth-of-type(33) a')
                              if _.has_attr('href') and re.match(r'(^l.+)', _['href']).group()]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('td.subject > a')]
                    date = [_.text.strip() for _ in dom.select('tbody > tr > td.date')]
                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if bob:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,1)',
                                            [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                             re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                self.conn.commit()
                            else:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,2)',
                                            [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                             re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def ilbe_date_update(self):
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=3 ORDER BY wdate ASC').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=3 ORDER BY wdate ASC').fetchall()]
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


    def ilbe(self, recent=True):
        if recent:
            url = 'https://www.ilbe.com/list/ilbe'
            params = {
                'page': '',
                'listStyle': 'list',
            }

            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=3 ORDER BY wdate DESC').fetchone()[0]
            seen = list()
            page = list()
            page.append(1)

            count = page[0]
            varbreak = 0

            while page:
                try:
                    params['page'] = page.pop(0)
                    count += 1
                    seen.append(params['page'])

                    resp = download(url, params=params, method='GET')
                    dom = BeautifulSoup(resp.text, 'lxml')

                    if '{}'.format(count) in [_.text.strip() for _ in dom.select('.paginate > a') if
                                              _.has_attr('class') == False]:
                        page.append(count)
                    if count % 10 == 1:
                        page.append(count)

                    head = [_.text.strip() for _ in dom.select('.board-body .subject') if _.has_attr('style') == False]
                    date = [_.text.strip() for _ in dom.select('li > .date')][7:]

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if re.search(r'-', date[_]):
                                if date[_] > seen_date:
                                    self.cur.execute(
                                        'INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,3)',
                                        [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                         params['page']])
                                    self.conn.commit()
                                else:
                                    varbreak = 1
                                    break
                            else:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,3)',
                                                 [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                  params['page']])
                                self.conn.commit()
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)
        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=3').fetchall()]
            url = 'https://www.ilbe.com/list/ilbe'
            params = {
                'page': '',
                'listStyle': 'list',
            }

            page = list()
            page.append(int(seen[-1])) if seen else page.append(1)

            count = page[0]

            while page:
                try:
                    params['page'] = page.pop(0)
                    count += 1
                    if params['page'] not in seen:
                        seen.append(params['page'])
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?,3)', [params['page']])
                        self.conn.commit()

                    resp = download(url, params=params, method='GET')
                    dom = BeautifulSoup(resp.text, 'lxml')

                    if '{}'.format(count) in [_.text.strip() for _ in dom.select('.paginate > a') if
                                              _.has_attr('class') == False]:
                        page.append(count)
                    if count % 10 == 1:
                        page.append(count)

                    head = [_.text.strip() for _ in dom.select('.board-body .subject') if _.has_attr('style') == False]
                    date = [_.text.strip() for _ in dom.select('li > .date')][7:]

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,3)',
                                             [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                              params['page']])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def dc(self, recent=True):
        if recent:
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=4 ORDER BY wdate DESC').fetchone()[0]

            url = 'https://gall.dcinside.com/board/lists/?id=baseball_new9&page=1'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}

            urls = list()
            seen = list()

            urls.append(url)

            count = 0
            varbreak = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.text, 'lxml')
                    seen.append(seed)

                    for _ in [_['href'] for _ in dom.select('div.bottom_paging_box > a')[:-1]
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/\w+(?:[./]\w+)+', _['href']).group()
                                 and _.text.strip() != '처음' and _.text.strip() != '이전']:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [i.text.strip() for _ in dom.select('tr.ub-content.us-post') if
                            _['data-type'] in ['icon_pic', 'icon_txt'] for i in
                            _.select('td:nth-of-type(2) > a:nth-of-type(1)')]
                    wdate = [i['title'] for _ in dom.select('tr.ub-content.us-post') if
                             _['data-type'] in ['icon_pic', 'icon_txt'] for i in _.select('td.gall_date')]
                    if len(head) == len(wdate):
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('page=(\d+)', urlparse(seed).query).group(1)
                        for _ in range(0, len(head)):
                            if wdate[_] > seen_date:
                                self.cur.execute('''
                                                INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,4)
                                                ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()
                            else:
                                varbreak = 1
                                break
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=4').fetchall()]
            url = seen[-1] if seen else 'https://gall.dcinside.com/board/lists/?id=baseball_new9&page=1'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}

            urls = list()

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.text, 'lxml')
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                            INSERT INTO history(seen,ref) VALUES(?,4)
                        ''', [seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select('div.bottom_paging_box > a')[:-1]
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/\w+(?:[./]\w+)+', _['href']).group()
                              and _.text.strip() != '처음' and  _.text.strip() != '이전']:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [i.text.strip() for _ in dom.select('tr.ub-content.us-post') if
                            _['data-type'] in ['icon_pic', 'icon_txt'] for i in
                            _.select('td:nth-of-type(2) > a:nth-of-type(1)')]
                    wdate = [i['title'] for _ in dom.select('tr.ub-content.us-post') if
                             _['data-type'] in ['icon_pic', 'icon_txt'] for i in _.select('td.gall_date')]
                    if len(head) == len(wdate):
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('page=(\d+)', urlparse(seed).query).group(1)
                        for _ in range(0, len(head)):
                            self.cur.execute('''
                                INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,4)
                                ''', [head[_], wdate[_], cdate, page])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def ppomppu(self, recent=True):
        if recent:
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=5 ORDER BY wdate DESC').fetchone()[0]
            url = 'http://www.ppomppu.co.kr/zboard/zboard.php?id=freeboard&page=1&divpage=1321'
            headers = {'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'}
            urls = list()
            seen = list()

            urls.append(url)

            count = 0
            varbreak = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    seen.append(seed)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.text, 'lxml')

                    for _ in [_['href'] for _ in dom.select('#page_list a')
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/?\w+(?:[./]\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('tr[class^=list] a > font') if
                            _.find('img') == None or _.find('img').has_attr('style') == False]
                    date = [_['title'] for _ in dom.select('tr[class^=list] td.eng') if
                            _.has_attr('title') and _['title'][:2] != '13']

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if date[_] > seen_date:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,5)',
                                                 [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                  re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                self.conn.commit()
                            else:
                                varbreak = 1
                                break
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=5').fetchall()]
            url = seen[-1] if seen else 'http://www.ppomppu.co.kr/zboard/zboard.php?id=freeboard&page=1&divpage=1321'
            headers = {'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'}
            urls = list()

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 5)', [seed])
                        self.conn.commit()

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.text, 'lxml')

                    for _ in [_['href'] for _ in dom.select('#page_list a')
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/?\w+(?:[./]\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('tr[class^=list] a > font') if
                            _.find('img') == None or _.find('img').has_attr('style') == False]
                    date = [_['title'] for _ in dom.select('tr[class^=list] td.eng') if
                            _.has_attr('title') and _['title'][:2] != '13']

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,5)',
                                        [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                         re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def nate_date_update(self, teen=True):
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=6 ORDER BY wdate ASC').fetchall()] if teen else [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=7').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=6 ORDER BY wdate ASC').fetchall()] if teen else [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=7').fetchall()]
        cdate = pd.DataFrame(cdate)[0]
        wdate = pd.DataFrame(wdate)[0]
        try:
            # 당일 수집된 데이터 날짜 수정
            today = \
                pd.DataFrame(['{0}.{1}.{2}'.format(cdate[_][:4], cdate[_][5:7], cdate[_][8:10]) for _ in range(0, len(wdate)) if re.search(r':', wdate[_])])[0]
            wdate_index = pd.DataFrame([_ for _ in range(0, len(wdate)) if re.search(r':', wdate[_])])[0]
            # 데이터 update
            for _ in range(0, len(today)):
                self.cur.execute('UPDATE head SET wdate="%s" WHERE wdate="%s"' % (today[_], wdate[wdate_index[_]]))
                self.conn.commit()
        except:
            print('오늘 수집된 데이터가 없습니다.')
        finally:
            print('update 완료')

    def nate(self, teen=True , recent=True):
        if recent:
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=6 ORDER BY wdate DESC').fetchone()[0] if teen else self.cur.execute('SELECT wdate FROM head WHERE ref=7 ORDER BY wdate DESC').fetchone()[0]
            if teen:
                url = 'https://pann.nate.com/talk/c20038?page=1'
            else:
                url = 'https://pann.nate.com/talk/c20002?page=1'

            urls = list()
            seen = list()

            urls.append(url)

            count = 0
            varbreak = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    seen.append(seed)

                    resp = download(seed)
                    dom = BeautifulSoup(resp.text, 'lxml')

                    for _ in [_['href'] for _ in dom.select('div.paginate > a.paging')
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/?\w+(?:[./]\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('tbody td.subject > a')]
                    date = [_.text.strip() for _ in dom.select('tbody > tr > td:nth-of-type(4)')]

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if re.search(r'[.]', date[_]):
                                if date[_] > seen_date:
                                    if teen:
                                        self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,6)',
                                                         [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                          re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                    else:
                                        self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,7)',
                                                         [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                          re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                    self.conn.commit()
                                else:
                                    varbreak = 1
                                    break
                            else:
                                if teen:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,6)',
                                                     [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                      re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                else:
                                    self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,7)',
                                                     [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                      re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                                self.conn.commit()
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=6').fetchall()] if teen else [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=7').fetchall()]
            if teen:
                url = seen[-1] if seen else 'https://pann.nate.com/talk/c20038?page=1'
            else:
                url = seen[-1] if seen else 'https://pann.nate.com/talk/c20002?page=1'

            urls = list()

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?,6)', [seed]) if teen else self.cur.execute('INSERT INTO history(seen, ref) VALUES(?,7)', [seed])
                        self.conn.commit()

                    resp = download(seed)
                    dom = BeautifulSoup(resp.text, 'lxml')

                    for _ in [_['href'] for _ in dom.select('div.paginate > a.paging')
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/?\w+(?:[./]\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('tbody td.subject > a')]
                    date = [_.text.strip() for _ in dom.select('tbody > tr > td:nth-of-type(4)')]

                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if teen:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,6)',
                                            [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                             re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                            else:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,7)',
                                        [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                         re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def nate_talker(self, recent=True):
        seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=8').fetchall()]

        if recent:
            url = 'https://pann.nate.com/talk/ranking/d?stdt=20200730&page=1'
            tempdate = str(datetime.datetime.now()).split('.')[0]
            url = urljoin(url,
                          'd?stdt={}&page={}'.format(str(int(tempdate[:4] + tempdate[5:7] + tempdate[8:10]) - 1), 1))
        else:
            if seen:
                url = seen[-1]
            else:
                url = 'https://pann.nate.com/talk/ranking/d?stdt=20200730&page=1'
                tempdate = str(datetime.datetime.now()).split('.')[0]
                url = urljoin(url, 'd?stdt={}&page={}'.format(
                    str(int(tempdate[:4] + tempdate[5:7] + tempdate[8:10]) - 1), 1))

        urls = list()

        urls.append(url)

        count = 0

        while urls:
            try:
                count += 1
                seed = urls.pop(0)
                if seed not in seen:
                    seen.append(seed)
                    self.cur.execute('INSERT INTO history(seen, ref) VALUES(?,8)', [seed])
                    self.conn.commit()

                resp = download(seed)
                dom = BeautifulSoup(resp.text, 'lxml')

                if re.search(r'page=(\d+)', urlparse(seed)[4]).group(1) == '1':
                    # page 넘기기
                    stdt = re.search(r",'(\d+)',(\d+)", str(dom.select_one('button.last'))).group(1)
                    page = re.search(r",'(\d+)',(\d+)", str(dom.select_one('button.last'))).group(2)
                    newUrls = urljoin(url, 'd?stdt={}&page={}'.format(stdt, page))

                    if newUrls not in urls and newUrls not in seen:
                        urls.append(newUrls)

                if re.search(r'page=(\d+)',urlparse(seed)[4]).group(1) == '2':
                    # 이전 날짜로 가기
                    stdt = re.search(r",'(\d+)',(\d+)", str(dom.select_one('button.prev'))).group(1)
                    page = re.search(r",'(\d+)',(\d+)", str(dom.select_one('button.prev'))).group(2)
                    newUrls = urljoin(url, 'd?stdt={}&page={}'.format(stdt, page))

                    if newUrls not in urls and newUrls not in seen:
                        urls.append(newUrls)

                head = [_.text.strip() for _ in dom.select('ul.post_wrap > li dt > a')]
                date = dom.select_one('span.tdate').text.strip()

                if head:
                    for _ in range(0, len(head)):
                        self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,8)',
                                         [head[_], date, str(datetime.datetime.now()).split('.')[0],
                                          re.search(r'=(\d+)', urlparse(seed)[4]).group(1)])
                        self.conn.commit()

                if count % 100 == 0:
                    print(count)

            except Exception as e:
                print(e)

class ECrawler:
    def __init__(self):
        self.conn = sqlite3.connect('Entertainment.db')
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

    # gallery 1 : 인방갤, 2 : 남자연예인갤러리, 3 : 여자연예인갤러리
    def dc(self, gallery,recent=True):
        if recent:
            if gallery == 1:
                seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=100 ORDER BY wdate DESC').fetchone()[0]
                url = 'https://gall.dcinside.com/board/lists/?id=ib_new1&page=1'
            elif gallery == 2:
                seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=101 ORDER BY wdate DESC').fetchone()[0]
                url = 'https://gall.dcinside.com/board/lists/?id=m_entertainer1&page=1'
            else:
                seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=102 ORDER BY wdate DESC').fetchone()[0]
                url = 'https://gall.dcinside.com/board/lists?id=w_entertainer&page=1'

            url = 'https://gall.dcinside.com/board/lists/?id=baseball_new9&page=1'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}

            urls = list()
            seen = list()

            urls.append(url)

            count = 0
            varbreak = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.text, 'lxml')
                    seen.append(seed)

                    for _ in [_['href'] for _ in dom.select('div.bottom_paging_box > a')[:-1]
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/\w+(?:[./]\w+)+', _['href']).group()
                                 and _.text.strip() != '처음' and _.text.strip() != '이전']:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [i.text.strip() for _ in dom.select('tr.ub-content.us-post') if
                            _['data-type'] in ['icon_pic', 'icon_txt'] for i in
                            _.select('td:nth-of-type(2) > a:nth-of-type(1)')]
                    wdate = [i['title'] for _ in dom.select('tr.ub-content.us-post') if
                             _['data-type'] in ['icon_pic', 'icon_txt'] for i in _.select('td.gall_date')]
                    if len(head) == len(wdate):
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('page=(\d+)', urlparse(seed).query).group(1)
                        for _ in range(0, len(head)):
                            if wdate[_] > seen_date:
                                if gallery == 1:
                                    self.cur.execute('''
                                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,100)
                                                    ''', [head[_], wdate[_], cdate, page])
                                elif gallery == 2:
                                    self.cur.execute('''
                                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,101)
                                                    ''', [head[_], wdate[_], cdate, page])
                                else:
                                    self.cur.execute('''
                                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,102)
                                                    ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()
                            else:
                                varbreak = 1
                                break
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

        else:
            if gallery == 1:
                seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=100').fetchall()]
                url = seen[-1] if seen else 'https://gall.dcinside.com/board/lists/?id=ib_new1&page=1'
            elif gallery == 2:
                seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=101').fetchall()]
                url = seen[-1] if seen else 'https://gall.dcinside.com/board/lists/?id=m_entertainer1&page=1'
            else:
                seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=102').fetchall()]
                url = seen[-1] if seen else 'https://gall.dcinside.com/board/lists?id=w_entertainer&page=1'

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}

            urls = list()

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.text, 'lxml')
                    if seed not in seen:
                        seen.append(seed)
                        if gallery == 1:
                            self.cur.execute('''
                                INSERT INTO history(seen,ref) VALUES(?,100)
                            ''', [seed])
                        elif gallery == 2:
                            self.cur.execute('''
                                INSERT INTO history(seen,ref) VALUES(?, 101)
                                ''',[seed])
                        else:
                            self.cur.execute('''
                                INSERT INTO history(seen,ref) VALUES(?, 102)
                                ''',[seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select('div.bottom_paging_box > a')[:-1]
                              if _.has_attr('href') and re.match(r'(?:https?:/)?/\w+(?:[./]\w+)+', _['href']).group()
                              and _.text.strip() != '처음' and  _.text.strip() != '이전']:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [i.text.strip() for _ in dom.select('tr.ub-content.us-post') if
                            _['data-type'] in ['icon_pic', 'icon_txt'] for i in
                            _.select('td:nth-of-type(2) > a:nth-of-type(1)')]
                    wdate = [i['title'] for _ in dom.select('tr.ub-content.us-post') if
                             _['data-type'] in ['icon_pic', 'icon_txt'] for i in _.select('td.gall_date')]
                    if len(head) == len(wdate):
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('page=(\d+)', urlparse(seed).query).group(1)
                        for _ in range(0, len(head)):
                            if gallery == 1:
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,100)
                                    ''', [head[_], wdate[_], cdate, page])
                            elif gallery == 2:
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,101)
                                    ''', [head[_], wdate[_], cdate, page])
                            else:
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,102)
                                    ''', [head[_], wdate[_], cdate, page])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def instize_date_update(self):
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=103 ORDER BY wdate ASC').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=103 ORDER BY wdate ASC').fetchall()]
        cdate = pd.DataFrame(cdate)[0]
        wdate = pd.DataFrame(wdate)[0]
        try:
            # 당일 수집된 데이터 날짜 수정
            today = \
                pd.DataFrame(['{0}.{1} {2}'.format(cdate[_][5:7], cdate[_][8:10], wdate[_]) for _ in range(0, len(wdate)) if not re.search(r'[.]', wdate[_])])[0]
            wdate_index = pd.DataFrame([_ for _ in range(0, len(wdate)) if re.search(r':', wdate[_])])[0]
            # 데이터 update
            for _ in range(0, len(today)):
                self.cur.execute('UPDATE head SET wdate="%s" WHERE wdate="%s"' % (today[_], wdate[wdate_index[_]]))
                self.conn.commit()
        except:
            print('오늘 수집된 데이터가 없습니다.')
        finally:
            print('update 완료')


    def instize(self, recent=True):
        if recent:
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=103 ORDER BY wdate DESC').fetchone()[0]
            url = 'https://www.instiz.net/pt'
            params = {
                'page': ''
            }

            pages = list()
            pages.append('1')
            seen = list()

            count = int(pages[0])
            varbreak = 0

            while pages:
                try:
                    count += 1
                    params['page'] = pages.pop(0)

                    resp = download(url, params=params)
                    dom = BeautifulSoup(resp.text, 'html.parser')

                    if params['page'] not in seen:
                        seen.append(params['page'])

                    if '다음' in [_.text.strip() for _ in dom.select('#indextable a') if _.has_attr('href')]:
                        pages.append(str(count))

                    if dom.select('#subject > a') != None:
                        head = [_.text.strip() for _ in dom.select('#subject > a')]
                        wdate = [_.text.strip() for _ in dom.select('td.listno.regdate')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                if wdate[_] > seen_date:
                                    self.cur.execute('''
                                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,103)
                                                    ''', [head[_], wdate[_], cdate, params['page']])
                                    self.conn.commit()
                                else:
                                    varbreak = 1
                                    break
                            if varbreak == 1:
                                break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=103').fetchall()]
            url = 'https://www.instiz.net/pt'
            params = {
                'page': ''
            }

            pages = list()
            pages.append(seen[-1]) if seen else pages.append('1')


            count = int(pages[0])

            while pages:
                try:
                    count += 1
                    params['page'] = pages.pop(0)

                    resp = download(url, params=params)
                    dom = BeautifulSoup(resp.text, 'html.parser')


                    if params['page'] not in seen:
                        seen.append(params['page'])
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?,103)', [params['page']])
                        self.conn.commit()


                    if '다음' in [_.text.strip() for _ in dom.select('#indextable a') if _.has_attr('href')]:
                        pages.append(str(count))

                    if dom.select('#subject > a') != None:
                        head = [_.text.strip() for _ in dom.select('#subject > a')]
                        wdate = [_.text.strip() for _ in dom.select('td.listno.regdate')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,103)
                                    ''', [head[_], wdate[_], cdate, params['page']])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)


class NCrawler:
    def __init__(self):
        self.conn = sqlite3.connect('News.db')
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

    def han(self,recent=True):
        if recent:
            url = 'http://www.hani.co.kr/arti/list1.html'
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=300 ORDER BY wdate DESC').fetchone()[0]
            urls = list()
            seen = list()

            urls.append(url)

            count = 0
            varbreak = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 300)', [seed])
                        self.conn.commit()

                    resp = download(seed)
                    dom = BeautifulSoup(resp.content, 'lxml')

                    for _ in [_['href'] for _ in dom.select('.paginate > a') if
                              _.has_attr('href') and re.match(r'(?:[?./=&_]+\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('.article-title > a')]
                    date = [_.text.strip() for _ in dom.select('.article-prologue > .date')]
                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            if date[_] > seen_date:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,300)',
                                                 [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                                  re.search(r'list(\d+)', seed).group(1)])
                                self.conn.commit()
                            else:
                                varbreak = 1
                                break
                        if varbreak == 1:
                            break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=300').fetchall()]
            url = seen[-1] if seen else 'http://www.hani.co.kr/arti/list1.html'

            urls = list()

            urls.append(url)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 300)', [seed])
                        self.conn.commit()

                    resp = download(seed)
                    dom = BeautifulSoup(resp.content, 'lxml')

                    for _ in [_['href'] for _ in dom.select('.paginate > a') if _.has_attr('href') and re.match(r'(?:[?./=&_]+\w+)+', _['href'])]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    head = [_.text.strip() for _ in dom.select('.article-title > a')]
                    date = [_.text.strip() for _ in dom.select('.article-prologue > .date')]
                    if len(head) == len(date):
                        for _ in range(0, len(date)):
                            self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,300)',
                                        [head[_], date[_], str(datetime.datetime.now()).split('.')[0],
                                         re.search(r'list(\d+)', seed).group(1)])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)

    def khan(self, recent=True):
        if recent:
            url = 'http://www.khan.co.kr/bestnews/khan_art_list_new.html'
            params = {
                'media': 'khan',
                'depth3': 'bestnews',
                'year': '',
                'month': '',
                'day': ''
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}
            seen = list()
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=301 ORDER BY wdate DESC').fetchone()[0]
            seen_date = [int(_) for _ in seen_date.split('-')]
            seen_date = datetime.date(seen_date[0], seen_date[1], seen_date[2])
            base = datetime.date.today()
            date_list = [base - datetime.timedelta(days=x) for x in range(365)]
            count = 0
            varbreak = 0

            while date_list:
                try:
                    count += 1
                    seed = date_list
                    if seed not in seen:
                        seen.append(seed)
                        params['year'] = seed.year
                        if len(str(seed.month)) == 1:
                            params['month'] = '0' + str(seed.month)
                        else:
                            params['month'] = str(seed.month)
                        if len(str(seed.day)) == 1:
                            params['day'] = '0' + str(seed.day)
                        else:
                            params['day'] = str(seed.day)
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 301)', [seed])
                        self.conn.commit()

                    resp = download(url, params=params, headers=headers, method='POST')
                    dom = BeautifulSoup(resp.content, 'lxml')

                    head = [_.text.strip() for _ in dom.select('.list_cm > li > a')]
                    for _ in range(0, len(head)):
                        if seed > seen_date:
                            self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,300)',
                                        [head[_], seed, str(datetime.datetime.now()).split('.')[0],
                                         0])
                            self.conn.commit()
                        else:
                            varbreak = 1
                            break
                    if varbreak == 1:
                        break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)
        else:
            url = 'http://www.khan.co.kr/bestnews/khan_art_list_new.html'
            params = {
                'media': 'khan',
                'depth3': 'bestnews',
                'year': '',
                'month': '',
                'day': ''
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=301').fetchall()]
            base = seen[-1] if seen else datetime.date.today()
            if seen:
                base = [int(_) for _ in base.split('-')]
                base = datetime.date(base[0], base[1], base[2])
            date_list = [base - datetime.timedelta(days=x) for x in range(365)]
            count = 0

            while date_list:
                try:
                    count += 1
                    seed = date_list.pop(0)
                    if seed not in seen:
                        seen.append(seed)
                        params['year'] = seed.year
                        if len(str(seed.month)) == 1:
                            params['month'] = '0' + str(seed.month)
                        else:
                            params['month'] = str(seed.month)
                        if len(str(seed.day)) == 1:
                            params['day'] = '0' + str(seed.day)
                        else:
                            params['day'] = str(seed.day)
                        self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 301)', [seed])
                        self.conn.commit()

                    resp = download(url, params=params, headers=headers, method='POST')
                    dom = BeautifulSoup(resp.content, 'lxml')

                    head = [_.text.strip() for _ in dom.select('.list_cm > li > a')]
                    for _ in range(0, len(head)):
                        self.cur.execute('INSERT INTO head(head, wdate, cdate,page, ref) VALUES(?,?,?,?,301)',
                                    [head[_], seed, str(datetime.datetime.now()).split('.')[0],
                                     0])
                        self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print(e)


    def mk(self, recent=True):
        if recent:
            url = 'https://www.mk.co.kr/news/bestclick.php?BCC=%BA%CE%B5%BF%BB%EA'
            params = {
                'NY': '2020',
                'NM': '8',
                'ND': '13'
            }
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=302 ORDER BY wdate DESC').fetchone()[0]
            seen_date = [int(_) for _ in seen_date.split('-')]
            seen_date = datetime.date(seen_date[0], seen_date[1], seen_date[2])
            base = datetime.date.today()
            date_list = [base - datetime.timedelta(days=x) for x in range(365)]
            count = 0
            varbreak = 0
            seen = list()

            while date_list:
                BOC_list = ['%B4%BA%BD%BA%C1%BE%C7%D5', '%B0%E6%C1%A6', '%B1%E2%BE%F7', '%BB%E7%C8%B8', '%B1%B9%C1%A6',
                            '%BA%CE%B5%BF%BB%EA', '%C1%F5%B1%C7', '%C1%A4%C4%A1', 'IT%B0%FA%C7%D0', '%B9%AE%C8%AD',
                            '%BF%AC%BF%B9', '%BD%BA%C6%F7%C3%F7']
                seed0 = date_list.pop(0)
                while len(BOC_list) != 0:
                    try:
                        seed1 = BOC_list.pop(0)
                        count += 1
                        if [str(seed0) + '/' + seed1] not in seen:
                            self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 302)',
                                             [str(seed0) + '/' + seed1])
                            self.conn.commit()
                            seen.append([str(seed0) + '/' + seed1])
                            params['NY'] = str(seed0.year)
                            params['NM'] = str(seed0.month)
                            params['ND'] = str(seed0.day)

                        url = urljoin(url, '?BCC={}'.format(seed1))
                        resp = download(url, params=params, method='GET')
                        dom = BeautifulSoup(resp.content, 'lxml')

                        head = [_.text.strip() for _ in dom.select('.list_area .tit > a')]
                        for _ in range(0, len(head)):
                            if seed0 > seen_date:
                                self.cur.execute('INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,302)',
                                                 [head[_], seed0, str(datetime.datetime.now()).split('.')[0],
                                                  seed1])
                                self.conn.commit()
                            else:
                                varbreak = 1
                                break
                        if varbreak == 1:
                            break

                        if count % 100 == 0:
                            print(count)

                    except Exception as e:
                        print(e)
                if varbreak == 1:
                    break
        else:
            url = 'https://www.mk.co.kr/news/bestclick.php?BCC=%BA%CE%B5%BF%BB%EA'
            params = {
                'NY': '2020',
                'NM': '8',
                'ND': '13'
            }
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=302 ORDER BY seen DESC').fetchall()]
            base = seen[-1].split('/')[0] if seen else datetime.date.today()
            if seen:
                base = [int(_) for _ in base.split('-')]
                base = datetime.date(base[0], base[1], base[2])
            date_list = [base - datetime.timedelta(days=x) for x in range(365)]
            count = 0

            while date_list:
                BOC_list = ['%B4%BA%BD%BA%C1%BE%C7%D5', '%B0%E6%C1%A6', '%B1%E2%BE%F7', '%BB%E7%C8%B8', '%B1%B9%C1%A6',
                            '%BA%CE%B5%BF%BB%EA', '%C1%F5%B1%C7', '%C1%A4%C4%A1', 'IT%B0%FA%C7%D0', '%B9%AE%C8%AD',
                            '%BF%AC%BF%B9', '%BD%BA%C6%F7%C3%F7']
                seed0 = date_list.pop(0)
                while len(BOC_list) != 0:
                    try:
                        seed1 = BOC_list.pop(0)
                        count += 1
                        if [str(seed0) + '/' + seed1] not in seen:
                            self.cur.execute('INSERT INTO history(seen, ref) VALUES(?, 302)', [str(seed0) + '/' + seed1])
                            self.conn.commit()
                            seen.append([str(seed0) + '/' + seed1])
                            params['NY'] = str(seed0.year)
                            params['NM'] = str(seed0.month)
                            params['ND'] = str(seed0.day)

                        url = urljoin(url, '?BCC={}'.format(seed1))
                        resp = download(url, params=params, method='GET')
                        dom = BeautifulSoup(resp.content, 'lxml')

                        head = [_.text.strip() for _ in dom.select('.list_area .tit > a')]
                        for _ in range(0, len(head)):
                            self.cur.execute('INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,302)',
                                        [head[_], seed0, str(datetime.datetime.now()).split('.')[0],
                                         seed1])
                            self.conn.commit()

                        if count % 100 == 0:
                            print(count)

                    except Exception as e:
                        print(e)

    def chosun(self, recent=True):
        if recent:
            seen = list()
            seen_date = [_[0] for _ in
                         self.cur.execute('SELECT seen FROM history WHERE ref=303 ORDER BY seen DESC').fetchall()]
            seen_date = re.search(r'indate=(\d+)', seen_date[0]).group(1)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
                'cookie': '_ga=GA1.2.155331207.1590371425; _ss_pp_id=6d5c749e45df5fc2e3f1588636203804; __gads=ID=32309e63460e7bec:T=1590587589:S=ALNI_MbT83O-w-NBELV4M2sBrRwfoU4ZtQ; PCID=15946360484484587904430; OAX=gIYFPF8MNw4AAKeC; __utmz=222464713.1594814175.4.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); adfit_sdk_id=27c83848-9b3d-4f52-bd4d-abbd9d93a0ef; __utma=222464713.155331207.1590371425.1594814175.1595161152.5; _td=8dc8df98-07d4-4639-aa8b-f5bcd75c27b4; _cb_ls=1; _cb=BwJni3Czf8gSDbs39n; _gid=GA1.2.780937476.1597652887; _chartbeat2=.1597235265832.1597657270138.100001.P_loMBN6GXFO-uI2DZimj6lyt7i.1; _gat=1; _gat_chosun_total=1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6'}

            # 시간변수 만들기
            start_date = datetime.datetime.strptime(seen_date, '%Y%m%d')
            end_date = datetime.datetime.today()

            str_date_list = []
            while start_date.strftime('%Y%m%d') != end_date.strftime('%Y%m%d'):
                str_date_list.append(start_date.strftime('%Y%m%d'))
                start_date += datetime.timedelta(days=1)

            url = 'https://news.chosun.com/svc/list_in/list_title.html?indate='
            urls = list()
            for i in str_date_list:
                u = url + i + '&source=1&pn=1'
                urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.content.decode('utf-8', 'replace'), 'html.parser')
                    if seen not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                            INSERT INTO history(seen, ref) VALUES(?, 303)
                        ''', [seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select('#list_body_id > div.paginate > ul > li > a')
                              if _.has_attr('href') or _.has_attr('next')]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    if dom.select('#list_body_id > div.list_content > dl > dt') != None:
                        head = [_.text.strip() for _ in dom.select('#list_body_id > div.list_content > dl > dt')]
                        wdate = [_.text.strip() for _ in
                                 dom.select('#list_body_id > div.list_content > dl > dd.date_author > span.date')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('pn=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,303)
                                    ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)
        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=303 ORDER BY seen DESC').fetchall()]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
                'cookie': '_ga=GA1.2.155331207.1590371425; _ss_pp_id=6d5c749e45df5fc2e3f1588636203804; __gads=ID=32309e63460e7bec:T=1590587589:S=ALNI_MbT83O-w-NBELV4M2sBrRwfoU4ZtQ; PCID=15946360484484587904430; OAX=gIYFPF8MNw4AAKeC; __utmz=222464713.1594814175.4.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); adfit_sdk_id=27c83848-9b3d-4f52-bd4d-abbd9d93a0ef; __utma=222464713.155331207.1590371425.1594814175.1595161152.5; _td=8dc8df98-07d4-4639-aa8b-f5bcd75c27b4; _cb_ls=1; _cb=BwJni3Czf8gSDbs39n; _gid=GA1.2.780937476.1597652887; _chartbeat2=.1597235265832.1597657270138.100001.P_loMBN6GXFO-uI2DZimj6lyt7i.1; _gat=1; _gat_chosun_total=1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6'}

            # 시간변수 만들기
            start_date = datetime.datetime.strptime('20190817', '%Y%m%d')
            end_date = datetime.datetime.strptime(re.search(r'indate=(\d+)', seen[-1]).group(1),
                                         '%Y%m%d') if seen else datetime.datetime.today()

            str_date_list = []
            while start_date.strftime('%Y%m%d') != end_date.strftime('%Y%m%d'):
                str_date_list.append(start_date.strftime('%Y%m%d'))
                start_date += datetime.timedelta(days=1)

            url = 'https://news.chosun.com/svc/list_in/list_title.html?indate='
            urls = list()
            for i in str_date_list:
                u = url + i + '&source=1&pn=1'
                urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.content.decode('utf-8', 'replace'), 'html.parser')
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                            INSERT INTO history(seen, ref) VALUES(?, 303)
                        ''', [seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select('#list_body_id > div.paginate > ul > li > a')
                              if _.has_attr('href') or _.has_attr('next')]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    if dom.select('#list_body_id > div.list_content > dl > dt') != None:
                        head = [_.text.strip() for _ in dom.select('#list_body_id > div.list_content > dl > dt')]
                        wdate = [_.text.strip() for _ in
                                 dom.select('#list_body_id > div.list_content > dl > dd.date_author > span.date')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('pn=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,303)
                                    ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

    def digital_times(self, recent=True):
        if recent:
            seen = list()
            seen_date = [_[0] for _ in
                    self.cur.execute('SELECT seen FROM history WHERE ref=304 ORDER BY seen DESC').fetchall()]
            seen_date = re.search(r'p_date=([\d+-]+)', seen_date[0]).group(1)
            seen_date = ''.join(seen_date.split('-'))
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'
            }
            params = {
                '__VIEWSTATE': '/wEPDwULLTEyMTI4MTYxMjIPZBYCAgMPZBYCAgEPDxYCHgRUZXh0BQwyMDIwLiAwOC4gMThkZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUGc2VhcmNomyRP70CWd1D8LnYgMGWG5YGgBBk=',
                '__VIEWSTATEGENERATOR': '8903B0C1',
                '__EVENTVALIDATION': '/wEWAwK95sj+CgK4y9eRBwLH0pL8CYEABvtNhMvEhlw5kV7Y98D0eTOW',
                'actionURL': 'http://www.dt.co.kr/eyescrap/eyescrapAction.html',
                # 'p_date': '2020-08-13'
            }

            # 시간변수 만들기
            start_date = datetime.datetime.strptime(seen_date, '%Y%m%d')
            end_date = datetime.datetime.today()

            str_date_list = []
            while start_date.strftime('%Y-%m-%d') != end_date.strftime('%Y-%m-%d'):
                str_date_list.append(start_date.strftime('%Y-%m-%d'))
                start_date += datetime.timedelta(days=1)

            url = 'http://papers.eyescrap.com/dt/list.aspx?actionURL=http%3a%2f%2fwww.dt.co.kr%2feyescrap%2feyescrapAction.html&p_date='  # 주소 합치는거 고치기
            urls = list()
            for i in str_date_list:
                u = url + i
                urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, params=params, headers=headers, method='GET')
                    dom = BeautifulSoup(resp.text, 'html.parser')
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                                        INSERT INTO history(seen, ref) VALUES(?, 304)
                                    ''', [seed])
                        self.conn.commit()

                    if dom.select(
                            '#form1 > table > tr > td > table > tr > td > table > tr > td > table > tr > td > a') != None:
                        head = [_.text.strip() for _ in dom.select(
                            '#form1 > table > tr > td > table > tr > td > table > tr > td > table > tr > td > a')
                                if _.text.strip() != '' and _.text.strip() != '[광고]' and _.select('b') == []]
                        wdate = re.search('p_date=(\d+-\d+-\d+)', urlparse(seed).query).group(1)
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = '1'
                        for _ in range(0, len(head)):
                            self.cur.execute('''
                                            INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,304)
                                            ''', [head[_], wdate, cdate, page])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

        else:
            seen = [_[0] for _ in self.cur.execute('SELECT seen FROM history WHERE ref=304 ORDER BY seen DESC').fetchall()]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'
            }
            params = {
                '__VIEWSTATE': '/wEPDwULLTEyMTI4MTYxMjIPZBYCAgMPZBYCAgEPDxYCHgRUZXh0BQwyMDIwLiAwOC4gMThkZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUGc2VhcmNomyRP70CWd1D8LnYgMGWG5YGgBBk=',
                '__VIEWSTATEGENERATOR': '8903B0C1',
                '__EVENTVALIDATION': '/wEWAwK95sj+CgK4y9eRBwLH0pL8CYEABvtNhMvEhlw5kV7Y98D0eTOW',
                'actionURL': 'http://www.dt.co.kr/eyescrap/eyescrapAction.html',
                # 'p_date': '2020-08-13'
            }

            # 시간변수 만들기
            start_date = datetime.datetime.strptime('2019-08-17', '%Y-%m-%d')
            end_date = datetime.datetime.strptime(''.join(re.search(r'p_date=([\d+-]+)', seen[-1]).group(1).split('-')),
                                                  '%Y%m%d') if seen else datetime.datetime.today()
            str_date_list = []
            while start_date.strftime('%Y-%m-%d') != end_date.strftime('%Y-%m-%d'):
                str_date_list.append(start_date.strftime('%Y-%m-%d'))
                start_date += datetime.timedelta(days=1)

            url = 'http://papers.eyescrap.com/dt/list.aspx?actionURL=http%3a%2f%2fwww.dt.co.kr%2feyescrap%2feyescrapAction.html&p_date='  # 주소 합치는거 고치기
            urls = list()
            for i in str_date_list:
                u = url + i
                urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, params=params, headers=headers, method='GET')
                    dom = BeautifulSoup(resp.text, 'html.parser')
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                            INSERT INTO history(seen, ref) VALUES(?, 304)
                        ''', [seed])
                        self.conn.commit()

                    if dom.select(
                            '#form1 > table > tr > td > table > tr > td > table > tr > td > table > tr > td > a') != None:
                        head = [_.text.strip() for _ in dom.select(
                            '#form1 > table > tr > td > table > tr > td > table > tr > td > table > tr > td > a')
                                if _.text.strip() != '' and _.text.strip() != '[광고]' and _.select('b') == []]
                        wdate = re.search('p_date=(\d+-\d+-\d+)', urlparse(seed).query).group(1)
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = '1'
                        for _ in range(0, len(head)):
                            self.cur.execute('''
                                INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,304)
                                ''', [head[_], wdate, cdate, page])
                            self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

    def donga(self, recent=True):
        if recent:
            seen = list()
            seen_date = [_[0] for _ in
                    self.cur.execute('SELECT seen FROM history WHERE ref=305 ORDER BY seen DESC').fetchall()]
            seen_date = re.search(r'ymd=([\d+-]+)', seen_date[0]).group(1)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}

            # 시간변수 만들기
            start_date = datetime.datetime.strptime(seen_date, '%Y%m%d')
            end_date = datetime.datetime.today()

            str_date_list = []
            while start_date.strftime('%Y%m%d') != end_date.strftime('%Y%m%d'):
                str_date_list.append(start_date.strftime('%Y%m%d'))
                start_date += datetime.timedelta(days=1)

            url = 'https://www.donga.com/news/List?p=1&prod=news&ymd='  # 주소 합치는거 고치기
            urls = list()
            for i in str_date_list:
                u = url + i + '&m='
                urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.content.decode('utf-8', 'replace'), 'html.parser')
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                                        INSERT INTO history(seen, ref) VALUES(?, 305)
                                    ''', [seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select('#content > div.page > a')
                              if _.has_attr('href') or _.has_attr('right on')]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    if dom.select('#list_body_id > div.list_content > dl > dt') != None:
                        head = [_.text.strip() for _ in dom.select('#content > div > div.rightList > a > span.tit')]
                        wdate = [_.text.strip() for _ in dom.select('#content > div > div > a > span.date')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('p=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                                INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,305)
                                                ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

        else:
            seen = [_[0] for _ in
                    self.cur.execute('SELECT seen FROM history WHERE ref=305 ORDER BY seen DESC').fetchall()]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}

            # 시간변수 만들기
            start_date = datetime.datetime.strptime('20190817', '%Y%m%d')
            end_date = datetime.datetime.strptime(re.search(r'ymd=([\d+-]+)', seen[-1]).group(1),
                                                  '%Y%m%d') if seen else datetime.datetime.today()

            str_date_list = []
            while start_date.strftime('%Y%m%d') != end_date.strftime('%Y%m%d'):
                str_date_list.append(start_date.strftime('%Y%m%d'))
                start_date += datetime.timedelta(days=1)

            url = 'https://www.donga.com/news/List?p=1&prod=news&ymd='  # 주소 합치는거 고치기
            urls = list()
            for i in str_date_list:
                u = url + i + '&m='
                urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.content.decode('utf-8', 'replace'), 'html.parser')
                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                            INSERT INTO history(seen, ref) VALUES(?, 305)
                        ''', [seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select('#content > div.page > a')
                              if _.has_attr('href') or _.has_attr('right on')]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    if dom.select('#list_body_id > div.list_content > dl > dt') != None:
                        head = [_.text.strip() for _ in dom.select('#content > div > div.rightList > a > span.tit')]
                        wdate = [_.text.strip() for _ in dom.select('#content > div > div > a > span.date')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('p=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,305)
                                    ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

    def SBS(self, recent=True):
        if recent:
            seen = list()
            seen_date = [_[0] for _ in
                    self.cur.execute('SELECT seen FROM history WHERE ref=306 ORDER BY seen DESC').fetchall()]
            seen_date = re.search(r'pageDate=([\d+-]+)', seen_date[0]).group(1)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}

            # 시간변수 만들기, 시작날짜 종료날짜 정하기
            start_date = datetime.datetime.strptime(seen_date, '%Y%m%d')
            end_date = datetime.datetime.today()

            str_date_list = []
            while start_date.strftime('%Y%m%d') != end_date.strftime('%Y%m%d'):
                str_date_list.append(start_date.strftime('%Y%m%d'))
                start_date += datetime.timedelta(days=1)

            url = 'https://news.sbs.co.kr/news/newsflash.do?pageDate='  # 주소 합치는거 고치기
            urls = list()
            for i in str_date_list:
                for k in range(40):
                    u = url + i + '&pageIdx=' + str(k + 1)
                    urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.content.decode('utf-8', 'replace'), 'html.parser')
                    if seed not in seen:
                        seen.append(seed)
                        if len(dom.select(
                                '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > span.date')) != 0:
                            self.cur.execute('''
                                            INSERT INTO history(seen, ref) VALUES(?, 306)
                                        ''', [seed])
                            self.conn.commit()

                    if len(dom.select(
                            '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > span.date')) != 0:
                        head = [_.text.strip() for _ in dom.select(
                            '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > strong')]
                        wdate = [_.text.strip() for _ in dom.select(
                            '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > span.date')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('pageIdx=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                                INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,306)
                                                ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()
                    else:
                        date = re.search('pageDate=(\d+)', urlparse(seed).query).group(1)
                        while date == re.search('pageDate=(\d+)', urlparse(urls[0]).query).group(1):
                            urls.pop(0)

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

        else:
            seen = [_[0] for _ in
                    self.cur.execute('SELECT seen FROM history WHERE ref=306 ORDER BY seen DESC').fetchall()]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}

            # 시간변수 만들기, 시작날짜 종료날짜 정하기
            start_date = datetime.datetime.strptime('20190817', '%Y%m%d')
            end_date = datetime.datetime.strptime(re.search(r'pageDate=([\d+-]+)', seen[-1]).group(1),
                                                  '%Y%m%d') if seen else datetime.datetime.today()

            str_date_list = []
            while start_date.strftime('%Y%m%d') != end_date.strftime('%Y%m%d'):
                str_date_list.append(start_date.strftime('%Y%m%d'))
                start_date += datetime.timedelta(days=1)

            url = 'https://news.sbs.co.kr/news/newsflash.do?pageDate='  # 주소 합치는거 고치기
            urls = list()
            for i in str_date_list:
                for k in range(40):
                    u = url + i + '&pageIdx=' + str(k + 1)
                    urls.append(u)

            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(-1)

                    resp = download(seed, headers=headers)
                    dom = BeautifulSoup(resp.content.decode('utf-8', 'replace'), 'html.parser')
                    if seed not in seen:
                        seen.append(seed)
                        if len(dom.select(
                                '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > span.date')) != 0:
                            self.cur.execute('''
                                INSERT INTO history(seen, ref) VALUES(?, 306)
                            ''', [seed])
                            self.conn.commit()

                    if len(dom.select(
                            '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > span.date')) != 0:
                        head = [_.text.strip() for _ in dom.select(
                            '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > strong')]
                        wdate = [_.text.strip() for _ in dom.select(
                            '#container > div > div.w_news_list.type_issue > ul > li > a.news > p > span.date')]
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('pageIdx=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(wdate):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,306)
                                    ''', [head[_], wdate[_], cdate, page])
                                self.conn.commit()
                    else:
                        date = re.search('pageDate=(\d+)', urlparse(seed).query).group(1)
                        while date == re.search('pageDate=(\d+)', urlparse(urls[0]).query).group(1):
                            urls.pop(0)

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

    def hankyung(self, recent=True):
        if recent:
            seen = list()
            seen_date = self.cur.execute('SELECT wdate FROM head WHERE ref=307 ORDER BY wdate DESC').fetchone()[0]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
                'Cookie': 'dable_uid=56241276.1588668566321; __gads=ID=32ec6ccd891b6cb1:T=1588668565:S=ALNI_Mb-cg_Eg1b8md7cdvKumpaG3T20ww; gtmdlkr=; _gid=GA1.2.295727024.1597748733; onlytitle=check; _gat_UA-109163096-1=1; _gat_UA-109163096-3=1; _gat_UA-136144676-1=1; _ga_PBVPGVW46M=GS1.1.1597748731.3.1.1597749317.0; _ga=GA1.2.402869033.1588668573'
            }
            params = {
                'page': '1'
            }

            url = 'https://www.hankyung.com/all-news/?page=1'

            urls = list()
            urls.append(url)
            count = 0
            varbreak=0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)

                    params['page'] = re.search('page=(\d+)', urlparse(seed).query).group(1)
                    resp = download(seed, params=params, headers=headers, method='GET')
                    dom = BeautifulSoup(resp.text, 'html.parser')

                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                                        INSERT INTO history(seen, ref) VALUES(?, 307)
                                    ''', [seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.paging > a')[
                                                 2:-1]]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    if dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div > h3 > a') != None:
                        head = [_.text.strip() for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div > h3 > a')]
                        date = [re.search('(\d{8})', _['href']).group(1) for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div > h3 > a')]
                        time = [_.text.strip() for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div.txt > p.time')]
                        t = list()
                        for i in range(len(date)):
                            t.append(date[i] + ' ' + time[i])
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('page=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(t):
                            for _ in range(0, len(head)):
                                if t[_]> seen_date:
                                    self.cur.execute('''
                                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,307)
                                                    ''', [head[_], t[_], cdate, page])
                                    self.conn.commit()
                                else:
                                    varbreak=1
                                    break
                            if varbreak == 1:
                                break

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)

        else:
            seen = [_[0] for _ in
                    self.cur.execute('SELECT seen FROM history WHERE ref=307 ORDER BY seen DESC').fetchall()]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
                'Cookie': 'dable_uid=56241276.1588668566321; __gads=ID=32ec6ccd891b6cb1:T=1588668565:S=ALNI_Mb-cg_Eg1b8md7cdvKumpaG3T20ww; gtmdlkr=; _gid=GA1.2.295727024.1597748733; onlytitle=check; _gat_UA-109163096-1=1; _gat_UA-109163096-3=1; _gat_UA-136144676-1=1; _ga_PBVPGVW46M=GS1.1.1597748731.3.1.1597749317.0; _ga=GA1.2.402869033.1588668573'
                }
            params = {
                'page': '1'
            }

            url = seen[0] if seen else 'https://www.hankyung.com/all-news/?page=1'

            urls = list()
            urls.append(url)
            count = 0

            while urls:
                try:
                    count += 1
                    seed = urls.pop(0)

                    params['page'] = re.search('page=(\d+)', urlparse(seed).query).group(1)
                    resp = download(seed, params=params, headers=headers, method='GET')
                    dom = BeautifulSoup(resp.text, 'html.parser')

                    if seed not in seen:
                        seen.append(seed)
                        self.cur.execute('''
                            INSERT INTO history(seen, ref) VALUES(?, 307)
                        ''', [seed])
                        self.conn.commit()

                    for _ in [_['href'] for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.paging > a')[
                                                 2:-1]]:
                        newUrls = urljoin(seed, _)
                        if newUrls not in urls and newUrls not in seen:
                            urls.append(newUrls)

                    if dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div > h3 > a') != None:
                        head = [_.text.strip() for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div > h3 > a')]
                        date = [re.search('(\d{8})', _['href']).group(1) for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div > h3 > a')]
                        time = [_.text.strip() for _ in dom.select(
                            '#container > div.contents_wrap > div.contents > div.article_content > div.daily_article > div > ul > li > div.txt > p.time')]
                        t = list()
                        for i in range(len(date)):
                            t.append(date[i] + ' ' + time[i])
                        cdate = str(datetime.datetime.now()).split('.')[0]
                        page = re.search('page=(\d+)', urlparse(seed).query).group(1)
                        if len(head) == len(t):
                            for _ in range(0, len(head)):
                                self.cur.execute('''
                                    INSERT INTO head(head, wdate, cdate, page, ref) VALUES(?,?,?,?,307)
                                    ''', [head[_], t[_], cdate, page])
                                self.conn.commit()

                    if count % 100 == 0:
                        print(count)

                except Exception as e:
                    print('Error', e)