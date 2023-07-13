import re

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

tqdm.pandas()


def get_item_list(info: list) -> list:
    """
    Provide all attributes that appeared in any of urls.
    :param info: List of dictionaries with cars info.
    :return: List of unique keys that appeared in any of urls.
    """
    all_keys = [item.keys() for item in info]
    flat_list = []
    for sublist in all_keys:
        for item in sublist:
            flat_list.append(item)
    return list(set(flat_list))


def get_links(url: str, max_pages: int = 100) -> list:
    """
    Collect links to cars from main page / filtered main page.
    :param url: Url to scrap.
    :param max_pages: Maximum pages to scrap.
    :return: List of links with cars.
    """
    all_pages = []
    i = 1
    while i <= max_pages:
        response = requests.get(url.format(i))
        soup = BeautifulSoup(response.text, 'lxml')
        boxes = [item.a.attrs['href'] for item in soup.find_all('h2') if item.a is not None]
        all_pages.extend(boxes)
        i += 1
    return list(set(all_pages))


def get_car_info(url: str) -> dict:
    """
    Collect information about car from provided url.
    :param url: Url to the car.
    :return: Dictionary with collected info about the car.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    attrs = [item.span.text for item in soup.find_all('li', class_='offer-params__item')]
    values = [item.div.a.text.strip() if item.div.a is not None else item.div.text.strip() for item in
              soup.find_all('li', class_='offer-params__item')
              ]

    car_info = dict(zip(attrs, values))
    try:
        price = int(soup.find_all('span', class_='offer-price__number')[0].text.replace('PLN', '').replace(' ', ''))
        location = soup.find_all('a', class_="seller-card__links__link__cta")[0].text.strip()

        car_info['Cena'] = price
        car_info['Lokalizacja'] = location
    except:
        print(url)
    car_info['Url'] = url
    return car_info


def change_value_type(x: str, regex: str, desired_type: type):
    """
    If column should be numerical but contains some string value,
    reformat it to correct form/
    :param x: Provided value
    :param regex: Regular expression to replace to get actual type
    :param desired_type: Desired type of value
    :return:
    """
    try:
        x = desired_type(re.sub(regex, '', str(x)))
    except (TypeError, ValueError):
        x = np.nan
    return x


def main():
    url = "https://www.otomoto.pl/osobowe/seg-city-car--seg-mini/od-2003?search%5Bfilter_enum_damaged%5D=0&search%5Bfilter_float_mileage%3Ato%5D=200000&search%5Bfilter_float_price%3Ato%5D=15000&page={}&search%5Badvanced_search_expanded%5D=true"
    links = get_links(url, max_pages=100)

    # get cars info
    cars_info = []
    for url in tqdm(links):
        cars_info.append(get_car_info(url))

    car_attrs = get_item_list(cars_info)

    cars_dict = {}
    for attr in car_attrs:
        info_list = []
        for car_info in cars_info:
            info_list.append(car_info.get(attr))
        cars_dict[attr] = info_list

    # Create df and clean
    df = pd.DataFrame(cars_dict)

    df[sorted(df.columns)].to_excel('../data/cars_raw.xlsx', index=False)

    # define columns to refactor and refactor them
    cols = ['Przebieg', 'Pojemność skokowa', 'Liczba drzwi', 'Liczba miejsc', 'Rok produkcji', 'Moc']
    regexs = ['km|\s', 'cm3|\s', '', '', '', 'KM|\s']
    fill_nas = [True, True, False, False, False, True]

    for col, regex, fill_na in zip(cols, regexs, fill_nas):
        df[col] = df[col].apply(lambda x: change_value_type(x, regex, int))
        if fill_na:
            df[col] = df[col].fillna(df[col].mean()).astype(int)

    df[sorted(df.columns)].to_excel('../data/cars.xlsx', index=False)


if __name__ == '__main__':
    main()
