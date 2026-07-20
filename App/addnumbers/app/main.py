from fastapi import FastAPI
from fastapi.responses import JSONResponse

app=FastAPI()

@app.get("/")
def homepage():
    return {"Hello": "World"}

@app.get("/add/{num1}/{num2}")
def add(num1:int, num2:int):
    return JSONResponse({'Sum':num1+num2})