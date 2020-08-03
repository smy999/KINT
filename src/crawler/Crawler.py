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
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=3').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=3').fetchall()]
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

                    for _ in [_['href'] for _ in dom.select('div.bottom_paging_box > a')
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

                    for _ in [_['href'] for _ in dom.select('div.bottom_paging_box > a')
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
        cdate = [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=6').fetchall()] if teen else [_[0] for _ in self.cur.execute('SELECT cdate FROM head WHERE ref=7').fetchall()]
        wdate = [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=6').fetchall()] if teen else [_[0] for _ in self.cur.execute('SELECT wdate FROM head WHERE ref=7').fetchall()]
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