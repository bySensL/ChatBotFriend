import httpx


class OWMClient:
    def __init__(self, token):
        """
        self.base_url - базовый url, одинаковый для всех запросов
        self.token - токен доступа, заполняется из аргумента конструктора token
        self.client - асинхронный сетевой клиент, через него будем делать запросы
        """

        self.base_url = 'https://api.openweathermap.org'
        self.token = token
        self.client = httpx.AsyncClient()

    async def make_request(self, url: str, params: dict):
        """
        метод для запросов к API

        :param url: параметр с путем, куда нужно сделать запрос (/data/2.5/weather)
        :param params: словарь параметров запроса, то что будет после ? (?lat=123,lon=321)
        """

        url = self.base_url + url
        resp = await self.client.get(url, params=params)
        return resp.json()

    # /data/2.5/weather?lat=41.721927&lon=44.769648&appid=token&lang=RU&units=metric
    async def get_current_data(self, lat: float, lng: float):
        params = {
            'lat': lat,
            'lon': lng,
            'appid': self.token,
            'lang': 'RU',
            'units': 'metric'
        }

        return await self.make_request('/data/2.5/weather', params)

    async def geocode_cities(self, city_name: str, country: str):
        params = {
            'q': f'{city_name},{country}',
            'limit': 3,
            'appid': self.token,
        }

        return await self.make_request('/geo/1.0/direct', params)