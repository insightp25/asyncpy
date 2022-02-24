from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.models import mongodb
from app.models.book import BookModel
from app.book_scraper import NaverBookScraper

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # book = BookModel(keyword="파이썬", publisher="비제이퍼블릭", price=15000, image="mi.png")
    # print(await mongodb.engine.save(book))  # DB에 저장
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "콜렉터 붘붘이"}
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str):
    keyword = request.query_params.get("q")  # 쿼리에서 키워드 추출
    if not keyword:  # 키워드가 없다면 사용자에게 검색을 요구
        context = {"request": request}
        return templates.TemplateResponse("index.html", context=context)
    if await mongodb.engine.find_one(BookModel, BookModel.keyword == keyword):
        # 키워드에 대해 수집된 데이터가 DB에 존재한다면 해당 데이터를 사용자에게 보여준다.
        books = await mongodb.engine.find(BookModel, BookModel.keyword == keyword)
        context = {"request": request, "keyword": keyword, "books": books}
        return templates.TemplateResponse("index.html", context=context)
    naver_book_scraper = NaverBookScraper()  # 수집기 인스턴스
    books = await naver_book_scraper.search(keyword, 10)  # 데이터 수집
    book_models = []
    for book in books:  # 수집된 각각의 데이터에 대해서 DB에 들어갈 모델 인스턴스를 찍는다.
        book_model = BookModel(
            keyword=keyword,
            publisher=book["publisher"],
            price=book["price"],
            image=book["image"],
        )
        book_models.append(book_model)
    await mongodb.engine.save_all(book_models)  # 각 모델 인스턴스를 DB에 저장한다.
    context = {"request": request, "keyword": keyword, "books": books}
    return templates.TemplateResponse("index.html", context=context)

    # 3. DB에 수집된 데이터를 저장한다.
    # - 수집된 각각의 데이터에 대해서 DB에 들어갈 모델 인스턴스를 찍는다.
    # - 각 모델 인스턴스를 DB에 저장한다.

    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "콜렉터 붘붘이", "keyword": q}
    )


@app.on_event("startup")
def on_app_start():
    """befor app starts"""
    mongodb.connect()


@app.on_event("shutdown")
def on_app_shutdown():
    """after app shutdown"""
    mongodb.close()
