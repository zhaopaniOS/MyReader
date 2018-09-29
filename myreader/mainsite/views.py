# encoding: utf-8

from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.core.files.base import ContentFile
from django.urls import reverse
from .models import Book, Chapter, BookOriginalSource
import json
import re
import requests
from bs4 import BeautifulSoup
import datetime

# Create your views here.
def homepage(request):
    template = get_template('index.html')
    books = Book.objects.all()
    html = template.render(locals())
    return HttpResponse(html)

def book(request, bookid):
    template = get_template('book.html')
    try:
        book = Book.objects.get(id=bookid)
        chapters = Chapter.objects.filter(book=book).order_by('section')
        html = template.render(locals())
        return HttpResponse(html)
    except:
        return HttpResponseNotFound()

def book_section(request, bookid, section):
    template = get_template('book_section.html')
    try:
        book = Book.objects.get(id=bookid)
        chapter = Chapter.objects.get(book=book, section=section)
        max = Chapter.objects.filter(book=book).order_by('-section')[0]

        home_url = reverse('book_url', args=(bookid,))
        if section == 0:
            prev_url = home_url
        else:
            prev_url = reverse('book_section_url', args=(bookid, section - 1,))

        if section == max.section:
            next_url = home_url
        else:
            next_url = reverse('book_section_url', args=(bookid, section + 1,))

        html = template.render(locals())
        return HttpResponse(html)
    except Exception as e:
        print(str(e))
        return HttpResponseNotFound()

def book_manager(request):
    template = get_template('book_manager.html')
    sources = BookOriginalSource.objects.all()
    html = template.render(locals())
    return HttpResponse(html)

def book_manager_source(request, sourceid):
    template = get_template('book_manager_source.html')
    try:
        source = BookOriginalSource.objects.get(id=sourceid)
        current = 0
        # 如果没有book信息，则请求源url创建
        book = Book.objects.filter(title=source.book_name,author=source.author)
        if not book:
            res = requests.get(source.url)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "html.parser")
                book = Book()
                book.title = soup.head.find("meta", property="og:novel:book_name")["content"]
                book.author = soup.head.find("meta", property="og:novel:author")["content"]
                book.desc = soup.head.find("meta", property="og:description")["content"]
                image = soup.head.find("meta", property="og:image")["content"]
                img_res = requests.get(image)
                if img_res.status_code == 200:
                    book.poster.save(book.title+".jpg", ContentFile(img_res.content))
                book.tag = soup.head.find("meta", property="og:novel:category")["content"]
                book.status = soup.head.find("meta", property="og:novel:status")["content"]
                book.latest = 0
                book.updated = datetime.datetime.now(tz=timezone.utc)
                book.save()
        else:
            book = book[0]
            if book.latest and type(book.latest) == int:
                current = book.latest + 1

        res = requests.get(source.all)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            div_tag = soup.find("div", id="chapterlist")

            a_tags = div_tag.find_all("a", href=re.compile("^/"))
            a_links = []
            sa = requests.utils.urlparse(source.all)
            for a_tag in a_tags:
                a_links.append({
                    'href': sa.scheme + '://' + sa.netloc + a_tag['href'],
                    'title': a_tag.string
                })

        html = template.render(locals())
        return HttpResponse(html)
    except Exception as exp:
        print(str(exp))
        return HttpResponseNotFound()

def get_chapter_content(href):
    sa = requests.utils.urlparse(href)
    res = requests.get(href)
    if res.status_code == 200:
        soup = BeautifulSoup(res.content, "html.parser")
        div_tag = soup.find("div", id="chaptercontent")

        # 移除chaptercontent下边的子节点，修正br
        for child in div_tag.children:
            if child and child.name:
                if child.name != 'br':
                    child.decompose()

        # 删除属性class、style
        del div_tag['class']
        del div_tag['style']

        # 意外情况，有分页
        a_tag = soup.find("a", string=re.compile("下一页"))
        if a_tag:
            next_page = sa.scheme + "://" + sa.netloc + a_tag['href']
            return (div_tag, next_page)

        return (div_tag, None)

    return (None, None)

def copy_div_tag_to_another(div_tag, next_tag):
    for child in next_tag.children:
        div_tag.append(child.extract())

def get_all_chapter_content(href):
    div_tag, next_page = get_chapter_content(href)
    if not div_tag:
        return None
    if not next_page:
        return div_tag
    while True:
        tmp_div_tag, tmp_next_page = get_chapter_content(next_page)
        if not tmp_div_tag:
            break
        # copy to div_tag
        copy_div_tag_to_another(div_tag, tmp_div_tag)
        # check if continue
        if not tmp_next_page:
            break
        next_page = tmp_next_page
    return div_tag

def book_manager_source_section(request, sourceid, section):
    # 这里请求的是json
    if request.method == 'POST':
        try:
            content_type = request.META.get('CONTENT_TYPE', '')
            json_data = None
            if content_type.startswith('application/json'):
                json_data = request.body
            else:
                json_data = json.dumps(request.POST)

            request_body = json_data
            if isinstance(request_body, (bytes,)):
                request_body = request_body.decode('utf-8')
            jsonobj = json.loads(request_body)

            href = jsonobj['href']
            title = jsonobj['title']

            div_tag = get_all_chapter_content(href)
            if div_tag:
                content = div_tag.prettify()
                if not content or len(content) < 35:
                    return JsonResponse({'code': 500, 'msg': '源文件正文内容不正常，请手动核实'})

                # 构建数据库对象
                source = BookOriginalSource.objects.get(id=sourceid)
                book = Book.objects.get(title=source.book_name, author=source.author)

                chapter, created = Chapter.objects.get_or_create(book=book, section=section)
                if created:
                    # means you have created a new person
                    chapter.book = book
                    chapter.title = title
                    chapter.section = section
                    chapter.content = content
                    chapter.save()
                else:
                    # just refers to the existing one
                    chapter.title = title
                    chapter.content = content
                    chapter.save()

                # 同步更新book
                book.latest = section
                book.updated = datetime.datetime.now(tz=timezone.utc)
                book.save()
                return JsonResponse({'code': 200, 'msg': 'success'})

        except Exception as exp:
            print(str(exp))
            return HttpResponseBadRequest()

    return HttpResponseNotFound()